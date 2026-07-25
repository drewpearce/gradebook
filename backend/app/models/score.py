import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Numeric,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.coursework import Assignment
    from app.models.roster import Student


class Score(UUIDMixin, TimestampMixin, Base):
    """The points a Student earned on a single Assignment."""

    __tablename__ = "scores"
    __table_args__ = (
        UniqueConstraint("student_id", "assignment_id"),
        CheckConstraint("points_earned >= 0", name="points_earned_non_negative"),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("students.id", ondelete="CASCADE")
    )
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("assignments.id", ondelete="CASCADE")
    )
    points_earned: Mapped[Decimal] = mapped_column(Numeric(6, 2))

    student: Mapped["Student"] = relationship(back_populates="scores")
    assignment: Mapped["Assignment"] = relationship(back_populates="scores")
