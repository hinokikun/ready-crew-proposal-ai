from app.models import ProposalAnalysis


def _bullets(items: list[str]) -> str:
    if not items:
        return "- 次回確認事項として整理します。"
    return "\n".join(f"- {item}" for item in items)


def build_markdown(analysis: ProposalAnalysis) -> str:
    issue_lines = "\n".join(
        [
            f"### {index}. {issue.issue}\n"
            f"- 背景: {issue.background}\n"
            f"- 根拠: {issue.evidence}\n"
            f"- 確度: {issue.confidence}"
            for index, issue in enumerate(analysis.assumed_customer_issues, start=1)
        ]
    )

    priority_lines = "\n".join(
        [
            f"### 優先度 {item.rank}: {item.issue}\n"
            f"- 理由: {item.reason}\n"
            f"- 提案対応: {item.proposed_response}"
            for item in analysis.issue_priorities
        ]
    )

    win = analysis.win_probability
    risk_label = win.risk_label or f"{'★' * win.risk_score}{'☆' * (5 - win.risk_score)}"
    probability = win.probability or 0
    projected = win.projected_probability_after_actions or probability
    win_probability_lines = (
        f"### {win.rank}ランク: {win.label}\n\n"
        f"- 受注確率: {probability}%\n"
        f"- 受注リスク: {risk_label}\n"
        f"- 受注確率向上予測: {probability}% → {projected}%\n\n"
        f"{win.reason}\n\n"
        "#### プラス要因\n"
        f"{_bullets(win.positive_factors)}\n\n"
        "#### リスク要因\n"
        f"{_bullets(win.risk_factors)}\n\n"
        "#### 改善アクション\n"
        f"{_bullets(win.improvement_actions or win.recommended_next_actions)}\n\n"
        "#### 次に確認すべきこと\n"
        f"{_bullets(win.recommended_next_actions)}"
    )

    structure_lines = "\n".join(
        [
            f"| {index} | {item.section} | {item.objective} | {item.key_message} |"
            for index, item in enumerate(analysis.proposal_structure, start=1)
        ]
    )

    slide_lines = "\n\n".join(
        [
            f"### Slide {slide.slide_no}: {slide.title}\n"
            f"- セクション: {slide.section}\n"
            f"- 本文:\n{_bullets(slide.body)}\n"
            f"- 話者メモ: {slide.speaker_notes}\n"
            f"- ビジュアル案: {slide.visual_suggestion}"
            for slide in analysis.slide_scripts
        ]
    )

    qa_lines = "\n".join(
        [
            f"### Q{index}. {qa.question}\n{qa.answer}"
            for index, qa in enumerate(analysis.expected_questions_and_answers, start=1)
        ]
    )

    check = analysis.quality_check
    ppt_lines = "\n\n".join(
        [
            f"### Slide {slide.slide_no}: {slide.title}\n"
            f"- レイアウト: {slide.layout}\n"
            f"- 箇条書き:\n{_bullets(slide.bullets)}\n"
            f"- 話者メモ: {slide.speaker_notes}\n"
            f"- ビジュアル案: {slide.visual_suggestion}"
            for slide in analysis.powerpoint_generation_data.slides
        ]
    )

    return f"""# 提案資料初稿

## 1. 案件概要要約

{analysis.project_summary}

## 2. 顧客課題の推定

{issue_lines}

## 3. 課題優先順位

{priority_lines}

## 4. 受注確率判定

{win_probability_lines}

## 5. 提案方針

{analysis.proposal_policy}

## 6. 提案ストーリー

{analysis.proposal_story}

## 7. 提案資料構成案

| No | セクション | 目的 | キーメッセージ |
| --- | --- | --- | --- |
{structure_lines}

## 8. スライドごとの原稿

{slide_lines}

## 9. 想定質問と回答

{qa_lines}

## 10. 提案資料品質チェック結果

- 論理矛盾: {check.logical_consistency}
- 誤字脱字: {check.typos}
- 提案漏れ: {check.proposal_coverage}
- 競合との差別化: {check.competitive_differentiation}
- 顧客課題との整合性: {check.alignment_with_customer_issues}
- 人間による確認事項: {check.human_review_notes}

## 11. PowerPoint生成用データ

- デッキタイトル: {analysis.powerpoint_generation_data.deck_title}
- 提案先: {analysis.powerpoint_generation_data.client_name}

{ppt_lines}
"""

