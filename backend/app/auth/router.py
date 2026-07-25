from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.api.deps import SessionDep
from app.auth.deps import CurrentTeacher
from app.auth.schemas import TeacherRead, Token
from app.auth.security import create_access_token, hash_password, verify_password
from app.models import Teacher

router = APIRouter(prefix="/auth", tags=["auth"])

# Verify against this when the username is unknown so the response takes about the
# same time as a wrong password for a real user — no timing oracle for enumeration.
_DUMMY_PASSWORD_HASH = hash_password("timing-equalizer")


@router.post("/login", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep) -> Token:
    teacher = session.scalar(select(Teacher).where(Teacher.username == form.username))
    password_hash = teacher.password_hash if teacher is not None else _DUMMY_PASSWORD_HASH
    password_ok = verify_password(form.password, password_hash)
    if teacher is None or not password_ok:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(teacher.id))


@router.get("/me", response_model=TeacherRead)
def me(teacher: CurrentTeacher) -> Teacher:
    return teacher
