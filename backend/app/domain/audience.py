"""The Audience rule, pure (no ORM): which Grade Levels an Assignment applies to."""

from collections.abc import Collection
from uuid import UUID


def applies_to(audience_grade_level_ids: Collection[UUID], grade_level_id: UUID) -> bool:
    """Whether an Assignment with this Audience applies to a Grade Level.

    An empty Audience applies to every Grade Level — matching progressive
    disclosure, where a Class with a single Grade Level never sets an Audience.
    Otherwise the Assignment applies only to the listed Grade Levels. Per ADR-0002,
    an Assignment outside a Student's Audience is not counted for them — it is not
    a zero.
    """
    return not audience_grade_level_ids or grade_level_id in audience_grade_level_ids
