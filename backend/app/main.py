from fastapi import FastAPI

app = FastAPI(title="Gradebook API")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check. Deliberately does not touch the database."""
    return {"status": "ok"}
