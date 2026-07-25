from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.deps import get_current_teacher
from app.auth.security import hash_password
from app.db import get_db
from app.main import app
from app.models import Teacher

TEACHER_USERNAME = "teacher"
TEACHER_PASSWORD = "s3cret-pass"


@pytest.fixture
def teacher_credentials() -> tuple[str, str]:
    return TEACHER_USERNAME, TEACHER_PASSWORD


@pytest.fixture
def teacher(db_session: Session) -> Teacher:
    teacher = Teacher(username=TEACHER_USERNAME, password_hash=hash_password(TEACHER_PASSWORD))
    db_session.add(teacher)
    db_session.flush()
    return teacher


@pytest.fixture
def anon_client(db_session: Session) -> Iterator[TestClient]:
    """Client with the real auth dependency enforced (only the DB is overridden)."""
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def client(db_session: Session, teacher: Teacher) -> Iterator[TestClient]:
    """Auth-bypassed client for CRUD/grade tests: overrides both the DB session and
    the current-teacher dependency, so those tests don't each have to log in."""
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_teacher] = lambda: teacher
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
