from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, make_url
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
    """The test database engine. Refuses any database whose name does not end in ``_test``.

    This stops a test run from touching the dev database (or another project's
    Postgres) when ``DATABASE_URL`` points at the wrong place.
    """
    database = make_url(settings.database_url).database or ""
    if not database.endswith("_test"):
        pytest.exit(
            f"Refusing to run DB tests against {database!r}: the database name must end in "
            "'_test'. Set DATABASE_URL to the test database (see backend/README.md).",
            returncode=2,
        )
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
