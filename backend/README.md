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
```

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
uv run pytest                # tests
```

## Layout

- `app/` — application code (`main` app + `/health`, `config` settings, `db` engine/session/`Base`).
- `migrations/` — Alembic environment and versioned migrations.
- `tests/` — pytest suite.
