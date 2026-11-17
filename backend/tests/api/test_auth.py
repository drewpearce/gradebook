import datetime as dt
from collections import defaultdict
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy.orm import Session

from app.auth.security import create_access_token, hash_password, password_fingerprint
from app.config import settings
from app.main import api
from app.models import Teacher


def _login(client: TestClient, username: str, password: str) -> Response:
    return client.post("/auth/login", data={"username": username, "password": password})


def _forge_token(
    teacher: Teacher, *, secret: str | None = None, expires_in_minutes: int = 60
) -> str:
    now = dt.datetime.now(dt.UTC)
    return jwt.encode(
        {
            "sub": str(teacher.id),
            "pwd": password_fingerprint(teacher.password_hash),
            "iat": now,
            "exp": now + dt.timedelta(minutes=expires_in_minutes),
        },
        secret or settings.secret_key,
        algorithm="HS256",
    )


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_health_is_open(anon_client: TestClient) -> None:
    assert anon_client.get("/health").status_code == 200


def test_unauthenticated_data_request_is_rejected(anon_client: TestClient) -> None:
    assert anon_client.get("/classes").status_code == 401


def test_login_returns_a_bearer_token(
    anon_client: TestClient, teacher: Teacher, teacher_credentials: tuple[str, str]
) -> None:
    username, password = teacher_credentials
    response = _login(anon_client, username, password)
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_issued_token_opens_protected_routes(
    anon_client: TestClient, teacher: Teacher, teacher_credentials: tuple[str, str]
) -> None:
    username, password = teacher_credentials
    token = _login(anon_client, username, password).json()["access_token"]

    assert anon_client.get("/classes", headers=_auth(token)).status_code == 200
    me = anon_client.get("/auth/me", headers=_auth(token))
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
    token = _forge_token(teacher, expires_in_minutes=-5)
    assert anon_client.get("/classes", headers=_auth(token)).status_code == 401


def test_wrong_signature_is_rejected(anon_client: TestClient, teacher: Teacher) -> None:
    # Valid shape, correct teacher, but signed with the wrong secret.
    token = _forge_token(teacher, secret="a-different-secret-of-sufficient-length")
    assert anon_client.get("/classes", headers=_auth(token)).status_code == 401


def test_token_for_unknown_teacher_is_rejected(anon_client: TestClient) -> None:
    # Correctly signed, unexpired, but the subject is not a teacher in the DB.
    token = create_access_token(uuid4(), "any-hash")
    assert anon_client.get("/classes", headers=_auth(token)).status_code == 401


def _forge_claims(claims: dict[str, object]) -> str:
    now = dt.datetime.now(dt.UTC)
    full = {"iat": now, "exp": now + dt.timedelta(minutes=60), **claims}
    return jwt.encode(full, settings.secret_key, algorithm="HS256")


def test_token_with_non_uuid_subject_is_rejected(anon_client: TestClient) -> None:
    token = _forge_claims({"sub": "not-a-uuid"})
    assert anon_client.get("/classes", headers=_auth(token)).status_code == 401


def test_token_without_subject_is_rejected(anon_client: TestClient) -> None:
    token = _forge_claims({})
    assert anon_client.get("/classes", headers=_auth(token)).status_code == 401


_OPEN_PATHS = {"/health", "/auth/login"}
# Built from the OpenAPI schema: included routers do not appear flat in ``app.routes``.
_PROTECTED_ROUTES = [
    pytest.param(method.upper(), path, id=f"{method.upper()} {path}")
    for path, operations in api.openapi()["paths"].items()
    if path not in _OPEN_PATHS
    for method in sorted(operations)
]


def test_the_route_sweep_finds_the_data_routes() -> None:
    # Guard: an empty sweep would skip silently and prove nothing.
    assert len(_PROTECTED_ROUTES) >= 20


@pytest.mark.parametrize(("method", "path"), _PROTECTED_ROUTES)
def test_every_protected_route_rejects_a_missing_token(
    anon_client: TestClient, method: str, path: str
) -> None:
    url = path.format_map(defaultdict(uuid4))
    assert anon_client.request(method, url).status_code == 401


def test_login_with_a_password_over_72_bytes_is_401(
    anon_client: TestClient, teacher: Teacher, teacher_credentials: tuple[str, str]
) -> None:
    username, _ = teacher_credentials
    assert _login(anon_client, username, "x" * 100).status_code == 401


def test_token_without_expiry_is_rejected(anon_client: TestClient, teacher: Teacher) -> None:
    claims = {"sub": str(teacher.id), "pwd": password_fingerprint(teacher.password_hash)}
    token = jwt.encode(claims, settings.secret_key, algorithm="HS256")
    assert anon_client.get("/classes", headers=_auth(token)).status_code == 401


def test_token_without_password_fingerprint_is_rejected(
    anon_client: TestClient, teacher: Teacher
) -> None:
    token = _forge_claims({"sub": str(teacher.id)})
    assert anon_client.get("/classes", headers=_auth(token)).status_code == 401


def test_password_reset_revokes_existing_tokens(
    anon_client: TestClient,
    db_session: Session,
    teacher: Teacher,
    teacher_credentials: tuple[str, str],
) -> None:
    username, password = teacher_credentials
    token = _login(anon_client, username, password).json()["access_token"]
    assert anon_client.get("/classes", headers=_auth(token)).status_code == 200

    teacher.password_hash = hash_password("a-brand-new-password")
    db_session.flush()

    assert anon_client.get("/classes", headers=_auth(token)).status_code == 401


# --- login rate limiting -------------------------------------------------------------------


def _lock_out(client: TestClient, username: str, headers: dict[str, str] | None = None) -> None:
    for _ in range(10):
        response = client.post(
            "/auth/login", data={"username": username, "password": "wrong"}, headers=headers
        )
        assert response.status_code == 401


def test_login_locks_out_after_ten_failures(
    anon_client: TestClient, teacher: Teacher, teacher_credentials: tuple[str, str]
) -> None:
    username, password = teacher_credentials
    _lock_out(anon_client, username)

    response = _login(anon_client, username, "wrong")
    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) >= 1
    # Even the correct password is refused while locked out.
    assert _login(anon_client, username, password).status_code == 429


def test_success_resets_the_pair_counter(
    anon_client: TestClient, teacher: Teacher, teacher_credentials: tuple[str, str]
) -> None:
    username, password = teacher_credentials
    for _ in range(9):
        assert _login(anon_client, username, "wrong").status_code == 401
    assert _login(anon_client, username, password).status_code == 200
    # Counter was reset, so nine more failures are tolerated again.
    for _ in range(9):
        assert _login(anon_client, username, "wrong").status_code == 401


def test_a_different_client_ip_is_not_blocked(
    anon_client: TestClient,
    teacher: Teacher,
    teacher_credentials: tuple[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    username, password = teacher_credentials
    monkeypatch.setattr(settings, "trust_proxy_ip_header", True)
    _lock_out(anon_client, username, {"Fly-Client-IP": "203.0.113.1"})

    blocked = anon_client.post(
        "/auth/login",
        data={"username": username, "password": password},
        headers={"Fly-Client-IP": "203.0.113.1"},
    )
    other = anon_client.post(
        "/auth/login",
        data={"username": username, "password": password},
        headers={"Fly-Client-IP": "203.0.113.2"},
    )
    assert blocked.status_code == 429
    assert other.status_code == 200
