#!/usr/bin/env bash
# Restore an Orbit backup (ADR 0028; runbook: docs/operations.md).
#
#   deploy/restore.sh <backup> --verify   restore into a scratch database, print counts, drop it
#   deploy/restore.sh <backup> --live     replace the live database (stops the app first)
#
# <backup> is an age-encrypted dump (needs ORBIT_BACKUP_IDENTITY, the private key file, which
# is brought to this host only for the restore) or a plain pg_dump custom-format file.
set -euo pipefail

PROJECT="${ORBIT_PROJECT:-orbit}"
AGE="${ORBIT_AGE:-age}"
backup="${1:-}"
mode="${2:-}"

die() { printf 'restore: ERROR: %s\n' "$*" >&2; exit 1; }
log() { printf 'restore: %s\n' "$*" >&2; }

[[ -f "$backup" ]] || die "usage: $0 <backup> --verify|--live"
[[ "$mode" == --verify || "$mode" == --live ]] || die "choose --verify or --live"
if [[ "$backup" == *.age && ! -f "${ORBIT_BACKUP_IDENTITY:-}" ]]; then
  die "set ORBIT_BACKUP_IDENTITY to the age private key file"
fi
db="$(docker ps -q --filter "label=com.docker.compose.project=$PROJECT" \
  --filter label=com.docker.compose.service=db)"
[[ -n "$db" ]] || die "no running db container for project $PROJECT"

plain() {
  if [[ "$backup" == *.age ]]; then
    [[ -f "${ORBIT_BACKUP_IDENTITY:-}" ]] || die "set ORBIT_BACKUP_IDENTITY to the age private key file"
    $AGE -d -i "$ORBIT_BACKUP_IDENTITY" "$backup"
  else
    cat "$backup"
  fi
}

psql_db() { docker exec -i "$db" psql -v ON_ERROR_STOP=1 -U orbit -d "$1" -Atq "${@:2}"; }

counts() {
  psql_db "$1" -F ' ' -c "select 'schema', version_num from alembic_version
    union all select 'users', count(*)::text from users
    union all select 'holdings', count(*)::text from holdings
    union all select 'filings', count(*)::text from filings
    union all select 'passages', count(*)::text from filing_passages"
}

if [[ "$mode" == --verify ]]; then
  target="orbit_restore_check"
  psql_db postgres -c "drop database if exists $target" -c "create database $target"
  trap 'psql_db postgres -c "drop database if exists '"$target"'" >/dev/null' EXIT
  psql_db "$target" -c "create extension if not exists vector"
  plain | docker exec -i "$db" pg_restore -U orbit -d "$target" --no-owner --exit-on-error
  log "restored copy (scratch database, now dropped):"
  counts "$target"
  log "live database for comparison:"
  counts orbit
  exit 0
fi

read -r -p "Replace the LIVE Orbit database from $(basename "$backup")? Type 'replace': " answer
[[ "$answer" == replace ]] || die "cancelled"
app="$(docker ps -q --filter "label=com.docker.compose.project=$PROJECT" | grep -v "$db" || true)"
if [[ -n "$app" ]]; then
  # shellcheck disable=SC2086  # one container ID per word
  docker stop $app >/dev/null
fi
psql_db postgres -c "drop database orbit with (force)" -c "create database orbit"
psql_db orbit -c "create extension if not exists vector"
plain | docker exec -i "$db" pg_restore -U orbit -d orbit --no-owner --exit-on-error
counts orbit
log "restored. Start the app again with: deploy/deploy.sh --rollback (or redeploy the current release)"
