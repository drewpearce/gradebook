from collections.abc import Callable, Iterator

import pytest
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.auth.security import verify_password
from app.cli import create_teacher
from app.db import Base
from app.models import Teacher

SessionFactory = Callable[[], Session]


@pytest.fixture
def factory(engine: Engine) -> Iterator[SessionFactory]:
    """Session factory on a rolled-back connection (see ``db_session``)."""
    connection = engine.connect()
    transaction = connection.begin()
    Base.metadata.create_all(bind=connection)

    def make() -> Session:
        return Session(bind=connection, join_transaction_mode="create_savepoint")

    try:
        yield make
    finally:
        transaction.rollback()
        connection.close()


def _teachers(factory: SessionFactory) -> list[Teacher]:
    with factory() as session:
        return list(session.scalars(select(Teacher)))


def test_creates_the_first_teacher(factory: SessionFactory) -> None:
    create_teacher("katie", "long-enough-pw", session_factory=factory)
    [teacher] = _teachers(factory)
    assert teacher.username == "katie"
    assert verify_password("long-enough-pw", teacher.password_hash)


def test_resets_the_password_of_an_existing_username(factory: SessionFactory) -> None:
    create_teacher("katie", "long-enough-pw", session_factory=factory)
    create_teacher("katie", "another-good-pw", session_factory=factory)
    [teacher] = _teachers(factory)
    assert verify_password("another-good-pw", teacher.password_hash)


def test_refuses_a_second_new_username_and_names_the_existing_one(
    factory: SessionFactory,
) -> None:
    create_teacher("katie", "long-enough-pw", session_factory=factory)
    with pytest.raises(SystemExit, match="katie"):
        create_teacher("katy", "long-enough-pw", session_factory=factory)
    assert [t.username for t in _teachers(factory)] == ["katie"]


def test_allows_a_second_teacher_with_the_flag(factory: SessionFactory) -> None:
    create_teacher("katie", "long-enough-pw", session_factory=factory)
    create_teacher("aide", "long-enough-pw", session_factory=factory, allow_second_teacher=True)
    assert sorted(t.username for t in _teachers(factory)) == ["aide", "katie"]


@pytest.mark.parametrize("password", ["short", "x" * 73, "é" * 40])
def test_refuses_a_password_that_is_too_short_or_over_72_bytes(
    factory: SessionFactory, password: str
) -> None:
    with pytest.raises(SystemExit):
        create_teacher("katie", password, session_factory=factory)
    assert _teachers(factory) == []
