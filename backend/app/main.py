from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import classes, coursework, grades, scores, students
from app.auth import router as auth_router
from app.auth.deps import get_current_teacher
from app.config import settings

app = FastAPI(title="Gradebook API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],  # bearer token rides in Authorization; no cookies, so no credentials
)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check. Deliberately does not touch the database."""
    return {"status": "ok"}


# Open: authentication.
app.include_router(auth_router.router)

# Protected: every data endpoint requires a valid Teacher token.
_auth = [Depends(get_current_teacher)]
app.include_router(classes.router, dependencies=_auth)
app.include_router(students.router, dependencies=_auth)
app.include_router(coursework.router, dependencies=_auth)
app.include_router(scores.router, dependencies=_auth)
app.include_router(grades.router, dependencies=_auth)
