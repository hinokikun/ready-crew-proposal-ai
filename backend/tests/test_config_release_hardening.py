from __future__ import annotations

import importlib


def _main_with_env(monkeypatch, **values):
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    import app.config as config
    import app.main as main

    importlib.reload(config)
    return importlib.reload(main)


def test_explicit_production_origin_is_allowed(monkeypatch):
    main = _main_with_env(monkeypatch, APP_ENV="production", CORS_ORIGINS="https://app.example.com")
    assert main._resolved_cors_origins() == ["https://app.example.com"]


def test_unlisted_vercel_origin_is_not_allowed(monkeypatch):
    main = _main_with_env(monkeypatch, APP_ENV="production", CORS_ORIGINS="https://app.example.com")
    assert "https://other.vercel.app" not in main._resolved_cors_origins()


def test_placeholder_is_not_allowed(monkeypatch):
    main = _main_with_env(monkeypatch, APP_ENV="production", CORS_ORIGINS="https://your-vercel-app.vercel.app")
    assert main._resolved_cors_origins() == []


def test_production_localhost_is_removed(monkeypatch):
    main = _main_with_env(monkeypatch, APP_ENV="production", CORS_ORIGINS="http://localhost:3000")
    assert main._resolved_cors_origins() == []


def test_local_development_origins_are_available(monkeypatch):
    main = _main_with_env(monkeypatch, APP_ENV="local", CORS_ORIGINS="")
    assert "http://localhost:3000" in main._resolved_cors_origins()


def test_production_missing_origins_is_fail_safe(monkeypatch):
    main = _main_with_env(monkeypatch, APP_ENV="production", CORS_ORIGINS="")
    assert main._resolved_cors_origins() == []


def test_production_regex_is_ignored(monkeypatch):
    main = _main_with_env(
        monkeypatch,
        APP_ENV="production",
        CORS_ORIGINS="https://app.example.com",
        CORS_ORIGIN_REGEX=r"^https://.*\.vercel\.app$",
    )
    assert main._resolved_cors_origin_regex() is None


def test_origin_trailing_slash_is_normalized(monkeypatch):
    main = _main_with_env(monkeypatch, APP_ENV="production", CORS_ORIGINS="HTTPS://APP.EXAMPLE.COM/")
    assert main._resolved_cors_origins() == ["https://app.example.com"]


def test_origin_with_path_is_rejected(monkeypatch):
    main = _main_with_env(monkeypatch, APP_ENV="production", CORS_ORIGINS="https://app.example.com/path")
    assert main._resolved_cors_origins() == []


def test_wildcard_origin_is_not_allowed(monkeypatch):
    main = _main_with_env(monkeypatch, APP_ENV="production", CORS_ORIGINS="*")
    assert main._resolved_cors_origins() == []
