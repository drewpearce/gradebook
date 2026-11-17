from collections.abc import Awaitable, Callable

from fastapi import Depends, FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from starlette.types import Scope

from app.api.routers import classes, coursework, grades, scores, students
from app.auth import router as auth_router
from app.auth.deps import get_current_teacher
from app.config import settings

_prod = settings.environment == "production"

# The JSON API, mounted under /api (the SPA owns every other path).
api = FastAPI(
    title="Gradebook API",
    docs_url=None if _prod else "/docs",
    redoc_url=None if _prod else "/redoc",
    openapi_url=None if _prod else "/openapi.json",
)


@api.get("/health")
def health() -> dict[str, str]:
    """Liveness check. Deliberately does not touch the database."""
    return {"status": "ok"}


# Open: authentication.
api.include_router(auth_router.router)

# Protected: every data endpoint requires a valid Teacher token.
_auth = [Depends(get_current_teacher)]
api.include_router(classes.router, dependencies=_auth)
api.include_router(students.router, dependencies=_auth)
api.include_router(coursework.router, dependencies=_auth)
api.include_router(scores.router, dependencies=_auth)
api.include_router(grades.router, dependencies=_auth)


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


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/api", api)
if settings.static_dir:
    app.mount("/", SPAStaticFiles(directory=settings.static_dir, html=True), name="spa")


@app.middleware("http")
async def security_headers(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    if _prod:
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
        )
    return response
