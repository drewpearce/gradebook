import datetime as dt
import uuid

import bcrypt
import jwt

from app.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(teacher_id: uuid.UUID) -> str:
    now = dt.datetime.now(dt.UTC)
    payload = {
        "sub": str(teacher_id),
        "iat": now,
        "exp": now + dt.timedelta(minutes=settings.access_token_expire_minutes),
    }
    # PyJWT's `key` param type carries an Unknown from its optional cryptography
    # backend (unused for HS256); the call itself is fully typed here.
    return jwt.encode(  # pyright: ignore[reportUnknownMemberType]
        payload, settings.secret_key, algorithm=settings.jwt_algorithm
    )


def decode_token(token: str) -> uuid.UUID:
    """Return the teacher id from a valid token.

    Raises ``jwt.InvalidTokenError`` (expired / bad signature / malformed) or
    ``ValueError`` / ``KeyError`` if the ``sub`` claim isn't a UUID.
    """
    payload = jwt.decode(  # pyright: ignore[reportUnknownMemberType]
        token, settings.secret_key, algorithms=[settings.jwt_algorithm]
    )
    return uuid.UUID(payload["sub"])
