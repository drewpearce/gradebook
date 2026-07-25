---
status: accepted
---

# React SPA + FastAPI JSON API on PostgreSQL

We are building the gradebook as a **React + TypeScript single-page app (Vite)**
talking to a **FastAPI JSON API** backed by **PostgreSQL** (SQLAlchemy 2.0 typed
ORM + Alembic migrations). The teacher's grade-entry workflow is interaction-heavy
(spreadsheet-like editing, live-recomputed grades), which a client-rendered SPA
serves well, and the decision-maker is fluent in both typed Python/FastAPI and
React/TypeScript.

## Considered options

- **Server-rendered monolith (FastAPI + Jinja / HTMX).** Simpler deploy, one
  codebase, no API contract to maintain. Rejected: the grid-style grade entry and
  live grade recomputation push toward rich client state that HTMX would fight.
- **Next.js full-stack (TypeScript everywhere).** One language, great DX.
  Rejected: gives up FastAPI/typed-Python for the backend, which is the author's
  strongest and preferred backend stack, and pulls in a heavier framework than a
  single-teacher tool needs.
- **SPA + JSON API (chosen).** Clean separation, plays to existing strengths on
  both ends, and leaves room to add a student-facing client later against the same
  API.

## Consequences

- We own an explicit API contract between the two halves (worth generating types
  from FastAPI's OpenAPI schema to keep the frontend in sync).
- Auth is token/session across an origin boundary — a real decision to make when
  we get to auth, not free as it would be in a monolith.
- PostgreSQL is a deliberate lock-in for relational integrity (students,
  assignments, scores, audiences) over a document store.
