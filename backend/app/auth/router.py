from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.api.deps import SessionDep
from app.auth.deps import CurrentTeacher
from app.auth.rate_limit import ip_limiter, pair_limiter
from app.auth.schemas import TeacherRead, Token
from app.auth.security import create_access_token, hash_password, verify_password
from app.config import settings
from app.models import Teacher

router = APIRouter(prefix="/auth", tags=["auth"])

# Verify against this when the username is unknown so the response takes about the
# same time as a wrong password for a real user — no timing oracle for enumeration.
_DUMMY_PASSWORD_HASH = hash_password("timing-equalizer")


@router.post("/login", response_model=Token)
def login(
    request: Request,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
) -> Token:
    ip = (settings.trust_proxy_ip_header and request.headers.get("Fly-Client-IP")) or (
        request.client.host if request.client else "unknown"
    )
    # Hit BEFORE verifying so a crash during verify still counts. Successes also count toward
    # the per-IP limit (a hit can't be undone per-key; 50/15min is ample for one teacher).
    pair_key = f"{ip}|{form.username}"
    waits = [pair_limiter.hit(pair_key), ip_limiter.hit(ip)]
    if retry_after := max((w for w in waits if w is not None), default=None):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )
    teacher = session.scalar(select(Teacher).where(Teacher.username == form.username))
    password_hash = teacher.password_hash if teacher is not None else _DUMMY_PASSWORD_HASH
    password_ok = verify_password(form.password, password_hash)
    if teacher is None or not password_ok:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    pair_limiter.reset(pair_key)
    return Token(access_token=create_access_token(teacher.id, teacher.password_hash))


@router.get("/me", response_model=TeacherRead)
def me(teacher: CurrentTeacher) -> Teacher:
    return teacher
