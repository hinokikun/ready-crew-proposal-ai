from __future__ import annotations

import re

INTERNAL_LABEL_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (r"\bPoint A\b", "主要論点"),
    (r"\bPoint B\b", "補足論点"),
    (r"\bTheme\s*\d+\b", "重点テーマ"),
    (r"\bCurrent\b", "現状"),
    (r"\bIssue\b", "課題"),
    (r"\bAfter\b", "目指す姿"),
    (r"\bWinning Point\b", "本提案の強み"),
    (r"\bEvidence\b", "判断根拠"),
    (r"\bNext Check\b", "次回確認事項"),
    (r"\bConfirm with customer\b", "お客様と確認"),
    (r"\bDecision Gate\b", "意思決定ポイント"),
    (r"\bQuality Rule\b", "品質確認"),
    (r"\bNumeric Integrity\b", "数値の確認"),
    (r"\bMetric\s*\d+\b", "評価指標"),
    (r"\bKPI Design\s*\d+\b", "KPI設計"),
    (r"\bAction\s*\d+\b", "次のアクション"),
    (r"\bValue\s*\d+\b", "提供価値"),
    (r"\bStep\s*\d+\b", "工程"),
    (r"\bHigh priority\b", "優先度が高い"),
    (r"\bHigh impact\b", "効果が大きい"),
    (r"\bNeeds review\b", "確認が必要"),
    (r"\bLow priority\b", "優先度を調整"),
    (r"\bEstimate Range\b", "概算費用"),
    (r"\bBudget Fit\b", "予算適合"),
    (r"\bScope\b", "提案範囲"),
    (r"\bAI Processing\b", "AI判定"),
    (r"\bHuman Review\b", "人の確認"),
    (r"\bLearning\s*&\s*Ops\b", "改善運用"),
    (r"\bIntegration\b", "連携"),
    (r"\bInput\b", "入力"),
)

INTERNAL_LABEL_PATTERNS = tuple(pattern for pattern, _ in INTERNAL_LABEL_REPLACEMENTS)


def normalize_customer_facing_text(value: str, *, limit: int | None = None) -> str:
    clean = re.sub(r"[ \t]+", " ", (value or "").replace("\r\n", "\n")).strip()
    for pattern, replacement in INTERNAL_LABEL_REPLACEMENTS:
        clean = re.sub(pattern, replacement, clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bWEB PROPOSAL\b", "Web制作提案書", clean, flags=re.IGNORECASE)
    if limit and len(clean) > limit:
        clean = clean[: limit - 1].rstrip("、。・ /-") + "…"
    return clean


def normalize_customer_facing_title(value: str, *, limit: int = 44) -> str:
    title = normalize_customer_facing_text(value)
    title = re.sub(r"\s+", " ", title.replace("\n", " ")).strip(" 。.．")
    if len(title) > limit:
        title = title[: limit - 1].rstrip("、。・ /-") + "…"
    return title or "提案の要点"


def normalize_customer_name(value: str) -> str:
    name = re.sub(r"[ \t\r\n]+", " ", value or "").strip()
    name = re.split(r"[/／|｜]", name)[0].strip()
    name = re.sub(r"^(提案先|顧客|お客様)[:：]\s*", "", name)
    name = re.sub(r"(では|について|向け|御中|様)\s*$", "", name).strip()
    if not name or name in {"不明", "未定", "提案先企業"}:
        return "提案先企業"
    return name[:40]


def find_internal_label_leaks(values: list[str]) -> list[str]:
    leaks: list[str] = []
    for value in values:
        text = value or ""
        for pattern in INTERNAL_LABEL_PATTERNS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                leaks.append(text[:80])
                break
    return leaks


def text_density_score(title: str, bullets: list[str]) -> int:
    body_chars = len("".join(bullets))
    bullet_penalty = max(0, len([item for item in bullets if item.strip()]) - 5) * 10
    title_penalty = max(0, len(title) - 44) * 2
    char_penalty = max(0, body_chars - 180) // 8
    return min(100, body_chars // 4 + bullet_penalty + title_penalty + char_penalty)


def split_label_body(value: str, fallback_label: str) -> tuple[str, str]:
    clean = normalize_customer_facing_text(value)
    if "：" in clean:
        label, body = clean.split("：", 1)
        return normalize_customer_facing_text(label, limit=16), normalize_customer_facing_text(body, limit=58)
    if ":" in clean:
        label, body = clean.split(":", 1)
        return normalize_customer_facing_text(label, limit=16), normalize_customer_facing_text(body, limit=58)
    return fallback_label, normalize_customer_facing_text(clean, limit=58)
