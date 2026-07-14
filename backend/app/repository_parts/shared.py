from __future__ import annotations

import re
from sqlite3 import Connection
from typing import Any


def _count_rows(db: Connection, table_name: str, where_clause: str = "", params: tuple[Any, ...] = ()) -> int:
    sql = f"SELECT COUNT(*) AS count FROM {table_name}"
    if where_clause:
        sql = f"{sql} WHERE {where_clause}"
    row = db.execute(sql, params).fetchone()
    return int(row["count"]) if row else 0


def _scope_value(scope: Any, key: str, fallback: Any = None) -> Any:
    if scope is None:
        return fallback
    if isinstance(scope, dict):
        return scope.get(key, fallback)
    return getattr(scope, key, fallback)


def _scope_filter(scope: Any | None, alias: str = "") -> tuple[str, tuple[Any, ...]]:
    if not scope:
        return "", ()
    prefix = f"{alias}." if alias else ""
    scope_name = str(_scope_value(scope, "scope", "workspace") or "workspace")
    organization_id = int(_scope_value(scope, "organization_id", 1) or 1)
    workspace_id = _scope_value(scope, "workspace_id")
    if scope_name == "system":
        return "", ()
    if scope_name == "organization":
        return f"{prefix}organization_id = ?", (organization_id,)
    return f"{prefix}organization_id = ? AND {prefix}workspace_id = ?", (organization_id, int(workspace_id or 1))


def _scope_label(scope: Any | None) -> dict[str, Any]:
    if not scope:
        return {
            "scope": "system",
            "organization_id": None,
            "workspace_id": None,
            "organization_name": "All Organizations",
            "workspace_name": "All Workspaces",
        }
    return {
        "scope": _scope_value(scope, "scope", "workspace"),
        "organization_id": _scope_value(scope, "organization_id"),
        "workspace_id": _scope_value(scope, "workspace_id"),
        "organization_name": _scope_value(scope, "organization_name", ""),
        "workspace_name": _scope_value(scope, "workspace_name", ""),
    }


def _count_rows_in_scope(
    db: Connection,
    table_name: str,
    scope: Any | None,
    where_clause: str = "",
    params: tuple[Any, ...] = (),
) -> int:
    scope_where, scope_params = _scope_filter(scope)
    clauses = []
    if scope_where:
        clauses.append(scope_where)
    if where_clause:
        clauses.append(f"({where_clause})")
    return _count_rows(db, table_name, " AND ".join(clauses), (*scope_params, *params))


def _feedback_score_metrics(db: Connection) -> dict[str, Any]:
    rows = db.execute("SELECT rating, comment FROM feedback_entries").fetchall()
    if not rows:
        return {
            "average_usability": 0,
            "practical_usability_rate": 0,
            "time_saved_rate": 0,
            "continue_intent_rate": 0,
            "score_count": 0,
        }
    rating_scores = {"usable": 5.0, "needs_revision": 3.5, "hard_to_use": 2.0}
    scores: list[float] = []
    time_saved_hits = 0
    time_saved_total = 0
    continue_hits = 0
    continue_total = 0
    practical_hits = 0
    for row in rows:
        rating = str(row["rating"] or "")
        comment = str(row["comment"] or "")
        practical_hits += 1 if rating in {"usable", "needs_revision"} else 0
        scores.append(rating_scores.get(rating, 3.0))
        for label, value in re.findall(r"([^:\n：]{2,30})[:：]\s*([1-5])\s*/\s*5", comment):
            numeric = int(value)
            if any(token in label for token in ("迷わず", "使いやす", "UI", "操作")):
                scores.append(float(numeric))
            if any(token in label for token in ("時間", "短縮")):
                time_saved_total += 1
                time_saved_hits += 1 if numeric >= 4 else 0
            if any(token in label for token in ("今後", "継続", "使いたい")):
                continue_total += 1
                continue_hits += 1 if numeric >= 4 else 0
    return {
        "average_usability": round(sum(scores) / len(scores), 1) if scores else 0,
        "practical_usability_rate": round((practical_hits / len(rows)) * 100) if rows else 0,
        "time_saved_rate": round((time_saved_hits / time_saved_total) * 100) if time_saved_total else 0,
        "continue_intent_rate": round((continue_hits / continue_total) * 100) if continue_total else 0,
        "score_count": len(scores),
    }
