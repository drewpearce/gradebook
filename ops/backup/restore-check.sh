#!/usr/bin/env bash
# Restore drill: restore the newest R2 dump into a throwaway Postgres on the machine itself,
# then compare table and row counts with prod. Runs on a one-off BACKUP_APP machine, so the
# dump and the secrets never leave Fly. See docs/runbook.md, "Restore drill".
set -euo pipefail

latest=$(aws s3 ls "s3://$R2_BUCKET/gradebook/" --endpoint-url "$R2_ENDPOINT" | sort | tail -1 | awk '{print $4}')
echo "restoring: $latest"
aws s3 cp "s3://$R2_BUCKET/gradebook/$latest" /tmp/gb.dump --endpoint-url "$R2_ENDPOINT" --quiet

mkdir -p /tmp/pg && chown postgres /tmp/pg
su postgres -c "initdb -D /tmp/pg -A trust >/dev/null && pg_ctl -D /tmp/pg -o '-k /tmp -c listen_addresses=' -l /tmp/pg.log -w start >/dev/null"
createdb -h /tmp -U postgres scratch
pg_restore --no-owner --no-acl -h /tmp -U postgres -d scratch /tmp/gb.dump

restored() { psql -h /tmp -U postgres -d scratch -tAc "$1"; }
prod() { psql "$BACKUP_DATABASE_URL" -tAc "$1"; }
q="select count(*) from pg_tables where schemaname='public'"
echo "tables: prod=$(prod "$q") restored=$(restored "$q")"
for t in teachers classes grade_levels students subjects categories assignments scores grading_scales grade_bands; do
  echo "$t: prod=$(prod "select count(*) from $t") restored=$(restored "select count(*) from $t")"
done
q="select version_num from alembic_version"
echo "alembic: prod=$(prod "$q") restored=$(restored "$q")"
echo "restore check done"
