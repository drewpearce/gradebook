from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.api.deps import SessionDep
from app.auth.deps import CurrentTeacher
from app.auth.schemas import TeacherRead, Token
from app.auth.security import create_access_token, verify_password
from app.models import Teacher

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep) -> Token:
    teacher = session.scalar(select(Teacher).where(Teacher.username == form.username))
    if teacher is None or not verify_password(form.password, teacher.password_hash):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(teacher.id))


@router.get("/me", response_model=TeacherRead)
def me(teacher: CurrentTeacher) -> Teacher:
    return teacher
