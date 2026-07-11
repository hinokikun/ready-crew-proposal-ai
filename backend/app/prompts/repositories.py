from __future__ import annotations

import re
from sqlite3 import Connection
from typing import Any

from app.repositories import create_audit_log, row_to_dict

PROMPT_STATUSES = {"draft", "testing", "active", "archived"}
EXPERIMENT_STATUSES = {"draft", "testing", "active", "paused", "completed", "archived"}
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*[^\s]+"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
]


def _safe_text(value: Any, limit: int = 1000) -> str:
    text = str(value or "").strip()
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("[redacted]", text)
    return text[:limit]


def _row(row: Any) -> dict[str, Any] | None:
    return row_to_dict(row)


def _rows(rows: list[Any]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def list_prompt_versions(db: Connection) -> list[dict[str, Any]]:
    rows = db.execute(
        """
        SELECT pv.*, COALESCE(u.email, '') AS created_by_email
        FROM prompt_versions pv
        LEFT JOIN users u ON u.id = pv.created_by
        ORDER BY pv.prompt_name ASC, pv.created_at DESC, pv.id DESC
        """
    ).fetchall()
    return _rows(rows)


def get_prompt_version(db: Connection, prompt_name: str, version: str) -> dict[str, Any] | None:
    return _row(
        db.execute(
            "SELECT * FROM prompt_versions WHERE prompt_name = ? AND version = ?",
            (_safe_text(prompt_name, 80), _safe_text(version, 40)),
        ).fetchone()
    )


def create_prompt_version(
    db: Connection,
    *,
    prompt_name: str,
    version: str,
    description: str,
    target_agent: str,
    prompt_template: str,
    status: str,
    user_id: int | None,
) -> dict[str, Any]:
    safe_status = status if status in PROMPT_STATUSES else "draft"
    safe_name = _safe_text(prompt_name, 80)
    safe_version = _safe_text(version, 40)
    if get_prompt_version(db, safe_name, safe_version):
        raise ValueError("Prompt version already exists.")
    if safe_status == "active":
        db.execute("UPDATE prompt_versions SET status = 'archived' WHERE prompt_name = ? AND status = 'active'", (safe_name,))
    cursor = db.execute(
        """
        INSERT INTO prompt_versions
        (prompt_name, version, description, target_agent, prompt_template, created_by, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            safe_name,
            safe_version,
            _safe_text(description, 500),
            _safe_text(target_agent, 80),
            _safe_text(prompt_template, 4000),
            user_id,
            safe_status,
        ),
    )
    create_audit_log(db, user_id, "save", "prompt_version", str(cursor.lastrowid or ""), "success", f"name={safe_name};version={safe_version};status={safe_status}")
    return _row(db.execute("SELECT * FROM prompt_versions WHERE id = ?", (cursor.lastrowid,)).fetchone()) or {}


def update_prompt_version_status(db: Connection, *, version_id: int, status: str, user_id: int | None) -> dict[str, Any] | None:
    safe_status = status if status in PROMPT_STATUSES else "draft"
    current = _row(db.execute("SELECT * FROM prompt_versions WHERE id = ?", (version_id,)).fetchone())
    if not current:
        return None
    if safe_status == "active":
        db.execute("UPDATE prompt_versions SET status = 'archived' WHERE prompt_name = ? AND status = 'active'", (current["prompt_name"],))
    db.execute("UPDATE prompt_versions SET status = ? WHERE id = ?", (safe_status, version_id))
    create_audit_log(db, user_id, "setting_change", "prompt_version", str(version_id), "success", f"status={safe_status}")
    return _row(db.execute("SELECT * FROM prompt_versions WHERE id = ?", (version_id,)).fetchone())


def rollback_prompt_version(db: Connection, *, prompt_name: str, version: str, user_id: int | None) -> dict[str, Any] | None:
    safe_name = _safe_text(prompt_name, 80)
    safe_version = _safe_text(version, 40)
    target = get_prompt_version(db, safe_name, safe_version)
    if not target:
        return None
    db.execute("UPDATE prompt_versions SET status = 'archived' WHERE prompt_name = ? AND status = 'active'", (safe_name,))
    db.execute("UPDATE prompt_versions SET status = 'active' WHERE id = ?", (target["id"],))
    create_audit_log(db, user_id, "setting_change", "prompt_rollback", str(target["id"]), "success", f"name={safe_name};version={safe_version}")
    return _row(db.execute("SELECT * FROM prompt_versions WHERE id = ?", (target["id"],)).fetchone())


def list_experiments(db: Connection) -> list[dict[str, Any]]:
    rows = db.execute(
        """
        SELECT e.*, COALESCE(u.email, '') AS created_by_email
        FROM experiments e
        LEFT JOIN users u ON u.id = e.created_by
        ORDER BY e.created_at DESC, e.id DESC
        """
    ).fetchall()
    return _rows(rows)


def create_experiment(
    db: Connection,
    *,
    experiment_name: str,
    target_prompt: str,
    control_version: str,
    candidate_version: str,
    traffic_ratio: int,
    status: str,
    start_at: str,
    end_at: str,
    user_id: int | None,
) -> dict[str, Any]:
    safe_status = status if status in EXPERIMENT_STATUSES else "draft"
    safe_prompt = _safe_text(target_prompt, 80)
    cursor = db.execute(
        """
        INSERT INTO experiments
        (experiment_name, target_prompt, control_version, candidate_version, traffic_ratio, status, start_at, end_at, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            _safe_text(experiment_name, 120),
            safe_prompt,
            _safe_text(control_version, 40),
            _safe_text(candidate_version, 40),
            max(0, min(100, int(traffic_ratio))),
            safe_status,
            _safe_text(start_at, 40),
            _safe_text(end_at, 40),
            user_id,
        ),
    )
    create_audit_log(db, user_id, "save", "prompt_experiment", str(cursor.lastrowid or ""), "success", f"target={safe_prompt};status={safe_status}")
    return _row(db.execute("SELECT * FROM experiments WHERE id = ?", (cursor.lastrowid,)).fetchone()) or {}


def select_prompt_version_for_project(db: Connection, *, prompt_name: str, project_id: int | None, user_id: int | None) -> dict[str, Any]:
    safe_name = _safe_text(prompt_name, 80)
    experiment = _row(
        db.execute(
            """
            SELECT * FROM experiments
            WHERE target_prompt = ? AND status IN ('testing', 'active')
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (safe_name,),
        ).fetchone()
    )
    if experiment:
        assignment_key = f"{experiment['id']}:{project_id or 0}:{user_id or 0}:{safe_name}"
        existing = _row(db.execute("SELECT * FROM experiment_assignments WHERE assignment_key = ?", (assignment_key,)).fetchone())
        if existing:
            selected_version = existing["selected_version"]
        else:
            bucket = sum((index + 1) * ord(char) for index, char in enumerate(assignment_key)) % 100
            selected_version = experiment["candidate_version"] if bucket < int(experiment["traffic_ratio"] or 0) else experiment["control_version"]
            db.execute(
                """
                INSERT INTO experiment_assignments (experiment_id, project_id, user_id, selected_version, assignment_key)
                VALUES (?, ?, ?, ?, ?)
                """,
                (experiment["id"], project_id, user_id, selected_version, assignment_key),
            )
        version_row = get_prompt_version(db, safe_name, selected_version)
        return {
            "prompt_name": safe_name,
            "version": selected_version,
            "experiment_id": experiment["id"],
            "experiment_name": experiment["experiment_name"],
            "prompt_template": (version_row or {}).get("prompt_template", ""),
            "target_agent": (version_row or {}).get("target_agent", ""),
            "reason": f"traffic_ratio={experiment['traffic_ratio']};selected={selected_version}",
        }

    active = _row(
        db.execute(
            """
            SELECT * FROM prompt_versions
            WHERE prompt_name = ? AND status = 'active'
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (safe_name,),
        ).fetchone()
    )
    fallback = active or _row(
        db.execute(
            "SELECT * FROM prompt_versions WHERE prompt_name = ? ORDER BY created_at DESC, id DESC LIMIT 1",
            (safe_name,),
        ).fetchone()
    )
    if not fallback:
        return {"prompt_name": safe_name, "version": "default", "experiment_id": None, "experiment_name": "", "prompt_template": "", "target_agent": "", "reason": "no_registered_prompt"}
    return {
        "prompt_name": safe_name,
        "version": fallback["version"],
        "experiment_id": None,
        "experiment_name": "",
        "prompt_template": fallback["prompt_template"],
        "target_agent": fallback["target_agent"],
        "reason": f"status={fallback['status']}",
    }


def record_prompt_metric(
    db: Connection,
    *,
    experiment_id: int | None,
    prompt_name: str,
    prompt_version: str,
    project_id: int | None,
    outcome: str,
    review_count: int,
    quality_gate_passed: bool,
    proposal_time_seconds: int,
    user_rating: str,
) -> dict[str, Any]:
    cursor = db.execute(
        """
        INSERT INTO prompt_experiment_metrics
        (experiment_id, prompt_name, prompt_version, project_id, outcome, review_count, quality_gate_passed, proposal_time_seconds, user_rating)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            experiment_id,
            _safe_text(prompt_name, 80),
            _safe_text(prompt_version, 40),
            project_id,
            _safe_text(outcome, 40),
            max(0, int(review_count)),
            1 if quality_gate_passed else 0,
            max(0, int(proposal_time_seconds)),
            _safe_text(user_rating, 40),
        ),
    )
    return _row(db.execute("SELECT * FROM prompt_experiment_metrics WHERE id = ?", (cursor.lastrowid,)).fetchone()) or {}


def build_prompt_analytics_from_db(db: Connection) -> dict[str, Any]:
    rows = db.execute(
        """
        SELECT
            prompt_name,
            prompt_version,
            COUNT(*) AS sample_count,
            SUM(CASE WHEN outcome = 'won' THEN 1 ELSE 0 END) AS won_count,
            SUM(CASE WHEN outcome = 'lost' THEN 1 ELSE 0 END) AS lost_count,
            SUM(review_count) AS review_count,
            SUM(CASE WHEN quality_gate_passed = 1 THEN 1 ELSE 0 END) AS quality_gate_passed_count,
            AVG(proposal_time_seconds) AS average_proposal_time_seconds
        FROM prompt_experiment_metrics
        GROUP BY prompt_name, prompt_version
        ORDER BY sample_count DESC, prompt_name ASC
        LIMIT 100
        """
    ).fetchall()
    prompt_metrics = []
    for row in rows:
        item = dict(row)
        sample_count = int(item.get("sample_count") or 0)
        decided_count = int(item.get("won_count") or 0) + int(item.get("lost_count") or 0)
        item["win_rate"] = round((int(item.get("won_count") or 0) / decided_count) * 100, 1) if decided_count else 0
        item["quality_gate_pass_rate"] = round((int(item.get("quality_gate_passed_count") or 0) / sample_count) * 100, 1) if sample_count else 0
        item["average_proposal_time_seconds"] = round(float(item.get("average_proposal_time_seconds") or 0), 1)
        prompt_metrics.append(item)
    return {
        "prompt_versions_count": int(db.execute("SELECT COUNT(*) AS count FROM prompt_versions").fetchone()["count"] or 0),
        "experiments_count": int(db.execute("SELECT COUNT(*) AS count FROM experiments").fetchone()["count"] or 0),
        "active_experiments_count": int(db.execute("SELECT COUNT(*) AS count FROM experiments WHERE status IN ('testing', 'active')").fetchone()["count"] or 0),
        "assignments_count": int(db.execute("SELECT COUNT(*) AS count FROM experiment_assignments").fetchone()["count"] or 0),
        "metrics_count": int(db.execute("SELECT COUNT(*) AS count FROM prompt_experiment_metrics").fetchone()["count"] or 0),
        "prompt_metrics": prompt_metrics,
        "winner_recommendations": judge_experiment_winners(db, min_samples=3, persist=False),
    }


def judge_experiment_winners(db: Connection, *, min_samples: int = 3, persist: bool = True) -> list[dict[str, Any]]:
    experiments = list_experiments(db)
    recommendations: list[dict[str, Any]] = []
    for experiment in experiments:
        if experiment["status"] not in {"testing", "active"}:
            continue
        metrics = {
            row["prompt_version"]: dict(row)
            for row in db.execute(
                """
                SELECT
                    prompt_version,
                    COUNT(*) AS sample_count,
                    SUM(CASE WHEN outcome = 'won' THEN 1 ELSE 0 END) AS won_count,
                    SUM(CASE WHEN outcome = 'lost' THEN 1 ELSE 0 END) AS lost_count,
                    SUM(review_count) AS review_count,
                    SUM(CASE WHEN quality_gate_passed = 1 THEN 1 ELSE 0 END) AS quality_gate_passed_count,
                    AVG(proposal_time_seconds) AS average_proposal_time_seconds
                FROM prompt_experiment_metrics
                WHERE experiment_id = ?
                GROUP BY prompt_version
                """,
                (experiment["id"],),
            ).fetchall()
        }
        control = metrics.get(experiment["control_version"])
        candidate = metrics.get(experiment["candidate_version"])
        control_samples = int((control or {}).get("sample_count") or 0)
        candidate_samples = int((candidate or {}).get("sample_count") or 0)
        if control_samples < min_samples or candidate_samples < min_samples:
            recommendations.append(
                {
                    "experiment_id": experiment["id"],
                    "experiment_name": experiment["experiment_name"],
                    "target_prompt": experiment["target_prompt"],
                    "recommended_version": "",
                    "reason": f"判定には各{min_samples}件以上のサンプルが必要です。",
                    "confidence": 30,
                }
            )
            continue
        control_score = _metric_score(control)
        candidate_score = _metric_score(candidate)
        winner = experiment["candidate_version"] if candidate_score >= control_score else experiment["control_version"]
        confidence = min(95, 55 + abs(candidate_score - control_score))
        reason = f"{winner} は受注率・品質ゲート通過率・レビュー回数の総合スコアが高いです。"
        if persist:
            db.execute("UPDATE experiments SET winner = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (winner, experiment["id"]))
            create_audit_log(db, None, "setting_change", "prompt_experiment_winner", str(experiment["id"]), "success", f"winner={winner}")
        recommendations.append(
            {
                "experiment_id": experiment["id"],
                "experiment_name": experiment["experiment_name"],
                "target_prompt": experiment["target_prompt"],
                "recommended_version": winner,
                "reason": reason,
                "confidence": int(confidence),
            }
        )
    return recommendations


def _metric_score(metric: dict[str, Any] | None) -> float:
    if not metric:
        return 0
    sample_count = max(1, int(metric.get("sample_count") or 0))
    decided_count = max(1, int(metric.get("won_count") or 0) + int(metric.get("lost_count") or 0))
    win_rate = (int(metric.get("won_count") or 0) / decided_count) * 100
    quality_gate = (int(metric.get("quality_gate_passed_count") or 0) / sample_count) * 100
    reviews_penalty = (int(metric.get("review_count") or 0) / sample_count) * 4
    time_penalty = float(metric.get("average_proposal_time_seconds") or 0) / 600
    return win_rate * 0.5 + quality_gate * 0.35 - reviews_penalty - time_penalty
