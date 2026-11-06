from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import inspect
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm import Session

from app.db import Base, get_db

SessionDep = Annotated[Session, Depends(get_db)]


def get_or_404[ModelT: Base](
    session: Session, model: type[ModelT], ident: UUID, name: str
) -> ModelT:
    """Fetch a row by primary key or raise 404 with a domain-friendly name."""
    obj = session.get(model, ident)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"{name} not found")
    return obj


def commit_or_conflict(session: Session) -> None:
    """Commit, translating a DB constraint violation into a 409 rather than a 500."""
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Conflicts with an existing record or violates a constraint.",
        ) from exc
    except DataError as exc:
        session.rollback()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="A value is out of range or not storable.",
        ) from exc


def apply_patch(obj: Base, data: dict[str, object]) -> None:
    """Set each field from a PATCH body; an explicit null on a NOT NULL column is a 422."""
    columns = inspect(type(obj)).columns
    for field, value in data.items():
        if value is None and not columns[field].nullable:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"{field} cannot be null"
            )
        setattr(obj, field, value)
