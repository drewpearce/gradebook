import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    ForeignKeyConstraint,
    Numeric,
    String,
    Table,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.class_ import Class, GradeLevel
    from app.models.score import Score


# Audience: the set of Grade Levels an Assignment applies to.
assignment_audience = Table(
    "assignment_audience",
    Base.metadata,
    Column[uuid.UUID](
        "assignment_id",
        Uuid,
        ForeignKey("assignments.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column[uuid.UUID](
        "grade_level_id",
        Uuid,
        ForeignKey("grade_levels.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Subject(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "subjects"
    __table_args__ = (UniqueConstraint("class_id", "name"),)

    class_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("classes.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(80))

    class_: Mapped["Class"] = relationship(back_populates="subjects")
    categories: Mapped[list["Category"]] = relationship(
        back_populates="subject", cascade="all, delete-orphan", passive_deletes=True
    )
    assignments: Mapped[list["Assignment"]] = relationship(
        back_populates="subject",
        cascade="all, delete-orphan",
        foreign_keys="Assignment.subject_id",
        passive_deletes=True,
    )


class Category(UUIDMixin, TimestampMixin, Base):
    """A weighted grouping of Assignments within a Subject."""

    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("subject_id", "name"),
        # Target for the assignments(subject_id, category_id) composite FK.
        UniqueConstraint("subject_id", "id"),
        CheckConstraint("weight >= 0 AND weight <= 100", name="weight_range"),
    )

    subject_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("subjects.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(80))
    weight: Mapped[Decimal] = mapped_column(Numeric(5, 2))

    subject: Mapped["Subject"] = relationship(back_populates="categories")
    assignments: Mapped[list["Assignment"]] = relationship(
        back_populates="category",
        foreign_keys="Assignment.category_id",
        passive_deletes=True,
    )


class Assignment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "assignments"
    __table_args__ = (
        # Cross-entity invariant: an Assignment's Category must belong to its
        # Subject. Kept ALONGSIDE the single-column subject_id / category_id FKs
        # below (which carry ON DELETE CASCADE) — this composite FK adds only the
        # (subject_id, category_id) consistency check. Both are needed; don't
        # collapse into one.
        ForeignKeyConstraint(
            ["subject_id", "category_id"],
            ["categories.subject_id", "categories.id"],
        ),
        CheckConstraint("max_points > 0", name="max_points_positive"),
    )

    subject_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("subjects.id", ondelete="CASCADE")
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("categories.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(160))
    max_points: Mapped[Decimal] = mapped_column(Numeric(6, 2))

    subject: Mapped["Subject"] = relationship(
        back_populates="assignments", foreign_keys=[subject_id]
    )
    category: Mapped["Category"] = relationship(
        back_populates="assignments", foreign_keys=[category_id]
    )
    audience: Mapped[list["GradeLevel"]] = relationship(
        secondary=assignment_audience, back_populates="assignments"
    )
    scores: Mapped[list["Score"]] = relationship(
        back_populates="assignment", cascade="all, delete-orphan", passive_deletes=True
    )
