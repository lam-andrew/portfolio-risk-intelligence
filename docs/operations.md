# Operations runbook — self-hosted Orbit

How to deploy, roll back, back up and restore Orbit on its homelab VM ([ADR 0028](adr/0028-self-hosted-private-deployment.md)).
Status: **scripts rehearsed locally; not yet deployed to the VM.** Network addresses,
credentials and personal data never belong in this file.

## Layout on the VM

| Path | Contents | Owner / mode |
|---|---|---|
| `/srv/orbit` | A clone of this repository at the release commit (Compose file, `db/init`, `deploy/`) | root |
| `/etc/orbit/orbit.env` | Secrets and settings, from [`deploy/orbit.env.example`](../deploy/orbit.env.example) | root, 600 |
| `/etc/orbit/backup-recipients.txt` | age **public** key(s) for backups | root, 644 |
| `/var/lib/orbit/{current,previous}.env` | The running release and the one before it | root |
| `/var/backups/orbit/{daily,weekly}` | Encrypted dumps | root, 700 |

Docker volumes: `orbit_db_data` (database) and `orbit_encoder_models` (pinned model, reproducible).

## Releases

CI ([`release-images.yml`](../.github/workflows/release-images.yml)) builds amd64 images on
pushes to `main` (release) and to the #92 integration branch (pre-release), fails on fixable
critical vulnerabilities, pushes to GHCR, and attaches `release.env` with digest-pinned images.
Download that artifact to the VM as `/srv/orbit/releases/<sha>.env`.

## First install (once)

1. Install Docker Engine, the Compose plugin and `age`; log Docker in to GHCR with a read-only
   package token (Orbit's packages only).
2. Clone the repository to `/srv/orbit`, check out the release commit, create `/etc/orbit/orbit.env`.
3. `deploy/deploy.sh --provision-model releases/<sha>.env` (one-time checksum-pinned download).
4. `deploy/deploy.sh releases/<sha>.env`.
5. `tailscale serve --bg --https=443 http://127.0.0.1:8080` and check `https://<vm>.<tailnet>.ts.net/api/health`.

## Deploy

```bash
cd /srv/orbit && git fetch && git checkout <sha>
deploy/deploy.sh releases/<sha>.env
```

The script refuses images that aren't pinned by digest. It takes a pre-deploy backup, runs
migrations as a one-shot service (a failure leaves the running release untouched), starts the
stack and waits up to 120 s for container health and `/api/health`. If the new release isn't
healthy, it restarts the previous one automatically and exits non-zero.

## Roll back

`deploy/deploy.sh --rollback` restarts the previous release. The script prints the schema
revision. If the failed release had migrated the schema and the old code misbehaves, restore the
pre-deploy dump (below).

## Backups

`deploy/backup.sh` runs nightly from a systemd timer and before every deploy. Dumps are encrypted
to the public key; the private key stays off the VM, in the owner's password manager and on the
Mac that pulls copies. Retention: 7 days daily, 35 days weekly. The VM snapshot in Proxmox is on
the same SSD and doesn't count as a backup.

## Restore

- **Verify a backup** (monthly and after schema changes): copy the private key file in temporarily, then
  `ORBIT_BACKUP_IDENTITY=<key> deploy/restore.sh <file> --verify`. It restores into a scratch
  database, prints schema and row counts beside the live database's, and drops the copy. Delete
  the key file afterwards and record the date and result below.
- **Replace the live database:** `deploy/restore.sh <file> --live` stops the app, asks for
  confirmation, restores, then asks you to start the release again.

## Restore and rehearsal log

| Date | Where | What | Result |
|---|---|---|---|
| 2026-10-23 | Mac, rehearsal project | See [deployment rehearsal](deployment-rehearsal-2026-10-23.md) | Recorded there |

## When things go wrong

- **API won't start:** `docker logs orbit-api-1`. A production refusal names the missing setting
  in `orbit.env`.
- **Q&A says the daily limit was reached:** expected under the free tier (ADR 0022). Don't raise
  limits or enable billing.
- **SEC throttling or failed downloads:** the worker retries hourly; check `docker logs orbit-filing-worker-1`.
- **Encoder missing or wrong model:** rerun `--provision-model`; the encoder never downloads by itself.
- **Disk above 80 %:** prune old images (`docker image prune`) before touching volumes. Never
  delete `orbit_db_data`.
