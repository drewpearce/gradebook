from fastapi import FastAPI

from app.api.routers import classes, coursework, grades, scores, students

app = FastAPI(title="Gradebook API")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check. Deliberately does not touch the database."""
    return {"status": "ok"}


app.include_router(classes.router)
app.include_router(students.router)
app.include_router(coursework.router)
app.include_router(scores.router)
app.include_router(grades.router)
