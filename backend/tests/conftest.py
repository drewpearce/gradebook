from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

import app.models  # noqa: F401  # pyright: ignore[reportUnusedImport]  (registers tables)
from app.config import settings
from app.db import Base
from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    engine = create_engine(settings.database_url)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def db_session(engine: Engine) -> Iterator[Session]:
    """A Session over a rolled-back transaction with a freshly built schema.

    Postgres DDL is transactional, so ``create_all`` + ``rollback`` gives each test
    an isolated schema and leaves the database untouched afterwards. The savepoint
    join mode lets tests call ``commit()`` without escaping the outer rollback.
    """
    connection = engine.connect()
    transaction = connection.begin()
    Base.metadata.create_all(bind=connection)
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
