#!/usr/bin/env bash
# Deploy a digest-pinned Orbit release to this host (ADR 0028; runbook: docs/operations.md).
#
#   deploy/deploy.sh <release.env>        back up, pull, migrate, start, verify; roll back on failure
#   deploy/deploy.sh --rollback           redeploy the previous release (no migration)
#   deploy/deploy.sh --provision-model <release.env>   one-time, checksum-pinned encoder download
#
# A release file holds ORBIT_RELEASE plus ORBIT_API_IMAGE, ORBIT_WEB_IMAGE and
# ORBIT_ENCODER_IMAGE, each pinned as image@sha256:<digest> (CI writes it).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT="${ORBIT_PROJECT:-orbit}"
ENV_FILE="${ORBIT_ENV_FILE:-/etc/orbit/orbit.env}"
STATE_DIR="${ORBIT_STATE_DIR:-/var/lib/orbit}"
HEALTH_TIMEOUT="${ORBIT_HEALTH_TIMEOUT:-120}"

log() { printf '%s deploy: %s\n' "$(date -u +%H:%M:%SZ)" "$*" >&2; }
die() { log "ERROR: $*"; exit 1; }

compose() {
  local release="$1"; shift
  docker compose -p "$PROJECT" -f "$ROOT/docker-compose.prod.yml" \
    --env-file "$ENV_FILE" --env-file "$release" "$@"
}

check_release() {
  local release="$1" var value
  [[ -f "$release" ]] || die "release file not found: $release"
  for var in ORBIT_API_IMAGE ORBIT_WEB_IMAGE ORBIT_ENCODER_IMAGE; do
    value="$(sed -n "s/^${var}=//p" "$release")"
    [[ "$value" == *@sha256:* ]] || die "$var must be pinned by digest in $release"
  done
}

http_port() { sed -n 's/^ORBIT_HTTP_PORT=//p' "$ENV_FILE" | tail -1; }

wait_healthy() {
  local port deadline unhealthy
  port="$(http_port)"; port="${port:-8080}"
  deadline=$((SECONDS + HEALTH_TIMEOUT))
  while ((SECONDS < deadline)); do
    unhealthy="$(docker ps --filter "label=com.docker.compose.project=$PROJECT" \
      --format '{{.Names}} {{.Status}}' | grep -E 'unhealthy|starting|Restarting' || true)"
    if [[ -z "$unhealthy" ]] && curl -fsS "http://127.0.0.1:${port}/api/health" >/dev/null 2>&1; then
      return 0
    fi
    sleep 3
  done
  log "not healthy after ${HEALTH_TIMEOUT}s: ${unhealthy:-health endpoint unreachable}"
  return 1
}

schema_revision() {
  local db
  db="$(docker ps -q --filter "label=com.docker.compose.project=$PROJECT" \
    --filter label=com.docker.compose.service=db)"
  [[ -n "$db" ]] || { echo "none"; return; }
  docker exec "$db" psql -U orbit -d orbit -Atc 'select version_num from alembic_version' 2>/dev/null \
    || echo "none"
}

start_release() {
  local release="$1"
  compose "$release" up -d --remove-orphans db encoder api filing-worker embedding-worker web
}

[[ -f "$ENV_FILE" ]] || die "settings file not found: $ENV_FILE (see deploy/orbit.env.example)"
mkdir -p "$STATE_DIR"

case "${1:-}" in
  --provision-model)
    check_release "${2:-}"
    compose "$2" --profile model-setup run --rm provision-encoder
    exit 0 ;;
  --rollback)
    [[ -f "$STATE_DIR/previous.env" ]] || die "no previous release recorded in $STATE_DIR"
    log "rolling back to $(sed -n 's/^ORBIT_RELEASE=//p' "$STATE_DIR/previous.env")"
    # An older release cannot start on a schema a newer release migrated: say so plainly.
    compose "$STATE_DIR/previous.env" run --rm migrate >/dev/null 2>&1 \
      || die "the previous release does not recognise schema $(schema_revision). Restore the pre-deploy dump first (deploy/restore.sh <dump> --live), then rerun --rollback"
    if ! { start_release "$STATE_DIR/previous.env" && wait_healthy; }; then
      die "previous release is not healthy either; see docs/operations.md"
    fi
    cp "$STATE_DIR/current.env" "$STATE_DIR/failed.env" 2>/dev/null || true
    cp "$STATE_DIR/previous.env" "$STATE_DIR/current.env"
    log "rollback complete; schema at $(schema_revision)"
    exit 0 ;;
  ""|-h|--help)
    sed -n '2,10p' "$0"; exit 0 ;;
esac

RELEASE="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
check_release "$RELEASE"
log "release $(sed -n 's/^ORBIT_RELEASE=//p' "$RELEASE")"

compose "$RELEASE" pull --quiet || die "could not pull the release images; the running release was not changed"

before="$(schema_revision)"
if [[ "$before" != "none" ]]; then
  log "pre-deploy backup (schema $before)"
  "$ROOT/deploy/backup.sh" pre-deploy
fi

log "migrating"
compose "$RELEASE" up -d db
compose "$RELEASE" run --rm migrate || die "migration failed; the running release was not changed"
after="$(schema_revision)"
[[ "$before" == "$after" ]] || log "schema $before -> $after"

log "starting"
# `compose up` itself fails when a dependency turns unhealthy; test it as a condition so the
# rollback below always runs instead of `set -e` ending the script half-deployed.
if start_release "$RELEASE" && wait_healthy; then
  # Redeploying the running release changes nothing; only a new release rotates `previous`.
  if ! cmp -s "$RELEASE" "$STATE_DIR/current.env"; then
    if [[ -f "$STATE_DIR/current.env" ]]; then cp "$STATE_DIR/current.env" "$STATE_DIR/previous.env"; fi
    cp "$RELEASE" "$STATE_DIR/current.env.new" && mv "$STATE_DIR/current.env.new" "$STATE_DIR/current.env"
  fi
  log "healthy; deploy complete"
  exit 0
fi

if [[ -f "$STATE_DIR/current.env" ]]; then
  log "new release unhealthy; restarting $(sed -n 's/^ORBIT_RELEASE=//p' "$STATE_DIR/current.env")"
  if ! { start_release "$STATE_DIR/current.env" && wait_healthy; }; then
    die "previous release is not healthy either; see docs/operations.md"
  fi
  [[ "$before" == "$after" ]] \
    || log "WARNING: schema moved $before -> $after; restore the pre-deploy dump if the old release misbehaves"
  die "deploy failed and was rolled back"
fi
die "deploy failed and there is no previous release to roll back to"
