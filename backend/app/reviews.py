from __future__ import annotations

from sqlite3 import Connection
from typing import Any

from app.repositories import create_audit_log, get_user_context_ids
from app.scoping.service import attach_project_scope
from app.workspace.services import sanitize_workspace_text

REVIEW_STATUSES = {"draft", "review_requested", "approved", "changes_requested", "rejected"}


def _row_to_dict(row: Any) -> dict[str, Any] | None:
    return dict(row) if row else None


def get_review_by_project(db: Connection, project_id: str, user_id: int | None = None) -> dict[str, Any] | None:
    safe_project_id = sanitize_workspace_text(project_id, 120)
    organization_id, workspace_id = get_user_context_ids(db, user_id)
    return _row_to_dict(
        db.execute(
            """
            SELECT r.*, creator.email AS creator_email, reviewer.email AS reviewer_email
            FROM proposal_reviews r
            LEFT JOIN users creator ON creator.id = r.creator_user_id
            LEFT JOIN users reviewer ON reviewer.id = r.reviewer_user_id
            WHERE r.project_id = ? AND r.organization_id = ? AND r.workspace_id = ?
            ORDER BY r.updated_at DESC, r.id DESC
            LIMIT 1
            """,
            (safe_project_id, organization_id, workspace_id),
        ).fetchone()
    )


def list_reviews(db: Connection, limit: int = 100, user_id: int | None = None) -> list[dict[str, Any]]:
    organization_id, workspace_id = get_user_context_ids(db, user_id)
    rows = db.execute(
        """
        SELECT r.*, creator.email AS creator_email, reviewer.email AS reviewer_email
        FROM proposal_reviews r
        LEFT JOIN users creator ON creator.id = r.creator_user_id
        LEFT JOIN users reviewer ON reviewer.id = r.reviewer_user_id
        WHERE r.organization_id = ? AND r.workspace_id = ?
        ORDER BY r.updated_at DESC, r.id DESC
        LIMIT ?
        """,
        (organization_id, workspace_id, limit),
    ).fetchall()
    return [dict(row) for row in rows]


def request_review(db: Connection, project_id: str, project_name: str, creator_user_id: int) -> dict[str, Any]:
    safe_project_id = sanitize_workspace_text(project_id, 120)
    safe_project_name = sanitize_workspace_text(project_name, 160) or "AI Workspace提案"
    fallback_org, fallback_workspace = get_user_context_ids(db, creator_user_id)
    project_org, project_workspace = attach_project_scope(db, project_id=safe_project_id)
    organization_id = project_org or fallback_org
    workspace_id = project_workspace or fallback_workspace
    existing = db.execute(
        """
        SELECT id FROM proposal_reviews
        WHERE project_id = ? AND organization_id = ? AND workspace_id = ?
        ORDER BY updated_at DESC, id DESC LIMIT 1
        """,
        (safe_project_id, organization_id, workspace_id),
    ).fetchone()
    if existing:
        db.execute(
            """
            UPDATE proposal_reviews
            SET project_name = ?, creator_user_id = ?, status = 'review_requested',
                review_requested_at = CURRENT_TIMESTAMP, reviewer_user_id = NULL,
                reviewed_at = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (safe_project_name, creator_user_id, existing["id"]),
        )
        review_id = int(existing["id"])
    else:
        cursor = db.execute(
            """
            INSERT INTO proposal_reviews
            (project_id, project_name, creator_user_id, status, review_requested_at, organization_id, workspace_id)
            VALUES (?, ?, ?, 'review_requested', CURRENT_TIMESTAMP, ?, ?)
            """,
            (safe_project_id, safe_project_name, creator_user_id, organization_id, workspace_id),
        )
        review_id = int(cursor.lastrowid)

    create_audit_log(db, creator_user_id, "review_request", "proposal_review", str(review_id), "success", f"project_id={safe_project_id}")
    return dict(
        db.execute(
            "SELECT * FROM proposal_reviews WHERE id = ? AND organization_id = ? AND workspace_id = ?",
            (review_id, organization_id, workspace_id),
        ).fetchone()
    )


def update_review_status(db: Connection, review_id: int, reviewer_user_id: int, status: str, review_comment: str) -> dict[str, Any] | None:
    if status not in {"approved", "changes_requested", "rejected"}:
        return None
    organization_id, workspace_id = get_user_context_ids(db, reviewer_user_id)
    safe_comment = sanitize_workspace_text(review_comment, 800)
    db.execute(
        """
        UPDATE proposal_reviews
        SET status = ?, review_comment = ?, reviewer_user_id = ?,
            reviewed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND organization_id = ? AND workspace_id = ?
        """,
        (status, safe_comment, reviewer_user_id, review_id, organization_id, workspace_id),
    )
    review = _row_to_dict(
        db.execute(
            "SELECT * FROM proposal_reviews WHERE id = ? AND organization_id = ? AND workspace_id = ?",
            (review_id, organization_id, workspace_id),
        ).fetchone()
    )
    if review:
        event_type = {"approved": "approve", "changes_requested": "changes_requested", "rejected": "reject"}[status]
        create_audit_log(db, reviewer_user_id, event_type, "proposal_review", str(review_id), "success", f"status={status};comment_updated={bool(safe_comment)}")
        if safe_comment:
            create_audit_log(db, reviewer_user_id, "comment_update", "proposal_review", str(review_id), "success", "sanitized=true")
    return review


def build_ai_improvement_policy(review_comment: str, current_summary: str = "") -> dict[str, Any]:
    comment = sanitize_workspace_text(review_comment, 500) or "上司コメントに沿って提案内容を見直します。"
    summary = sanitize_workspace_text(current_summary, 300)
    focus = "費用対効果" if any(word in comment for word in ["費用", "効果", "ROI", "投資"]) else "提案の説得力"
    if any(word in comment for word in ["納期", "スケジュール", "体制"]):
        focus = "実行計画"
    if any(word in comment for word in ["競合", "差別化", "強み"]):
        focus = "競合差別化"

    policy_items = [
        f"AI営業：{focus}が伝わる提案メッセージへ修正します。",
        f"AIディレクター：上司コメント「{comment}」を提案ストーリーへ反映します。",
        "AI PM：費用、納期、実行範囲の前提を再確認します。",
        "Knowledge：過去ナレッジと類似案件の成功パターンを優先して補強します。",
    ]
    diff_items = [
        f"{focus}を提案サマリーとまとめに追加します。",
        "上司コメントに対応する説明を本文とスライド原稿へ反映します。",
        "次回確認事項に、人が確認すべき前提条件を残します。",
    ]
    if summary:
        diff_items.append("元の提案要約を維持しつつ、差し戻し箇所だけを補強します。")

    return {
        "ai_improvement_policy": "\n".join(policy_items),
        "diff_summary": diff_items[:5],
        "diff_summary_text": "\n".join(diff_items[:5]),
    }


def apply_review_feedback(db: Connection, review_id: int, user_id: int, current_summary: str = "") -> dict[str, Any] | None:
    organization_id, workspace_id = get_user_context_ids(db, user_id)
    review = _row_to_dict(
        db.execute(
            "SELECT * FROM proposal_reviews WHERE id = ? AND organization_id = ? AND workspace_id = ?",
            (review_id, organization_id, workspace_id),
        ).fetchone()
    )
    if not review:
        return None

    previous_status = str(review.get("status") or "")
    comment = str(review.get("review_comment") or "")
    policy = build_ai_improvement_policy(comment, current_summary)
    next_status = "draft"
    db.execute(
        """
        INSERT INTO proposal_review_revisions
        (review_id, project_id, previous_status, next_status, review_comment, ai_improvement_policy, diff_summary, executed_by_user_id, organization_id, workspace_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            review_id,
            review["project_id"],
            previous_status,
            next_status,
            sanitize_workspace_text(comment, 800),
            policy["ai_improvement_policy"],
            policy["diff_summary_text"],
            user_id,
            organization_id,
            workspace_id,
        ),
    )
    db.execute(
        """
        UPDATE proposal_reviews
        SET status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND organization_id = ? AND workspace_id = ?
        """,
        (next_status, review_id, organization_id, workspace_id),
    )
    create_audit_log(db, user_id, "apply_review_feedback", "proposal_review", str(review_id), "success", "sanitized=true")
    create_audit_log(db, user_id, "regenerate", "proposal_review", str(review_id), "success", "mode=review_feedback")
    create_audit_log(db, user_id, "diff_summary", "proposal_review", str(review_id), "success", "items=3")
    updated = _row_to_dict(
        db.execute(
            "SELECT * FROM proposal_reviews WHERE id = ? AND organization_id = ? AND workspace_id = ?",
            (review_id, organization_id, workspace_id),
        ).fetchone()
    )
    return {
        "review": updated,
        "ai_improvement_policy": policy["ai_improvement_policy"],
        "diff_summary": policy["diff_summary"],
    }


def request_review_again(db: Connection, review_id: int, user_id: int) -> dict[str, Any] | None:
    organization_id, workspace_id = get_user_context_ids(db, user_id)
    review = _row_to_dict(
        db.execute(
            "SELECT * FROM proposal_reviews WHERE id = ? AND organization_id = ? AND workspace_id = ?",
            (review_id, organization_id, workspace_id),
        ).fetchone()
    )
    if not review:
        return None
    previous_status = str(review.get("status") or "")
    db.execute(
        """
        UPDATE proposal_reviews
        SET status = 'review_requested', creator_user_id = ?,
            review_requested_at = CURRENT_TIMESTAMP, reviewed_at = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND organization_id = ? AND workspace_id = ?
        """,
        (user_id, review_id, organization_id, workspace_id),
    )
    db.execute(
        """
        INSERT INTO proposal_review_revisions
        (review_id, project_id, previous_status, next_status, review_comment, ai_improvement_policy, diff_summary, executed_by_user_id, organization_id, workspace_id)
        VALUES (?, ?, ?, 'review_requested', ?, ?, ?, ?, ?, ?)
        """,
        (
            review_id,
            review["project_id"],
            previous_status,
            sanitize_workspace_text(str(review.get("review_comment") or ""), 800),
            "再作成後の内容を上司レビューへ戻しました。",
            "再レビュー依頼を送信しました。",
            user_id,
            organization_id,
            workspace_id,
        ),
    )
    create_audit_log(db, user_id, "rereview_request", "proposal_review", str(review_id), "success", "sanitized=true")
    return _row_to_dict(
        db.execute(
            "SELECT * FROM proposal_reviews WHERE id = ? AND organization_id = ? AND workspace_id = ?",
            (review_id, organization_id, workspace_id),
        ).fetchone()
    )


def list_review_revisions(db: Connection, review_id: int, user_id: int | None = None) -> list[dict[str, Any]]:
    organization_id, workspace_id = get_user_context_ids(db, user_id)
    rows = db.execute(
        """
        SELECT rr.*, u.email AS executed_by_email
        FROM proposal_review_revisions rr
        LEFT JOIN users u ON u.id = rr.executed_by_user_id
        WHERE rr.review_id = ? AND rr.organization_id = ? AND rr.workspace_id = ?
        ORDER BY rr.created_at DESC, rr.id DESC
        LIMIT 50
        """,
        (review_id, organization_id, workspace_id),
    ).fetchall()
    return [dict(row) for row in rows]
