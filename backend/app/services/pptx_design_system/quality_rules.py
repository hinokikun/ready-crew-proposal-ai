from __future__ import annotations

from dataclasses import dataclass

from .typography import find_internal_label_leaks, text_density_score


@dataclass(frozen=True)
class ConsultingQualityIssue:
    code: str
    severity: str
    message: str
    recommendation: str


def evaluate_text_quality(title: str, bullets: list[str], layout_sequence: list[str] | None = None) -> list[ConsultingQualityIssue]:
    issues: list[ConsultingQualityIssue] = []
    if len(title) > 44:
        issues.append(ConsultingQualityIssue("CGV3-TITLE", "P1", "タイトルが長く、結論が伝わりにくい可能性があります。", "2行以内の結論タイトルへ短縮してください。"))
    if len([item for item in bullets if item.strip()]) > 5:
        issues.append(ConsultingQualityIssue("CGV3-BULLETS", "P1", "箇条書きが多く、顧客が読み切りにくい状態です。", "5件以内に絞るか図解化してください。"))
    if text_density_score(title, bullets) > 70:
        issues.append(ConsultingQualityIssue("CGV3-DENSITY", "P1", "本文量が多く、文字切れリスクがあります。", "圧縮、分割、図解化の順で改善してください。"))
    leaks = find_internal_label_leaks([title, *bullets])
    if leaks:
        issues.append(ConsultingQualityIssue("CGV3-LABEL", "P0", "顧客向け資料に内部ラベルが残っています。", "自然な日本語ラベルへ置換してください。"))
    if layout_sequence and len(layout_sequence) >= 3 and len(set(layout_sequence[-3:])) == 1:
        issues.append(ConsultingQualityIssue("CGV3-REPEAT", "P1", "同一レイアウトが3枚連続しています。", "目的に合う別シルエットへ切り替えてください。"))
    return issues
