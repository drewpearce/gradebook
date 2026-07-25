from fastapi.testclient import TestClient
from httpx import Response

from app.models import Teacher


def _login(client: TestClient, username: str, password: str) -> Response:
    return client.post("/auth/login", data={"username": username, "password": password})


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
    bad = {"Authorization": "Bearer not-a-real-jwt"}
    assert anon_client.get("/classes", headers=bad).status_code == 401
