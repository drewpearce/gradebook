import uuid
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class CategoryBreakdown(BaseModel):
    category_id: uuid.UUID
    name: str
    weight: Decimal
    percent: Decimal | None
    points_earned: Decimal
    points_possible: Decimal
    scored_count: int


class IncompleteReason(BaseModel):
    code: Literal["empty_category", "weights_not_100"]
    message: str
    category_id: uuid.UUID | None = None


class GradeResponse(BaseModel):
    student_id: uuid.UUID
    subject_id: uuid.UUID
    is_incomplete: bool
    percent: Decimal | None
    letter: str | None
    categories: list[CategoryBreakdown]
    incomplete_reasons: list[IncompleteReason]


class RosterGrades(BaseModel):
    subject_id: uuid.UUID
    grades: list[GradeResponse]
