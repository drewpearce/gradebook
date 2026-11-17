from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import CONTENT_SECURITY_POLICY, create_api, create_app


def _static_dir(tmp_path: Path) -> Path:
    (tmp_path / "index.html").write_text("<html>spa</html>")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "a.js").write_text("console.log(1)")
    return tmp_path


@pytest.fixture
def spa_client(tmp_path: Path) -> Iterator[TestClient]:
    config = Settings(environment="dev", static_dir=str(_static_dir(tmp_path)))
    with TestClient(create_app(config, create_api(production=False))) as client:
        yield client


@pytest.fixture
def prod_client(tmp_path: Path) -> Iterator[TestClient]:
    config = Settings(
        environment="production",
        secret_key="a-real-secret-of-sufficient-length!!",
        database_url="postgresql+psycopg://u:p@db.example/gradebook",
        static_dir=str(_static_dir(tmp_path)),
    )
    with TestClient(create_app(config, create_api(production=True))) as client:
        yield client


@pytest.mark.parametrize("path", ["/", f"/classes/{uuid4()}/grades"])
def test_spa_routes_return_index_html_uncached(spa_client: TestClient, path: str) -> None:
    response = spa_client.get(path)
    assert response.status_code == 200
    assert response.text == "<html>spa</html>"
    assert response.headers["Cache-Control"] == "no-cache"


def test_assets_are_served(spa_client: TestClient) -> None:
    response = spa_client.get("/assets/a.js")
    assert response.status_code == 200
    assert response.text == "console.log(1)"


def test_missing_asset_is_404(spa_client: TestClient) -> None:
    assert spa_client.get("/assets/missing.js").status_code == 404


def test_api_is_mounted_under_api(spa_client: TestClient) -> None:
    response = spa_client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_security_headers_are_set(spa_client: TestClient) -> None:
    response = spa_client.get("/api/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Referrer-Policy"] == "same-origin"
    assert "Content-Security-Policy" not in response.headers  # dev Swagger UI needs its CDN


def test_dev_serves_api_docs(spa_client: TestClient) -> None:
    assert spa_client.get("/api/docs").status_code == 200


def test_production_sets_csp_and_hsts(prod_client: TestClient) -> None:
    response = prod_client.get("/")
    assert response.headers["Content-Security-Policy"] == CONTENT_SECURITY_POLICY
    assert "style-src 'self' 'unsafe-inline'" in CONTENT_SECURITY_POLICY  # Radix <style>
    assert response.headers["Strict-Transport-Security"] == "max-age=31536000"


@pytest.mark.parametrize("path", ["/api/docs", "/api/redoc", "/api/openapi.json"])
def test_production_hides_api_docs(prod_client: TestClient, path: str) -> None:
    assert prod_client.get(path).status_code == 404
