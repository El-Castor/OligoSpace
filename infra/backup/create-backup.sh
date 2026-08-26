#!/bin/sh
set -eu

: "${BACKUP_DIR:?BACKUP_DIR must be an explicit backup directory}"
: "${PGHOST:?PGHOST is required}"
: "${PGDATABASE:?PGDATABASE is required}"

case "$BACKUP_DIR" in
  /|/home|/root|"") echo "Refusing unsafe BACKUP_DIR" >&2; exit 2 ;;
esac

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT INT TERM
artifact="$workdir/${PGDATABASE}-${timestamp}.dump"

pg_dump --format=custom --compress=9 --file="$artifact" "$PGDATABASE"
pg_restore --list "$artifact" > "$workdir/${PGDATABASE}-${timestamp}.manifest"
sha256sum "$artifact" > "$workdir/${PGDATABASE}-${timestamp}.sha256"

install -m 0600 "$artifact" "$BACKUP_DIR/${PGDATABASE}-${timestamp}.dump"
install -m 0600 "$workdir/${PGDATABASE}-${timestamp}.manifest" "$BACKUP_DIR/${PGDATABASE}-${timestamp}.manifest"
install -m 0600 "$workdir/${PGDATABASE}-${timestamp}.sha256" "$BACKUP_DIR/${PGDATABASE}-${timestamp}.sha256"

echo "Created PostgreSQL archive and manifest. Restore verification remains required."
