#!/usr/bin/env bash
# Encrypted PostgreSQL backup for Orbit (ADR 0028; runbook: docs/operations.md).
#
#   deploy/backup.sh [label]     e.g. nightly from a systemd timer, or "pre-deploy" from deploy.sh
#
# Writes <dir>/daily/orbit-<UTC time>[-label].dump.age, encrypted with age to the public
# recipient(s) in ORBIT_BACKUP_RECIPIENTS. The private key never lives on this host. Sunday's
# nightly copy is also kept under weekly/. Retention: 7 days daily, 35 days weekly.
set -euo pipefail

PROJECT="${ORBIT_PROJECT:-orbit}"
DIR="${ORBIT_BACKUP_DIR:-/var/backups/orbit}"
RECIPIENTS="${ORBIT_BACKUP_RECIPIENTS:-/etc/orbit/backup-recipients.txt}"
AGE="${ORBIT_AGE:-age}"
label="${1:-}"

die() { printf 'backup: ERROR: %s\n' "$*" >&2; exit 1; }

[[ -s "$RECIPIENTS" ]] || die "age recipients file missing: $RECIPIENTS"
[[ -z "$label" || "$label" =~ ^[a-z0-9-]+$ ]] || die "label must be lowercase letters, digits or -"
db="$(docker ps -q --filter "label=com.docker.compose.project=$PROJECT" \
  --filter label=com.docker.compose.service=db)"
[[ -n "$db" ]] || die "no running db container for project $PROJECT"

umask 077
mkdir -p "$DIR/daily" "$DIR/weekly"
name="orbit-$(date -u +%Y%m%dT%H%M%SZ)${label:+-$label}.dump.age"
tmp="$DIR/daily/.$name.partial"
trap 'rm -f "$tmp"' EXIT

docker exec "$db" pg_dump -U orbit -d orbit -Fc | $AGE -R "$RECIPIENTS" > "$tmp"
[[ -s "$tmp" ]] || die "empty backup"
mv "$tmp" "$DIR/daily/$name"
trap - EXIT

if [[ -z "$label" && "$(date -u +%u)" == 7 ]]; then
  cp "$DIR/daily/$name" "$DIR/weekly/$name"
fi
find "$DIR/daily" -name 'orbit-*.dump.age' -mtime +7 -delete
find "$DIR/weekly" -name 'orbit-*.dump.age' -mtime +35 -delete

printf '%s\n' "$DIR/daily/$name"
