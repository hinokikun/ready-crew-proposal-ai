from __future__ import annotations

import json
from sqlite3 import Connection
from typing import Any

from app.beautiful_ai.schemas import BeautifulAiPresentationRequest
from app.config import settings
from app.repositories import create_audit_log, get_user_context_ids
from app.scoping.service import attach_project_scope
from app.services.beautiful_ai_service import BeautifulAiServiceError, create_beautiful_ai_presentation
from app.workspace.services import sanitize_workspace_text


REVIEW_CATEGORIES: tuple[dict[str, Any], ...] = (
    {
        "key": "story",
        "label": "ストーリー",
        "keywords": ("summary", "concept", "strategy", "サマリー", "戦略", "方針", "流れ"),
        "action_type": "revise_slide",
        "action_title": "提案ストーリーを補強",
        "instruction": "課題、提案、効果、次アクションの流れが一貫するように見出しと説明順を整える。",
    },
    {
        "key": "persuasiveness",
        "label": "説得力",
        "keywords": ("why", "reason", "効果", "根拠", "成果", "理由", "実績"),
        "action_type": "add_evidence",
        "action_title": "根拠・数値を追加",
        "instruction": "提案内容の根拠となるKPI、成果、想定効果を短く追加する。",
    },
    {
        "key": "customer_understanding",
        "label": "課題理解",
        "keywords": ("課題", "現状", "problem", "issue", "顧客理解", "困りごと"),
        "action_type": "revise_slide",
        "action_title": "課題理解を明確化",
        "instruction": "顧客の現状、困りごと、提案が解決する範囲を明確にする。",
    },
    {
        "key": "roi",
        "label": "ROI",
        "keywords": ("ROI", "投資対効果", "費用対効果", "売上", "CV", "問い合わせ"),
        "action_type": "add_roi",
        "action_title": "費用対効果スライドを追加",
        "instruction": "投資額、期待効果、回収期間、KPIを整理したROI説明を追加する。",
        "critical": True,
    },
    {
        "key": "competition",
        "label": "競合比較",
        "keywords": ("競合", "比較", "差別化", "competitor", "勝ち筋"),
        "action_type": "add_competitor_comparison",
        "action_title": "競合比較を追加",
        "instruction": "競合との違い、勝ち筋、提案上の優位性を比較表として追加する。",
        "critical": True,
    },
    {
        "key": "implementation",
        "label": "導入計画",
        "keywords": ("スケジュール", "ロードマップ", "体制", "進め方", "timeline"),
        "action_type": "add_roadmap",
        "action_title": "導入ロードマップを追加",
        "instruction": "制作工程、確認タイミング、公開までの流れをロードマップで整理する。",
    },
    {
        "key": "risk",
        "label": "リスク説明",
        "keywords": ("リスク", "前提", "注意", "契約", "法務"),
        "action_type": "add_faq",
        "action_title": "リスク・前提条件を追加",
        "instruction": "前提条件、確認事項、リスク、よくある質問をまとめる。",
    },
    {
        "key": "next_action",
        "label": "次アクション",
        "keywords": ("次回", "アクション", "next", "contact"),
        "action_type": "revise_next_action",
        "action_title": "次アクションを明確化",
        "instruction": "提案後に顧客が取るべき次アクションを短く明確にする。",
    },
    {
        "key": "summary",
        "label": "まとめ",
        "keywords": ("まとめ", "今後", "next", "conclusion"),
        "action_type": "revise_slide",
        "action_title": "まとめを補強",
        "instruction": "提案の要点、期待効果、次の進め方を1枚に整理する。",
    },
    {
        "key": "design",
        "label": "デザイン",
        "keywords": ("デザイン", "UI", "UX", "ブランド", "visual", "図表"),
        "action_type": "add_chart",
        "action_title": "図表・カードUIを追加",
        "instruction": "文章中心の説明を図表、カード、タイムラインなどの構成指示へ置き換える。",
    },
)

ACTION_CHANGE_TYPE = {
    "add_slide": "追加",
    "delete_slide": "削除",
    "revise_slide": "修正",
    "merge_slides": "統合",
    "reorder_slide": "順序変更",
    "add_chart": "図表追加",
    "add_evidence": "根拠追加",
    "add_case_study": "事例追加",
    "add_roi": "ROI追加",
    "add_competitor_comparison": "競合比較追加",
    "add_roadmap": "ロードマップ追加",
    "add_faq": "FAQ追加",
    "revise_next_action": "次アクション修正",
}

VALID_REVISION_STATUSES = {
    "draft",
    "reviewing",
    "generation_requested",
    "generating",
    "generated",
    "approved",
    "rejected",
    "failed",
    "archived",
}


def _row_to_dict(row: Any) -> dict[str, Any] | None:
    return dict(row) if row else None


def _safe_json(value: Any, limit: int = 60000) -> str:
    text = json.dumps(value, ensure_ascii=False)
    if len(text) <= limit:
        return text
    return json.dumps({"truncated": True, "item_count": len(value) if hasattr(value, "__len__") else None}, ensure_ascii=False)


def _parse_json(value: str | None, fallback: Any) -> Any:
    try:
        return json.loads(value or "")
    except (TypeError, json.JSONDecodeError):
        return fallback


def _safe_text(value: Any, limit: int = 300) -> str:
    return sanitize_workspace_text(str(value or ""), limit)


def _slides(powerpoint_data: dict[str, Any]) -> list[dict[str, Any]]:
    slides = powerpoint_data.get("slides") or []
    return [slide for slide in slides if isinstance(slide, dict)][:80]


def _slide_count(powerpoint_data: dict[str, Any]) -> int:
    return len(_slides(powerpoint_data))


def build_presentation_outline(powerpoint_data: dict[str, Any], *, version: int = 1) -> dict[str, Any]:
    """Build a sanitized structure outline. It intentionally avoids full slide/body persistence."""
    outline_slides: list[dict[str, Any]] = []
    for index, slide in enumerate(_slides(powerpoint_data), start=1):
        bullets = slide.get("bullets") if isinstance(slide.get("bullets"), list) else []
        evidence_summary = " / ".join(_safe_text(item, 80) for item in bullets[:2] if _safe_text(item, 80))
        title = _safe_text(slide.get("title") or slide.get("heading") or f"Slide {index}", 120)
        outline_slides.append(
            {
                "slide_id": f"s{index}",
                "order": index,
                "title": title,
                "purpose": _safe_text(slide.get("layout") or "proposal", 120),
                "content_blocks": ["summary", "evidence"] if evidence_summary else ["summary"],
                "key_message": title,
                "evidence_summary": evidence_summary,
                "visual_intent": _safe_text(slide.get("visual_suggestion") or "", 180),
                "chart_intent": "",
                "image_prompt": _safe_text(slide.get("visual_suggestion") or "", 180),
                "speaker_notes": "",
                "source_type": "generated_outline",
                "requires_confirmation": any(keyword in title for keyword in ("未定", "要確認", "確認")),
            }
        )
    return {
        "presentation_title": _safe_text(powerpoint_data.get("deck_title") or "Proposal", 180),
        "version": f"v{version}",
        "language": "ja",
        "slides": outline_slides,
    }


def _outline_to_powerpoint_data(base_outline: dict[str, Any], *, client_name: str, title_suffix: str) -> dict[str, Any]:
    slides: list[dict[str, Any]] = []
    for slide in base_outline.get("slides") or []:
        if not isinstance(slide, dict):
            continue
        slides.append(
            {
                "slide_no": int(slide.get("order") or len(slides) + 1),
                "layout": "proposal",
                "title": _safe_text(slide.get("title"), 140),
                "bullets": [
                    _safe_text(slide.get("key_message"), 180),
                    _safe_text(slide.get("evidence_summary"), 180),
                    "AI推奨構成のため、提出前に人が確認してください。",
                ],
                "speaker_notes": "Presentation Reviewで作成したRevision構成です。",
                "visual_suggestion": _safe_text(slide.get("visual_intent") or slide.get("chart_intent"), 180),
            }
        )
    return {
        "deck_title": f"{_safe_text(base_outline.get('presentation_title'), 160)} {title_suffix}".strip(),
        "client_name": _safe_text(client_name or "提案先企業", 120),
        "slides": slides,
    }


def _score_category(outline: dict[str, Any], criterion: dict[str, Any]) -> dict[str, Any]:
    text = " ".join(str(slide.get("title") or "") for slide in outline.get("slides") or []).lower()
    text += " " + " ".join(str(slide.get("key_message") or "") for slide in outline.get("slides") or []).lower()
    hits = sum(1 for keyword in criterion["keywords"] if str(keyword).lower() in text)
    score = 2.6 + min(hits, 3) * 0.65
    if len(outline.get("slides") or []) >= 10:
        score += 0.15
    if criterion.get("critical") and hits == 0:
        score -= 0.7
    score = round(max(1.0, min(score, 5.0)), 1)
    return {
        "key": criterion["key"],
        "label": criterion["label"],
        "score": score,
        "reason": "該当構成の有無とスライド見出しをもとに評価しました。",
        "evidence": f"keyword_hits={hits}; slide_count={len(outline.get('slides') or [])}",
        "confidence": 0.72 if hits else 0.56,
        "requires_human_review": bool(score < 4.0 or criterion.get("critical")),
    }


def _action_for_score(score: dict[str, Any], criterion: dict[str, Any], index: int) -> dict[str, Any] | None:
    if float(score["score"]) >= 4.0:
        return None
    priority = "high" if float(score["score"]) < 3.0 or criterion.get("critical") else "medium"
    action_type = str(criterion["action_type"])
    return {
        "action_id": f"a{index:02d}_{criterion['key']}",
        "action_type": action_type,
        "change_type": ACTION_CHANGE_TYPE.get(action_type, "修正"),
        "target_slide_id": None,
        "priority": priority,
        "title": criterion["action_title"],
        "reason": f"{criterion['label']}の評価が{score['score']}点のため改善候補にしました。",
        "instruction": criterion["instruction"],
        "status": "candidate",
        "selected": priority == "high",
    }


def build_presentation_review(powerpoint_data: dict[str, Any]) -> dict[str, Any]:
    outline = build_presentation_outline(powerpoint_data, version=1)
    scores = [_score_category(outline, criterion) for criterion in REVIEW_CATEGORIES]
    actions = [
        action
        for index, (score, criterion) in enumerate(zip(scores, REVIEW_CATEGORIES, strict=True), start=1)
        if (action := _action_for_score(score, criterion, index))
    ]
    titles = [str(slide.get("title") or "") for slide in outline.get("slides") or []]
    if len(titles) != len(set(titles)):
        actions.append(
            {
                "action_id": "a99_duplicate",
                "action_type": "merge_slides",
                "change_type": "統合",
                "target_slide_id": None,
                "priority": "medium",
                "title": "重複スライドを統合",
                "reason": "似た見出しのスライドが複数あります。",
                "instruction": "重複した説明を1枚にまとめ、差分だけを残してください。",
                "status": "candidate",
                "selected": False,
            }
        )
    overall_score = round(sum(float(item["score"]) for item in scores) / len(scores), 1) if scores else 0.0
    unresolved_critical = sum(1 for item in actions if item["priority"] == "high")
    return {
        "overall_score": overall_score,
        "scores": scores,
        "score_map": {item["key"]: item["score"] for item in scores},
        "issues": [
            {
                "category": action["title"],
                "severity": "high" if action["priority"] == "high" else "medium",
                "summary": action["reason"],
            }
            for action in actions
        ],
        "actions": actions,
        "improvements": [
            {
                "type": action["title"],
                "change_type": action["change_type"],
                "summary": action["instruction"],
                "target": action["action_type"],
                **action,
            }
            for action in actions
        ],
        "improvement_summary": f"平均レビュー点は{overall_score}点です。改善候補{len(actions)}件、重要指摘{unresolved_critical}件を検出しました。",
        "slide_count": len(outline.get("slides") or []),
        "added_count": sum(1 for item in actions if item["action_type"].startswith("add_")),
        "removed_count": sum(1 for item in actions if item["action_type"] == "delete_slide"),
        "modified_count": sum(1 for item in actions if item["action_type"] not in {"delete_slide"} and not item["action_type"].startswith("add_")),
        "unresolved_issue_count": unresolved_critical,
        "outline": outline,
    }


def _project_scope(db: Connection, project_id: str, user_id: int) -> tuple[int, int]:
    fallback_org, fallback_workspace = get_user_context_ids(db, user_id)
    project_org, project_workspace = attach_project_scope(db, project_id=project_id)
    return project_org or fallback_org, project_workspace or fallback_workspace


def _next_revision_number(db: Connection, project_id: str, organization_id: int, workspace_id: int) -> int:
    row = db.execute(
        """
        SELECT MAX(revision_number) AS number
        FROM presentation_revisions
        WHERE project_id = ? AND organization_id = ? AND workspace_id = ?
        """,
        (project_id, organization_id, workspace_id),
    ).fetchone()
    return int(row["number"] or 0) + 1 if row else 1


def _max_revisions() -> int:
    return max(1, int(settings.presentation_max_revisions or 3))


def _decorate_review(row: Any) -> dict[str, Any] | None:
    item = _row_to_dict(row)
    if not item:
        return None
    item["scores"] = _parse_json(item.get("scores_json"), [])
    item["issues"] = _parse_json(item.get("issues_json"), [])
    item["improvements"] = _parse_json(item.get("improvements_json"), [])
    item["actions"] = _parse_json(item.get("actions_json"), item["improvements"])
    item["outline"] = _parse_json(item.get("outline_json"), {})
    item["approved"] = bool(item.get("approved"))
    item["overall_score"] = float(item.get("average_score") or 0)
    item["unresolved_issue_count"] = int(item.get("unresolved_issue_count") or 0)
    return item


def _decorate_revision(row: Any) -> dict[str, Any] | None:
    item = _row_to_dict(row)
    if not item:
        return None
    item["approved"] = bool(item.get("approved"))
    item["selected_actions"] = _parse_json(item.get("selected_actions_json"), [])
    item["outline"] = _parse_json(item.get("outline_json"), {})
    item["diff"] = _parse_json(item.get("diff_json"), [])
    return item


def _review_row(db: Connection, review_id: int, organization_id: int, workspace_id: int) -> dict[str, Any] | None:
    row = db.execute(
        "SELECT * FROM presentation_reviews WHERE id = ? AND organization_id = ? AND workspace_id = ?",
        (review_id, organization_id, workspace_id),
    ).fetchone()
    return _decorate_review(row)


def _revision_row(db: Connection, revision_id: int, organization_id: int, workspace_id: int) -> dict[str, Any] | None:
    row = db.execute(
        "SELECT * FROM presentation_revisions WHERE id = ? AND organization_id = ? AND workspace_id = ?",
        (revision_id, organization_id, workspace_id),
    ).fetchone()
    return _decorate_revision(row)


def _record_revision_history(
    db: Connection,
    *,
    project_id: str,
    from_revision_id: int | None,
    to_revision_id: int,
    user_id: int,
    organization_id: int,
    workspace_id: int,
    changes: list[dict[str, Any]],
) -> None:
    for item in changes[:40]:
        db.execute(
            """
            INSERT INTO presentation_revision_history
            (project_id, from_revision_id, to_revision_id, change_type, change_summary, created_by, organization_id, workspace_id,
             change_reason, before_summary, after_summary, field_name, human_action, action_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                from_revision_id,
                to_revision_id,
                _safe_text(item.get("change_type") or "修正", 40),
                _safe_text(item.get("summary") or item.get("instruction"), 300),
                user_id,
                organization_id,
                workspace_id,
                _safe_text(item.get("reason"), 300),
                _safe_text(item.get("before_summary"), 300),
                _safe_text(item.get("after_summary") or item.get("instruction"), 300),
                _safe_text(item.get("field_name") or item.get("target") or "slide_outline", 80),
                _safe_text(item.get("human_action") or item.get("status") or "adopted", 80),
                _safe_text(item.get("action_id"), 80),
            ),
        )


def _apply_actions_to_outline(outline: dict[str, Any], actions: list[dict[str, Any]], revision_number: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    next_outline = json.loads(json.dumps(outline, ensure_ascii=False))
    next_outline["version"] = f"v{revision_number}"
    slides = next_outline.setdefault("slides", [])
    changes: list[dict[str, Any]] = []
    for action in actions[:20]:
        action_type = str(action.get("action_type") or "revise_slide")
        title = _safe_text(action.get("title") or "改善指示", 120)
        instruction = _safe_text(action.get("instruction") or action.get("summary"), 260)
        change_type = ACTION_CHANGE_TYPE.get(action_type, _safe_text(action.get("change_type") or "修正", 40))
        if action_type.startswith("add_"):
            slide_id = f"r{revision_number}_{len(slides) + 1}"
            slides.append(
                {
                    "slide_id": slide_id,
                    "order": len(slides) + 1,
                    "title": title,
                    "purpose": action_type,
                    "content_blocks": ["summary", "evidence", "human_review"],
                    "key_message": instruction,
                    "evidence_summary": _safe_text(action.get("reason"), 180),
                    "visual_intent": "Beautiful.aiでカード、表、タイムラインなどに整形",
                    "chart_intent": "必要に応じて図表化",
                    "image_prompt": "",
                    "speaker_notes": "",
                    "source_type": "presentation_review_action",
                    "requires_confirmation": True,
                }
            )
            after_summary = f"{title}: {instruction}"
        else:
            after_summary = instruction
        changes.append(
            {
                **action,
                "change_type": change_type,
                "summary": instruction,
                "before_summary": "v1 outline field summary",
                "after_summary": after_summary,
                "field_name": "slide_outline",
                "human_action": action.get("status") or "adopted",
            }
        )
    for index, slide in enumerate(slides, start=1):
        if isinstance(slide, dict):
            slide["order"] = index
    return next_outline, changes


def create_presentation_review(
    db: Connection,
    *,
    user_id: int,
    project_id: str,
    project_name: str,
    powerpoint_data: dict[str, Any],
    beautiful_ai_presentation_id: str = "",
) -> dict[str, Any]:
    safe_project_id = _safe_text(project_id, 120)
    safe_project_name = _safe_text(project_name, 160) or "Presentation Review"
    organization_id, workspace_id = _project_scope(db, safe_project_id, user_id)
    review = build_presentation_review(powerpoint_data)
    cursor = db.execute(
        """
        INSERT INTO presentation_reviews
        (project_id, project_name, created_by, average_score, scores_json, issues_json, improvements_json,
         improvement_summary, improvement_count, approved, beautiful_ai_presentation_id, organization_id, workspace_id,
         actions_json, outline_json, unresolved_issue_count, score_schema_version)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, '19.1')
        """,
        (
            safe_project_id,
            safe_project_name,
            user_id,
            float(review["overall_score"]),
            _safe_json(review["scores"]),
            _safe_json(review["issues"]),
            _safe_json(review["improvements"]),
            _safe_text(review["improvement_summary"], 600),
            len(review["actions"]),
            _safe_text(beautiful_ai_presentation_id, 240),
            organization_id,
            workspace_id,
            _safe_json(review["actions"]),
            _safe_json(review["outline"]),
            int(review["unresolved_issue_count"]),
        ),
    )
    review_id = int(cursor.lastrowid)
    revision_number = _next_revision_number(db, safe_project_id, organization_id, workspace_id)
    revision_cursor = db.execute(
        """
        INSERT INTO presentation_revisions
        (project_id, review_id, revision_number, revision_label, slide_count, added_slide_count, removed_slide_count,
         modified_slide_count, improvement_summary, beautiful_ai_presentation_id, approved, created_by, organization_id, workspace_id,
         status, outline_json, selected_actions_json, diff_json, editor_url, player_url)
        VALUES (?, ?, ?, ?, ?, 0, 0, 0, ?, ?, 0, ?, ?, ?, 'generated', ?, '[]', '[]', '', '')
        """,
        (
            safe_project_id,
            review_id,
            revision_number,
            f"Proposal v{revision_number}",
            int(review["slide_count"]),
            "Initial generated outline for Presentation Review.",
            _safe_text(beautiful_ai_presentation_id, 240),
            user_id,
            organization_id,
            workspace_id,
            _safe_json(review["outline"]),
        ),
    )
    _record_revision_history(
        db,
        project_id=safe_project_id,
        from_revision_id=None,
        to_revision_id=int(revision_cursor.lastrowid),
        user_id=user_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        changes=[{"change_type": "追加", "summary": "Initial Presentation Review revision created.", "action_id": "initial"}],
    )
    create_audit_log(db, user_id, "presentation_review", "presentation_review", str(review_id), "success", f"score={review['overall_score']};sanitized=true")
    result = _review_row(db, review_id, organization_id, workspace_id) or {}
    result["latest_revision"] = get_latest_revision(db, safe_project_id, user_id)
    return result


def list_presentation_reviews(db: Connection, *, project_id: str, user_id: int) -> list[dict[str, Any]]:
    organization_id, workspace_id = get_user_context_ids(db, user_id)
    safe_project_id = _safe_text(project_id, 120)
    rows = db.execute(
        """
        SELECT *
        FROM presentation_reviews
        WHERE project_id = ? AND organization_id = ? AND workspace_id = ?
        ORDER BY created_at DESC, id DESC
        LIMIT 20
        """,
        (safe_project_id, organization_id, workspace_id),
    ).fetchall()
    return [item for row in rows if (item := _decorate_review(row))]


def list_presentation_revisions(db: Connection, *, project_id: str, user_id: int) -> list[dict[str, Any]]:
    organization_id, workspace_id = get_user_context_ids(db, user_id)
    safe_project_id = _safe_text(project_id, 120)
    rows = db.execute(
        """
        SELECT r.*, u.email AS created_by_email
        FROM presentation_revisions r
        LEFT JOIN users u ON u.id = r.created_by
        WHERE r.project_id = ? AND r.organization_id = ? AND r.workspace_id = ?
        ORDER BY r.revision_number DESC, r.id DESC
        LIMIT 30
        """,
        (safe_project_id, organization_id, workspace_id),
    ).fetchall()
    return [item for row in rows if (item := _decorate_revision(row))]


def get_latest_revision(db: Connection, project_id: str, user_id: int) -> dict[str, Any] | None:
    revisions = list_presentation_revisions(db, project_id=project_id, user_id=user_id)
    return revisions[0] if revisions else None


def create_revision_from_review(
    db: Connection,
    *,
    review_id: int,
    user_id: int,
    selected_actions: list[dict[str, Any]] | None = None,
    beautiful_ai_presentation_id: str = "",
) -> dict[str, Any] | None:
    organization_id, workspace_id = get_user_context_ids(db, user_id)
    review = _review_row(db, review_id, organization_id, workspace_id)
    if not review:
        return None
    project_id = str(review["project_id"])
    previous = get_latest_revision(db, project_id, user_id)
    revision_number = _next_revision_number(db, project_id, organization_id, workspace_id)
    if revision_number > _max_revisions():
        raise ValueError("max_revisions_reached")
    if previous and previous.get("status") == "approved":
        raise ValueError("revision_already_approved")
    actions = selected_actions if selected_actions is not None else [item for item in (review.get("actions") or []) if item.get("selected")]
    actions = [item for item in actions if str(item.get("status") or "adopted") not in {"rejected", "not_adopted"}]
    if not actions:
        raise ValueError("no_actions_selected")
    previous_outline = previous.get("outline") if previous and previous.get("outline") else review.get("outline") or {}
    next_outline, changes = _apply_actions_to_outline(previous_outline, actions, revision_number)
    added = sum(1 for item in changes if str(item.get("action_type") or "").startswith("add_"))
    removed = sum(1 for item in changes if item.get("action_type") == "delete_slide")
    modified = len(changes) - added - removed
    cursor = db.execute(
        """
        INSERT INTO presentation_revisions
        (project_id, review_id, revision_number, revision_label, slide_count, added_slide_count, removed_slide_count,
         modified_slide_count, improvement_summary, beautiful_ai_presentation_id, approved, created_by, organization_id, workspace_id,
         status, outline_json, selected_actions_json, diff_json, editor_url, player_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, 'draft', ?, ?, ?, '', '')
        """,
        (
            project_id,
            review_id,
            revision_number,
            f"Proposal v{revision_number}",
            len(next_outline.get("slides") or []),
            added,
            removed,
            modified,
            f"Selected {len(actions)} Presentation Review actions for Proposal v{revision_number}.",
            _safe_text(beautiful_ai_presentation_id or str(review.get("beautiful_ai_presentation_id") or ""), 240),
            user_id,
            organization_id,
            workspace_id,
            _safe_json(next_outline),
            _safe_json(actions),
            _safe_json(changes),
        ),
    )
    revision_id = int(cursor.lastrowid)
    _record_revision_history(
        db,
        project_id=project_id,
        from_revision_id=int(previous["id"]) if previous else None,
        to_revision_id=revision_id,
        user_id=user_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        changes=changes,
    )
    create_audit_log(db, user_id, "presentation_revision_draft", "presentation_revision", str(revision_id), "success", f"actions={len(actions)};sanitized=true")
    return _revision_row(db, revision_id, organization_id, workspace_id)


def approve_revision(db: Connection, *, revision_id: int, user_id: int, comment: str = "") -> dict[str, Any] | None:
    organization_id, workspace_id = get_user_context_ids(db, user_id)
    db.execute(
        """
        UPDATE presentation_revisions
        SET approved = 1, status = 'approved', approved_by = ?, approved_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND organization_id = ? AND workspace_id = ? AND status IN ('draft', 'reviewing', 'generated')
        """,
        (user_id, revision_id, organization_id, workspace_id),
    )
    row = _revision_row(db, revision_id, organization_id, workspace_id)
    if not row:
        return None
    create_audit_log(db, user_id, "approve", "presentation_revision", str(revision_id), "success", f"comment={_safe_text(comment, 80)};sanitized=true")
    return row


def reject_revision(db: Connection, *, revision_id: int, user_id: int, comment: str = "") -> dict[str, Any] | None:
    organization_id, workspace_id = get_user_context_ids(db, user_id)
    db.execute(
        """
        UPDATE presentation_revisions
        SET approved = 0, status = 'rejected', updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND organization_id = ? AND workspace_id = ?
        """,
        (revision_id, organization_id, workspace_id),
    )
    row = _revision_row(db, revision_id, organization_id, workspace_id)
    if row:
        create_audit_log(db, user_id, "reject", "presentation_revision", str(revision_id), "success", f"comment={_safe_text(comment, 80)};sanitized=true")
    return row


async def generate_beautiful_ai_revision(
    db: Connection,
    *,
    revision_id: int,
    user_id: int,
    base_request: dict[str, Any],
) -> dict[str, Any] | None:
    organization_id, workspace_id = get_user_context_ids(db, user_id)
    revision = _revision_row(db, revision_id, organization_id, workspace_id)
    if not revision:
        return None
    if revision.get("status") not in {"approved", "generation_requested", "failed"}:
        raise ValueError("revision_not_approved")
    outline = revision.get("outline") or {}
    client_name = str((base_request.get("powerpoint_generation_data") or {}).get("client_name") or "")
    revision_label = str(revision.get("revision_label") or f"Proposal v{revision.get('revision_number')}")
    revised_ppt = _outline_to_powerpoint_data(outline, client_name=client_name, title_suffix=revision_label)
    request_payload = {
        **base_request,
        "project_id": str(revision["project_id"]),
        "powerpoint_generation_data": revised_ppt,
        "force_new": True,
    }
    db.execute(
        """
        UPDATE presentation_revisions
        SET status = 'generating', updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND organization_id = ? AND workspace_id = ?
        """,
        (revision_id, organization_id, workspace_id),
    )
    try:
        response = await create_beautiful_ai_presentation(
            db,
            request=BeautifulAiPresentationRequest(**request_payload),
            user_id=user_id,
        )
    except BeautifulAiServiceError as exc:
        db.execute(
            """
            UPDATE presentation_revisions
            SET status = 'failed', generation_error_type = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND organization_id = ? AND workspace_id = ?
            """,
            (exc.error_type, revision_id, organization_id, workspace_id),
        )
        create_audit_log(db, user_id, "presentation_revision_generation_failed", "presentation_revision", str(revision_id), "failure", f"error_type={exc.error_type}")
        raise
    db.execute(
        """
        UPDATE presentation_revisions
        SET status = 'generated',
            beautiful_ai_presentation_id = ?,
            editor_url = ?,
            player_url = ?,
            generated_at = CURRENT_TIMESTAMP,
            generation_error_type = '',
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND organization_id = ? AND workspace_id = ?
        """,
        (response.presentation_id, response.editor_url, response.player_url, revision_id, organization_id, workspace_id),
    )
    create_audit_log(db, user_id, "presentation_revision_generated", "presentation_revision", str(revision_id), "success", "provider=beautiful.ai;force_new=true")
    return _revision_row(db, revision_id, organization_id, workspace_id)


def compare_revisions(db: Connection, *, project_id: str, user_id: int, from_revision_id: int | None, to_revision_id: int | None) -> dict[str, Any]:
    organization_id, workspace_id = get_user_context_ids(db, user_id)
    safe_project_id = _safe_text(project_id, 120)
    revisions = list_presentation_revisions(db, project_id=safe_project_id, user_id=user_id)
    if not revisions:
        return {"from_revision": None, "to_revision": None, "changes": []}
    to_revision = next((item for item in revisions if int(item["id"]) == int(to_revision_id or 0)), revisions[0])
    from_revision = next((item for item in revisions if int(item["id"]) == int(from_revision_id or 0)), revisions[1] if len(revisions) > 1 else None)
    rows = db.execute(
        """
        SELECT *
        FROM presentation_revision_history
        WHERE project_id = ? AND organization_id = ? AND workspace_id = ?
          AND to_revision_id = ?
          AND (? IS NULL OR from_revision_id = ?)
        ORDER BY created_at ASC, id ASC
        LIMIT 50
        """,
        (
            safe_project_id,
            organization_id,
            workspace_id,
            int(to_revision["id"]),
            int(from_revision["id"]) if from_revision else None,
            int(from_revision["id"]) if from_revision else None,
        ),
    ).fetchall()
    return {"from_revision": from_revision, "to_revision": to_revision, "changes": [dict(row) for row in rows]}


def build_presentation_analytics(db: Connection, scope: Any | None = None) -> dict[str, Any]:
    if scope:
        from app.scope_policy import scope_where

        where, params = scope_where(scope, "r")
    else:
        where, params = "1 = 1", ()
    row = db.execute(
        f"""
        SELECT
            COUNT(*) AS review_count,
            COALESCE(AVG(average_score), 0) AS average_score,
            COALESCE(SUM(improvement_count), 0) AS improvement_count,
            COALESCE(SUM(unresolved_issue_count), 0) AS unresolved_issue_count
        FROM presentation_reviews r
        WHERE {where}
        """,
        params,
    ).fetchone()
    revision_row = db.execute(
        f"""
        SELECT
            COUNT(*) AS revision_count,
            COALESCE(SUM(added_slide_count), 0) AS added_slide_count,
            COALESCE(SUM(removed_slide_count), 0) AS removed_slide_count,
            COALESCE(SUM(CASE WHEN approved = 1 THEN 1 ELSE 0 END), 0) AS approved_count,
            COALESCE(SUM(CASE WHEN status = 'generated' AND beautiful_ai_presentation_id != '' THEN 1 ELSE 0 END), 0) AS generated_count,
            COALESCE(SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END), 0) AS failed_count
        FROM presentation_revisions r
        WHERE {where}
        """,
        params,
    ).fetchone()
    review_count = int(row["review_count"] or 0) if row else 0
    revision_count = int(revision_row["revision_count"] or 0) if revision_row else 0
    approved_count = int(revision_row["approved_count"] or 0) if revision_row else 0
    generated_count = int(revision_row["generated_count"] or 0) if revision_row else 0
    return {
        "average_review_score": round(float(row["average_score"] or 0), 1) if row else 0,
        "review_count": review_count,
        "improvement_count": int(row["improvement_count"] or 0) if row else 0,
        "revision_count": revision_count,
        "added_slide_count": int(revision_row["added_slide_count"] or 0) if revision_row else 0,
        "removed_slide_count": int(revision_row["removed_slide_count"] or 0) if revision_row else 0,
        "improvement_adoption_rate": round((approved_count / revision_count) * 100, 1) if revision_count else 0,
        "beautiful_ai_revision_success_rate": round((generated_count / revision_count) * 100, 1) if revision_count else 0,
        "approval_rate": round((approved_count / revision_count) * 100, 1) if revision_count else 0,
        "unresolved_issue_count": int(row["unresolved_issue_count"] or 0) if row else 0,
        "generation_failure_count": int(revision_row["failed_count"] or 0) if revision_row else 0,
    }
