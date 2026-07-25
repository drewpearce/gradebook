import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.coursework import Assignment, Subject
    from app.models.roster import Student


class Class(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "classes"

    name: Mapped[str] = mapped_column(String(120))

    grade_levels: Mapped[list["GradeLevel"]] = relationship(
        back_populates="class_", cascade="all, delete-orphan", passive_deletes=True
    )
    students: Mapped[list["Student"]] = relationship(
        back_populates="class_",
        cascade="all, delete-orphan",
        foreign_keys="Student.class_id",
        passive_deletes=True,
    )
    subjects: Mapped[list["Subject"]] = relationship(
        back_populates="class_", cascade="all, delete-orphan", passive_deletes=True
    )
    grading_scale: Mapped["GradingScale | None"] = relationship(
        back_populates="class_",
        cascade="all, delete-orphan",
        uselist=False,
        passive_deletes=True,
    )


class GradeLevel(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "grade_levels"
    __table_args__ = (
        UniqueConstraint("class_id", "name"),
        # Target for the students(class_id, grade_level_id) composite FK.
        UniqueConstraint("class_id", "id"),
    )

    class_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("classes.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(40))
    position: Mapped[int] = mapped_column(default=0)

    class_: Mapped["Class"] = relationship(back_populates="grade_levels")
    students: Mapped[list["Student"]] = relationship(
        back_populates="grade_level",
        foreign_keys="Student.grade_level_id",
        passive_deletes=True,
    )
    assignments: Mapped[list["Assignment"]] = relationship(
        secondary="assignment_audience", back_populates="audience"
    )


class GradingScale(UUIDMixin, TimestampMixin, Base):
    """The cutoffs mapping a percentage Grade to a Letter Grade. One per Class."""

    __tablename__ = "grading_scales"

    class_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("classes.id", ondelete="CASCADE"), unique=True
    )

    class_: Mapped["Class"] = relationship(back_populates="grading_scale")
    bands: Mapped[list["GradeBand"]] = relationship(
        back_populates="grading_scale",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class GradeBand(UUIDMixin, TimestampMixin, Base):
    """One A–F band: its Letter Grade and inclusive lower percentage bound."""

    __tablename__ = "grade_bands"
    __table_args__ = (
        UniqueConstraint("grading_scale_id", "letter"),
        UniqueConstraint("grading_scale_id", "min_percent"),
        CheckConstraint("min_percent >= 0 AND min_percent <= 100", name="min_percent_range"),
    )

    grading_scale_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("grading_scales.id", ondelete="CASCADE")
    )
    letter: Mapped[str] = mapped_column(String(4))
    min_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2))

    grading_scale: Mapped["GradingScale"] = relationship(back_populates="bands")
