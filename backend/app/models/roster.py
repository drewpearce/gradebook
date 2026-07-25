import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, ForeignKeyConstraint, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.class_ import Class, GradeLevel
    from app.models.score import Score


class Student(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "students"
    __table_args__ = (
        # Cross-entity invariant: a Student's Grade Level must belong to their
        # Class. Kept ALONGSIDE the single-column class_id / grade_level_id FKs
        # below (which carry ON DELETE CASCADE) — this composite FK adds only the
        # (class_id, grade_level_id) consistency check. Both are needed; don't
        # collapse into one.
        ForeignKeyConstraint(
            ["class_id", "grade_level_id"],
            ["grade_levels.class_id", "grade_levels.id"],
        ),
    )

    class_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("classes.id", ondelete="CASCADE"))
    grade_level_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("grade_levels.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(120))

    class_: Mapped["Class"] = relationship(back_populates="students", foreign_keys=[class_id])
    grade_level: Mapped["GradeLevel"] = relationship(
        back_populates="students", foreign_keys=[grade_level_id]
    )
    scores: Mapped[list["Score"]] = relationship(
        back_populates="student", cascade="all, delete-orphan", passive_deletes=True
    )
