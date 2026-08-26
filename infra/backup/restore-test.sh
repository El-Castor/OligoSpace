#!/bin/sh
set -eu

: "${RESTORE_ARTIFACT:?Path to a pg_dump custom archive is required}"
: "${RESTORE_TEST_DATABASE:?Explicit disposable database name is required}"
: "${ALLOW_DESTRUCTIVE_RESTORE_TEST:?Set to yes after confirming the disposable target}"

if [ "$ALLOW_DESTRUCTIVE_RESTORE_TEST" != "yes" ]; then
  echo "Restore test not authorized." >&2
  exit 2
fi
case "$RESTORE_TEST_DATABASE" in
  *_restore_test) ;;
  *) echo "Database name must end in _restore_test." >&2; exit 2 ;;
esac

dropdb --if-exists "$RESTORE_TEST_DATABASE"
createdb "$RESTORE_TEST_DATABASE"
pg_restore --exit-on-error --no-owner --dbname="$RESTORE_TEST_DATABASE" "$RESTORE_ARTIFACT"
psql --dbname="$RESTORE_TEST_DATABASE" --command="SELECT count(*) AS migration_rows FROM alembic_version;"
psql --dbname="$RESTORE_TEST_DATABASE" --command="SELECT count(*) AS oligo_rows FROM oligos;"

echo "Database restore completed. Application and object-storage smoke tests are still required."
