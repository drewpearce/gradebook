# Gradebook — backend

FastAPI JSON API on PostgreSQL (SQLAlchemy 2.0 typed ORM + Alembic), managed with
[`uv`](https://docs.astral.sh/uv/). See [`ADR-0001`](../docs/adr/0001-spa-plus-json-api.md)
for the architecture and [`CONTEXT.md`](../CONTEXT.md) for the domain language.

## Prerequisites

- Python 3.12+ (uv will fetch it if missing)
- Docker (for local Postgres)

## Setup

```bash
# From the repo root: start Postgres
docker compose up -d

# From backend/: install dependencies (incl. dev group)
uv sync

# Configure the database URL (defaults already match docker-compose)
cp .env.example .env

# Apply migrations
uv run alembic upgrade head

# Create the single teacher login (prompts for a password)
uv run python -m app.cli create-teacher --username katie
```

Set a real `SECRET_KEY` in `.env` before deploying — the default is insecure.

## Auth

Single-teacher, bearer-JWT auth (see [`ADR-0001`](../docs/adr/0001-spa-plus-json-api.md)).
Data endpoints require a token; `/health` and `/auth/login` are open.

```bash
# Log in (OAuth2 password form) → {"access_token": "...", "token_type": "bearer"}
curl -s -X POST localhost:8000/auth/login \
  -d 'username=katie&password=YOUR_PASSWORD'

# Call a protected endpoint
curl localhost:8000/classes -H "Authorization: Bearer $TOKEN"
```

`python -m app.cli create-teacher --username <name>` also resets the password if the
teacher already exists.

## Run

```bash
uv run uvicorn app.main:app --reload
# Health check:
curl localhost:8000/health   # -> {"status":"ok"}
```

## Checks

```bash
uv run ruff check            # lint
uv run ruff format --check   # formatting
uv run pyright               # types (strict)
TEST_DB=postgresql+psycopg://gradebook:gradebook@localhost:5432/gradebook_test
DATABASE_URL=$TEST_DB uv run pytest   # tests
```

The tests refuse to run unless the database name ends in `_test`. This keeps them off the
dev database. A fresh `docker compose up` creates `gradebook_test`
(`docker/initdb/`). On an existing volume, create it once:
`docker compose exec db createdb -U gradebook gradebook_test`.
Change the port in `TEST_DB` if your local Postgres does not use 5432.

## Layout

- `app/` — application code (`main` app + `/health`, `config` settings, `db` engine/session/`Base`).
- `migrations/` — Alembic environment and versioned migrations.
- `tests/` — pytest suite.
