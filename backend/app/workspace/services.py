from __future__ import annotations

import re
from typing import Any


MAX_TEXT_LENGTH = 240

SENSITIVE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "[メールアドレス省略]"),
    (re.compile(r"https?://[^\s)）]+"), "[URL省略]"),
    (re.compile(r"\b(?:\+81[-\s]?)?0\d{1,4}[-\s]?\d{1,4}[-\s]?\d{3,4}\b"), "[電話番号省略]"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"), "[APIキー省略]"),
    (re.compile(r"(?i)(api[_-]?key|password|secret|token)\s*[:=]\s*[^\s,;]+"), r"\1=[機密情報省略]"),
)

ALLOWED_AGENT_NAMES = {"AI秘書", "AI営業", "AIディレクター", "AI PM", "AI社長", "あなた"}
ALLOWED_MESSAGE_TYPES = {"normal", "system", "active", "done", "request", "handoff", "thinking", "explanation", "human"}


def sanitize_workspace_text(value: str, limit: int = MAX_TEXT_LENGTH) -> str:
    text = " ".join((value or "").split())
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    if len(text) > limit:
        return text[: limit - 1].rstrip() + "…"
    return text


def normalize_agent_name(value: str) -> str:
    name = sanitize_workspace_text(value, 40)
    return name if name in ALLOWED_AGENT_NAMES else "AI Workspace"


def normalize_message_type(value: str) -> str:
    return value if value in ALLOWED_MESSAGE_TYPES else "normal"


def normalize_status(value: str) -> str:
    status = sanitize_workspace_text(value, 40).lower()
    return status if status in {"active", "done", "pending", "archived"} else "active"


def build_workspace_summary(project_id: str, conversations: list[dict[str, Any]], work_logs: list[dict[str, Any]]) -> dict[str, Any]:
    by_agent: dict[str, list[str]] = {}
    for item in conversations:
        agent_name = str(item.get("agent_name") or "")
        message = str(item.get("message_body") or "")
        if not agent_name or not message:
            continue
        by_agent.setdefault(agent_name, []).append(message)

    log_texts = [str(item.get("action_summary") or "") for item in work_logs if item.get("action_summary")]

    def pick(agent_name: str, fallback: str) -> str:
        values = by_agent.get(agent_name) or []
        return values[-1] if values else fallback

    summary = {
        "project_id": project_id,
        "reception": pick("AI秘書", "案件受付内容は会話履歴から確認してください。"),
        "proposal_policy": pick("AI営業", "提案方針は提案書作成結果と合わせて確認してください。"),
        "review": pick("AIディレクター", "レビュー内容は作業ログから確認してください。"),
        "schedule_check": pick("AI PM", "スケジュールと見積の確認結果は提案書で確認してください。"),
        "final_decision": pick("AI社長", "最終判断は提出前チェックと合わせて確認してください。"),
        "next_action": "要約PPTを確認し、金額・納期・AI推測ラベルを人が最終確認してください。",
        "log_count": len(work_logs),
        "conversation_count": len(conversations),
    }
    if log_texts:
        summary["latest_log"] = log_texts[-1]

    markdown = "\n".join(
        [
            "# AI Workspace作業まとめ",
            "",
            f"- 案件ID: {project_id}",
            f"- 受付内容: {summary['reception']}",
            f"- 提案方針: {summary['proposal_policy']}",
            f"- レビュー内容: {summary['review']}",
            f"- スケジュール確認: {summary['schedule_check']}",
            f"- 最終判断: {summary['final_decision']}",
            f"- 次アクション: {summary['next_action']}",
        ]
    )
    summary["markdown"] = markdown
    return summary
