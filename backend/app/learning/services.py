from __future__ import annotations

from sqlite3 import Connection
from typing import Any

from app.learning.analyzer import analyze_learning_signals
from app.learning.repositories import (
    build_learning_analytics_from_db,
    collect_learning_signals,
    create_learning_run,
    get_latest_learning_run,
    list_latest_learning_improvements,
    save_learning_improvements,
    update_improvement_status,
)


def run_learning_analysis(db: Connection, *, user_id: int | None) -> dict[str, Any]:
    metrics = collect_learning_signals(db, user_id)
    analysis = analyze_learning_signals(metrics)
    run_id = create_learning_run(
        db,
        user_id=user_id,
        metrics=metrics,
        release_candidate=analysis["release_candidate"],
    )
    improvements = save_learning_improvements(db, run_id=run_id, improvements=analysis["improvements"])
    return {
        "run": get_latest_learning_run(db, user_id),
        "improvements": improvements,
        "release_candidate": analysis["release_candidate"],
        "analytics": build_learning_analytics(db, user_id),
    }


def get_learning_dashboard(db: Connection, user_id: int | None = None) -> dict[str, Any]:
    run = get_latest_learning_run(db, user_id)
    improvements = list_latest_learning_improvements(db, 30, user_id)
    release_candidate = {
        "version": (run or {}).get("release_candidate_version", "13.6候補"),
        "summary": (run or {}).get("release_candidate_summary", "Learningを実行すると、Version 13.6候補が表示されます。"),
    }
    return {
        "run": run,
        "improvements": improvements,
        "release_candidate": release_candidate,
        "analytics": build_learning_analytics(db, user_id),
    }


def adopt_learning_improvement(db: Connection, *, improvement_id: int, status: str, user_id: int | None) -> dict[str, Any] | None:
    return update_improvement_status(db, improvement_id=improvement_id, status=status, user_id=user_id)


def build_learning_analytics(db: Connection, user_id: int | None = None) -> dict[str, Any]:
    return build_learning_analytics_from_db(db, user_id)
