import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class SubjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class SubjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)


class SubjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    class_id: uuid.UUID
    name: str
    created_at: datetime
    updated_at: datetime


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    weight: Decimal = Field(ge=0, le=100)


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    weight: Decimal | None = Field(default=None, ge=0, le=100)


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subject_id: uuid.UUID
    name: str
    weight: Decimal
    created_at: datetime
    updated_at: datetime


class AssignmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    category_id: uuid.UUID
    max_points: Decimal = Field(gt=0)
    audience_grade_level_ids: list[uuid.UUID] = []


class AssignmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    category_id: uuid.UUID | None = None
    max_points: Decimal | None = Field(default=None, gt=0)
    # Omit to leave the Audience unchanged; send [] or null to clear it (⇒ all).
    audience_grade_level_ids: list[uuid.UUID] | None = None


class AssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subject_id: uuid.UUID
    category_id: uuid.UUID
    name: str
    max_points: Decimal
    audience_grade_level_ids: list[uuid.UUID]
    created_at: datetime
    updated_at: datetime
