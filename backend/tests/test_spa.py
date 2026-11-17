from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import SPAStaticFiles, app


@pytest.fixture
def spa_client(tmp_path: Path) -> Iterator[TestClient]:
    (tmp_path / "index.html").write_text("<html>spa</html>")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "a.js").write_text("console.log(1)")
    # The real app mounts this only when STATIC_DIR is set; mount it on the same outer app.
    app.mount("/", SPAStaticFiles(directory=tmp_path, html=True), name="spa-test")
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.router.routes.pop()


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
