from collections.abc import Awaitable, Callable

from fastapi import Depends, FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from starlette.types import Scope

from app.api.routers import classes, coursework, grades, scores, students
from app.auth import router as auth_router
from app.auth.deps import get_current_teacher
from app.config import Settings, settings

# 'unsafe-inline' styles: Radix Dialog's scroll lock injects a <style> element without a
# nonce. Low risk while scripts stay 'self'.
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; style-src 'self' 'unsafe-inline'; base-uri 'none'; "
    "frame-ancestors 'none'; form-action 'self'"
)


def health() -> dict[str, str]:
    """Liveness check. Deliberately does not touch the database."""
    return {"status": "ok"}


def create_api(production: bool) -> FastAPI:
    """The JSON API, mounted under /api (the SPA owns every other path)."""
    api = FastAPI(
        title="Gradebook API",
        docs_url=None if production else "/docs",
        redoc_url=None if production else "/redoc",
        openapi_url=None if production else "/openapi.json",
    )
    api.get("/health")(health)

    # Open: authentication.
    api.include_router(auth_router.router)

    # Protected: every data endpoint requires a valid Teacher token.
    auth = [Depends(get_current_teacher)]
    api.include_router(classes.router, dependencies=auth)
    api.include_router(students.router, dependencies=auth)
    api.include_router(coursework.router, dependencies=auth)
    api.include_router(scores.router, dependencies=auth)
    api.include_router(grades.router, dependencies=auth)
    return api


class SPAStaticFiles(StaticFiles):
    """Serve the built SPA: unknown extension-less paths fall back to index.html."""

    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            response = await super().get_response(path, scope)
        except HTTPException as exc:
            # A stale hashed asset (has an extension) must stay a 404, not become index.html.
            if exc.status_code != 404 or "." in path.rsplit("/", 1)[-1]:
                raise
            response = await super().get_response("index.html", scope)
            path = "index.html"
        if path in ("", ".", "index.html") or path.endswith("/"):  # html=True maps dirs to index
            response.headers["Cache-Control"] = "no-cache"
        return response


def create_app(config: Settings, api: FastAPI) -> FastAPI:
    """The served app: ``api`` under /api, the built SPA at / (when configured)."""
    production = config.environment == "production"
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.mount("/api", api)
    if config.static_dir:
        app.mount("/", SPAStaticFiles(directory=config.static_dir, html=True), name="spa")

    @app.middleware("http")
    async def security_headers(  # pyright: ignore[reportUnusedFunction]
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        if production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
            response.headers["Content-Security-Policy"] = CONTENT_SECURITY_POLICY
        return response

    return app


api = create_api(settings.environment == "production")
app = create_app(settings, api)
