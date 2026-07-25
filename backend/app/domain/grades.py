"""Pure Subject-Grade computation, per ADR-0002.

No database, no ORM: this operates on plain value objects so it can be unit-tested
exhaustively and reused by the API (#5) and the Grades view (#10). The caller maps
its data (ORM rows, request payloads) into a ``GradeInput``.

Policy (ADR-0002): a Category's percentage is computed only over the Assignments a
Student has actually been **scored** on within their Audience — unscored applicable
Assignments are excluded, not zeroed. If any weighted Category has no scored
applicable Assignment the Subject Grade is **Incomplete**; only when every weighted
Category has content is a numeric Grade produced, as the weighted roll-up of the
Categories (weights sum to 100%, no re-scaling).
"""

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

_CENT = Decimal("0.01")
_HUNDRED = Decimal("100")


@dataclass(frozen=True)
class ScaleBand:
    """One Grading-Scale cutoff: a Letter Grade and its inclusive lower bound."""

    letter: str
    min_percent: Decimal


@dataclass(frozen=True)
class CategoryWeight:
    category_id: UUID
    weight: Decimal


@dataclass(frozen=True)
class AssignmentScore:
    """An Assignment plus, if any, this Student's Score on it.

    ``points_earned is None`` means the Assignment is unscored (blank) for this
    Student. An empty ``audience_grade_level_ids`` means the Assignment applies to
    every Grade Level (see ``CONTEXT.md``).
    """

    assignment_id: UUID
    category_id: UUID
    max_points: Decimal
    audience_grade_level_ids: frozenset[UUID]
    points_earned: Decimal | None


@dataclass(frozen=True)
class GradeInput:
    """Everything needed to compute one Student's Grade in one Subject."""

    student_grade_level_id: UUID
    categories: Sequence[CategoryWeight]
    assignments: Sequence[AssignmentScore]
    scale: Sequence[ScaleBand]


@dataclass(frozen=True)
class CategoryResult:
    """A Category's contribution, for explainability. ``percent is None`` when the
    Student has no scored applicable Assignment in this Category."""

    category_id: UUID
    weight: Decimal
    points_earned: Decimal
    points_possible: Decimal
    percent: Decimal | None
    scored_count: int


@dataclass(frozen=True)
class SubjectGrade:
    """The computed Grade. ``percent`` and ``letter`` are ``None`` iff Incomplete.

    ``incomplete_category_ids`` names the empty weighted Categories that caused the
    Incomplete, so the UI can tell the Teacher what to enter.
    """

    is_incomplete: bool
    percent: Decimal | None
    letter: str | None
    categories: tuple[CategoryResult, ...]
    incomplete_category_ids: tuple[UUID, ...]


def _applies(assignment: AssignmentScore, grade_level_id: UUID) -> bool:
    """Whether an Assignment is in the Student's Audience (empty Audience ⇒ all)."""
    return (
        not assignment.audience_grade_level_ids
        or grade_level_id in assignment.audience_grade_level_ids
    )


def letter_for_percent(percent: Decimal, scale: Sequence[ScaleBand]) -> str | None:
    """The Letter Grade for a percentage: the highest band it reaches.

    Bands are inclusive lower bounds. Returns ``None`` only when no band sits at or
    below ``percent`` (a scale that doesn't cover 0).
    """
    best: ScaleBand | None = None
    for band in scale:
        if percent >= band.min_percent and (best is None or band.min_percent > best.min_percent):
            best = band
    return best.letter if best is not None else None


def compute_subject_grade(inp: GradeInput) -> SubjectGrade:
    """Compute a Student's Subject Grade from their Scores, Audience, and weights."""
    applicable_by_category: dict[UUID, list[AssignmentScore]] = {}
    for assignment in inp.assignments:
        if _applies(assignment, inp.student_grade_level_id):
            applicable_by_category.setdefault(assignment.category_id, []).append(assignment)

    results: list[CategoryResult] = []
    incomplete_category_ids: list[UUID] = []
    for category in inp.categories:
        # Only scored Assignments count — blanks are excluded from both sides.
        scored: list[tuple[Decimal, Decimal]] = [
            (a.points_earned, a.max_points)
            for a in applicable_by_category.get(category.category_id, [])
            if a.points_earned is not None
        ]
        earned = sum((pe for pe, _ in scored), Decimal(0))
        possible = sum((mp for _, mp in scored), Decimal(0))
        # max_points > 0 is a DB invariant, so `possible` is 0 only when nothing is
        # scored — in which case the Category is empty (percent None).
        percent = (earned / possible * _HUNDRED) if scored else None
        results.append(
            CategoryResult(
                category_id=category.category_id,
                weight=category.weight,
                points_earned=earned,
                points_possible=possible,
                percent=percent,
                scored_count=len(scored),
            )
        )
        if category.weight > 0 and percent is None:
            incomplete_category_ids.append(category.category_id)

    weighted = [r for r in results if r.weight > 0]
    # Incomplete if any weighted Category is empty, or there is nothing to weigh.
    if incomplete_category_ids or not weighted:
        return SubjectGrade(
            is_incomplete=True,
            percent=None,
            letter=None,
            categories=tuple(results),
            incomplete_category_ids=tuple(incomplete_category_ids),
        )

    # Weighted mean over the (exact) Category percentages; no re-scaling.
    total_weight = sum((r.weight for r in weighted), Decimal(0))
    weighted_sum = sum(
        (r.percent * r.weight for r in weighted if r.percent is not None), Decimal(0)
    )
    percent = (weighted_sum / total_weight).quantize(_CENT, rounding=ROUND_HALF_UP)
    return SubjectGrade(
        is_incomplete=False,
        percent=percent,
        letter=letter_for_percent(percent, inp.scale),
        categories=tuple(results),
        incomplete_category_ids=(),
    )
