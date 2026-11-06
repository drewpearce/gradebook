import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.types import NoNulStr


class StudentCreate(BaseModel):
    name: NoNulStr = Field(min_length=1, max_length=120)
    grade_level_id: uuid.UUID


class StudentUpdate(BaseModel):
    name: NoNulStr | None = Field(default=None, min_length=1, max_length=120)
    grade_level_id: uuid.UUID | None = None


class StudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    class_id: uuid.UUID
    grade_level_id: uuid.UUID
    name: str
    created_at: datetime
    updated_at: datetime
