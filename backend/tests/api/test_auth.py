import datetime as dt
from uuid import UUID, uuid4

import jwt
from fastapi.testclient import TestClient
from httpx import Response

from app.auth.security import create_access_token
from app.config import settings
from app.models import Teacher


def _login(client: TestClient, username: str, password: str) -> Response:
    return client.post("/auth/login", data={"username": username, "password": password})


def _forge_token(sub: UUID, *, secret: str | None = None, expires_in_minutes: int = 60) -> str:
    now = dt.datetime.now(dt.UTC)
    return jwt.encode(
        {"sub": str(sub), "iat": now, "exp": now + dt.timedelta(minutes=expires_in_minutes)},
        secret or settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_health_is_open(anon_client: TestClient) -> None:
    assert anon_client.get("/health").status_code == 200


def test_unauthenticated_data_request_is_rejected(anon_client: TestClient) -> None:
    assert anon_client.get("/classes").status_code == 401


def test_login_issues_a_usable_token(
    anon_client: TestClient, teacher: Teacher, teacher_credentials: tuple[str, str]
) -> None:
    username, password = teacher_credentials
    response = _login(anon_client, username, password)
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    headers = {"Authorization": f"Bearer {body['access_token']}"}

    assert anon_client.get("/classes", headers=headers).status_code == 200
    me = anon_client.get("/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["username"] == username


def test_login_with_wrong_password_is_rejected(
    anon_client: TestClient, teacher: Teacher, teacher_credentials: tuple[str, str]
) -> None:
    username, _ = teacher_credentials
    assert _login(anon_client, username, "not-the-password").status_code == 401


def test_login_unknown_user_is_rejected(anon_client: TestClient) -> None:
    assert _login(anon_client, "nobody", "whatever").status_code == 401


def test_malformed_token_is_rejected(anon_client: TestClient) -> None:
    assert anon_client.get("/classes", headers=_auth("not-a-real-jwt")).status_code == 401


def test_expired_token_is_rejected(anon_client: TestClient, teacher: Teacher) -> None:
    token = _forge_token(teacher.id, expires_in_minutes=-5)
    assert anon_client.get("/classes", headers=_auth(token)).status_code == 401


def test_wrong_signature_is_rejected(anon_client: TestClient, teacher: Teacher) -> None:
    # Valid shape, correct teacher, but signed with the wrong secret.
    token = _forge_token(teacher.id, secret="a-different-secret-of-sufficient-length")
    assert anon_client.get("/classes", headers=_auth(token)).status_code == 401


def test_token_for_unknown_teacher_is_rejected(anon_client: TestClient) -> None:
    # Correctly signed, unexpired, but the subject is not a teacher in the DB.
    token = create_access_token(uuid4())
    assert anon_client.get("/classes", headers=_auth(token)).status_code == 401
