import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.types import NoNulStr


class ClassCreate(BaseModel):
    name: NoNulStr = Field(min_length=1, max_length=120)


class ClassUpdate(BaseModel):
    name: NoNulStr | None = Field(default=None, min_length=1, max_length=120)


class ClassRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_at: datetime
    updated_at: datetime


class GradeLevelCreate(BaseModel):
    name: NoNulStr = Field(min_length=1, max_length=40)
    position: int = Field(default=0, ge=0, le=10_000)


class GradeLevelUpdate(BaseModel):
    name: NoNulStr | None = Field(default=None, min_length=1, max_length=40)
    position: int | None = Field(default=None, ge=0, le=10_000)


class GradeLevelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    class_id: uuid.UUID
    name: str
    position: int
    created_at: datetime
    updated_at: datetime


class GradeBandInput(BaseModel):
    letter: NoNulStr = Field(min_length=1, max_length=4)
    min_percent: Decimal = Field(ge=0, le=100, max_digits=5, decimal_places=2)


class GradeBandRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    letter: str
    min_percent: Decimal


class GradingScaleUpsert(BaseModel):
    """Replace the Class's Grading Scale with these bands."""

    bands: list[GradeBandInput] = Field(min_length=1)


class GradingScaleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    class_id: uuid.UUID
    bands: list[GradeBandRead]


class StudentCounts(BaseModel):
    scores: int


class SubjectCounts(BaseModel):
    categories: int
    assignments: int
    scores: int


class CategoryCounts(BaseModel):
    assignments: int
    scores: int


class ClassTotals(BaseModel):
    students: int
    subjects: int
    categories: int
    assignments: int
    scores: int


class ClassCounts(BaseModel):
    """What deleting the Class (or one Student/Subject/Category in it) would take with it."""

    totals: ClassTotals
    students: dict[uuid.UUID, StudentCounts]
    subjects: dict[uuid.UUID, SubjectCounts]
    categories: dict[uuid.UUID, CategoryCounts]
