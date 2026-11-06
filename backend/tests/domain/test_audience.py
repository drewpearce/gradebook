from uuid import uuid4

from app.domain.audience import applies_to

FIRST = uuid4()
SECOND = uuid4()


def test_listed_grade_level_applies() -> None:
    assert applies_to({FIRST}, FIRST) is True


def test_unlisted_grade_level_does_not_apply() -> None:
    assert applies_to({FIRST}, SECOND) is False


def test_empty_audience_applies_to_every_grade_level() -> None:
    assert applies_to(frozenset(), FIRST) is True
    assert applies_to([], SECOND) is True
