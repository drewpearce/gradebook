from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import TimestampMixin, UUIDMixin


class Teacher(UUIDMixin, TimestampMixin, Base):
    """The sole user of the app in v1. Holds only login credentials — ownership of
    Classes is implicit (single teacher) and not modelled."""

    __tablename__ = "teachers"

    username: Mapped[str] = mapped_column(String(80), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
