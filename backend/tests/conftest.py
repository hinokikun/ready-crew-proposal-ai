import importlib
import sys
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient


def _reload_app_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            del sys.modules[module_name]


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("USE_MOCK_AI", "true")
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("INITIAL_ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("INITIAL_ADMIN_PASSWORD", "admin-password")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")
    _reload_app_modules()
    main = importlib.import_module("app.main")
    with TestClient(main.app) as test_client:
        yield test_client


@pytest.fixture()
def admin_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "admin-password"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


@pytest.fixture()
def sample_proposal_payload() -> dict[str, Any]:
    return {
        "project_brief": "株式会社サンプル不動産のWebサイトリニューアル案件。問い合わせ増加、SEO改善、CMS更新性向上を目的とする。",
        "client_company_info": "株式会社サンプル不動産\n担当者：山田様",
        "competitor_site_url": "https://example.com",
        "competitor_company_name": "地域競合A社",
        "estimated_page_count": "10ページ程度",
        "cms_required": "WordPress希望",
        "contact_form_required": "あり",
        "special_function_required": "物件検索は将来検討",
        "seo_required": "あり",
        "content_creation_required": "原稿作成一部あり",
        "desired_launch_timing": "3か月以内",
        "budget_range": "300〜500万円",
        "hearing_result": "問い合わせ導線と更新体制を改善したい。",
        "own_service_info": "Web戦略、CMS構築、SEO初期設計、運用改善を提供。",
        "past_proposal_template": "表紙、現状理解、Web戦略、費用概算、今後の進め方",
        "case_studies": "不動産会社A：問い合わせ件数150%増加",
    }


@pytest.fixture()
def sample_pptx_payload(sample_proposal_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        **sample_proposal_payload,
        "powerpoint_generation_data": {
            "deck_title": "Webサイト制作ご提案書",
            "client_name": "株式会社サンプル不動産",
            "slides": [
                {
                    "slide_no": 1,
                    "layout": "summary",
                    "title": "提案サマリー",
                    "bullets": ["問い合わせ増加を狙う", "CMSで更新性を高める", "SEO流入を改善する"],
                    "speaker_notes": "営業確認用メモ",
                    "visual_suggestion": "カードUI",
                }
            ],
        },
        "win_probability": {
            "rank": "B",
            "probability": 60,
            "label": "Bランク",
            "reason": "予算と目的が整理されている",
            "risk_score": 3,
            "risk_label": "★★★☆☆",
            "positive_factors": ["予算感あり"],
            "risk_factors": ["決裁者未確認"],
            "recommended_next_actions": ["決裁者を確認"],
            "improvement_actions": ["予算と範囲を確認"],
            "projected_probability_after_actions": 75,
        },
    }
