---
status: accepted
---

# pyright (strict) for type checking, with ty as the future direction

The backend is type-checked with **pyright** in `strict` mode, wired into CI as a
required gate (see the backend scaffold, #2). Application code (`app/`) is fully
strict; only the `unknown`-family rules are relaxed for `tests/`, where Starlette's
`TestClient` forwards to loosely-typed `httpx` internals. This ADR records why
pyright over the alternatives, and the intent to migrate to **ty** once it is
mature.

## Considered options

- **mypy.** The reference implementation and a de-facto standard (and the
  decision-maker's tool at work). Rejected for this project: slower, and its
  SQLAlchemy support has historically leaned on the `sqlalchemy[mypy]` plugin,
  whereas we are on the typed SQLAlchemy 2.0 ORM (`Mapped[...]` / `DeclarativeBase`)
  that pyright reads natively without a plugin. Given #3 is a schema-heavy ticket,
  native 2.0 typing is worth more here than mypy's maturity.
- **ty (Astral).** Same vendor as `uv` and `ruff`, which this project already
  standardises on; Rust, very fast, single-binary (no Node dependency, which
  pyright pulls in). The natural long-term fit. Rejected _for now_ only because it
  is pre-1.0 and too early to stand behind as a CI gate.
- **pyrefly (Meta).** Rust, fast, large-codebase focus. Rejected: also pre-stable,
  and less aligned with our Astral tooling than ty.
- **pyright (chosen).** Mature, fast, first-class `strict` mode, and native typed
  SQLAlchemy 2.0 support. It is also what #2's spec called for.

## Consequences

- CI runs `uv run pyright`; pyright downloads a pinned Node on first run in a
  clean environment (observed in CI — a few seconds, cached thereafter).
- Diagnostics are pyright's, which can differ from mypy's on identical code. When
  cross-referencing mypy behaviour from other work, expect divergence — pyright is
  the source of truth here.
- The strict-relaxation for `tests/` is a deliberate, narrow boundary
  accommodation, not a general loosening; new non-test code stays fully strict.
- **Revisit ty when it reaches a stable release** (a good checkpoint is around
  #3–#5). Migrating would drop the Node dependency and unify on Astral tooling;
  the main cost to weigh is whether ty matches pyright's strictness and typed-ORM
  inference at that point.
