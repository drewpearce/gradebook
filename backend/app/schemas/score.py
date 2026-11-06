import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ScoreUpsert(BaseModel):
    points_earned: Decimal = Field(ge=0, max_digits=6, decimal_places=2)


class ScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID
    assignment_id: uuid.UUID
    points_earned: Decimal
    created_at: datetime
    updated_at: datetime
