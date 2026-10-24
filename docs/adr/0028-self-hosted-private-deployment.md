# 0028. Self-hosted private deployment on a dedicated homelab VM

- **Status:** Accepted (supersedes [0008](0008-defer-continuous-deployment.md)); deployment not yet verified
- **Date:** 2026-10-23

## Context

ADR 0008 deferred Continuous Deployment until a host was chosen. The owner has now chosen
the existing Proxmox homelab: a small x86-64 CPU-only machine with 16 GB RAM and one SATA SSD,
which already runs unrelated applications in another VM and must keep running them. Orbit
stores portfolios and holds a model API key. The current containers are development-only:
the frontend runs the Vite dev server, the backend image includes test tools and is run
with source bind-mounted and `--reload`, and the development Compose file publishes the
database and API ports. The course needs a reachable, recoverable deployment, not high
availability.

## Decision

We will run Orbit in its own VM (`orbit-01`) on the homelab, reachable only over the
owner's Tailscale network:

- **Ingress:** one Caddy container serves the built frontend and proxies `/api` to the API on
  the same origin. It is the only published port, bound to the VM's loopback and exposed
  through Tailscale Serve (HTTPS). The database, encoder, API and workers have no published
  ports. No public internet exposure; any public demo needs a separate decision.
- **Images:** production images are separate build targets. The backend image contains
  runtime dependencies only and runs without `--reload` or source mounts. The frontend is
  compiled and served as static files. CI builds amd64 images, scans them, and pushes them to
  Orbit's own GHCR packages. Deploys use image digests, not mutable tags.
- **Configuration:** with `APP_ENVIRONMENT=production`, the API and workers refuse to start
  on the default database password, and the API also refuses to start when its provider
  settings are missing. Errors name the setting, never its value. Secrets live in one
  root-owned file on the VM, never in Git or CI.
- **Deploys:** manual and pull-based. A deploy script on the VM takes a database dump, pulls
  pinned digests, runs migrations as a one-shot service, starts the stack, and rolls back to
  the previous digests if health checks fail. GitHub has no credentials into the homelab.
- **Data protection:** nightly encrypted `pg_dump` files, pulled off-host, plus restore tests
  recorded in the runbook. The pinned encoder model and container images are reproducible,
  so they aren't backed up. A VM snapshot on the same SSD is not a backup.
- **Monitoring:** container health checks with `restart: unless-stopped`, plus the existing
  Uptime Kuma instance for HTTP health and backup age.

Where answer generation runs (hosted Gemini or a separate local model server) is a separate,
pending decision. This deployment works with either.

## Consequences

- Orbit gets a real, private, recoverable home without changing the existing homelab VM.
- Production can't start on development defaults by accident.
- Deploys are deliberate and auditable by digest. Rollback is a redeploy of earlier digests,
  or a dump restore when a migration changed data.
- Costs: the owner must enrol the VM in Tailscale, keep the secrets file and backup key, and
  run a deploy command. The instructor needs Tailscale access or a recorded walkthrough.
- Risks: CPU-only embedding throughput and memory headroom on the shared host are unmeasured
  until benchmarked there. A single SSD makes off-host copies mandatory.
- Development Compose stays unchanged and is never a production configuration.

## Alternatives Considered

- **Add Orbit to the existing apps VM:** the least setup, but it shares 4 GiB RAM, the database
  engine version and the failure domain with unrelated apps. Rejected.
- **Public cloud host:** costs money, adds a provider-specific setup, and moves portfolio
  data off owner-controlled hardware. Rejected for now.
- **Push-based CD from GitHub Actions:** needs inbound credentials into the home network.
  Pull-based manual deploys keep the homelab closed. Automation can come later.
- **Public exposure (port forwarding or a public tunnel):** a larger attack surface for an
  app holding portfolios and a model key. Excluded unless separately approved and time-boxed.
