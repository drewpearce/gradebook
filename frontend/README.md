# Gradebook — frontend

React + TypeScript SPA (Vite) for the Gradebook API. Data fetching with
[TanStack Query](https://tanstack.com/query); UI with [shadcn/ui](https://ui.shadcn.com)
(Tailwind v4); a fully-typed API client generated from the backend's OpenAPI schema.
See [`ADR-0001`](../docs/adr/0001-spa-plus-json-api.md).

## Setup

```bash
npm install
cp .env.example .env   # VITE_API_URL — defaults to http://localhost:8000
```

## Run

Start the backend first (see [`../backend/README.md`](../backend/README.md)) — it must
be running and have a Teacher (via `uv run python -m app.cli create-teacher`), and its
CORS allows `http://localhost:5173`.

```bash
npm run dev        # http://localhost:5173
```

Sign in with the Teacher's credentials; the home page lists Classes fetched through the
generated client.

## The typed API client

`src/api/schema.d.ts` is **generated** from `openapi.json` — never edit it by hand.
When the backend API changes, refresh the contract and regenerate:

```bash
# from ../backend, with the backend deps installed:
uv run python scripts/export_openapi.py ../frontend/openapi.json
# then, from here:
npm run gen:api
```

CI fails if `schema.d.ts` is out of sync with the committed `openapi.json`.

## Checks

```bash
npm run lint          # oxlint (warnings fail)
npm run format:check  # prettier
npm run typecheck     # tsc
npm run build         # tsc + vite build
```

## Layout

- `src/api/` — generated types, the `openapi-fetch` client (Bearer + 401 handling), and one query/mutation hook module per entity.
- `src/auth/` — token storage, `AuthProvider`, `useAuth`, the route guard.
- `src/routes/` — pages (`LoginPage`, `HomePage`, `ClassDetailPage`, `ScoreEntryPage`, `GradesPage`).
- `src/components/` — `setup/`, `scores/`, `grades/` feature components; `ui/` shadcn primitives; `Layout.tsx` app shell.
- `src/lib/` — small shared helpers (`audience`, `format`, `active-id`, `errors`, `utils`).

### Data-layer conventions

Every write goes through `unwrap` (`api/client.ts`, throws on error) and
`useInvalidatingMutation` (`api/mutations.ts`, invalidates query keys on success).
The per-entity hook files (`classes.ts`, `students.ts`, `assignments.ts`, …) are
kept **deliberately flat rather than folded into a generic CRUD factory**: a factory
would have to take the endpoint path as a parameter, which forfeits `openapi-fetch`'s
literal-path type inference (typed params + response). Flat, greppable files that
each spell out their literal paths preserve full type safety — the priority here (see
[`ADR-0003`](../docs/adr/0003-pyright-for-type-checking.md)'s heavily-typed stance) —
at the cost of a little repetition.
