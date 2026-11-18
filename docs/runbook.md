# Runbook

Production runs on Fly.io (app `APP`, region `iad`) with a Neon Postgres database.
Nightly backups run from a second Fly app (`BACKUP_APP`) to a Cloudflare R2 bucket.
See [ADR-0004](adr/0004-fly-neon-hosting.md).

`APP` is the Fly app name (for example `drew-gradebook`). `BACKUP_APP` is `APP-backup`.
Run `fly` commands from the repo root unless a section says otherwise. If `fly` is not on
your PATH, use `~/.fly/bin/fly`.

## First-time setup

Do this once, in order. Do M3 from `main`, so `fly deploy` ships reviewed code.

Generate secrets locally. Never paste them into chat. Use hex for DB passwords, so no `%`
or URL-unsafe characters appear:

```bash
openssl rand -hex 24          # one per DB role password
python3 -c "import secrets; print(secrets.token_urlsafe(48))"   # SECRET_KEY
```

Keep them in a password manager entry named "gradebook prod".

### M1. Fly.io account and CLI

1. Sign up at fly.io and add a payment card (Fly is pay-as-you-go).
2. `fly auth login`, then `fly orgs list` to confirm the personal org.
3. `fly apps create APP` (the name is final; it sets the URL `https://APP.fly.dev`).
4. Set `app = "APP"` in `fly.toml` (replace `CHANGE-ME-gradebook`).
5. Optional: in the Fly dashboard, Billing, set a spending alert, for example $10.

### M2. Neon project and roles

1. Sign up at neon.tech (free plan). Create a project named `gradebook`, **Postgres 18**,
   region **AWS US East (N. Virginia), us-east-1** (closest to Fly `iad`).
2. In the project, rename the default database to `gradebook`, or create it. The
   console-created role (for example `neondb_owner`, or rename it `gradebook_owner`) is the
   **owner**. It is used only for migrations.
3. Connection details: **turn the "Connection pooling" toggle OFF** (the direct endpoint,
   with no `-pooler` in the host). Copy the owner URL. It looks like
   `postgresql://gradebook_owner:...@ep-xxx.us-east-1.aws.neon.tech/gradebook?sslmode=require`.
4. Open the **SQL Editor** (connected as the owner) and run this, with the generated
   passwords:
   ```sql
   CREATE ROLE gradebook_app LOGIN PASSWORD '<hex>';
   CREATE ROLE gradebook_backup LOGIN PASSWORD '<hex>';
   GRANT USAGE ON SCHEMA public TO gradebook_app, gradebook_backup;
   ALTER DEFAULT PRIVILEGES FOR ROLE gradebook_owner IN SCHEMA public
     GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO gradebook_app;
   ALTER DEFAULT PRIVILEGES FOR ROLE gradebook_owner IN SCHEMA public
     GRANT SELECT ON TABLES TO gradebook_backup;
   ```
   - Use the actual owner role name in `FOR ROLE`.
   - The default privileges come first, so the tables created by the first migration get the
     grants automatically. That includes `alembic_version`, which `pg_dump` needs.
   - PUBLIC already has CONNECT, so no grant is needed for it.
   - The keys are UUIDs, so there are no sequences to grant.
5. Build the two URLs from the owner URL by swapping user and password:
   - `gradebook_app:<hex>@...` is `DATABASE_URL`
   - `gradebook_backup:<hex>@...` is `BACKUP_DATABASE_URL`
6. Optional local check: `psql "$OWNER_URL" -c 'select version()'` shows 18.x.

### M3. Fly secrets and first deploy

```bash
fly secrets set -a APP --stage \
  DATABASE_URL='postgresql://gradebook_app:...@ep-xxx.us-east-1.aws.neon.tech/gradebook?sslmode=require' \
  MIGRATIONS_DATABASE_URL='postgresql://gradebook_owner:...@.../gradebook?sslmode=require' \
  SECRET_KEY='<token_urlsafe>'
fly deploy -a APP --ha=false   # one machine; builds, runs release_command, starts the machine
```

- Run the deploy in a terminal tab so the output is visible. `ENVIRONMENT` and
  `TRUST_PROXY_IP_HEADER` come from `[env]` in `fly.toml`; `STATIC_DIR` from the Dockerfile.
- `--ha=false` matters on the first deploy only: without it Fly creates two machines.
- If the release_command fails with `permission denied for schema public`, the URLs are
  swapped: `MIGRATIONS_DATABASE_URL` must be the owner (`neondb_owner`), not the app or
  backup role. Re-set it with `fly secrets set --stage` and deploy again. Nothing is written
  until migrations succeed. Other failures: `fly logs -a APP`, then check the URL and grants.
- After the first deploy, confirm the app role is not the owner:
  `psql "$APP_URL" -c 'create table x(i int)'` must fail with "permission denied for schema public".

### M4. Cloudflare R2 bucket and token

1. Cloudflare dashboard, R2, **Create bucket** `gradebook-backups`. The location hint is
   Eastern North America. Leave public access **off**.
2. Bucket, Settings, **Object lifecycle rules**: add a rule that deletes objects 30 days
   after upload.
3. R2, **Manage R2 API Tokens**, Create API token. The permission is **Object Read & Write**,
   scoped to **gradebook-backups only**, with no TTL. Copy the Access Key ID, the Secret
   Access Key, and the S3 endpoint `https://<account_id>.r2.cloudflarestorage.com`.
4. Optional hardening: Bucket, Settings, **Bucket lock rules**, keep objects for 7 days. A
   leaked backup token can then not delete recent dumps.

### M4b. healthchecks.io failure alert

1. Sign up at healthchecks.io (free plan) and create the check "gradebook nightly backup",
   with **Period 1 day** and **Grace 12 hours** (`--schedule daily` runs at a best-effort time, so gaps can exceed 24 h). Email notifications are on by default.
2. Copy its ping URL (`https://hc-ping.com/<uuid>`). It becomes the `HC_PING_URL` secret in M5.

### M5. Backup app and schedule

Set `app = "BACKUP_APP"` in `ops/backup/fly.toml` first (replace
`CHANGE-ME-gradebook-backup`).

```bash
cd ops/backup
fly apps create BACKUP_APP
fly secrets set -a BACKUP_APP --stage \
  BACKUP_DATABASE_URL='postgresql://gradebook_backup:...@.../gradebook?sslmode=require' \
  AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... AWS_DEFAULT_REGION=auto \
  R2_ENDPOINT='https://<account_id>.r2.cloudflarestorage.com' R2_BUCKET=gradebook-backups \
  HC_PING_URL='https://hc-ping.com/<uuid>'
fly deploy --build-only --push --local-only --image-label nightly-1   # registry.fly.io/BACKUP_APP:nightly-1
fly machine run registry.fly.io/BACKUP_APP:nightly-1 -a BACKUP_APP \
  --schedule daily --region iad --restart no \
  --vm-cpu-kind shared --vm-size shared-cpu-1x --vm-memory 256 --name nightly-backup
```

- The `--vm-cpu-kind`/`--vm-size` flags are required: without them flyctl fails with
  `invalid CPU kind ''`.
- `fly machine run` starts the machine once right away, so this is the first backup. Check
  `fly logs -a BACKUP_APP --no-tail` for `backup ok: gradebook/...`. The healthchecks.io check
  turns green.

### M6. Prove one restore

Run the [restore drill](#restore-drill). Every line must show `prod=` equal to `restored=`.
Repeat it once real data exists: on an empty database it proves only the schema.

### M7. Katie's account and the prod smoke test

1. Open `https://APP.fly.dev` once to wake the machine.
2. `fly ssh console -a APP`, then `python -m app.cli create-teacher --username katie`.
   Katie types her password, in person or on a call. Do it promptly: auto-stop can end an
   idle SSH session. If it does, wake the site and rerun the command.
3. Smoke test, signed in as Katie with her present, or using a temporary second teacher
   (`--allow-second-teacher`, removed afterwards):
   - log in, create class "Smoke", add a student and a subject, enter a score, check that
     Grades shows a value
   - delete "Smoke"
4. `curl -sI http://APP.fly.dev` must return a 301 to https.
5. `curl -s https://APP.fly.dev/api/docs` must return 404.
6. `curl -sI https://APP.fly.dev/` must show the CSP and HSTS headers.

### M8. Cost check

- Fly: one shared-cpu-1x/512MB machine with auto-stop (well under $3.2/mo) plus a scheduled
  backup machine for a few seconds a day (cents).
- Neon free: $0. R2 free tier (10 GB): $0.
- Expected total: under $5/mo. Check Fly, Billing, after a week.
- Also check that the healthchecks.io check is green after the first scheduled run.

## Deploy

**Automatic:** every push to `main` runs `.github/workflows/deploy.yml`. It runs the full
backend and frontend gates, then `flyctl deploy --local-only` on the GitHub runner, then
checks `/api/health`. Pushes that only touch `docs/`, `ops/` or Markdown do not deploy.
Watch it in GitHub, Actions, Deploy. To redeploy without a new commit, run the workflow
by hand there (`workflow_dispatch`).

The workflow needs the `FLY_API_TOKEN` secret in the GitHub `production` environment. It is a
deploy token for `APP` only:

```bash
fly tokens create deploy -a APP --expiry 8760h | gh secret set FLY_API_TOKEN --env production --repo drewpearce/gradebook
```

The token expires after a year. Rerun the same command to rotate it. The pipe means the token
is never shown on screen.

**By hand** (when Actions is down), from the repo root on `main`:

```bash
fly deploy -a APP     # builds, runs the release_command (migrations), replaces the machine
fly status -a APP
fly logs -a APP
```

The release_command runs `alembic -c /app/alembic.ini upgrade head` with the owner role
(`MIGRATIONS_DATABASE_URL`). If it fails, the deploy stops and the old version keeps running.

If the build sits at `Waiting for depot builder...` for more than a few minutes, press Ctrl-C
and add `--local-only`. Docker on your machine then builds the image (for amd64) and pushes it.

## Run migrations by hand

```bash
fly ssh console -a APP -C "alembic -c /app/alembic.ini upgrade head"
```

## Create or reset the teacher

Open `https://APP.fly.dev` to wake the machine, then:

```bash
fly ssh console -a APP
python -m app.cli create-teacher --username katie
```

Katie types the password. A reset revokes old sessions (the `pwd` claim). SSH is not proxy
traffic, so auto-stop can end a slow session. The command is idempotent, so rerun it.

## Backups

A scheduled machine on `BACKUP_APP` runs `ops/backup/backup.sh`. It runs `pg_dump` (custom
format) and uploads to R2 under `gradebook/<timestamp>.dump`, then pings healthchecks.io.
An R2 lifecycle rule deletes objects after 30 days. `--schedule daily` runs at a best-effort
time, not a fixed one.

```bash
fly machine list -a BACKUP_APP                   # find the machine id
fly machine start <id> -a BACKUP_APP             # run a backup now
fly logs -a BACKUP_APP                           # look for "backup ok: gradebook/..."
aws s3 ls s3://gradebook-backups/gradebook/ --endpoint-url "$R2_ENDPOINT"   # list objects
```

The `aws` command needs the R2 keys in your local shell env (`AWS_ACCESS_KEY_ID`,
`AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION=auto`). Do not store them in the repo.

**Failure alert:** healthchecks.io emails you when the nightly ping is missing (Period 1
day, Grace 12 hours) or when the script pings `/fail` (any failure, including a missing secret). When it fires, check
`fly logs -a BACKUP_APP`. Fix it before the 30-day R2 lifecycle rule deletes the last good dump.

**Update the backup image** (after editing `ops/backup/`): `fly deploy --build-only --push`
does not change the existing machine, so update it by hand.

```bash
cd ops/backup
fly deploy --build-only --push --image-label nightly-2   # use a new label each time
fly machine update <id> --image registry.fly.io/BACKUP_APP:nightly-2 -a BACKUP_APP
```

A second safety net is Neon's own point-in-time restore window (Neon's free-plan restore
window; check the current limit on Neon's pricing page).

## Restore drill

`ops/backup/restore-check.sh` restores the newest dump into a throwaway Postgres on a one-off
`BACKUP_APP` machine and prints prod vs restored counts for every table. The dump and the
secrets stay on Fly. Run it from the repo root:

```bash
fly machine run registry.fly.io/BACKUP_APP:nightly-1 bash /restore.sh -a BACKUP_APP \
  --file-local /restore.sh=ops/backup/restore-check.sh \
  --region iad --restart no --rm --vm-cpu-kind shared --vm-size shared-cpu-1x --vm-memory 512 \
  --name restore-check
fly logs -a BACKUP_APP --no-tail | grep -E "restoring:|prod=|restore check done"
```

Mount the script as a file. Do not pass `bash -c "..."`: flyctl reads `-c` as its own
`--config` flag. Use the image label the nightly machine runs.

## Restore

Restore to a scratch database first (the [restore drill](#restore-drill) does this), or to
prod only if prod is lost.

```bash
aws s3 cp s3://gradebook-backups/gradebook/<key>.dump /tmp/gb.dump --endpoint-url "$R2_ENDPOINT"
docker run --rm -v /tmp:/tmp postgres:18 \
  pg_restore --no-owner --no-acl --clean --if-exists -d "<target url>" /tmp/gb.dump
rm /tmp/gb.dump
```

Use pg_restore **18** (the `postgres:18` image does this). An older client or server rejects a
PG18 dump. `<target url>` is a `postgresql://` URL for the owner role. Delete the dump
afterwards: it holds student data.

## Rotate secrets

- `SECRET_KEY`: `fly secrets set -a APP SECRET_KEY='<new token_urlsafe>'`. Every session logs out.
- DB passwords: in the Neon SQL Editor run `ALTER ROLE gradebook_app PASSWORD '<new hex>';`
  (or `gradebook_backup`, or the owner), then update the secret:
  `fly secrets set -a APP DATABASE_URL='...'` (owner: `MIGRATIONS_DATABASE_URL`;
  backup role: `fly secrets set -a BACKUP_APP BACKUP_DATABASE_URL='...'`).
- R2 token: roll it in the Cloudflare dashboard, then
  `fly secrets set -a BACKUP_APP AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=...`.

## Known limits

- Single machine: a deploy or a crash means a short outage.
- The login rate limit is in memory and resets when the machine stops (auto-stop). An
  attacker's own traffic keeps the machine awake, so the limit still holds during an attack.
- Cold start of about 1-3 s after auto-stop, plus Neon suspend on idle.
