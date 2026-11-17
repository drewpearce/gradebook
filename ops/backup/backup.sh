#!/usr/bin/env bash
# Nightly: pg_dump the prod DB to R2, then ping healthchecks.io. Config is all env vars (Fly secrets).
set -euo pipefail

: "${BACKUP_DATABASE_URL:?}"
: "${R2_ENDPOINT:?}"
: "${R2_BUCKET:?}"
: "${AWS_ACCESS_KEY_ID:?}"
: "${AWS_SECRET_ACCESS_KEY:?}"
: "${AWS_DEFAULT_REGION:?}"
: "${HC_PING_URL:?}"

trap 'curl -fsS -m 10 "$HC_PING_URL/fail" || true' ERR

key="gradebook/$(date -u +%Y-%m-%dT%H%M%SZ).dump"
# Dump to a file first: a failed dump must not leave a partial object that looks like a backup.
pg_dump --format=custom --no-owner --no-acl --file=/tmp/gb.dump "$BACKUP_DATABASE_URL"
aws s3 cp /tmp/gb.dump "s3://$R2_BUCKET/$key" --endpoint-url "$R2_ENDPOINT"
echo "backup ok: $key"
curl -fsS -m 10 "$HC_PING_URL"
