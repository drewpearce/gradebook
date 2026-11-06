import datetime as dt
import uuid

import bcrypt
import jwt

from app.config import settings

MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    # bcrypt 5 raises ValueError above 72 bytes (it does not truncate); callers must check.
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    if len(password.encode()) > MAX_PASSWORD_BYTES:
        return False
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
        payload, settings.secret_key, algorithm="HS256"
    )


def decode_token(token: str) -> uuid.UUID:
    """Return the teacher id from a valid token.

    Raises ``jwt.InvalidTokenError`` (expired / bad signature / malformed) or
    ``ValueError`` / ``KeyError`` if the ``sub`` claim isn't a UUID.
    """
    payload = jwt.decode(  # pyright: ignore[reportUnknownMemberType]
        token,
        settings.secret_key,
        algorithms=["HS256"],
        options={"require": ["exp", "sub"]},
    )
    return uuid.UUID(payload["sub"])
