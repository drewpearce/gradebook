"""Bridge the ORM to the pure grade-computation module (app.domain.grades).

Loads the Subject's Categories, Assignments (with Audience) and Grading Scale, plus
a Student's Scores, builds a ``GradeInput``, runs ``compute_subject_grade``, and
maps the result to the API's ``GradeResponse``. The grade policy itself lives in
the domain module; this module only maps.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.grades import (
    AssignmentScore,
    CategoryResult,
    CategoryWeight,
    GradeInput,
    ScaleBand,
    compute_subject_grade,
)
from app.models import Assignment, Category, GradeBand, GradingScale, Score, Student, Subject
from app.schemas.grade import CategoryBreakdown, GradeResponse, IncompleteReason

_CENT = Decimal("0.01")


@dataclass
class _SubjectData:
    """The Subject-wide inputs, loaded once and reused across a roster."""

    categories: list[Category]
    assignments: list[Assignment]
    scale: list[ScaleBand]


def _load_subject_data(session: Session, subject: Subject) -> _SubjectData:
    categories = list(
        session.scalars(
            select(Category).where(Category.subject_id == subject.id).order_by(Category.name)
        )
    )
    assignments = list(
        session.scalars(
            select(Assignment)
            .where(Assignment.subject_id == subject.id)
            .options(selectinload(Assignment.audience))
        )
    )
    scale: list[ScaleBand] = []
    grading_scale = session.scalar(
        select(GradingScale).where(GradingScale.class_id == subject.class_id)
    )
    if grading_scale is not None:
        bands = session.scalars(
            select(GradeBand).where(GradeBand.grading_scale_id == grading_scale.id)
        )
        scale = [ScaleBand(band.letter, band.min_percent) for band in bands]
    return _SubjectData(categories=categories, assignments=assignments, scale=scale)


def _empty_category_message(name: str, category: CategoryResult) -> str:
    if category.applicable_count == 0:
        return f"{name} has no assignments for this grade level yet."
    return f"{name} has no scored assignments yet."


def _grade_response(
    data: _SubjectData,
    *,
    student_id: UUID,
    student_grade_level_id: UUID,
    subject_id: UUID,
    scores: dict[UUID, Decimal],
) -> GradeResponse:
    grade_input = GradeInput(
        student_grade_level_id=student_grade_level_id,
        categories=[CategoryWeight(c.id, c.weight) for c in data.categories],
        assignments=[
            AssignmentScore(
                assignment_id=a.id,
                category_id=a.category_id,
                max_points=a.max_points,
                audience_grade_level_ids=frozenset(gl.id for gl in a.audience),
                points_earned=scores.get(a.id),
            )
            for a in data.assignments
        ],
        scale=data.scale,
    )
    result = compute_subject_grade(grade_input)

    name_by_id = {c.id: c.name for c in data.categories}
    breakdown = [
        CategoryBreakdown(
            category_id=cr.category_id,
            name=name_by_id.get(cr.category_id, ""),
            weight=cr.weight,
            # Rounded for display only; the roll-up used the exact value.
            percent=None if cr.percent is None else cr.percent.quantize(_CENT, ROUND_HALF_UP),
            points_earned=cr.points_earned,
            points_possible=cr.points_possible,
            scored_count=cr.scored_count,
        )
        for cr in result.categories
    ]

    category_by_id = {cr.category_id: cr for cr in result.categories}
    reasons = [
        IncompleteReason(
            code="empty_category",
            category_id=category_id,
            message=_empty_category_message(
                name_by_id.get(category_id, "Category"), category_by_id[category_id]
            ),
        )
        for category_id in result.incomplete_category_ids
    ]
    if result.weights_not_100:
        reasons.append(
            IncompleteReason(
                code="weights_not_100",
                message=f"Category weights total {result.weights_total}%, must be 100%.",
            )
        )

    return GradeResponse(
        student_id=student_id,
        subject_id=subject_id,
        is_incomplete=result.is_incomplete,
        percent=result.percent,
        letter=result.letter,
        categories=breakdown,
        incomplete_reasons=reasons,
    )


def _scores_for(
    session: Session, student_ids: list[UUID], assignment_ids: list[UUID]
) -> dict[UUID, dict[UUID, Decimal]]:
    """Map student_id → {assignment_id → points_earned} in a single query."""
    by_student: dict[UUID, dict[UUID, Decimal]] = {sid: {} for sid in student_ids}
    if not student_ids or not assignment_ids:
        return by_student
    rows = session.scalars(
        select(Score).where(
            Score.student_id.in_(student_ids), Score.assignment_id.in_(assignment_ids)
        )
    )
    for score in rows:
        by_student.setdefault(score.student_id, {})[score.assignment_id] = score.points_earned
    return by_student


def grade_for_student(session: Session, student: Student, subject: Subject) -> GradeResponse:
    data = _load_subject_data(session, subject)
    scores = _scores_for(session, [student.id], [a.id for a in data.assignments])
    return _grade_response(
        data,
        student_id=student.id,
        student_grade_level_id=student.grade_level_id,
        subject_id=subject.id,
        scores=scores[student.id],
    )


def grades_for_roster(
    session: Session, students: list[Student], subject: Subject
) -> list[GradeResponse]:
    data = _load_subject_data(session, subject)
    scores = _scores_for(session, [s.id for s in students], [a.id for a in data.assignments])
    return [
        _grade_response(
            data,
            student_id=s.id,
            student_grade_level_id=s.grade_level_id,
            subject_id=subject.id,
            scores=scores.get(s.id, {}),
        )
        for s in students
    ]
