"""Pure Subject-Grade computation, per ADR-0002.

No database, no ORM: this operates on plain value objects so it can be unit-tested
exhaustively and reused by the API (#5) and the Grades view (#10). The caller maps
its data (ORM rows, request payloads) into a ``GradeInput``.

Policy (ADR-0002): a Category's percentage is computed only over the Assignments a
Student has actually been **scored** on within their Audience — unscored applicable
Assignments are excluded, not zeroed. If any weighted Category has no scored
applicable Assignment the Subject Grade is **Incomplete**; only when every weighted
Category has content, and the positive weights total exactly 100, is a numeric
Grade produced, as the weighted roll-up of the Categories (no re-scaling). Weights
that do not total 100 make the Grade Incomplete (soft rule: never rejected on save).
"""

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from app.domain.audience import applies_to

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
    """Everything needed to compute one Student's Grade in one Subject.

    Precondition the caller is responsible for: ``scale`` covers 0 (includes a
    band such as F at ``min_percent`` 0) so every numeric percentage maps to a
    Letter.
    """

    student_grade_level_id: UUID
    categories: Sequence[CategoryWeight]
    assignments: Sequence[AssignmentScore]
    scale: Sequence[ScaleBand]


@dataclass(frozen=True)
class CategoryResult:
    """A Category's contribution, for explainability. ``percent is None`` when the
    Student has no scored applicable Assignment in this Category.
    ``applicable_count`` is the number of Assignments in the Category whose Audience
    applies to the Student (scored or not)."""

    category_id: UUID
    weight: Decimal
    points_earned: Decimal
    points_possible: Decimal
    percent: Decimal | None
    scored_count: int
    applicable_count: int


@dataclass(frozen=True)
class SubjectGrade:
    """The computed Grade. ``percent`` and ``letter`` are ``None`` iff Incomplete.

    Two causes make it Incomplete, and both are reported together:
    ``incomplete_category_ids`` names the empty weighted Categories, and
    ``weights_not_100`` is set when ``weights_total`` (the sum of the positive
    weights) is not exactly 100.
    """

    is_incomplete: bool
    percent: Decimal | None
    letter: str | None
    categories: tuple[CategoryResult, ...]
    incomplete_category_ids: tuple[UUID, ...]
    weights_total: Decimal
    weights_not_100: bool


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


def compute_subject_grade(grade_input: GradeInput) -> SubjectGrade:
    """Compute a Student's Subject Grade from their Scores, Audience, and weights.

    A Category's percentage is points-based — ``Σ points_earned / Σ max_points``
    over the scored applicable Assignments (one fraction, not a mean of per-
    Assignment percentages), so Assignments with larger ``max_points`` carry
    proportionally more weight within the Category.

    The Grade is Incomplete when a weighted Category is empty or when the positive
    weights do not total exactly 100 (a soft rule, see ADR-0002: it never blocks a
    save). Assumes ``grade_input.scale`` covers 0; see ``GradeInput``.
    """
    applicable_by_category: dict[UUID, list[AssignmentScore]] = {}
    for assignment in grade_input.assignments:
        if applies_to(assignment.audience_grade_level_ids, grade_input.student_grade_level_id):
            applicable_by_category.setdefault(assignment.category_id, []).append(assignment)

    results: list[CategoryResult] = []
    incomplete_category_ids: list[UUID] = []
    weighted: list[tuple[Decimal, Decimal]] = []  # (percent, weight) of complete Categories
    for category in grade_input.categories:
        applicable = applicable_by_category.get(category.category_id, [])
        # Only scored Assignments count — blanks are excluded from both sides.
        scored: list[tuple[Decimal, Decimal]] = [
            (a.points_earned, a.max_points) for a in applicable if a.points_earned is not None
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
                applicable_count=len(applicable),
            )
        )
        if category.weight > 0:
            if percent is None:
                incomplete_category_ids.append(category.category_id)
            else:
                weighted.append((percent, category.weight))

    weights_total = sum((c.weight for c in grade_input.categories if c.weight > 0), Decimal(0))
    weights_not_100 = weights_total != _HUNDRED
    if incomplete_category_ids or weights_not_100:
        return SubjectGrade(
            is_incomplete=True,
            percent=None,
            letter=None,
            categories=tuple(results),
            incomplete_category_ids=tuple(incomplete_category_ids),
            weights_total=weights_total,
            weights_not_100=weights_not_100,
        )

    # Every weighted Category has a percent and the weights total exactly 100, so
    # this is ADR-0002's roll-up with no re-scaling.
    weighted_sum = sum((p * w for p, w in weighted), Decimal(0))
    percent = (weighted_sum / _HUNDRED).quantize(_CENT, rounding=ROUND_HALF_UP)
    return SubjectGrade(
        is_incomplete=False,
        percent=percent,
        letter=letter_for_percent(percent, grade_input.scale),
        categories=tuple(results),
        incomplete_category_ids=(),
        weights_total=weights_total,
        weights_not_100=False,
    )
