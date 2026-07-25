import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ClassCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class ClassUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)


class ClassRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_at: datetime
    updated_at: datetime


class GradeLevelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    position: int = 0


class GradeLevelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=40)
    position: int | None = None


class GradeLevelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    class_id: uuid.UUID
    name: str
    position: int
    created_at: datetime
    updated_at: datetime


class GradeBandInput(BaseModel):
    letter: str = Field(min_length=1, max_length=4)
    min_percent: Decimal = Field(ge=0, le=100)


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
