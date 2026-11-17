FROM node:22-slim AS web
WORKDIR /web
COPY frontend/package*.json frontend/.npmrc ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm AS app
COPY --from=ghcr.io/astral-sh/uv:0.13.9 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend/app ./app
COPY backend/migrations ./migrations
COPY backend/alembic.ini ./
RUN uv sync --frozen --no-dev
COPY --from=web /web/dist /app/static
RUN useradd --system --no-create-home app
USER app
ENV PATH=/app/.venv/bin:$PATH STATIC_DIR=/app/static
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
