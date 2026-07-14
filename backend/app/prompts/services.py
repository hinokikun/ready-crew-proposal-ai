from __future__ import annotations

import re
from sqlite3 import Connection
from typing import Any

from app.prompts.repositories import (
    build_prompt_analytics_from_db,
    create_experiment,
    create_prompt_version,
    judge_experiment_winners,
    list_experiments,
    list_prompt_versions,
    record_prompt_metric,
    rollback_prompt_version,
    select_prompt_version_for_project,
    update_prompt_version_status,
)
from app.repositories import create_audit_log, get_user_context_ids, row_to_dict


def get_prompt_studio_dashboard(db: Connection, user_id: int | None = None) -> dict[str, Any]:
    return {
        "versions": list_prompt_versions(db, user_id),
        "experiments": list_experiments(db, user_id),
        "analytics": build_prompt_experiment_analytics(db, user_id),
        "winner_recommendations": judge_experiment_winners(db, min_samples=3, persist=False, user_id=user_id),
    }


def build_prompt_experiment_analytics(db: Connection, user_id: int | None = None) -> dict[str, Any]:
    return build_prompt_analytics_from_db(db, user_id)


def create_prompt_version_from_payload(db: Connection, *, payload: Any, user_id: int | None) -> dict[str, Any]:
    return create_prompt_version(
        db,
        prompt_name=payload.prompt_name,
        version=payload.version,
        description=payload.description,
        target_agent=payload.target_agent,
        prompt_template=payload.prompt_template,
        status=payload.status,
        user_id=user_id,
    )


def update_prompt_status_from_payload(db: Connection, *, version_id: int, payload: Any, user_id: int | None) -> dict[str, Any] | None:
    return update_prompt_version_status(db, version_id=version_id, status=payload.status, user_id=user_id)


def rollback_prompt_from_payload(db: Connection, *, payload: Any, user_id: int | None) -> dict[str, Any] | None:
    return rollback_prompt_version(db, prompt_name=payload.prompt_name, version=payload.version, user_id=user_id)


def create_experiment_from_payload(db: Connection, *, payload: Any, user_id: int | None) -> dict[str, Any]:
    return create_experiment(
        db,
        experiment_name=payload.experiment_name,
        target_prompt=payload.target_prompt,
        control_version=payload.control_version,
        candidate_version=payload.candidate_version,
        traffic_ratio=payload.traffic_ratio,
        status=payload.status,
        start_at=payload.start_at,
        end_at=payload.end_at,
        user_id=user_id,
    )


def route_prompt_from_payload(db: Connection, *, payload: Any, user_id: int | None) -> dict[str, Any]:
    return select_prompt_version_for_project(db, prompt_name=payload.prompt_name, project_id=payload.project_id, user_id=user_id)


def record_prompt_metric_from_payload(db: Connection, *, payload: Any, user_id: int | None = None) -> dict[str, Any]:
    return record_prompt_metric(
        db,
        experiment_id=payload.experiment_id,
        prompt_name=payload.prompt_name,
        prompt_version=payload.prompt_version,
        project_id=payload.project_id,
        outcome=payload.outcome,
        review_count=payload.review_count,
        quality_gate_passed=payload.quality_gate_passed,
        proposal_time_seconds=payload.proposal_time_seconds,
        user_rating=payload.user_rating,
        user_id=user_id,
    )


def judge_experiment(db: Connection, *, experiment_id: int, user_id: int | None) -> dict[str, Any] | None:
    recommendations = judge_experiment_winners(db, min_samples=3, persist=True, user_id=user_id)
    selected = next((item for item in recommendations if int(item["experiment_id"]) == experiment_id), None)
    if selected:
        create_audit_log(db, user_id, "setting_change", "prompt_experiment_judgement", str(experiment_id), "success", f"winner={selected.get('recommended_version', '')}")
    return selected


def create_experiment_from_learning(db: Connection, *, improvement_id: int, user_id: int | None) -> dict[str, Any] | None:
    organization_id, workspace_id = get_user_context_ids(db, user_id)
    improvement = row_to_dict(
        db.execute(
            "SELECT * FROM learning_improvements WHERE id = ? AND organization_id = ? AND workspace_id = ?",
            (improvement_id, organization_id, workspace_id),
        ).fetchone()
    )
    if not improvement:
        return None
    prompt_name = _prompt_name_from_learning(improvement)
    target_agent = str(improvement.get("agent") or "AI営業")
    baseline = _ensure_baseline_prompt(db, prompt_name=prompt_name, target_agent=target_agent, user_id=user_id)
    candidate_version = _next_version(db, prompt_name)
    prompt = create_prompt_version(
        db,
        prompt_name=prompt_name,
        version=candidate_version,
        description=str(improvement.get("expected_effect") or "Learning候補から作成"),
        target_agent=target_agent,
        prompt_template=str(improvement.get("suggested_prompt") or improvement.get("recommendation") or "提案品質を改善する観点を追加してください。"),
        status="testing",
        user_id=user_id,
    )
    experiment = create_experiment(
        db,
        experiment_name=f"{prompt_name} {candidate_version} A/B",
        target_prompt=prompt_name,
        control_version=str(baseline["version"]),
        candidate_version=candidate_version,
        traffic_ratio=50,
        status="testing",
        start_at="",
        end_at="",
        user_id=user_id,
    )
    create_audit_log(db, user_id, "save", "learning_prompt_experiment", str(experiment.get("id", "")), "success", f"learning_improvement_id={improvement_id}")
    return {"prompt": prompt, "experiment": experiment, "source_improvement": improvement}


def _ensure_baseline_prompt(db: Connection, *, prompt_name: str, target_agent: str, user_id: int | None) -> dict[str, Any]:
    organization_id, workspace_id = get_user_context_ids(db, user_id)
    row = row_to_dict(
        db.execute(
            """
            SELECT * FROM prompt_versions
            WHERE prompt_name = ? AND status = 'active'
              AND (scope_type = 'system' OR (organization_id = ? AND workspace_id = ?))
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (prompt_name, organization_id, workspace_id),
        ).fetchone()
    )
    if row:
        return row
    existing = row_to_dict(
        db.execute(
            """
            SELECT * FROM prompt_versions
            WHERE prompt_name = ? AND (scope_type = 'system' OR (organization_id = ? AND workspace_id = ?))
            ORDER BY created_at ASC, id ASC LIMIT 1
            """,
            (prompt_name, organization_id, workspace_id),
        ).fetchone()
    )
    if existing:
        update_prompt_version_status(db, version_id=int(existing["id"]), status="active", user_id=user_id)
        existing["status"] = "active"
        return existing
    return create_prompt_version(
        db,
        prompt_name=prompt_name,
        version="v1",
        description="Baseline prompt before Learning optimization.",
        target_agent=target_agent,
        prompt_template="案件情報をもとに、顧客課題・提案方針・次アクションを簡潔に整理してください。",
        status="active",
        user_id=user_id,
    )


def _next_version(db: Connection, prompt_name: str) -> str:
    rows = db.execute("SELECT version FROM prompt_versions WHERE prompt_name = ?", (prompt_name,)).fetchall()
    max_number = 1
    for row in rows:
        match = re.search(r"(\d+)$", str(row["version"]))
        if match:
            max_number = max(max_number, int(match.group(1)))
    return f"v{max_number + 1}"


def _prompt_name_from_learning(improvement: dict[str, Any]) -> str:
    raw = f"{improvement.get('agent') or 'agent'}_{improvement.get('category') or improvement.get('improvement_type') or 'prompt'}"
    ascii_name = re.sub(r"[^a-zA-Z0-9_]+", "_", raw).strip("_").lower()
    return f"learning_{ascii_name or 'prompt'}"[:80]
