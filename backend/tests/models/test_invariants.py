from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.audience import assignment_applies_to_student
from app.models import (
    Assignment,
    Category,
    Class,
    GradeLevel,
    Score,
    Student,
    Subject,
)


def _class_with_grade_level(
    session: Session, class_name: str, grade_level_name: str = "1st"
) -> tuple[Class, GradeLevel]:
    class_ = Class(name=class_name)
    grade_level = GradeLevel(class_=class_, name=grade_level_name)
    session.add_all([class_, grade_level])
    session.flush()
    return class_, grade_level


def _subject_with_category(
    session: Session, class_: Class, subject_name: str
) -> tuple[Subject, Category]:
    subject = Subject(class_=class_, name=subject_name)
    category = Category(subject=subject, name="All", weight=Decimal("100"))
    session.add_all([subject, category])
    session.flush()
    return subject, category


def test_student_grade_level_must_belong_to_its_class(db_session: Session) -> None:
    class_a, _ = _class_with_grade_level(db_session, "A")
    _, grade_level_b = _class_with_grade_level(db_session, "B")

    db_session.add(Student(class_=class_a, grade_level=grade_level_b, name="Mismatch"))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_assignment_category_must_belong_to_its_subject(db_session: Session) -> None:
    class_, _ = _class_with_grade_level(db_session, "A")
    math, _ = _subject_with_category(db_session, class_, "Math")
    _, reading_category = _subject_with_category(db_session, class_, "Reading")

    db_session.add(
        Assignment(subject=math, category=reading_category, name="X", max_points=Decimal("10"))
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_duplicate_score_rejected(db_session: Session) -> None:
    class_, grade_level = _class_with_grade_level(db_session, "A")
    subject, category = _subject_with_category(db_session, class_, "Math")
    assignment = Assignment(
        subject=subject, category=category, name="Quiz", max_points=Decimal("10")
    )
    student = Student(class_=class_, grade_level=grade_level, name="Sam")
    db_session.add_all([assignment, student])
    db_session.flush()

    db_session.add(Score(student=student, assignment=assignment, points_earned=Decimal("8")))
    db_session.flush()
    db_session.add(Score(student=student, assignment=assignment, points_earned=Decimal("9")))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_category_weight_out_of_range_rejected(db_session: Session) -> None:
    class_, _ = _class_with_grade_level(db_session, "A")
    subject = Subject(class_=class_, name="Math")
    db_session.add(Category(subject=subject, name="Bad", weight=Decimal("150")))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_negative_score_rejected(db_session: Session) -> None:
    class_, grade_level = _class_with_grade_level(db_session, "A")
    subject, category = _subject_with_category(db_session, class_, "Math")
    assignment = Assignment(
        subject=subject, category=category, name="Quiz", max_points=Decimal("10")
    )
    student = Student(class_=class_, grade_level=grade_level, name="Sam")
    db_session.add_all([assignment, student])
    db_session.flush()

    db_session.add(Score(student=student, assignment=assignment, points_earned=Decimal("-1")))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_audience_membership_and_helper(db_session: Session) -> None:
    class_ = Class(name="Combined")
    first = GradeLevel(class_=class_, name="1st", position=1)
    second = GradeLevel(class_=class_, name="2nd", position=2)
    db_session.add_all([class_, first, second])
    db_session.flush()
    subject, category = _subject_with_category(db_session, class_, "Math")

    assignment = Assignment(
        subject=subject, category=category, name="Worksheet", max_points=Decimal("10")
    )
    assignment.audience = [first]  # 1st grade only
    first_grader = Student(class_=class_, grade_level=first, name="One")
    second_grader = Student(class_=class_, grade_level=second, name="Two")
    db_session.add_all([assignment, first_grader, second_grader])
    db_session.flush()

    assert assignment_applies_to_student(first_grader, assignment) is True
    assert assignment_applies_to_student(second_grader, assignment) is False

    # An empty Audience applies to every Grade Level.
    assignment.audience = []
    db_session.flush()
    assert assignment_applies_to_student(first_grader, assignment) is True
    assert assignment_applies_to_student(second_grader, assignment) is True
