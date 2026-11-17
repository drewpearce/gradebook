#!/usr/bin/env bash
# Nightly: pg_dump the prod DB to R2, then ping healthchecks.io. Config is all env vars (Fly secrets).
set -euo pipefail

: "${HC_PING_URL:?}"
# EXIT, not ERR: a failed ${VAR:?} check exits without firing ERR. Set right after
# HC_PING_URL so a missing secret alerts at once; disarmed just before the success ping.
trap 'curl -fsS -m 10 "$HC_PING_URL/fail" || true' EXIT
: "${BACKUP_DATABASE_URL:?}"
: "${R2_ENDPOINT:?}"
: "${R2_BUCKET:?}"
: "${AWS_ACCESS_KEY_ID:?}"
: "${AWS_SECRET_ACCESS_KEY:?}"
: "${AWS_DEFAULT_REGION:?}"

key="gradebook/$(date -u +%Y-%m-%dT%H%M%SZ).dump"
# Dump to a file first: a failed dump must not leave a partial object that looks like a backup.
pg_dump --format=custom --no-owner --no-acl --file=/tmp/gb.dump "$BACKUP_DATABASE_URL"
aws s3 cp /tmp/gb.dump "s3://$R2_BUCKET/$key" --endpoint-url "$R2_ENDPOINT"
echo "backup ok: $key"
trap - EXIT
curl -fsS -m 10 "$HC_PING_URL"
