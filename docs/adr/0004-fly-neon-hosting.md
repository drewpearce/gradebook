---
status: accepted
---

# Host on Fly.io + Neon, one origin, nightly dump to R2

We host the gradebook as **one Fly.io app in `iad`** that serves both the built SPA and
the JSON API (`/api`) from a single origin, with a **Neon free-tier Postgres** database.
Nightly `pg_dump` backups go to a **Cloudflare R2** bucket from a **Fly scheduled machine**
in a separate Fly app. Deploys are a manual `fly deploy`. The site stays on the
`*.fly.dev` URL at first; a custom domain can come later. See
[`docs/runbook.md`](../runbook.md).

The app role has data access only; migrations run as the schema owner
(`MIGRATIONS_DATABASE_URL`; see the limit under Consequences). Backups use a third,
read-only role.

## Considered options

- **Cloudflare (Workers/Pages).** Rejected: the FastAPI backend would need a refactor.
- **Fly Managed Postgres.** Rejected: about $38/mo, too much for one teacher.
- **Unmanaged Fly Postgres.** Rejected: unsupported by Fly.
- **Supabase free tier.** Rejected: the project pauses when idle.
- **GitHub Actions cron for backups.** Rejected: GitHub disables scheduled workflows after
  60 days with no repo activity (likely over summer break), and the repo is public, so
  workflow logs are public.
- **Fly app + Neon free + R2 (chosen).** Expected cost under $5/mo.

## Consequences

- Same origin in production, so there is no CORS and the token needs no cross-origin
  handling. Dev stays same-origin through the Vite proxy.
- A single machine with auto-stop: a cold start of about 1-3 s, and the in-memory login
  rate limit resets when the machine stops.
- Backups are our own: a nightly custom-format dump, kept 30 days by an R2 lifecycle rule,
  with a healthchecks.io dead-man check that emails on a missed or failed run.
- A second safety net is Neon's own point-in-time restore window (Neon's free-plan restore
  window; check the current limit on Neon's pricing page).
- `pg_dump` and `pg_restore` must be at least the Neon server's major version (17).
- `MIGRATIONS_DATABASE_URL` is a Fly secret, and Fly exposes secrets to every machine in the
  app, so the running app can read the owner URL. The DML-only role protects against SQL
  injection, not against code execution in the app. For the stronger guarantee, run
  `alembic upgrade head` from a local shell with the owner URL and drop `release_command`.
