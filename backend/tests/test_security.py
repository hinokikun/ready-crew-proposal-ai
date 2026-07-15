import importlib
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from app.security import hash_password, verify_password


def test_password_hash_verification() -> None:
    password_hash = hash_password("strong-password")

    assert verify_password("strong-password", password_hash)
    assert not verify_password("wrong-password", password_hash)


def test_security_headers_are_sent(client: TestClient) -> None:
    response = client.get("/health/live")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "camera=()" in response.headers["permissions-policy"]
    assert response.headers["cache-control"] == "no-store"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


def _reload_app_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            del sys.modules[module_name]


def test_production_cors_filters_localhost_and_wildcard(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "prod-cors.db"
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AUTO_SCHEMA_PATCH", "true")
    monkeypatch.setenv("USE_MOCK_AI", "true")
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("INITIAL_ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("INITIAL_ADMIN_PASSWORD", "test-password")
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com,http://localhost:3000,*")
    _reload_app_modules()
    main = importlib.import_module("app.main")
    with TestClient(main.app) as local_client:
        blocked = local_client.options(
            "/health",
            headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
        )
        allowed = local_client.options(
            "/health",
            headers={"Origin": "https://app.example.com", "Access-Control-Request-Method": "GET"},
        )

    assert blocked.headers.get("access-control-allow-origin") != "http://localhost:3000"
    assert allowed.headers["access-control-allow-origin"] == "https://app.example.com"


def test_known_mojibake_markers_are_not_in_release_text() -> None:
    root = Path(__file__).resolve().parents[2]
    markers = [
        "\u7e3a",
        "\u7e67",
        "\u7e5d",
        "\u8b41",
        "\u8b4c",
        "\u8b5b",
        "\u83f4",
        "\u9082",
        "\u879f",
        "\u96b1",
        "\u9b18",
        "\u870a",
        "\u8373",
        "\u9005",
        "\u8b6f",
        "\u9ae2",
        "\u8709",
        "\u87c6",
        "\u8763",
        "\u8389",
        "\u95d5",
        "\u96b0",
        "\u90e2",
        "\u90b5",
        "\u95d4",
        "\u96b4",
    ]
    checked_paths = [
        root / "backend" / "app" / "repository_parts" / "analytics.py",
        root / "backend" / "app" / "repository_parts" / "crm.py",
        root / "backend" / "app" / "auth.py",
        root / "docs" / "INCIDENT_RESPONSE.md",
        root / "docs" / "OPERATIONS.md",
        root / "README.md",
    ]
    hits = []
    for path in checked_paths:
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker in text:
                hits.append(f"{path.relative_to(root)} contains U+{ord(marker):04X}")

    assert hits == []
