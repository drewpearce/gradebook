from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.api.deps import SessionDep
from app.auth.security import decode_token
from app.models import Teacher

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_teacher(
    token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep
) -> Teacher:
    credentials_exception = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        teacher_id = decode_token(token)
    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise credentials_exception from None
    teacher = session.get(Teacher, teacher_id)
    if teacher is None:
        raise credentials_exception
    return teacher


CurrentTeacher = Annotated[Teacher, Depends(get_current_teacher)]
