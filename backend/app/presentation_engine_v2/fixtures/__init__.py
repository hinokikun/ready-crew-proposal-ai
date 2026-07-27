"""Offline fixtures for Presentation Engine 2.0 Phase 1."""

from __future__ import annotations

import copy
from typing import Any, Dict, List

from ..schema import example_blueprint_payload, invalid_blueprint_payloads


def _base() -> Dict[str, Any]:
    return copy.deepcopy(example_blueprint_payload())


def _with_common(payload: Dict[str, Any], suffix: str, *, slide_index: int, headline: str, main_message: str) -> Dict[str, Any]:
    payload["blueprint_id"] = f"bp-{suffix}"
    payload["slide_id"] = f"slide-{suffix}"
    payload["slide_index"] = slide_index
    payload["headline"] = headline
    payload["main_message"] = main_message
    payload["primary_element"] = "headline"
    payload["diagram_definition"]["diagram_id"] = f"diagram-{suffix}"
    return payload


def valid_fixture_payloads() -> List[Dict[str, Any]]:
    fixtures: List[Dict[str, Any]] = []

    cover = _with_common(
        _base(),
        "cover",
        slide_index=0,
        headline="AI-OCR導入により確認作業をレビュー中心へ変える",
        main_message="人手確認の品質を保ちながら、AI候補提示で処理負荷を下げる提案です。",
    )
    cover.update({"slide_type": "cover", "slide_goal": "cover", "visual_type": "hero", "diagram_type": "none"})
    fixtures.append(cover)

    agenda = _with_common(
        _base(),
        "agenda",
        slide_index=1,
        headline="本提案では現状課題からPoC判断までを順に確認する",
        main_message="課題、解決方針、PoC計画、評価基準、概算費用、次のアクションを短時間で確認します。",
    )
    agenda.update({"slide_type": "agenda", "slide_goal": "agenda", "visual_type": "text_only", "diagram_type": "none"})
    agenda["content_blocks"] = [
        {"block_id": "agenda-1", "role": "agenda", "text": "現状課題と業務フロー"},
        {"block_id": "agenda-2", "role": "agenda", "text": "AI画像認識による支援方針"},
        {"block_id": "agenda-3", "role": "agenda", "text": "PoC計画と評価基準"},
    ]
    fixtures.append(agenda)

    problem = _with_common(
        _base(),
        "problem",
        slide_index=2,
        headline="繁忙時の目視確認が処理遅延と品質差を生んでいる",
        main_message="画像確認、照合、分類が担当者の経験に依存し、判断履歴も再利用しにくい状態です。",
    )
    problem.update({"slide_type": "problem_statement", "slide_goal": "problem_sharing", "visual_type": "process_flow", "diagram_type": "process_flow"})
    problem["process_steps"] = [
        {"step_id": "step-image", "label": "画像確認"},
        {"step_id": "step-match", "label": "商品データ照合"},
        {"step_id": "step-register", "label": "商品登録"},
    ]
    problem["diagram_definition"].update(
        {
            "diagram_type": "process_flow",
            "nodes": [
                {"node_id": "n1", "label": "画像確認"},
                {"node_id": "n2", "label": "照合"},
                {"node_id": "n3", "label": "登録"},
            ],
            "connectors": [
                {"connector_id": "c1", "source_node_id": "n1", "target_node_id": "n2"},
                {"connector_id": "c2", "source_node_id": "n2", "target_node_id": "n3"},
            ],
        }
    )
    fixtures.append(problem)

    before_after = _base()
    fixtures.append(before_after)

    comparison = _with_common(
        _base(),
        "comparison",
        slide_index=4,
        headline="人手中心とAI支援型の違いを判断負荷で比較する",
        main_message="AI支援型では確認対象を候補に絞り、担当者は最終判断に集中できます。",
    )
    comparison.update({"slide_type": "competitor_comparison", "slide_goal": "comparison", "visual_type": "comparison_table", "diagram_type": "comparison_table"})
    comparison["table_data"] = {
        "columns": [
            {"column_id": "criteria", "label": "観点"},
            {"column_id": "manual", "label": "人手中心"},
            {"column_id": "ai", "label": "AI支援型"},
        ],
        "rows": [
            {"row_id": "workload", "cells": {"criteria": "作業負荷", "manual": "高い", "ai": "レビュー中心"}},
            {"row_id": "history", "cells": {"criteria": "履歴活用", "manual": "限定的", "ai": "再学習に活用"}},
        ],
    }
    fixtures.append(comparison)

    competitive = _with_common(
        _base(),
        "competitive",
        slide_index=5,
        headline="競合比較では精度だけでなく現場運用への適合を重視する",
        main_message="価格や機能だけでなく、人の最終確認を残せる運用設計を差別化ポイントにします。",
    )
    competitive.update({"slide_type": "competitive_landscape", "slide_goal": "competitive_analysis", "visual_type": "matrix_2x2", "diagram_type": "matrix_2x2"})
    competitive["diagram_definition"].update({"diagram_type": "matrix_2x2", "axes": ["運用適合性", "AI活用度"]})
    fixtures.append(competitive)

    kpi = _with_common(
        _base(),
        "kpi",
        slide_index=6,
        headline="PoCでは精度だけでなく確認時間と修正率を測定する",
        main_message="候補正答率、人手修正率、確認時間を評価し、本番化判断の根拠にします。",
    )
    kpi.update({"slide_type": "kpi_definition", "slide_goal": "kpi_definition", "visual_type": "kpi_dashboard", "diagram_type": "kpi_dashboard"})
    kpi["metrics"] = [
        {"metric_id": "m-accuracy", "label": "候補正答率", "value": "PoCで確定", "confidence": "medium"},
        {"metric_id": "m-review", "label": "確認時間", "value": "PoCで測定", "confidence": "medium"},
    ]
    fixtures.append(kpi)

    roi = _with_common(
        _base(),
        "roi",
        slide_index=7,
        headline="ROIは処理時間と誤登録削減の実測から判断する",
        main_message="根拠のない削減率を置かず、PoCで測定した値から投資判断を行います。",
    )
    roi.update({"slide_type": "roi_estimate", "slide_goal": "roi_explanation", "visual_type": "metric_cards", "diagram_type": "metric_cards"})
    roi["metrics"] = [{"metric_id": "m-roi", "label": "ROI", "value": "PoC後に算定", "confidence": "low"}]
    fixtures.append(roi)

    estimate = _with_common(
        _base(),
        "estimate",
        slide_index=8,
        headline="概算費用はPoC範囲と連携条件により調整する",
        main_message="予算上限を前提に、データ準備、モデル検証、連携、運用支援の範囲を確定します。",
    )
    estimate.update({"slide_type": "estimate_overview", "slide_goal": "estimate", "visual_type": "table", "diagram_type": "cost_breakdown"})
    estimate["metrics"] = [{"metric_id": "m-budget", "label": "予算上限", "value": "1,000万円", "confidence": "high"}]
    estimate["table_data"] = {
        "columns": [{"column_id": "item", "label": "区分"}, {"column_id": "note", "label": "内容"}],
        "rows": [
            {"row_id": "poc", "cells": {"item": "PoC設計", "note": "評価基準と対象範囲"}},
            {"row_id": "model", "cells": {"item": "モデル検証", "note": "画像分類と精度確認"}},
        ],
    }
    fixtures.append(estimate)

    timeline = _with_common(
        _base(),
        "timeline",
        slide_index=9,
        headline="PoCから本番判断までを段階的に進める",
        main_message="要件確認、データ確認、モデル検証、現場検証、本番判断の順にリスクを下げます。",
    )
    timeline.update({"slide_type": "timeline", "slide_goal": "timeline", "visual_type": "timeline", "diagram_type": "linear_timeline"})
    timeline["timeline_items"] = [
        {"item_id": "t1", "label": "要件確認", "period": "Step 1"},
        {"item_id": "t2", "label": "モデル検証", "period": "Step 2"},
        {"item_id": "t3", "label": "本番判断", "period": "Step 3", "milestone": True},
    ]
    fixtures.append(timeline)

    roadmap = _with_common(
        _base(),
        "roadmap",
        slide_index=10,
        headline="PoC後は対象カテゴリを広げながら段階展開する",
        main_message="初期カテゴリで運用を固め、確認履歴を活用して対象範囲を広げます。",
    )
    roadmap.update({"slide_type": "roadmap", "slide_goal": "roadmap", "visual_type": "roadmap", "diagram_type": "roadmap_lanes"})
    roadmap["timeline_items"] = [
        {"item_id": "r1", "label": "PoC", "period": "Phase 1"},
        {"item_id": "r2", "label": "限定導入", "period": "Phase 2"},
        {"item_id": "r3", "label": "対象拡大", "period": "Phase 3"},
    ]
    fixtures.append(roadmap)

    process = _with_common(
        _base(),
        "process",
        slide_index=11,
        headline="AI候補提示と人の承認を組み合わせて運用する",
        main_message="画像入力から候補判定、確認、連携、履歴活用までを一連の業務として設計します。",
    )
    process.update({"slide_type": "business_process", "slide_goal": "process", "visual_type": "process_flow", "diagram_type": "human_in_the_loop"})
    process["process_steps"] = [
        {"step_id": "p1", "label": "画像入力"},
        {"step_id": "p2", "label": "AI候補判定"},
        {"step_id": "p3", "label": "人が承認"},
    ]
    fixtures.append(process)

    architecture = _with_common(
        _base(),
        "architecture",
        slide_index=12,
        headline="画像、AI判定、人の確認、既存システム連携を分けて設計する",
        main_message="入力、AI処理、Human Review、Integration、Learningの5層で責務を明確にします。",
    )
    architecture.update({"slide_type": "solution_architecture", "slide_goal": "architecture", "visual_type": "architecture_map", "diagram_type": "layered_architecture"})
    architecture["diagram_definition"].update(
        {
            "diagram_type": "layered_architecture",
            "nodes": [
                {"node_id": "input", "label": "Input"},
                {"node_id": "ai", "label": "AI Processing"},
                {"node_id": "review", "label": "Human Review"},
            ],
        }
    )
    fixtures.append(architecture)

    team = _with_common(
        _base(),
        "team",
        slide_index=13,
        headline="PoCは業務、データ、AI、連携の役割分担で進める",
        main_message="現場責任者、データ担当、AI検証担当、システム連携担当の役割を明確にします。",
    )
    team.update({"slide_type": "team_structure", "slide_goal": "team", "visual_type": "tree", "diagram_type": "stakeholder_map"})
    fixtures.append(team)

    case_study = _with_common(
        _base(),
        "case-study",
        slide_index=14,
        headline="類似業務ではAI候補提示と人の確認を組み合わせる設計が有効",
        main_message="人の判断を完全に置き換えず、確認負荷を下げる進め方が現場定着につながります。",
    )
    case_study.update({"slide_type": "case_study", "slide_goal": "case_study", "visual_type": "three_column", "diagram_type": "none"})
    fixtures.append(case_study)

    risk = _with_common(
        _base(),
        "risk",
        slide_index=15,
        headline="精度、データ量、現場運用のリスクをPoCで確認する",
        main_message="誤判定、カテゴリ不足、運用負荷を事前に見える化し、本番判断の材料にします。",
    )
    risk.update({"slide_type": "risk_register", "slide_goal": "risk_handling", "visual_type": "risk_matrix", "diagram_type": "risk_matrix"})
    fixtures.append(risk)

    faq = _with_common(
        _base(),
        "faq",
        slide_index=16,
        headline="完全自動化ではなく確認支援として導入する",
        main_message="AIは候補を提示し、最終判断は担当者が担うため、現場の責任分界を維持できます。",
    )
    faq.update({"slide_type": "faq", "slide_goal": "faq", "visual_type": "two_column", "diagram_type": "none"})
    fixtures.append(faq)

    next_action = _with_common(
        _base(),
        "next-action",
        slide_index=17,
        headline="次に画像サンプルと評価基準を確認する",
        main_message="PoC範囲を確定するため、対象カテゴリ、正解データ、連携条件を確認します。",
    )
    next_action.update({"slide_type": "next_action", "slide_goal": "next_action", "visual_type": "closing", "diagram_type": "next_action_board"})
    next_action["cta"] = {"cta_type": "start_poc", "cta_label": "PoC範囲を確定する", "cta_detail": "画像サンプルと評価基準を確認します。"}
    fixtures.append(next_action)

    closing = _with_common(
        _base(),
        "closing",
        slide_index=18,
        headline="人の判断を活かしたAI画像認識導入を小さく始める",
        main_message="PoCで現場適合性を確認し、無理なく本番導入へ進めます。",
    )
    closing.update({"slide_type": "closing", "slide_goal": "closing", "visual_type": "closing", "diagram_type": "none"})
    closing["cta"] = {"cta_type": "next_meeting", "cta_label": "次回打ち合わせを設定する", "cta_detail": "PoC条件を合意します。"}
    fixtures.append(closing)

    appendix = _with_common(
        _base(),
        "appendix",
        slide_index=19,
        headline="補足情報は本編と分けて確認できるようにする",
        main_message="技術条件やデータ仕様の詳細は必要に応じて補足資料として扱います。",
    )
    appendix.update({"slide_type": "appendix", "slide_goal": "appendix", "visual_type": "text_only", "diagram_type": "none"})
    fixtures.append(appendix)

    return fixtures


def golden_payloads() -> List[Dict[str, Any]]:
    return valid_fixture_payloads()[:10]


def invalid_fixture_payloads() -> List[Dict[str, Any]]:
    invalid = invalid_blueprint_payloads()
    duplicate = _base()
    duplicate["content_blocks"] = [
        {"block_id": "dup", "role": "body", "text": "最初の説明"},
        {"block_id": "dup", "role": "body", "text": "重複IDの説明"},
    ]
    invalid.append(duplicate)

    cta_missing = _with_common(
        _base(),
        "invalid-cta",
        slide_index=21,
        headline="次に実施することを確認する",
        main_message="次回までに確認事項を整理します。",
    )
    cta_missing.update({"slide_type": "next_action", "slide_goal": "next_action", "visual_type": "closing", "diagram_type": "none"})
    invalid.append(cta_missing)

    return invalid
