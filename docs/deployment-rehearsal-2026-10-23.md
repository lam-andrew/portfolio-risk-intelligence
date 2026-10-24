# Deployment rehearsal — October 23, 2026 (PDT)

Phase A rehearsal of [ADR 0028](adr/0028-self-hosted-private-deployment.md) on the development
Mac, before any VM exists. The scripts, Compose file and images are the ones in this PR. This
proves the procedure, not the homelab: OptiPlex capacity, Tailscale Serve, systemd timers and
off-host copies come in Phase B and C.

## Setup

- Images: production targets built for **linux/amd64** (emulated on Apple Silicon), pushed to a
  throwaway local registry, and deployed **by digest** exactly as from GHCR.
- Separate Compose project `orbit-rehearsal`, loopback port 8090, its own volumes. The
  development preview and its data weren't touched.
- Settings: random database password; obviously fake provider keys (no provider calls made).
  Backups were encrypted to a test-only age key. Settings and keys were kept outside the
  repository and deleted afterwards.
- Rehearsal-only images: release 2 adds a harmless migration (`0009_rehearsal`, creates
  one table). Release 3 is release 1's code. Release 4 is release 2 with an API that never
  becomes healthy. None of them is committed.

## Results

| # | Scenario | Result |
|---|---|---|
| 1 | Release file with a tag instead of a digest | Refused before any change |
| 2 | One-time model provisioning | Checksum-pinned BGE-small verified |
| 3 | Fresh deploy (release 1) | Empty database migrated to 0008, healthy in 35 s. `/api/health` reports `environment: production`. Web 200 |
| 4 | Exposure | Only the web proxy publishes a port, on 127.0.0.1. `data` and `inference` networks are internal (no route out) |
| 5 | Secure session cookie over plain HTTP | Registration 201; wrong password 401. Browser sign-in requires HTTPS, which Tailscale Serve provides |
| 6 | Encrypted backup | `age` file, mode 600, ~30 KB for 3 test users |
| 7 | Restore verification | Scratch copy matched live: schema 0008, 3 users. Scratch database dropped. Without the key: refused before touching the database (after a fix) |
| 8 | Deploy with migration (release 2) | Pre-deploy backup, migration 0008 → 0009, healthy in 34 s, `previous` = release 1 |
| 9 | Release older than the schema (release 3) | Migration step refused; release 2 kept running unchanged |
| 10 | Unhealthy release (release 4) | Rolled back to release 2 automatically, non-zero exit, state unchanged (after fix) |
| 11 | `--rollback` to release 1 on schema 0009 | Refused with "restore the pre-deploy dump first"; release 2 kept serving (after fix) |
| 12 | Live restore of the pre-deploy dump, then `--rollback` | Schema back to 0008, migration table gone, release 1 healthy, `failed.env` = release 2 |
| 13 | Redeploy the running release | Healthy, state unchanged (after fix) |
| 14 | API process exits | Restarted by Docker (restart count 1) and healthy again. A manual `docker kill` is, by design, not restarted |

Idle memory with no filings loaded: database 88 MiB, encoder 249 MiB, workers 74–82 MiB,
web 23 MiB. All are well under their limits, but these aren't peak figures.

## Defects found and fixed before the PR

1. `docker compose up` fails when a dependency turns unhealthy, and `set -e` then ended
   `deploy.sh` before its rollback branch. Start-and-verify now runs as a condition, so
   rollback always runs (scenario 10 failed before the fix and passed after).
2. `--rollback` to a release that predates the current schema failed with Compose output only.
   It now checks first and gives the recovery step (scenario 11).
3. Redeploying the running release copied `current.env` onto itself and left `previous`
   wrong. State now rotates only when the release changes (scenario 13).
4. `restore.sh` created and dropped its scratch database before noticing a missing key; it
   now checks first.
5. A failed image pull ended the script silently; it now says so.

## Not covered here

The amd64 timings are emulated; real figures come from the OptiPlex benchmark in Phase B.
Also deferred to Phases B–C: the CI publishing workflow's first real run, GHCR read tokens,
Tailscale Serve and HTTPS sign-in, the systemd backup timer, off-host pulls and Kuma alerts.
