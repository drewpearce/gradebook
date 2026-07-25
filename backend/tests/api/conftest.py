from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import get_db
from app.main import app


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    """TestClient whose requests run against the test's rolled-back transaction.

    Overrides the ``get_db`` dependency so the API and the test share one Session;
    the override returns the session directly (not a generator), so FastAPI never
    closes it — the ``db_session`` fixture owns its lifecycle and rollback.
    """
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
