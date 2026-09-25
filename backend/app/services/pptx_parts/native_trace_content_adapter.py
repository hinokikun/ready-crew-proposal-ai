"""Fail-closed content binding for the isolated native-trace runtime.

This module deliberately stops at an internal dry-run boundary.  It adapts
existing proposal context objects into slot payloads, clones a runtime PPTX,
and validates the injected copy.  It does not import the production slide
dispatcher and it never mutates a source template.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from enum import Enum
import json
from math import ceil
from pathlib import Path
import re
import tempfile
from typing import Any, Callable, Iterable, Mapping
from zipfile import ZIP_DEFLATED, ZipFile
import xml.etree.ElementTree as ET

from app.services.pptx_parts.native_trace_registry import (
    REPO_ROOT,
    canonical_runtime_role,
    get_runtime_native_role_spec,
    load_runtime_native_registry,
)
from app.services.pptx_parts.native_trace_validation import (
    clone_template_package,
    sha256_file,
    validate_injected_template_package,
)


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}
for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)

CONTRACT_PATH = REPO_ROOT / "backend" / "app" / "presentation_assets" / "native_trace" / "schemas" / "role_contracts.json"


class FailureReason(str, Enum):
    ROLE_NOT_REGISTERED = "ROLE_NOT_REGISTERED"
    MISSING_REQUIRED_SLOT = "MISSING_REQUIRED_SLOT"
    UNBOUND_REQUIRED_CONTENT = "UNBOUND_REQUIRED_CONTENT"
    EVIDENCE_REQUIRED = "EVIDENCE_REQUIRED"
    EVIDENCE_IMAGE_REQUIRED = "EVIDENCE_IMAGE_REQUIRED"
    TEXT_OVERFLOW_RISK = "TEXT_OVERFLOW_RISK"
    TEMPLATE_CLONE_FAILED = "TEMPLATE_CLONE_FAILED"
    UNSUPPORTED_RELATIONSHIP = "UNSUPPORTED_RELATIONSHIP"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    SAMPLE_CONTENT_LEAK = "SAMPLE_CONTENT_LEAK"


@dataclass
class NativeSlotPayload:
    role: str
    slide_id: str
    surface: str
    slots: dict[str, str | list[dict[str, Any]]] = field(default_factory=dict)
    source_fields: dict[str, str] = field(default_factory=dict)
    evidence_status: dict[str, str] = field(default_factory=dict)
    unresolved_required_slots: list[str] = field(default_factory=list)
    cleared_optional_slots: list[str] = field(default_factory=list)
    text_fit_constraints: dict[str, Any] = field(default_factory=dict)
    text_replacements: dict[str, str] = field(default_factory=dict)
    table_cell_bindings: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    clear_matching_text: list[str] = field(default_factory=list)
    clear_slots: list[str] = field(default_factory=list)
    font_size_adjustments: dict[str, float] = field(default_factory=dict)
    prohibited_sample_strings: list[str] = field(default_factory=list)
    diagnostics: list[dict[str, Any]] = field(default_factory=list)
    renderable: bool = True
    reason: str | None = None
    failure_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NativeRoleRenderResult:
    success: bool
    role: str
    slide_id: str | None
    surface: str | None
    template: str | None
    package_path: str | None = None
    pptx_bytes: bytes | None = None
    injected_slots: list[str] = field(default_factory=list)
    cleared_optional_slots: list[str] = field(default_factory=list)
    unresolved_slots: list[str] = field(default_factory=list)
    evidence_diagnostics: list[dict[str, Any]] = field(default_factory=list)
    text_fit: dict[str, Any] = field(default_factory=dict)
    validation: dict[str, Any] = field(default_factory=dict)
    reason: str | None = None
    failure_reason: str | None = None
    payload: NativeSlotPayload | None = None

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["payload"] = self.payload.as_dict() if self.payload else None
        data.pop("pptx_bytes", None)
        return data


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _iter_shapes(root: ET.Element) -> Iterable[ET.Element]:
    for element in root.iter():
        if _local_name(element.tag) in {"sp", "pic", "graphicFrame", "grpSp", "cxnSp"}:
            yield element


def _text_nodes(shape: ET.Element) -> list[ET.Element]:
    return [node for node in shape.iter() if _local_name(node.tag) == "t"]


def _shape_name(shape: ET.Element) -> str:
    for node in shape.iter():
        if _local_name(node.tag) == "cNvPr":
            return node.attrib.get("name", "")
    return ""


def _shape_text(shape: ET.Element) -> str:
    return "".join(node.text or "" for node in _text_nodes(shape))


def _get(value: Any, path: str, default: Any = None) -> Any:
    current = value
    for part in path.split("."):
        if current is None:
            return default
        if isinstance(current, Mapping):
            current = current.get(part, default)
        else:
            current = getattr(current, part, default)
    return current


def _first_nonempty(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "" and value != [] and value != {}:
            return value
    return None


PROVENANCE_STATES = frozenset({"VERIFIED", "USER_PROVIDED", "DERIVED", "GENERATED", "UNKNOWN"})
_CONFIRMED_REVIEW_STATES = frozenset({"CONFIRMED", "CORRECTED", "verified", "confirmed", "corrected", "approved"})
_TRUSTED_AUTHORITIES = frozenset({"USER_EXPLICIT", "SYSTEM_EXTRACTED", "EXTERNAL_VERIFIED", "USER_PROVIDED", "EXTERNAL"})
_GENERATED_SOURCE_TYPES = frozenset({"analysis", "ai", "ai_generated", "generated", "proposal_generated", "reasoning_output"})
_DERIVED_SOURCE_TYPES = frozenset({"derived", "rule_based", "heuristic", "inferred"})


def _raw_candidate_records(value: Any) -> list[Mapping[str, Any]]:
    """Read the existing semantic-candidate transport without inventing fields."""

    if value is None:
        return []
    if isinstance(value, Mapping):
        candidates = value.get("candidates")
        if isinstance(candidates, (list, tuple)):
            return [item for item in candidates if isinstance(item, Mapping)]
        return [value]
    candidates = getattr(value, "candidates", None)
    if isinstance(candidates, (list, tuple)):
        result: list[Mapping[str, Any]] = []
        for item in candidates:
            if isinstance(item, Mapping):
                result.append(item)
            elif hasattr(item, "__dict__"):
                result.append(vars(item))
        return result
    if isinstance(value, (list, tuple)):
        return [item for item in value if isinstance(item, Mapping)]
    return []


def _semantic_candidate_records(data: Any, context: Any) -> list[Mapping[str, Any]]:
    records: list[Mapping[str, Any]] = []
    for source in (
        _get(data, "semantic_candidates"),
        _get(context, "semantic_candidates"),
    ):
        records.extend(_raw_candidate_records(source))
    return records


def classify_provenance(record: Mapping[str, Any] | None) -> str:
    """Classify only explicit provenance metadata; absence never becomes VERIFIED."""

    if not record:
        return "UNKNOWN"
    source_type = str(record.get("source_type") or "").strip().lower()
    authority = str(record.get("authority") or "").strip().upper()
    review_state = str(record.get("review_state") or "").strip()
    inferred = bool(record.get("inferred", False))
    if inferred or authority in {"AI_PROPOSED", "EXISTING_STRUCTURED_AI_OUTPUT"} or source_type in _GENERATED_SOURCE_TYPES:
        return "GENERATED"
    if source_type in _DERIVED_SOURCE_TYPES:
        return "DERIVED"
    if review_state in _CONFIRMED_REVIEW_STATES and (
        bool(record.get("admissible_as_evidence"))
        or authority in _TRUSTED_AUTHORITIES
        or bool(record.get("source_reference"))
    ):
        return "VERIFIED"
    if source_type in {"user_input", "user_text", "customer_input", "supplied", "proposal_input"}:
        return "USER_PROVIDED"
    return "UNKNOWN"


def _evidence_records(data: Any, context: Any, *keywords: str) -> list[dict[str, Any]]:
    normalized_keywords = tuple(keyword.lower() for keyword in keywords)
    matched: list[dict[str, Any]] = []
    for record in _semantic_candidate_records(data, context):
        haystack = " ".join(
            str(record.get(key) or "")
            for key in ("semantic_type", "id", "value", "source_field", "source_reference")
        ).lower()
        if normalized_keywords and not any(keyword in haystack for keyword in normalized_keywords):
            continue
        item = dict(record)
        item["classification"] = classify_provenance(record)
        matched.append(item)
    return matched


def _allowed_evidence_records(data: Any, context: Any, *keywords: str, allowed: Iterable[str] = ("VERIFIED", "USER_PROVIDED")) -> list[dict[str, Any]]:
    allowed_states = set(allowed)
    return [record for record in _evidence_records(data, context, *keywords) if record["classification"] in allowed_states]


def _record_diagnostics(payload: NativeSlotPayload, field: str, records: list[dict[str, Any]]) -> None:
    if records:
        payload.diagnostics.append(
            {
                "field": field,
                "provenance": [record["classification"] for record in records],
                "source_fields": [record.get("source_field", "") for record in records],
            }
        )
    else:
        payload.diagnostics.append({"field": field, "provenance": ["UNKNOWN"], "source_fields": []})


def _load_contracts() -> dict[tuple[str, str], dict[str, Any]]:
    if not CONTRACT_PATH.is_file():
        return {}
    with CONTRACT_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return {(str(item.get("surface")), str(item.get("role"))): item for item in payload.get("roles", [])}


ROLE_CONTRACTS = _load_contracts()
RUNTIME_ROLES = {
    (str(item.get("surface")), str(item.get("role")))
    for item in load_runtime_native_registry().get("roles", [])
}

EVIDENCE_SENSITIVE_ROLES = frozenset(
    {
        "MARKET_ANALYSIS",
        "TARGET_ANALYSIS",
        "KPI",
        "ESTIMATE",
        "ROI_OR_EFFECT",
        "COMPETITIVE_COMPARISON",
        "COMPETITION",
        "CASE_STUDY",
        "WIN_PROBABILITY",
        "RISK",
        "SCHEDULE",
        "ROADMAP",
        "IMPLEMENTATION_CONFIGURATION",
    }
)

_GENERIC_PROPOSAL_SAMPLE_STRINGS = (
    "提案資料作成",
    "過去提案",
    "ナレッジ共有",
    "提案エンジン",
    "Proposal Engine",
    "提案書自動生成AI",
    "ナレッジ活用",
    "レビュー運用",
    "提案業務の効率化",
    "提案業務の効率化と提案品質の向上",
    "約70%削減",
    "約1.5倍",
    "約20%向上",
    "約60%増",
    "約1.8倍",
    "約20%",
    "1.5倍",
    "提案資料の叩き台",
    "過去提案・事例・テンプレート",
    "提案書を作成",
    "提案品質・速度・再現性",
    "現行の提案業務フロー",
    "情報整理の自動化",
    "構成提案の最適化",
    "継続改善の仕組み化",
    "業務の自動化",
    "提案品質の向上",
    "提案回数の増加",
    "受注確度の向上",
    "提案の質と量",
    "過去の提案事例",
    "組織で再利用",
    "2 週間",
    "2 ～ 3週間",
    "4 ～ 8週間",
    "約70%削減",
    "約1.5倍",
    "約20%向上",
    "過去の提案資料・競合情報・顧客情報",
    "Proposal Engine",
    "2週間",
    "2～3週間",
    "4～8週間",
)


SAMPLE_STRINGS: dict[str, tuple[str, ...]] = {
    "CURRENT_STATE": _GENERIC_PROPOSAL_SAMPLE_STRINGS,
    "PROBLEM_ANALYSIS": _GENERIC_PROPOSAL_SAMPLE_STRINGS,
    "SOLUTION_CONCEPT": _GENERIC_PROPOSAL_SAMPLE_STRINGS,
    "SOLUTION_APPROACH": _GENERIC_PROPOSAL_SAMPLE_STRINGS,
    "EXECUTIVE_SUMMARY": (
        "導入判断に必要な論点を整理し、課題適合と運用定着の両面から、優先して確認すべき事項を明確化します。",
        "導入範囲を明確化し、対象業務・連携先・期待成果を共通認識化する必要があります。",
        "目的と課題、判断基準、必要データが分散し、導入判断に時間がかかっています。",
        "ERPを基盤に業務情報を整理し、標準化・可視化・再利用性を高める進め方が有効です。",
        "業務時間削減",
        "判断スピード向上",
        "運用定着",
        "情報整理と資料準備の工数を削減",
        "判断材料の可視化で意思決定を迅速化",
        "範囲・役割・KPIを明確にし定着を支援",
        "対象業務・対象部門・連携先の確定",
        "現状値・目標値・測定方法の整理",
        "必須・推奨・任意の費用レンジ確認",
        "決裁者・担当者・導入スケジュールの確認",
        "範囲・KPI・予算の合意を起点に、段階導入で早期成果と運用定着を両立します。",
    ),
    "DECISION_AND_EXPECTED_EFFECTS": (
        "2025年6月22日",
        "ERP導入により、業務の標準化とデータの一元化を実現し",
        "経営の意思決定スピードと事業成長を加速します",
        "本提案は、業務・データ・組織を統合したERP基盤の導入により、全社最適な業務運営と経営の可視化を実現し、持続的な成長に向けた経営基盤を構築するものです。",
        "業務の個別最適化により全社での非効率が発生",
        "データが分散し経営の可視化が困難",
        "事業拡大に向けた業務基盤の強化が急務",
        "業務の標準化とプロセスの最適化",
        "データの一元化とリアルタイムな可視化",
        "現場に適合した段階的な導入・定着",
        "ERPライセンス・インフラ投資",
        "業務設計・開発・移行教育・チェンジマネジメント",
        "運用保守・継続的改善",
        "業務効率化によるコスト削減",
        "データに基づく迅速な意思決定",
        "業務品質の向上と内部統制の強化",
        "事業成長を支えるスケーラブルな基盤",
        "ERP導入の実行承認初期投資の予算確保",
        "全社的な推進体制の構築導入スケジュールの確定",
        "ERP導入は、業務効率化にとどまらず、経営の可視化と事業成長を支える戦略的投資です。",
    ),
    "PROPOSAL_SUMMARY": (
        "提案業務の効率化",
        "提案業務の効率化と提案品質の向上を両立するため、3つの施策を一体で実行します。",
        "提案業務において、以下のような",
        "課題が発生しています。",
        "提案資料作成に時間がかかる",
        "担当者ごとに品質差が生じる",
        "過去提案の再利用が進んでいない",
        "3つの施策で解決",
        "効率化・品質向上・継続改善を一体で推進",
        "提案書自動生成AI",
        "AIで提案資料の叩き台を自動生成し、作成時間を大幅に短縮。",
        "ナレッジ活用",
        "過去の提案・成功事例を組織の資産として活用し、提案精度を高める。",
        "レビュー運用",
        "提出前のレビューで品質を担保し、継続的な改善につなげる。",
        "案件情報から叩き台を自動作成",
        "過去提案・勝ちパターンを再利用",
        "提出前チェックで品質を担保",
        "業界・目的に応じた構成を提案",
        "実績・根拠・表現を資産化",
        "改善ポイントを可視化",
        "短時間で高品質な初稿を生成",
        "提案精度を継続的に向上",
        "継続的な改善サイクルを回す",
        "期待される成果",
        "作成時間の短縮",
        "約70%削減",
        "提案回数の増加",
        "約1.5倍",
        "受注確度の向上",
        "約20%向上",
        "ProposalPilot",
        "AI営業秘書",
        "ご提案の要点",
        "提案業務を効率化し、",
        "提案の質と量を高め、",
        "継続的に成果を生み出す仕組み",
        "を構築します。",
    ),
    "ESTIMATE": ("￥1,500,000", "￥1,200,000", "￥2,000,000", "￥10,500,000", "2026年6月", "1,500,000"),
    "KPI": ("20時間/件", "70%削減", "6時間/件", "月10件", "1.5倍", "5回/件", "30%削減", "20%", "20%向上"),
    "COMPETITIVE_COMPARISON": (
        "競合A", "競合B", "競合より優位", "他社より", "圧倒的",
        "業務理解から提案・制作・改善まで一気通貫で支援",
        "AI活用を前提にした運用設計まで提示",
        "概要見積・体制・スケジュールの透明性が高い",
        "公開後の改善伴走まで含めた提案",
        "当社提案を第一候補として比較継続し、条件調整後に最終判断へ進むことを推奨します。",
    ),
    "COMPETITION": (
        "競合A", "競合B", "競合より優位", "他社より", "圧倒的",
        "業務理解から提案・制作・改善まで一気通貫で支援",
        "AI活用を前提にした運用設計まで提示",
        "概要見積・体制・スケジュールの透明性が高い",
        "公開後の改善伴走まで含めた提案",
        "当社提案を第一候補として比較継続し、条件調整後に最終判断へ進むことを推奨します。",
    ),
    "WIN_PROBABILITY": ("72%", "2025年下期", "高い確度で受注"),
    "SCHEDULE": ("2026.06.22", "Week 1", "Week 6", "Week 12", "Week 20", "1 ～ 2 週", "2 ～ 3 週", "4 ～ 6 週", "2 週"),
        "ROADMAP": (
        "2026.06.22",
        "1ヶ月",
        "1〜2ヶ月",
        "2〜3ヶ月",
        "3〜6ヶ月",
        "Week 1",
        "Week 6",
        "Week 12",
        "Week 20",
        "キックオフ",
        "環境構築完了",
        "トライアル完了",
        "本格展開開始",
        "運用定着",
    ),
    "ROI_OR_EFFECT": ("約70%", "約40%", "約2倍", "約300万円", "約8ヶ月", "約1,140万円"),
    "CASE_STUDY": ("FAJ", "導入企業", "お客様の声", "成功事例"),
    "MARKET_ANALYSIS": ("市場規模", "成長率", "TAM", "SAM", "SOM"),
    "TARGET_ANALYSIS": ("中堅～大企業", "営業部門", "市場セグメント"),
    "RISK": ("営業責任者", "システム管理者", "運用責任者", "事業責任者"),
    "IMPLEMENTATION_CONFIGURATION": (
        "2025年6月22日",
        "業務の標準化・データの一元管理により、部門間の連携を強化し、効率的で拡張性の高いERP基盤を構築します。",
        "販売管理", "見積・受注・売上・請求", "在庫管理", "在庫・入出庫・棚卸",
        "購買管理", "発注・仕入・支払", "生産管理", "生産計画・工程・原価",
        "会計管理", "財務・管理会計・レポート", "基幹システム（既存）",
        "顧客・取引先・商品マスタ連携", "外部サービス", "EDI・電子請求・決済サービス",
        "グループシステム", "人事・勤怠・ワークフロー", "BIツール", "データ分析・経営ダッシュボード",
        "業務データ", "業務プロセス標準化", "ERP基盤", "統合DB", "業務プロセス", "マスタ管理", "権限・セキュリティ", "ERP",
        "データ連携", "外部データ取り込み",
        "1,200 万円〜", "年間 300 万円〜", "400 万円〜", "1,900 万円〜",
        "約 5,000 時間", "約 800 万円", "約 2.4 年", "約 2,400 万円",
        "準備・要件定義", "2か月", "設計・開発", "4か月", "テスト・教育", "本番稼働", "1か月",
        "業務の標準化とデータの一元管理により、コストを最適化し、持続的な成長を支えるERP基盤を構築します。",
    ),
}


def _slide_id_for(role: str, surface: str, slide_id: str | None = None) -> str | None:
    if slide_id:
        return slide_id
    contract = ROLE_CONTRACTS.get((surface, role))
    return str(contract.get("slide_id")) if contract else None


def _contract_for(role: str, surface: str, slide_id: str | None = None) -> dict[str, Any] | None:
    contract = ROLE_CONTRACTS.get((surface, role))
    if contract and (slide_id is None or contract.get("slide_id") == slide_id):
        return contract
    return None


def _title_from_inputs(data: Any, context: Any, slide: Any) -> tuple[str | None, str | None]:
    candidates = (
        ("slide.title", _get(slide, "title")),
        ("data.title", _get(data, "title")),
        ("data.deck_title", _get(data, "deck_title")),
        ("context.title", _get(context, "title")),
        ("context.deck_title", _get(context, "deck_title")),
    )
    for source, value in candidates:
        if value is not None and value != "":
            return str(value), source
    return None, None


def _base_payload(role: str, surface: str, data: Any, context: Any, slide: Any, slide_id: str | None = None) -> NativeSlotPayload:
    resolved_slide_id = _slide_id_for(role, surface, slide_id)
    if resolved_slide_id is None:
        return NativeSlotPayload(
            role=role,
            slide_id=slide_id or "",
            surface=surface,
            renderable=False,
            reason="role contract is missing",
            failure_reason=FailureReason.ROLE_NOT_REGISTERED.value,
        )
    payload = NativeSlotPayload(role=role, slide_id=resolved_slide_id, surface=surface)
    title, source = _title_from_inputs(data, context, slide)
    title_slot = f"trace:{resolved_slide_id}:title.primary"
    if title:
        payload.slots[title_slot] = title
        payload.source_fields[title_slot] = source or "unknown"
        payload.evidence_status[title_slot] = "USER_PROVIDED"
    else:
        payload.unresolved_required_slots.append(title_slot)
    contract = _contract_for(role, surface, resolved_slide_id) or {}
    payload.prohibited_sample_strings = list(SAMPLE_STRINGS.get(role, ()))
    payload.text_fit_constraints = dict(contract.get("slot_constraints", {}))
    return payload


def _blocked(payload: NativeSlotPayload, reason: FailureReason, message: str, *, unresolved: Iterable[str] = ()) -> NativeSlotPayload:
    payload.renderable = False
    payload.reason = message
    payload.failure_reason = reason.value
    payload.unresolved_required_slots.extend(value for value in unresolved if value not in payload.unresolved_required_slots)
    payload.diagnostics.append({"status": "BLOCKED", "reason": reason.value, "message": message})
    return payload


def _generic_adapter(role: str, surface: str, data: Any, context: Any, slide: Any, slide_id: str | None = None) -> NativeSlotPayload:
    payload = _base_payload(role, surface, data, context, slide, slide_id)
    if payload.failure_reason:
        return payload
    if role in EVIDENCE_SENSITIVE_ROLES:
        return _blocked(payload, FailureReason.EVIDENCE_REQUIRED, f"{role} requires current structured evidence")
    resolved_slide_id = payload.slide_id
    bullets = _first_nonempty(
        _get(slide, "bullets"),
        _get(context, "bullets"),
        _get(data, "bullets"),
    )
    dynamic_slot = f"trace:{resolved_slide_id}:content.auto.*"
    if isinstance(bullets, (list, tuple)) and bullets:
        payload.slots[dynamic_slot] = [str(value) for value in bullets if str(value).strip()]
        payload.source_fields[dynamic_slot] = "slide.bullets"
        payload.evidence_status[dynamic_slot] = "USER_PROVIDED"
    else:
        # The semantic contract identifies these as optional dynamic slots;
        # clear them in the clone instead of carrying Canonical/sample copy.
        payload.clear_slots.append(dynamic_slot)
        payload.cleared_optional_slots.append(dynamic_slot)
    if payload.unresolved_required_slots:
        return _blocked(payload, FailureReason.UNBOUND_REQUIRED_CONTENT, "title.primary has no current source value", unresolved=payload.unresolved_required_slots)
    return payload


def _evidence_adapter(role: str, surface: str, data: Any, context: Any, slide: Any, slide_id: str | None = None) -> NativeSlotPayload:
    payload = _base_payload(role, surface, data, context, slide, slide_id)
    if payload.failure_reason:
        return payload
    if payload.unresolved_required_slots:
        return _blocked(payload, FailureReason.UNBOUND_REQUIRED_CONTENT, "required title is unbound", unresolved=payload.unresolved_required_slots)
    return _blocked(payload, FailureReason.EVIDENCE_REQUIRED, f"{role} requires verified current data")


def _candidate_records_for_binding(data: Any, context: Any, *aliases: str) -> list[dict[str, Any]]:
    """Return only explicitly labelled, admissible runtime candidates.

    Values are intentionally excluded from the matching haystack.  A business
    sentence containing a keyword must not decide which semantic slot it
    belongs to; the candidate's explicit type/field metadata must do that.
    """

    normalized_aliases = tuple(alias.lower() for alias in aliases)
    matched: list[dict[str, Any]] = []
    for record in _semantic_candidate_records(data, context):
        haystack = " ".join(
            str(record.get(key) or "")
            for key in ("semantic_type", "id", "source_field", "source_reference", "slot", "field", "role")
        ).lower()
        if normalized_aliases and not any(alias in haystack for alias in normalized_aliases):
            continue
        item = dict(record)
        item["classification"] = classify_provenance(record)
        if item["classification"] in {"VERIFIED", "USER_PROVIDED"}:
            matched.append(item)
    return matched


def _bind_semantic_slots(
    payload: NativeSlotPayload,
    field: str,
    aliases: Iterable[str],
    slots: list[str],
    data: Any,
    context: Any,
) -> bool:
    records = _candidate_records_for_binding(data, context, *aliases)
    _record_diagnostics(payload, field, records)
    values = _direct_verified_values(records)
    if len(values) < len(slots):
        return False
    prohibited = tuple(payload.prohibited_sample_strings)
    if any(sample and sample in value for value in values for sample in prohibited):
        return False
    for index, slot in enumerate(slots):
        record = records[min(index, len(records) - 1)]
        payload.slots[slot] = values[index]
        payload.source_fields[slot] = str(record.get("source_field") or "semantic_candidates")
        payload.evidence_status[slot] = str(record.get("classification") or "UNKNOWN")
    return True


def _semantic_page_candidate_records(data: Any, context: Any, aliases: Iterable[str]) -> list[dict[str, Any]]:
    """Match page candidates on explicit metadata fields, not value text."""

    expected = {str(alias).lower() for alias in aliases}
    matched: list[dict[str, Any]] = []
    for record in _semantic_candidate_records(data, context):
        metadata = (
            str(record.get("semantic_type") or "").strip().lower(),
            str(record.get("source_field") or "").strip().lower(),
            str(record.get("slot") or "").strip().lower(),
            str(record.get("field") or "").strip().lower(),
        )
        if not any(
            value in expected
            or any(value.endswith(f".{alias}") for alias in expected if alias)
            for value in metadata
            if value
        ):
            continue
        item = dict(record)
        item["classification"] = classify_provenance(record)
        if item["classification"] in {"VERIFIED", "USER_PROVIDED"}:
            matched.append(item)
    return matched


def _bind_semantic_page_slot(
    payload: NativeSlotPayload,
    field: str,
    aliases: Iterable[str],
    slot: str,
    data: Any,
    context: Any,
) -> bool:
    records = _semantic_page_candidate_records(data, context, aliases)
    _record_diagnostics(payload, field, records)
    values = _direct_verified_values(records)
    if not values:
        return False
    if any(sample and sample in values[0] for sample in payload.prohibited_sample_strings):
        return False
    record = records[0]
    payload.slots[slot] = values[0]
    payload.source_fields[slot] = str(record.get("source_field") or "semantic_candidates")
    payload.evidence_status[slot] = str(record.get("classification") or "UNKNOWN")
    return True


def _semantic_trace_adapter(
    role: str,
    surface: str,
    data: Any,
    context: Any,
    slide: Any,
    slide_id: str | None = None,
) -> NativeSlotPayload:
    """Bind every business-content region or fail closed before cloning.

    The approved PPTX remains the visual authority, but its body copy is not a
    data source.  Native rendering is allowed only when each dynamic group has
    explicit user/verified provenance.  Otherwise the existing renderer owns
    the slide and the trace-only sample never reaches the output.
    """

    payload = _base_payload(role, surface, data, context, slide, slide_id)
    if payload.failure_reason:
        return payload
    expected_titles = {
        "EXECUTIVE_SUMMARY": "経営判断の要点",
        "DECISION_AND_EXPECTED_EFFECTS": "本提案の結論と期待効果",
    }
    title = payload.slots.get(f"trace:{payload.slide_id}:title.primary")
    if title != expected_titles.get(role):
        return _blocked(
            payload,
            FailureReason.UNBOUND_REQUIRED_CONTENT,
            "approved static trace title does not match the current role contract",
            unresolved=[f"trace:{payload.slide_id}:title.primary"],
        )
    if payload.unresolved_required_slots:
        return _blocked(payload, FailureReason.UNBOUND_REQUIRED_CONTENT, "required title is unbound", unresolved=payload.unresolved_required_slots)

    prefix = f"trace:{payload.slide_id}:"
    if role == "EXECUTIVE_SUMMARY":
        groups = (
            ("summary_context", ("executive_summary.summary_context", "executive_summary.context", "summary_context"), [f"{prefix}title.primary.2"]),
            ("background", ("executive_summary.background", "background", "current_background", "why_now"), [f"{prefix}lead"]),
            ("current_state", ("executive_summary.current_state", "current_state", "current_issue", "problem"), [f"{prefix}lead.2"]),
            ("conclusion", ("executive_summary.conclusion", "conclusion", "decision"), [f"{prefix}lead.3"]),
            ("expected_effects", ("executive_summary.expected_effect", "expected_effect", "expected_effects", "benefit"), [f"{prefix}title.primary.3", f"{prefix}lead.4", f"{prefix}content.auto.64"]),
            ("decision_items", ("executive_summary.decision", "decision_item", "decision_items", "judgment"), [f"{prefix}content.auto.75", f"{prefix}content.auto.90", f"{prefix}content.auto.101", f"{prefix}content.auto.112"]),
            ("insight", ("executive_summary.insight", "insight", "implication"), [f"{prefix}content.auto.118"]),
        )
    else:
        groups = (
            ("summary", ("decision_effects.summary", "decision_and_expected_effects.summary", "decision_summary"), [f"{prefix}title.primary.5"]),
            ("headline", ("decision_effects.headline", "decision_and_expected_effects.headline", "decision_headline"), [f"{prefix}title.primary.3", f"{prefix}title.primary.4"]),
            ("why_now", ("decision_effects.why_now", "why_now", "background"), [f"{prefix}content.auto.34", f"{prefix}content.auto.36", f"{prefix}content.auto.38"]),
            ("policy", ("decision_effects.policy", "basic_policy", "policy", "approach"), [f"{prefix}content.auto.45", f"{prefix}content.auto.47", f"{prefix}content.auto.49"]),
            ("investment", ("decision_effects.investment", "investment", "required_investment"), [f"{prefix}content.auto.60", f"{prefix}content.auto.62", f"{prefix}content.auto.64"]),
            ("effects", ("decision_effects.effects", "expected_effect", "expected_effects", "effect"), [f"{prefix}content.auto.73", f"{prefix}content.auto.75", f"{prefix}content.auto.77", f"{prefix}content.auto.79"]),
            ("decisions", ("decision_effects.decisions", "decisions", "decision_items", "management_decision"), [f"{prefix}content.auto.88", f"{prefix}content.auto.90"]),
            ("insight", ("decision_effects.insight", "insight", "strategic_effect"), [f"{prefix}content.auto.98"]),
        )

    missing: list[str] = []
    for field, aliases, slots in groups:
        if not _bind_semantic_slots(payload, field, aliases, slots, data, context):
            missing.append(field)

    # The date is optional, but a template date is never a current project
    # fact.  Clear it unless it has its own admissible source.
    if role == "DECISION_AND_EXPECTED_EFFECTS":
        date_slot = f"{prefix}title.primary.2"
        date_records = _candidate_records_for_binding(data, context, "decision_effects.date", "decision_date", "verified_date")
        date_values = _direct_verified_values(date_records)
        if date_values and not any(sample in date_values[0] for sample in payload.prohibited_sample_strings):
            payload.slots[date_slot] = date_values[0]
            payload.source_fields[date_slot] = str(date_records[0].get("source_field") or "semantic_candidates")
            payload.evidence_status[date_slot] = str(date_records[0].get("classification") or "UNKNOWN")
        else:
            payload.clear_slots.append(date_slot)
            payload.cleared_optional_slots.append(date_slot)

    if missing:
        # Keep the approved Proposal Master visual when evidence is missing,
        # but clear every unbound body slot before the visual fallback clones
        # the runtime package.  The frozen template copy is never a runtime
        # data source.
        _clear_unbound_semantic_page_slots(payload)
        _clear_unbound_semantic_trace_slots(payload)
        payload.clear_matching_text.extend(payload.prohibited_sample_strings)
        return _blocked(payload, FailureReason.EVIDENCE_REQUIRED, f"explicit runtime evidence is missing for: {', '.join(missing)}")
    payload.clear_matching_text.extend(payload.prohibited_sample_strings)
    return payload


_SEMANTIC_PAGE_BINDINGS: dict[str, dict[str, Any]] = {
    "CURRENT_STATE": {
        "expected_title": "現状理解",
        "groups": (
            ("current_state", ("current_state", "current_understanding", "business_flow"), "lead"),
            ("workflow", ("workflow", "process", "business_process"), "lead.2"),
            ("issue", ("current_issue", "issue", "problem", "pain_point"), "content.auto.30"),
            ("priority", ("priority_theme", "improvement_priority", "priority"), "content.auto.41"),
        ),
    },
    "PROBLEM_ANALYSIS": {
        "expected_title": "主要課題",
        "groups": (
            ("problem_summary", ("problem_summary", "current_issue", "issue", "pain_point"), "lead"),
            ("priority", ("priority_theme", "improvement_priority", "priority"), "content.auto.22"),
            ("evidence", ("evidence", "decision_basis", "verified_issue"), "content.auto.42"),
            ("next_step", ("next_step", "next_action", "improvement_condition", "condition"), "content.auto.78"),
        ),
    },
    "SOLUTION_CONCEPT": {
        "expected_title": "提案コンセプト",
        "groups": (
            ("concept", ("solution_concept", "concept", "proposal_policy", "policy"), "title.primary.2"),
            ("measure", ("measure", "initiative", "solution", "action"), "content.auto.23"),
            ("operation", ("operating_condition", "operation", "adoption_condition"), "content.auto.47"),
            ("outcome", ("expected_outcome", "outcome", "expected_effect"), "content.auto.100"),
        ),
    },
    "SOLUTION_APPROACH": {
        "expected_title": "導入戦略",
        "groups": (
            ("approach", ("solution_approach", "approach", "implementation_policy"), "title.primary.2"),
            ("step", ("implementation_step", "step", "phase", "rollout"), "title.primary.3"),
            ("condition", ("implementation_condition", "condition", "requirement"), "title.primary.4"),
            ("outcome", ("expected_outcome", "outcome", "expected_effect"), "content.auto.94"),
        ),
    },
}


def _clear_unbound_semantic_page_slots(payload: NativeSlotPayload) -> None:
    """Remove frozen body copy unless an explicit runtime slot replaced it."""

    spec = get_runtime_native_role_spec(payload.role, surface=payload.surface, slide_id=payload.slide_id) or {}
    prefix = f"trace:{payload.slide_id}:"
    protected = {
        f"{prefix}content.auto",
        f"{prefix}content.auto.2",
        f"{prefix}content.auto.3",
        f"{prefix}title.primary",
        f"{prefix}footer.brand",
        f"{prefix}footer.brand.2",
    }
    bound = set(payload.slots)
    for slot in spec.get("slot_coverage", ()):
        slot = str(slot)
        if not slot.startswith(prefix) or slot in protected or slot in bound:
            continue
        if slot.startswith(f"{prefix}footer."):
            if slot == f"{prefix}footer.date":
                payload.clear_slots.append(slot)
                payload.cleared_optional_slots.append(slot)
            continue
        if slot.startswith(f"{prefix}header."):
            continue
        if ":content.auto" in slot or ":lead" in slot or ":title.primary." in slot:
            payload.clear_slots.append(slot)
            payload.cleared_optional_slots.append(slot)


_SEMANTIC_TRACE_FALLBACK_SLOTS: dict[str, tuple[str, ...]] = {
    "EXECUTIVE_SUMMARY": (
        "title.primary.2",
        "lead",
        "lead.2",
        "lead.3",
        "content.auto.45",
        "title.primary.3",
        "content.auto.53",
        "lead.4",
        "content.auto.63",
        "content.auto.64",
        "content.auto.75",
        "content.auto.90",
        "content.auto.101",
        "content.auto.112",
        "content.auto.118",
    ),
    "DECISION_AND_EXPECTED_EFFECTS": (
        "title.primary.2",
        "title.primary.3",
        "title.primary.4",
        "title.primary.5",
        "content.auto.34",
        "content.auto.36",
        "content.auto.38",
        "content.auto.45",
        "content.auto.47",
        "content.auto.49",
        "content.auto.60",
        "content.auto.62",
        "content.auto.64",
        "content.auto.73",
        "content.auto.75",
        "content.auto.77",
        "content.auto.79",
        "content.auto.88",
        "content.auto.90",
        "content.auto.98",
    ),
}


_SEMANTIC_TRACE_FALLBACK_COPY: dict[str, dict[str, str]] = {
    "EXECUTIVE_SUMMARY": {
        "title.primary.2": "確認済み情報を整理し、未確認項目は確認後に確定します。",
        "lead": "確認済み情報を整理",
        "lead.2": "対象範囲を確認",
        "lead.3": "判断材料を整理",
        "content.auto.45": "確認済み情報を整理",
        "title.primary.3": "対象範囲を確認",
        "content.auto.53": "判断材料を整理",
        "lead.4": "確認済み情報を整理",
        "content.auto.63": "確認後に確定",
        "content.auto.64": "未確認項目は確認後に確定",
        "content.auto.75": "対象範囲を確認",
        "content.auto.90": "判断材料を整理",
        "content.auto.101": "費用は確認後に確定",
        "content.auto.112": "体制は確認後に確定",
        "content.auto.118": "確認済み情報を整理し、未確認項目は確認後に確定します。",
    },
    "DECISION_AND_EXPECTED_EFFECTS": {
        "title.primary.2": "2026.08.26",
        "title.primary.3": "確認済み課題を整理",
        "title.primary.4": "方針は確認後に確定",
        "title.primary.5": "必要条件を確認し、効果は確認後に確定します。",
        "content.auto.34": "確認済み課題を整理",
        "content.auto.36": "対象範囲を確認",
        "content.auto.38": "判断材料を整理",
        "content.auto.45": "方針は確認後に確定",
        "content.auto.47": "必要条件を確認",
        "content.auto.49": "実施内容を確認",
        "content.auto.60": "必要な情報を確認",
        "content.auto.62": "未確認項目は確認後に確定",
        "content.auto.64": "費用は確認後に確定",
        "content.auto.73": "確認済み情報を整理",
        "content.auto.75": "効果は確認後に確定",
        "content.auto.77": "判断材料を整理",
        "content.auto.79": "次に確認する項目を整理",
        "content.auto.88": "判断事項を整理",
        "content.auto.90": "必要条件を確認",
        "content.auto.98": "確認済み情報を整理し、未確認項目は確認後に確定します。",
    },
}


def _clear_unbound_semantic_trace_slots(payload: NativeSlotPayload) -> None:
    """Replace unbound trace copy with role-safe wording or clear it."""

    prefix = f"trace:{payload.slide_id}:"
    for relative_slot in _SEMANTIC_TRACE_FALLBACK_SLOTS.get(payload.role, ()):
        slot = f"{prefix}{relative_slot}"
        if slot in payload.slots:
            continue
        fallback_text = _SEMANTIC_TRACE_FALLBACK_COPY.get(payload.role, {}).get(relative_slot)
        if fallback_text is not None:
            payload.slots[slot] = fallback_text
            payload.source_fields[slot] = "evidence_safe_fallback"
            payload.evidence_status[slot] = "EVIDENCE_SAFE_FALLBACK"
            continue
        payload.clear_slots.append(slot)
        payload.cleared_optional_slots.append(slot)


def _semantic_page_adapter(
    role: str,
    surface: str,
    data: Any,
    context: Any,
    slide: Any,
    slide_id: str | None = None,
) -> NativeSlotPayload:
    """Bind Slides 05–08 from explicit FAJ evidence, otherwise fail closed."""

    payload = _base_payload(role, surface, data, context, slide, slide_id)
    if payload.failure_reason:
        return payload
    contract = _SEMANTIC_PAGE_BINDINGS.get(role)
    title = payload.slots.get(f"trace:{payload.slide_id}:title.primary")
    if not contract or title != contract["expected_title"]:
        return _blocked(
            payload,
            FailureReason.UNBOUND_REQUIRED_CONTENT,
            "approved static trace title does not match the current role contract",
            unresolved=[f"trace:{payload.slide_id}:title.primary"],
        )
    if payload.unresolved_required_slots:
        return _blocked(payload, FailureReason.UNBOUND_REQUIRED_CONTENT, "required title is unbound", unresolved=payload.unresolved_required_slots)

    missing: list[str] = []
    prefix = f"trace:{payload.slide_id}:"
    for field, aliases, relative_slot in contract["groups"]:
        slot = f"{prefix}{relative_slot}"
        scoped_aliases = tuple(f"{role.lower()}.{alias}" for alias in aliases) + tuple(aliases)
        if not _bind_semantic_page_slot(payload, field, scoped_aliases, slot, data, context):
            missing.append(field)
    if missing:
        return _blocked(payload, FailureReason.EVIDENCE_REQUIRED, f"explicit FAJ evidence is missing for: {', '.join(missing)}")

    # Every unbound body slot is cleared before package validation.  This is
    # what prevents frozen generic proposal copy from surviving a successful
    # native clone when the current payload only covers a subset of regions.
    _clear_unbound_semantic_page_slots(payload)
    _clear_unbound_semantic_trace_slots(payload)
    payload.clear_matching_text.extend(payload.prohibited_sample_strings)
    return payload


def _proposal_summary_adapter(
    role: str,
    surface: str,
    data: Any,
    context: Any,
    slide: Any,
    slide_id: str | None = None,
) -> NativeSlotPayload:
    """Bind Slide 04 business content or fail closed before cloning."""

    payload = _base_payload(role, surface, data, context, slide, slide_id)
    if payload.failure_reason:
        return payload
    if payload.slots.get(f"trace:{payload.slide_id}:title.primary") != "提案サマリー":
        return _blocked(
            payload,
            FailureReason.UNBOUND_REQUIRED_CONTENT,
            "approved static trace title does not match the current role contract",
            unresolved=[f"trace:{payload.slide_id}:title.primary"],
        )
    if payload.unresolved_required_slots:
        return _blocked(payload, FailureReason.UNBOUND_REQUIRED_CONTENT, "required title is unbound", unresolved=payload.unresolved_required_slots)

    prefix = f"trace:{payload.slide_id}:"
    groups = (
        ("summary", ("proposal_summary.summary", "proposal_summary.context", "summary_context", "proposal_context"), [f"{prefix}title.primary.2"]),
        ("current_state", ("proposal_summary.current_state", "proposal_summary.background", "current_state", "background", "current_issue", "problem"), [f"{prefix}title.primary.3", f"{prefix}title.primary.4", f"{prefix}content.auto.28", f"{prefix}content.auto.36"]),
        ("key_measures", ("proposal_summary.key_measure", "proposal_summary.measures", "key_measure", "major_measure", "measures", "solution"), [f"{prefix}title.primary.7", f"{prefix}content.auto.51", f"{prefix}title.primary.55", f"{prefix}content.auto.57", f"{prefix}title.primary.61", f"{prefix}content.auto.73"]),
        ("expected_effects", ("proposal_summary.expected_effect", "proposal_summary.effects", "expected_effect", "expected_effects", "benefit", "outcome"), [f"{prefix}title.primary.9", f"{prefix}content.auto.103", f"{prefix}title.primary.111", f"{prefix}content.auto.113", f"{prefix}title.primary.122", f"{prefix}content.auto.124"]),
        ("decision_items", ("proposal_summary.decision", "proposal_summary.actions", "decision_item", "decision_items", "judgment", "action"), [f"{prefix}content.auto.75", f"{prefix}content.auto.77", f"{prefix}content.auto.79", f"{prefix}content.auto.81", f"{prefix}content.auto.83", f"{prefix}content.auto.85", f"{prefix}content.auto.87", f"{prefix}content.auto.89", f"{prefix}content.auto.91"]),
        ("insight", ("proposal_summary.insight", "insight", "implication", "proposal_point"), [f"{prefix}content.auto.130", f"{prefix}content.auto.131", f"{prefix}content.auto.132", f"{prefix}content.auto.133"]),
    )
    missing: list[str] = []
    for field, aliases, slots in groups:
        if not _bind_semantic_slots(payload, field, aliases, slots, data, context):
            missing.append(field)

    # The template date is not a current project fact.  Clear it unless the
    # caller supplies a separately verified proposal-summary date.
    date_slot = f"{prefix}footer.date"
    date_records = _candidate_records_for_binding(data, context, "proposal_summary.date", "proposal_date", "verified_date")
    date_values = _direct_verified_values(date_records)
    if date_values and not any(sample in date_values[0] for sample in payload.prohibited_sample_strings):
        payload.slots[date_slot] = date_values[0]
        payload.source_fields[date_slot] = str(date_records[0].get("source_field") or "semantic_candidates")
        payload.evidence_status[date_slot] = str(date_records[0].get("classification") or "UNKNOWN")
    else:
        payload.clear_slots.append(date_slot)
        payload.cleared_optional_slots.append(date_slot)

    if missing:
        return _blocked(payload, FailureReason.EVIDENCE_REQUIRED, f"explicit runtime evidence is missing for: {', '.join(missing)}")
    payload.clear_matching_text.extend(payload.prohibited_sample_strings)
    return payload


def _direct_verified_values(records: Iterable[Mapping[str, Any]]) -> list[str]:
    values: list[str] = []
    for record in records:
        value = record.get("value")
        if isinstance(value, (list, tuple)):
            values.extend(str(item).strip() for item in value if str(item).strip())
        elif value is not None and str(value).strip():
            values.append(str(value).strip())
    return values


def _bind_trace_evidence_slots(
    payload: NativeSlotPayload,
    slots: list[str | None],
    records: list[dict[str, Any]],
    field: str,
) -> bool:
    values = _direct_verified_values(records)
    if len(values) < len(slots):
        return False
    prohibited = tuple(payload.prohibited_sample_strings)
    if any(sample and sample in value for value in values for sample in prohibited):
        return False
    for index, slot in enumerate(slots):
        if slot is None:
            continue
        record = records[min(index, len(records) - 1)]
        value = values[index]
        payload.slots[slot] = value
        payload.source_fields[slot] = str(record.get("source_field") or "semantic_candidates")
        payload.evidence_status[slot] = str(record.get("classification") or "UNKNOWN")
    return True


def _implementation_configuration_adapter(
    role: str,
    surface: str,
    data: Any,
    context: Any,
    slide: Any,
    slide_id: str | None = None,
) -> NativeSlotPayload:
    """Fail closed unless every trace-only evidence group is explicitly verified."""

    payload = _base_payload(role, surface, data, context, slide, slide_id)
    if payload.failure_reason:
        return payload
    if payload.unresolved_required_slots:
        return _blocked(payload, FailureReason.UNBOUND_REQUIRED_CONTENT, "required title is unbound", unresolved=payload.unresolved_required_slots)

    evidence_groups = (
        ("implementation_scope", ("implementation_scope", "scope", "target_scope", "coverage"), ["trace:S09:content.auto.13", "trace:S09:title.primary.5", "trace:S09:content.auto.16", "trace:S09:title.primary.6", "trace:S09:content.auto.28", "trace:S09:content.auto.29", "trace:S09:content.auto.37", "trace:S09:content.auto.38", "trace:S09:content.auto.44", "trace:S09:content.auto.45"]),
        ("integration_targets", ("integration", "integration_target", "system", "connection"), ["trace:S09:title.primary.8", "trace:S09:title.primary.9", "trace:S09:content.auto.99", "trace:S09:title.primary.10", "trace:S09:content.auto.105", "trace:S09:content.auto.106", "trace:S09:content.auto.112", "trace:S09:content.auto.113"]),
        ("architecture", ("implementation_architecture", "architecture", "erp_core", "database", "master", "security"), ["trace:S09:content.auto.47", "trace:S09:content.auto.49", "trace:S09:content.auto.52", "trace:S09:content.auto.60", "trace:S09:content.auto.72", "trace:S09:content.auto.75", "trace:S09:content.auto.78", "trace:S09:content.auto.85", "trace:S09:content.auto.115", "trace:S09:content.auto.117"]),
        ("configuration_summary", ("implementation_summary", "configuration_summary", "overall_view", "description"), ["trace:S09:title.primary.3", "trace:S09:content.auto.177"]),
        ("estimate", ("estimate", "cost", "price", "amount", "budget"), ["trace:S09:content.auto.128", "trace:S09:content.auto.130", "trace:S09:content.auto.132", "trace:S09:content.auto.135"]),
        ("roi", ("roi", "effect", "impact", "payback", "productivity", "return"), ["trace:S09:content.auto.144", "trace:S09:content.auto.146", "trace:S09:content.auto.148", "trace:S09:content.auto.151"]),
        ("schedule", ("schedule", "timeline", "milestone", "phase", "date"), [None, "trace:S09:content.auto.160", "trace:S09:content.auto.161", "trace:S09:content.auto.163", "trace:S09:content.auto.164", "trace:S09:content.auto.166", "trace:S09:content.auto.167", "trace:S09:content.auto.169"]),
    )
    missing: list[str] = []
    for field, keywords, slots in evidence_groups:
        records = _allowed_evidence_records(data, context, *keywords, allowed=("VERIFIED",))
        _record_diagnostics(payload, field, records)
        if not records or not _bind_trace_evidence_slots(payload, slots, records, field):
            missing.append(field)
    if missing:
        return _blocked(payload, FailureReason.EVIDENCE_REQUIRED, f"verified evidence is missing for: {', '.join(missing)}")
    payload.prohibited_sample_strings = list(SAMPLE_STRINGS["IMPLEMENTATION_CONFIGURATION"])
    # Every remaining trace-only business string is cleared after the explicit
    # replacements above. If a verified value itself contains one of these
    # samples, validation fails closed instead of allowing a disguised leak.
    payload.clear_matching_text.extend(payload.prohibited_sample_strings)
    return payload


def _estimate_adapter(role: str, surface: str, data: Any, context: Any, slide: Any, slide_id: str | None = None) -> NativeSlotPayload:
    payload = _base_payload(role, surface, data, context, slide, slide_id)
    if payload.failure_reason:
        return payload
    estimate = _first_nonempty(_get(context, "estimate"), _get(data, "estimate"), _get(data, "estimate_summary"))
    verified = bool(_get(context, "verified_estimate", False) or _get(data, "verified_estimate", False))
    records = _allowed_evidence_records(data, context, "estimate", "cost", "price", "amount", "budget")
    _record_diagnostics(payload, "estimate", records)
    if not estimate or not verified or not records:
        return _blocked(payload, FailureReason.EVIDENCE_REQUIRED, "estimate rows/prices are not verified in the current source")
    if payload.unresolved_required_slots:
        return _blocked(payload, FailureReason.UNBOUND_REQUIRED_CONTENT, "required title is unbound", unresolved=payload.unresolved_required_slots)
    payload.source_fields["estimate"] = "context.estimate"
    payload.evidence_status["estimate"] = "VERIFIED"
    return payload


def _kpi_adapter(role: str, surface: str, data: Any, context: Any, slide: Any, slide_id: str | None = None) -> NativeSlotPayload:
    payload = _base_payload(role, surface, data, context, slide, slide_id)
    if payload.failure_reason:
        return payload
    actuals = _first_nonempty(_get(context, "verified_kpi_rows"), _get(data, "verified_kpi_rows"))
    records = _allowed_evidence_records(data, context, "kpi", "metric", "actual", "value")
    if not actuals or not records:
        payload.diagnostics.append({"field": "kpi.current_value", "status": "CLEARED", "fallback": "未取得"})
        _record_diagnostics(payload, "kpi.current_value", records)
        return _blocked(payload, FailureReason.EVIDENCE_REQUIRED, "KPI actual values or measurement evidence are unavailable")
    _record_diagnostics(payload, "kpi.current_value", records)
    if payload.unresolved_required_slots:
        return _blocked(payload, FailureReason.UNBOUND_REQUIRED_CONTENT, "required title is unbound", unresolved=payload.unresolved_required_slots)
    payload.source_fields["kpi.current_value"] = "context.verified_kpi_rows"
    payload.evidence_status["kpi.current_value"] = "VERIFIED"
    return payload


def _normalized_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _required_strings(value: Any, count: int, field_name: str) -> tuple[list[str] | None, str | None]:
    if not isinstance(value, (list, tuple)) or len(value) < count:
        return None, f"{field_name} requires at least {count} structured values"
    values = [_normalized_string(item) for item in value[:count]]
    if any(item is None for item in values):
        return None, f"{field_name} contains an empty required value"
    return [str(item) for item in values], None


def _competition_row(item: Any) -> dict[str, str | None]:
    if isinstance(item, Mapping):
        return {
            "criterion": _first_nonempty(item.get("criterion"), item.get("comparison_criterion"), item.get("label"), item.get("name")),
            "own_value": _first_nonempty(item.get("own_value"), item.get("proposal_value"), item.get("our_value"), item.get("verified_value"), item.get("value")),
            "competitor_a_value": _first_nonempty(item.get("competitor_a_value"), item.get("competitor_a"), item.get("comparison_a"), item.get("a_value")),
            "competitor_b_value": _first_nonempty(item.get("competitor_b_value"), item.get("competitor_b"), item.get("comparison_b"), item.get("b_value")),
            "evaluation": _first_nonempty(item.get("evaluation"), item.get("assessment"), item.get("result")),
            "competitor_a_name": _first_nonempty(item.get("competitor_a_name"), item.get("competitor_a_label")),
            "competitor_b_name": _first_nonempty(item.get("competitor_b_name"), item.get("competitor_b_label")),
        }
    if isinstance(item, (list, tuple)):
        values = list(item)
        return {
            "criterion": values[0] if len(values) > 0 else None,
            "own_value": values[1] if len(values) > 1 else None,
            "competitor_a_value": values[2] if len(values) > 2 else None,
            "competitor_b_value": values[3] if len(values) > 3 else None,
            "evaluation": values[4] if len(values) > 4 else None,
            "competitor_a_name": None,
            "competitor_b_name": None,
        }
    return {"criterion": None, "own_value": None, "competitor_a_value": None, "competitor_b_value": None, "evaluation": None, "competitor_a_name": None, "competitor_b_name": None}


def _bind_table_rows(payload: NativeSlotPayload, table_slot: str, rows: list[dict[str, Any]]) -> None:
    payload.table_cell_bindings[table_slot] = rows


def _competition_adapter(role: str, surface: str, data: Any, context: Any, slide: Any, slide_id: str | None = None) -> NativeSlotPayload:
    payload = _base_payload(role, surface, data, context, slide, slide_id)
    rows = _first_nonempty(_get(context, "competitor_rows"), _get(data, "competitor_rows"))
    payload.source_fields["competition.rows"] = "context.competitor_rows" if rows else "unavailable"
    records = _allowed_evidence_records(data, context, "competitor", "competition", "comparison", "differentiation")
    payload.evidence_status["competition.rows"] = records[0]["classification"] if records else "UNKNOWN"
    _record_diagnostics(payload, "competition.rows", records)
    if not rows or not records:
        return _blocked(payload, FailureReason.EVIDENCE_REQUIRED, "competitor claims require provenance that the current model does not expose")
    row_items = list(rows) if isinstance(rows, (list, tuple)) else []
    normalized_rows = [_competition_row(item) for item in row_items]
    if len(normalized_rows) < 5:
        return _blocked(payload, FailureReason.UNBOUND_REQUIRED_CONTENT, "competition requires five complete comparison rows", unresolved=["competition.rows[0..4]"])
    required_row_fields = ("criterion", "own_value", "competitor_a_value", "competitor_b_value", "evaluation")
    missing_rows = [
        index + 1
        for index, row in enumerate(normalized_rows[:5])
        if any(_normalized_string(row.get(field)) is None for field in required_row_fields)
    ]
    if missing_rows:
        return _blocked(payload, FailureReason.UNBOUND_REQUIRED_CONTENT, "competition rows contain unbound required cells", unresolved=[f"competition.row.{index}" for index in missing_rows])
    competitor_a_name = _first_nonempty(
        _get(context, "competitor_a_name"), _get(data, "competitor_a_name"),
        normalized_rows[0].get("competitor_a_name"),
    )
    competitor_b_name = _first_nonempty(
        _get(context, "competitor_b_name"), _get(data, "competitor_b_name"),
        normalized_rows[0].get("competitor_b_name"),
    )
    if not competitor_a_name or not competitor_b_name:
        return _blocked(payload, FailureReason.UNBOUND_REQUIRED_CONTENT, "competition requires explicit competitor labels", unresolved=["competition.competitor_a_name", "competition.competitor_b_name"])
    criteria = [str(row["criterion"]) for row in normalized_rows[:5]]
    payload.slots.update({
        f"trace:{payload.slide_id}:content.auto.{35 + index}": value
        for index, value in enumerate(criteria, start=1)
    })
    payload.table_cell_bindings[f"trace:{payload.slide_id}:title.primary.4"] = [
        {"row": 0, "col": 2, "value": str(competitor_a_name)},
        {"row": 0, "col": 3, "value": str(competitor_b_name)},
        *[
            {"row": index, "col": col, "value": str(normalized_rows[index - 1][field])}
            for index in range(1, 6)
            for col, field in ((1, "own_value"), (2, "competitor_a_value"), (3, "competitor_b_value"), (4, "evaluation"))
        ],
    ]
    differentiation, differentiation_error = _required_strings(
        _first_nonempty(_get(context, "differentiation_bullets"), _get(data, "differentiation_bullets")),
        4,
        "competition.differentiation_bullets",
    )
    caution, caution_error = _required_strings(
        _first_nonempty(_get(context, "caution_items"), _get(data, "caution_items")),
        2,
        "competition.caution_items",
    )
    confirmation, confirmation_error = _required_strings(
        _first_nonempty(_get(context, "next_confirmation_items"), _get(data, "next_confirmation_items")),
        3,
        "competition.next_confirmation_items",
    )
    recommendation = _normalized_string(_first_nonempty(_get(context, "recommendation"), _get(data, "recommendation")))
    missing_content = [
        error for error in (differentiation_error, caution_error, confirmation_error)
        if error
    ]
    if recommendation is None:
        missing_content.append("competition.recommendation is required")
    if missing_content:
        return _blocked(payload, FailureReason.UNBOUND_REQUIRED_CONTENT, "competition contains unbound required dynamic regions", unresolved=missing_content)
    payload.slots.update({
        f"trace:{payload.slide_id}:title.primary.{5 + index}": value
        for index, value in enumerate(differentiation, start=1)
    })
    payload.slots[f"trace:{payload.slide_id}:lead"] = caution[0]
    payload.slots[f"trace:{payload.slide_id}:lead.2"] = caution[1]
    for index, value in enumerate(confirmation):
        payload.slots[f"trace:{payload.slide_id}:content.auto.{70 + (index * 2)}"] = value
    payload.slots[f"trace:{payload.slide_id}:content.auto.79"] = recommendation
    for slot in list(payload.slots) + list(payload.table_cell_bindings):
        if slot.startswith(f"trace:{payload.slide_id}:"):
            payload.source_fields[slot] = "context.competition_verified_binding"
            payload.evidence_status[slot] = records[0]["classification"]
    payload.text_replacements.update({"競合A": str(competitor_a_name), "競合B": str(competitor_b_name)})
    payload.text_replacements["2026.06.22"] = "2026.08.26"
    payload.clear_slots.append(f"trace:{payload.slide_id}:footer.date")
    payload.cleared_optional_slots.append(f"trace:{payload.slide_id}:footer.date")
    payload.clear_matching_text.extend(SAMPLE_STRINGS["COMPETITION"])
    payload.source_fields["competition.rows"] = "context.competitor_rows"
    payload.evidence_status["competition.rows"] = records[0]["classification"]
    return payload


def _win_probability_adapter(role: str, surface: str, data: Any, context: Any, slide: Any, slide_id: str | None = None) -> NativeSlotPayload:
    payload = _base_payload(role, surface, data, context, slide, slide_id)
    win = _first_nonempty(_get(context, "win_probability"), _get(data, "win_probability"))
    if not win:
        return _blocked(payload, FailureReason.EVIDENCE_REQUIRED, "win probability/confidence is unavailable")
    records = _allowed_evidence_records(data, context, "win_probability", "probability", "confidence", "受注確度")
    _record_diagnostics(payload, "win_probability", records)
    if not records:
        return _blocked(payload, FailureReason.EVIDENCE_REQUIRED, "win probability has no explicit verified/user-provided provenance")
    probability = _first_nonempty(_get(win, "probability"), _get(win, "percentage"), _get(win, "value"))
    probability_text = None
    if probability not in (None, "", 0, "0"):
        payload.source_fields["win_probability.value"] = records[0].get("source_field") or "semantic_candidates"
        payload.evidence_status["win_probability.value"] = records[0]["classification"]
        probability_text = f"{probability}%" if isinstance(probability, int) else str(probability)
    else:
        label = _first_nonempty(_get(win, "label"), _get(win, "confidence"))
        if label:
            payload.source_fields["win_probability.label"] = records[0].get("source_field") or "semantic_candidates"
            payload.evidence_status["win_probability.label"] = records[0]["classification"]
            probability_text = str(label)
            payload.diagnostics.append({"field": "win_probability.value", "fallback": "高 / 中 / 低 or 要確認"})
        else:
            return _blocked(payload, FailureReason.EVIDENCE_REQUIRED, "win probability has neither a current percentage nor a qualitative confidence")
    period = _first_nonempty(_get(win, "period"), _get(win, "evaluation_period"), _get(win, "evidence_period"))
    confidence = _first_nonempty(_get(win, "confidence"), _get(win, "label"), "要確認")
    evidence_rows = _first_nonempty(_get(win, "evidence_rows"), _get(context, "win_evidence_rows"), _get(data, "win_evidence_rows"))
    if not isinstance(evidence_rows, (list, tuple)) or len(evidence_rows) < 5:
        return _blocked(payload, FailureReason.UNBOUND_REQUIRED_CONTENT, "win probability requires five structured evidence rows", unresolved=["win_probability.evidence_rows[0..4]"])
    normalized_evidence: list[dict[str, str]] = []
    for index, item in enumerate(evidence_rows[:5], start=1):
        row = {
            "item": _first_nonempty(_get(item, "item"), _get(item, "label"), _get(item, "name")),
            "content": _first_nonempty(_get(item, "content"), _get(item, "evidence"), _get(item, "value"), _get(item, "text")),
            "weight": _first_nonempty(_get(item, "weight"), _get(item, "importance")),
            "evaluation": _first_nonempty(_get(item, "evaluation"), _get(item, "assessment"), _get(item, "result")),
        }
        if any(_normalized_string(row[key]) is None for key in row):
            return _blocked(payload, FailureReason.UNBOUND_REQUIRED_CONTENT, f"win probability evidence row {index} is incomplete", unresolved=[f"win_probability.evidence_row.{index}"])
        normalized_evidence.append({key: str(value) for key, value in row.items()})
    positive, positive_error = _required_strings(_get(win, "positive_factors"), 4, "win_probability.positive_factors")
    risks, risks_error = _required_strings(_get(win, "risk_factors"), 4, "win_probability.risk_factors")
    next_action_cards = _first_nonempty(_get(win, "next_action_cards"), _get(context, "win_next_action_cards"), _get(data, "win_next_action_cards"))
    next_actions: list[str] | None = None
    next_actions_error: str | None = None
    next_action_bodies: list[str] | None = None
    if not isinstance(next_action_cards, (list, tuple)) or len(next_action_cards) < 3:
        next_actions_error = "win_probability.next_action_cards requires at least 3 structured cards"
    else:
        next_actions = []
        next_action_bodies = []
        for index, card in enumerate(next_action_cards[:3], start=1):
            title = _normalized_string(_first_nonempty(_get(card, "title"), _get(card, "label"), _get(card, "name")))
            body = _normalized_string(_first_nonempty(_get(card, "body"), _get(card, "description"), _get(card, "text")))
            if title is None or body is None:
                next_actions_error = f"win_probability.next_action_cards[{index}] requires title and body"
                break
            next_actions.append(title)
            next_action_bodies.append(body)
    decision_direction = _normalized_string(_first_nonempty(_get(win, "decision_direction"), _get(win, "decision_text")))
    reason = _normalized_string(_first_nonempty(_get(win, "reason"), _get(win, "rationale")))
    missing_content = [error for error in (positive_error, risks_error, next_actions_error) if error]
    if decision_direction is None:
        missing_content.append("win_probability.decision_direction is required")
    if reason is None:
        missing_content.append("win_probability.reason is required")
    if missing_content:
        return _blocked(payload, FailureReason.UNBOUND_REQUIRED_CONTENT, "win probability contains unbound required dynamic regions", unresolved=missing_content)
    payload.slots[f"trace:{payload.slide_id}:content.auto.7"] = probability_text or "要確認"
    payload.slots[f"trace:{payload.slide_id}:content.auto.19"] = probability_text or "要確認"
    payload.slots[f"trace:{payload.slide_id}:title.primary.4"] = str(_first_nonempty(_get(win, "confidence_summary"), confidence))
    payload.slots[f"trace:{payload.slide_id}:title.primary.5"] = reason
    for index, value in enumerate(positive, start=6):
        payload.slots[f"trace:{payload.slide_id}:title.primary.{index}"] = value
    risk_slots = ("content.auto.54", "lead", "content.auto.57", "content.auto.59")
    for slot, value in zip(risk_slots, risks):
        payload.slots[f"trace:{payload.slide_id}:{slot}"] = value
    for index, value in enumerate(next_actions, start=1):
        payload.slots[f"trace:{payload.slide_id}:content.auto.{70 + ((index - 1) * 3)}"] = value
        payload.slots[f"trace:{payload.slide_id}:content.auto.{76 + index}"] = next_action_bodies[index - 1]
    payload.slots[f"trace:{payload.slide_id}:content.auto.84"] = decision_direction
    payload.table_cell_bindings[f"trace:{payload.slide_id}:content.auto.30"] = [
        {"row": index, "col": col, "value": value}
        for index, row in enumerate(normalized_evidence, start=1)
        for col, value in enumerate((row["item"], row["content"], row["weight"], row["evaluation"]))
    ]
    payload.text_replacements["72%"] = probability_text or "要確認"
    payload.text_replacements["2025年下期"] = str(period) if period else "要確認"
    payload.text_replacements["高い確度で受注"] = str(confidence)
    payload.clear_slots.append(f"trace:{payload.slide_id}:footer.date")
    payload.cleared_optional_slots.append(f"trace:{payload.slide_id}:footer.date")
    payload.clear_matching_text.extend(SAMPLE_STRINGS["WIN_PROBABILITY"])
    if payload.unresolved_required_slots:
        return _blocked(payload, FailureReason.UNBOUND_REQUIRED_CONTENT, "required title is unbound", unresolved=payload.unresolved_required_slots)
    return payload


def _schedule_adapter(role: str, surface: str, data: Any, context: Any, slide: Any, slide_id: str | None = None) -> NativeSlotPayload:
    payload = _base_payload(role, surface, data, context, slide, slide_id)
    phases = _first_nonempty(_get(context, "verified_schedule_phases"), _get(data, "verified_schedule_phases"))
    records = _allowed_evidence_records(data, context, "schedule", "phase", "milestone", "owner", "date")
    _record_diagnostics(payload, "schedule.phases", records)
    if not isinstance(phases, (list, tuple)) or not (3 <= len(phases) <= 5) or not records:
        return _blocked(payload, FailureReason.EVIDENCE_REQUIRED, "schedule dates, owners, and milestones are not verified")
    durations: list[str] = []
    for phase in phases:
        if not isinstance(phase, Mapping):
            return _blocked(payload, FailureReason.EVIDENCE_REQUIRED, "schedule phase is not structured")
        duration = _first_nonempty(phase.get("duration"), phase.get("period"), phase.get("timing"))
        owner = _first_nonempty(phase.get("owner"), phase.get("responsible"))
        milestone = _first_nonempty(phase.get("milestone"), phase.get("deliverable"), phase.get("review_point"))
        if not duration or not owner or not milestone:
            return _blocked(payload, FailureReason.EVIDENCE_REQUIRED, "schedule phase lacks explicit duration, owner, or milestone")
        durations.append(str(duration))
    start_date = _first_nonempty(
        _get(context, "verified_schedule_start_date"), _get(data, "verified_schedule_start_date"),
        _get(context, "schedule_start_date"), _get(data, "schedule_start_date"),
    )
    if not start_date:
        return _blocked(payload, FailureReason.EVIDENCE_REQUIRED, "schedule start date is not verified")
    sample_duration_strings = ("1 ～ 2 週", "2 ～ 3 週", "4 ～ 6 週", "2 週")
    payload.text_replacements["2026.06.22"] = str(start_date)
    for old, new in zip(sample_duration_strings, durations):
        payload.text_replacements[old] = new if str(new).startswith(("(", "約")) else str(new)
    payload.clear_slots.append(f"trace:{payload.slide_id}:footer.date")
    payload.cleared_optional_slots.append(f"trace:{payload.slide_id}:footer.date")
    payload.clear_matching_text.extend(SAMPLE_STRINGS["SCHEDULE"])
    if payload.unresolved_required_slots:
        return _blocked(payload, FailureReason.UNBOUND_REQUIRED_CONTENT, "required title is unbound", unresolved=payload.unresolved_required_slots)
    payload.source_fields["schedule.phases"] = "context.verified_schedule_phases"
    payload.evidence_status["schedule.phases"] = "VERIFIED"
    return payload


def _roadmap_provenance_allowed(record: Mapping[str, Any]) -> bool:
    """Accept only evidence that is explicit or derived from explicit evidence."""

    classification = str(record.get("classification") or "")
    if classification in {"VERIFIED", "USER_PROVIDED"}:
        return True
    if classification != "DERIVED":
        return False
    return bool(
        record.get("derived_from_verified")
        or record.get("derived_from") in {"VERIFIED", "USER_PROVIDED", "explicit_input"}
        or record.get("basis") in {"VERIFIED", "USER_PROVIDED"}
    )


def _roadmap_value(item: Any, *keys: str) -> Any:
    if isinstance(item, str) and any(key in {"text", "label", "value", "title", "name"} for key in keys):
        return item
    if isinstance(item, Mapping):
        return _first_nonempty(*(item.get(key) for key in keys))
    return _first_nonempty(*(getattr(item, key, None) for key in keys))


def _roadmap_text(item: Any, *keys: str) -> str | None:
    value = _roadmap_value(item, *keys)
    if isinstance(value, Mapping):
        value = _first_nonempty(value.get("text"), value.get("label"), value.get("value"))
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _roadmap_adapter(role: str, surface: str, data: Any, context: Any, slide: Any, slide_id: str | None = None) -> NativeSlotPayload:
    """Bind verified/user-provided roadmap groups to the five-column template.

    The template is intentionally fixed at five columns. Three and four phase
    plans clear unused columns; six or more phases require a Detail-only
    continuation and therefore fail closed for this single-slide renderer.
    """

    payload = _base_payload(role, surface, data, context, slide, slide_id)
    if payload.failure_reason:
        return payload

    roadmap = _first_nonempty(
        _get(context, "verified_roadmap"),
        _get(data, "verified_roadmap"),
        _get(context, "roadmap"),
        _get(data, "roadmap"),
    )
    phases = _first_nonempty(_get(roadmap, "phases"), _get(roadmap, "steps"))
    milestones = _first_nonempty(_get(roadmap, "milestones"), _get(roadmap, "milestone_points"))
    success_factors = _first_nonempty(_get(roadmap, "success_factors"), _get(roadmap, "successFactors"))
    objective = _roadmap_text(roadmap, "objective", "objective_message", "goal", "message")
    records = _evidence_records(data, context, "roadmap", "implementation", "schedule", "phase", "milestone", "success")
    allowed_records = [record for record in records if _roadmap_provenance_allowed(record)]
    _record_diagnostics(payload, "roadmap", allowed_records)

    if not isinstance(phases, (list, tuple)) or not phases:
        return _blocked(payload, FailureReason.EVIDENCE_REQUIRED, "roadmap phases require explicit current data")
    phase_count = len(phases)
    if phase_count < 3:
        return _blocked(payload, FailureReason.EVIDENCE_REQUIRED, "roadmap requires at least three explicit phases")
    if phase_count > 5:
        payload.diagnostics.append(
            {
                "status": "CONTINUATION_REQUIRED",
                "phase_count": phase_count,
                "continuation_policy": "Detail-only continuation; do not squeeze six or more phases into five columns",
            }
        )
        return _blocked(payload, FailureReason.TEXT_OVERFLOW_RISK, "six or more phases require a Detail continuation slide")
    if not allowed_records:
        return _blocked(payload, FailureReason.EVIDENCE_REQUIRED, "roadmap values are generated, unknown, or lack explicit provenance")

    classification = allowed_records[0]["classification"]
    source_field = allowed_records[0].get("source_field") or "semantic_candidates"

    for index in range(1, 6):
        title_slot = f"trace:{payload.slide_id}:phase.{index}.title"
        duration_slot = f"trace:{payload.slide_id}:phase.{index}.duration"
        description_slot = f"trace:{payload.slide_id}:phase.{index}.description"
        action_slots = [f"trace:{payload.slide_id}:phase.{index}.action.{action_index}" for action_index in range(1, 5)]
        if index > phase_count:
            payload.clear_slots.extend([title_slot, duration_slot, description_slot, *action_slots])
            payload.cleared_optional_slots.extend([title_slot, duration_slot, description_slot, *action_slots])
            continue
        phase = phases[index - 1]
        phase_name = _roadmap_text(phase, "title", "name", "phase", "label")
        duration = _roadmap_text(phase, "duration", "period", "timing")
        description = _roadmap_text(phase, "description", "summary", "body")
        actions = _roadmap_value(phase, "actions", "deliverables", "checks")
        if not phase_name or not duration or not description or not isinstance(actions, (list, tuple)):
            return _blocked(payload, FailureReason.EVIDENCE_REQUIRED, f"phase {index} is missing explicit title, duration, description, or actions")
        number = _roadmap_value(phase, "number", "no", "index")
        number_text = str(number).strip() if number not in (None, "") else str(index)
        title = phase_name if phase_name.startswith(f"{number_text}.") else f"{number_text}. {phase_name}"
        payload.slots[title_slot] = title
        payload.slots[duration_slot] = duration if duration.startswith("(") else f"({duration})"
        payload.slots[description_slot] = description
        for action_index in range(1, 5):
            action = actions[action_index - 1] if action_index <= len(actions) else None
            action_text = _roadmap_text(action, "text", "label", "title", "name") if action is not None else None
            if action_text:
                payload.slots[action_slots[action_index - 1]] = action_text
            else:
                payload.clear_slots.append(action_slots[action_index - 1])
                payload.cleared_optional_slots.append(action_slots[action_index - 1])
        for slot, field_name in (
            (title_slot, "title"),
            (duration_slot, "duration"),
            (description_slot, "description"),
        ):
            payload.source_fields[slot] = f"{source_field}.phases[{index - 1}].{field_name}"
            payload.evidence_status[slot] = classification
        for action_index, slot in enumerate(action_slots, start=1):
            if slot in payload.slots:
                payload.source_fields[slot] = f"{source_field}.phases[{index - 1}].actions[{action_index - 1}]"
                payload.evidence_status[slot] = classification

    if not isinstance(milestones, (list, tuple)) or len(milestones) < phase_count:
        return _blocked(payload, FailureReason.EVIDENCE_REQUIRED, "each roadmap phase requires an explicit milestone")
    for index in range(1, 6):
        title_slot = f"trace:{payload.slide_id}:milestone.{index}.title"
        timing_slot = f"trace:{payload.slide_id}:milestone.{index}.timing"
        if index > len(milestones):
            payload.clear_slots.extend([title_slot, timing_slot])
            payload.cleared_optional_slots.extend([title_slot, timing_slot])
            continue
        milestone = milestones[index - 1]
        milestone_title = _roadmap_text(milestone, "title", "name", "label")
        milestone_timing = _roadmap_text(milestone, "timing", "week", "date", "period")
        if not milestone_title or not milestone_timing:
            return _blocked(payload, FailureReason.EVIDENCE_REQUIRED, f"milestone {index} is missing explicit title or timing")
        payload.slots[title_slot] = milestone_title
        payload.slots[timing_slot] = milestone_timing if milestone_timing.startswith("(") else f"({milestone_timing})"
        payload.source_fields[title_slot] = f"{source_field}.milestones[{index - 1}].title"
        payload.source_fields[timing_slot] = f"{source_field}.milestones[{index - 1}].timing"
        payload.evidence_status[title_slot] = classification
        payload.evidence_status[timing_slot] = classification

    for index in range(1, 5):
        title_slot = f"trace:{payload.slide_id}:success.{index}.title"
        body_slot = f"trace:{payload.slide_id}:success.{index}.body"
        item = success_factors[index - 1] if isinstance(success_factors, (list, tuple)) and index <= len(success_factors) else None
        title = _roadmap_text(item, "title", "name", "label") if item is not None else None
        body = _roadmap_text(item, "body", "description", "text", "summary") if item is not None else None
        if title and body:
            payload.slots[title_slot] = title
            payload.slots[body_slot] = body
            payload.source_fields[title_slot] = f"{source_field}.success_factors[{index - 1}].title"
            payload.source_fields[body_slot] = f"{source_field}.success_factors[{index - 1}].body"
            payload.evidence_status[title_slot] = classification
            payload.evidence_status[body_slot] = classification
        else:
            payload.clear_slots.extend([title_slot, body_slot])
            payload.cleared_optional_slots.extend([title_slot, body_slot])

    objective_slot = f"trace:{payload.slide_id}:objective.message"
    if objective:
        payload.slots[objective_slot] = objective
        payload.source_fields[objective_slot] = f"{source_field}.objective"
        payload.evidence_status[objective_slot] = classification
    else:
        payload.clear_slots.append(objective_slot)
        payload.cleared_optional_slots.append(objective_slot)

    # The source date is a trace-only sample unless current data explicitly binds it.
    payload.clear_slots.append(f"trace:{payload.slide_id}:header.date")
    payload.cleared_optional_slots.append(f"trace:{payload.slide_id}:header.date")
    if payload.unresolved_required_slots:
        return _blocked(payload, FailureReason.UNBOUND_REQUIRED_CONTENT, "required title is unbound", unresolved=payload.unresolved_required_slots)
    payload.source_fields["roadmap.phases"] = source_field
    payload.evidence_status["roadmap.phases"] = classification
    # Any canonical timing/label that is not bound by the explicit phase or
    # milestone slots is cleared fail-closed rather than carried into runtime.
    payload.clear_matching_text.extend(SAMPLE_STRINGS["ROADMAP"])
    return payload


def _case_study_adapter(role: str, surface: str, data: Any, context: Any, slide: Any, slide_id: str | None = None) -> NativeSlotPayload:
    payload = _base_payload(role, surface, data, context, slide, slide_id)
    case = _first_nonempty(_get(context, "case_studies"), _get(data, "case_studies"))
    if role == "CASE_STUDY":
        image_records = _allowed_evidence_records(data, context, "case_study", "case", "image", "photo", "evidence")
        permitted = [
            record
            for record in image_records
            if str(record.get("permission_status") or record.get("safe_to_use") or "").lower()
            in {"approved", "permitted", "true", "yes"}
        ]
        if case and permitted and permitted[0].get("source_reference"):
            payload.source_fields["case_study.image"] = str(permitted[0]["source_reference"])
            payload.evidence_status["case_study.image"] = permitted[0]["classification"]
            _record_diagnostics(payload, "case_study.image", permitted)
            return payload
        payload.source_fields["case_study.image"] = "unbound"
        _record_diagnostics(payload, "case_study.image", image_records)
        return _blocked(payload, FailureReason.EVIDENCE_IMAGE_REQUIRED, "D20 requires a verified case image; Canonical photo is never bound")
    return _blocked(payload, FailureReason.EVIDENCE_REQUIRED, "case-study evidence is unavailable")


def _role_adapter_key(role: str, surface: str) -> tuple[str, str]:
    return surface, role


def _canonical_runtime_role(role: str, surface: str) -> str:
    # Keep the surface argument in the signature for callers that already use
    # it; role identity normalization itself is centralized in the registry.
    return canonical_runtime_role(role) or role


def _build_role_adapters() -> dict[tuple[str, str], Callable[..., NativeSlotPayload]]:
    adapters: dict[tuple[str, str], Callable[..., NativeSlotPayload]] = {
        key: (lambda role, surface, data, context, slide, slide_id=None, _fn=_generic_adapter: _fn(role, surface, data, context, slide, slide_id))
        for key in sorted(RUNTIME_ROLES)
    }
    for key in sorted(RUNTIME_ROLES):
        surface, role = key
        if role in {"ESTIMATE"}:
            adapters[key] = lambda role, surface, data, context, slide, slide_id=None: _estimate_adapter(role, surface, data, context, slide, slide_id)
        elif role in {"EXECUTIVE_SUMMARY", "DECISION_AND_EXPECTED_EFFECTS"}:
            adapters[key] = lambda role, surface, data, context, slide, slide_id=None: _semantic_trace_adapter(role, surface, data, context, slide, slide_id)
        elif role in _SEMANTIC_PAGE_BINDINGS:
            adapters[key] = lambda role, surface, data, context, slide, slide_id=None: _semantic_page_adapter(role, surface, data, context, slide, slide_id)
        elif role == "PROPOSAL_SUMMARY":
            adapters[key] = lambda role, surface, data, context, slide, slide_id=None: _proposal_summary_adapter(role, surface, data, context, slide, slide_id)
        elif role == "IMPLEMENTATION_CONFIGURATION":
            adapters[key] = lambda role, surface, data, context, slide, slide_id=None: _implementation_configuration_adapter(role, surface, data, context, slide, slide_id)
        elif role == "KPI":
            adapters[key] = lambda role, surface, data, context, slide, slide_id=None: _kpi_adapter(role, surface, data, context, slide, slide_id)
        elif role in {"COMPETITIVE_COMPARISON", "COMPETITION"}:
            adapters[key] = lambda role, surface, data, context, slide, slide_id=None: _competition_adapter(role, surface, data, context, slide, slide_id)
        elif role == "WIN_PROBABILITY":
            adapters[key] = lambda role, surface, data, context, slide, slide_id=None: _win_probability_adapter(role, surface, data, context, slide, slide_id)
        elif role == "SCHEDULE":
            adapters[key] = lambda role, surface, data, context, slide, slide_id=None: _schedule_adapter(role, surface, data, context, slide, slide_id)
        elif role == "ROADMAP":
            adapters[key] = lambda role, surface, data, context, slide, slide_id=None: _roadmap_adapter(role, surface, data, context, slide, slide_id)
        elif role == "CASE_STUDY":
            adapters[key] = lambda role, surface, data, context, slide, slide_id=None: _case_study_adapter(role, surface, data, context, slide, slide_id)
        elif role in EVIDENCE_SENSITIVE_ROLES:
            adapters[key] = lambda role, surface, data, context, slide, slide_id=None: _evidence_adapter(role, surface, data, context, slide, slide_id)
    return adapters


ROLE_ADAPTERS = _build_role_adapters()


def adapt_role(
    role: str,
    *,
    data: Any = None,
    context: Any = None,
    slide: Any = None,
    surface: str = "summary",
    slide_id: str | None = None,
) -> NativeSlotPayload:
    """Resolve one explicit ``(surface, role)`` adapter without guessing."""

    runtime_role = _canonical_runtime_role(role, surface)
    adapter = ROLE_ADAPTERS.get(_role_adapter_key(runtime_role, surface))
    if adapter is None:
        return NativeSlotPayload(
            role=role,
            slide_id=slide_id or "",
            surface=surface,
            renderable=False,
            reason="role is absent from the isolated runtime registry",
            failure_reason=FailureReason.ROLE_NOT_REGISTERED.value,
        )
    payload = adapter(runtime_role, surface, data, context, slide, slide_id)
    payload.role = role
    return payload


def _rich_text_value(value: str | list[dict[str, Any]]) -> str:
    if isinstance(value, list):
        return "".join(str(item.get("text", "")) if isinstance(item, Mapping) else str(item) for item in value)
    return str(value)


def _apply_accent_color(run: ET.Element, color: str) -> None:
    rpr = next((node for node in run.iter() if _local_name(node.tag) == "rPr"), None)
    if rpr is None:
        rpr = ET.Element(f"{{{NS['a']}}}rPr")
        run.insert(0, rpr)
    solid = next((node for node in list(rpr) if _local_name(node.tag) == "solidFill"), None)
    if solid is None:
        solid = ET.SubElement(rpr, f"{{{NS['a']}}}solidFill")
    for child in list(solid):
        solid.remove(child)
    ET.SubElement(solid, f"{{{NS['a']}}}srgbClr", {"val": color})


def _write_shape_value(shape: ET.Element, value: str | list[dict[str, Any]]) -> bool:
    nodes = _text_nodes(shape)
    if not nodes:
        return False
    if isinstance(value, list):
        paragraph = next((node for node in shape.iter() if _local_name(node.tag) == "p"), None)
        runs = [node for node in list(paragraph or []) if _local_name(node.tag) == "r"]
        if paragraph is None or not runs:
            nodes[0].text = _rich_text_value(value)
            for node in nodes[1:]:
                node.text = ""
            return True
        template_run = deepcopy(runs[0])
        for child in list(paragraph):
            if _local_name(child.tag) == "r":
                paragraph.remove(child)
        for item in value:
            run = deepcopy(template_run)
            text_node = next((node for node in run.iter() if _local_name(node.tag) == "t"), None)
            if text_node is None:
                text_node = ET.SubElement(run, f"{{{NS['a']}}}t")
            text_node.text = str(item.get("text", ""))
            if item.get("style") == "accent_red":
                _apply_accent_color(run, "D71920")
            paragraph.append(run)
        return True
    nodes[0].text = str(value)
    for node in nodes[1:]:
        node.text = ""
    return True


def _replace_or_clear_text(root: ET.Element, replacements: Mapping[str, str], clear_matching: Iterable[str]) -> list[str]:
    changed: list[str] = []
    needles = [value for value in clear_matching if value]
    for shape in _iter_shapes(root):
        for node in _text_nodes(shape):
            old = node.text or ""
            new = old
            for source, target in replacements.items():
                new = new.replace(source, target)
            if new != old:
                node.text = new
                changed.append(_shape_name(shape))
            if any(needle in new for needle in needles):
                node.text = ""
                changed.append(_shape_name(shape))
    return sorted(set(changed))


def preflight_text_fit(
    text: str,
    *,
    max_characters: int,
    max_lines: int,
    characters_per_line: int | None = None,
    preferred_font_size: float = 12,
    minimum_font_size: float = 9,
    allow_font_shrink: bool = False,
) -> dict[str, Any]:
    """Deterministic text-fit check used before OOXML injection."""

    character_limit = max(1, int(max_characters))
    line_capacity = max(1, int(characters_per_line or max_characters))
    estimated_lines = max(1, ceil(len(text) / line_capacity))
    result = {
        "status": "FIT",
        "valid": True,
        "text_length": len(text),
        "estimated_lines": estimated_lines,
        "characters_per_line": line_capacity,
        "max_lines": max_lines,
        "preferred_font_size": preferred_font_size,
        "minimum_font_size": minimum_font_size,
        "font_size": preferred_font_size,
    }
    if estimated_lines <= max_lines and len(text) <= character_limit:
        return result
    if allow_font_shrink:
        required = max(1, ceil(len(text) / max(1, max_lines)))
        scale = min(1.0, character_limit / required)
        adjusted = max(minimum_font_size, round(preferred_font_size * scale, 2))
        if adjusted >= minimum_font_size and adjusted < preferred_font_size:
            result.update({"status": "FIT_WITH_FONT_SHRINK", "font_size": adjusted})
            return result
    result.update({"status": "TEXT_OVERFLOW_RISK", "valid": False})
    return result


def _slot_metrics(path: str | Path | None, slot: str) -> dict[str, int | float | None]:
    if path is None or not Path(path).is_file() or slot.endswith(".*"):
        return {"box_width_emu": None, "box_height_emu": None, "font_size": None}
    with ZipFile(path, "r") as package:
        for name in package.namelist():
            if not (name.startswith("ppt/slides/slide") and name.endswith(".xml")):
                continue
            root = ET.fromstring(package.read(name))
            for shape in _iter_shapes(root):
                if _shape_name(shape) != slot:
                    continue
                xfrm = next((node for node in shape.iter() if _local_name(node.tag) == "xfrm"), None)
                ext = next((node for node in list(xfrm or []) if _local_name(node.tag) == "ext"), None)
                width = int(ext.attrib.get("cx", "0")) if ext is not None else 0
                height = int(ext.attrib.get("cy", "0")) if ext is not None else 0
                font_node = next(
                    (node for node in shape.iter() if _local_name(node.tag) in {"rPr", "defRPr"} and node.attrib.get("sz")),
                    None,
                )
                font_size = float(font_node.attrib["sz"]) / 100 if font_node is not None else None
                return {"box_width_emu": width, "box_height_emu": height, "font_size": font_size}
    return {"box_width_emu": None, "box_height_emu": None, "font_size": None}


def _apply_font_size(shape: ET.Element, font_size: float) -> None:
    size_value = str(int(round(font_size * 100)))
    for node in shape.iter():
        if _local_name(node.tag) in {"rPr", "defRPr"}:
            node.set("sz", size_value)


def _text_fit_for_payload(payload: NativeSlotPayload, contract: dict[str, Any], template_path: str | Path | None = None) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    valid = True
    constraints = contract.get("slot_constraints", {})
    prefix_constraints = contract.get("slot_prefix_constraints", {})
    for slot, value in payload.slots.items():
        logical = slot.rsplit(":", 1)[-1]
        setting = constraints.get(logical)
        if setting is None:
            for prefix, candidate in prefix_constraints.items():
                if logical == prefix or logical.startswith(f"{prefix}."):
                    setting = candidate
                    break
        setting = setting or constraints.get("content.body", {})
        text = _rich_text_value(value)
        metrics = _slot_metrics(template_path, slot)
        existing_font_size = metrics.get("font_size")
        width_emu = metrics.get("box_width_emu")
        characters_per_line = None
        if width_emu and existing_font_size:
            font_emu = float(existing_font_size) * 914400 / 72
            characters_per_line = max(1, int(float(width_emu) / max(1, font_emu * 0.92)))
        max_characters = int(setting.get("max_characters", contract.get("max_character_guidance", {}).get(logical, 120)))
        result = preflight_text_fit(
            text,
            max_characters=max_characters,
            max_lines=int(setting.get("max_lines", 4)),
            characters_per_line=characters_per_line,
            preferred_font_size=float(existing_font_size or setting.get("preferred_font_size", 12)),
            minimum_font_size=float(setting.get("minimum_font_size", 9)),
            allow_font_shrink=bool(setting.get("allow_font_shrink", False)),
        )
        result.update(
            {
                "box_width_emu": width_emu,
                "box_height_emu": metrics.get("box_height_emu"),
                "existing_font_size": existing_font_size,
                "characters_per_line": characters_per_line,
            }
        )
        fields[slot] = result
        if result.get("status") == "FIT_WITH_FONT_SHRINK":
            payload.font_size_adjustments[slot] = float(result["font_size"])
        valid = valid and bool(result.get("valid"))
    row_setting = constraints.get("content.row", {})
    for table_slot, bindings in payload.table_cell_bindings.items():
        for binding in bindings:
            value = _normalized_string(binding.get("value")) or ""
            field_slot = f"{table_slot}[r{binding.get('row')}c{binding.get('col')}]"
            result = preflight_text_fit(
                value,
                max_characters=int(row_setting.get("max_characters", contract.get("max_character_guidance", {}).get("content.row", 48))),
                max_lines=int(row_setting.get("max_lines", 3)),
                preferred_font_size=float(row_setting.get("preferred_font_size", 10)),
                minimum_font_size=float(row_setting.get("minimum_font_size", 8)),
                allow_font_shrink=bool(row_setting.get("allow_font_shrink", True)),
            )
            result.update({"table_slot": table_slot, "row": binding.get("row"), "col": binding.get("col")})
            fields[field_slot] = result
            valid = valid and bool(result.get("valid"))
    return {"valid": valid, "fields": fields}


def _table_rows(shape: ET.Element) -> list[list[ET.Element]]:
    rows: list[list[ET.Element]] = []
    for row in shape.iter():
        if _local_name(row.tag) != "tr":
            continue
        cells = [cell for cell in list(row) if _local_name(cell.tag) == "tc"]
        if cells:
            rows.append(cells)
    return rows


def _write_table_cell_value(cell: ET.Element, value: Any) -> bool:
    nodes = _text_nodes(cell)
    if not nodes:
        return False
    nodes[0].text = str(value)
    for node in nodes[1:]:
        node.text = ""
    return True


def write_slot_payload(
    package_path: str | Path,
    payload: NativeSlotPayload,
    *,
    required_slots: Iterable[str] = (),
) -> dict[str, Any]:
    """Write text payloads by exact semantic shape name, preserving geometry."""

    source = Path(package_path)
    required = set(required_slots)
    injected: list[str] = []
    unresolved = list(payload.unresolved_required_slots)
    cleared = list(payload.cleared_optional_slots)
    temp = source.with_suffix(".injected.tmp.pptx")
    with ZipFile(source, "r") as package:
        names = package.namelist()
        slide_xml: dict[str, bytes] = {}
        for name in names:
            if not (name.startswith("ppt/slides/slide") and name.endswith(".xml")):
                continue
            root = ET.fromstring(package.read(name))
            shapes = {_shape_name(shape): shape for shape in _iter_shapes(root) if _shape_name(shape)}
            for slot, value in payload.slots.items():
                if slot.endswith(".*"):
                    prefix = slot[:-1]
                    matching = [shape for shape_name, shape in sorted(shapes.items()) if shape_name.startswith(prefix)]
                    values = value if isinstance(value, list) and not all(isinstance(item, Mapping) for item in value) else [value]
                    for shape, item in zip(matching, values):
                        if _write_shape_value(shape, item):
                            if slot in payload.font_size_adjustments:
                                _apply_font_size(shape, payload.font_size_adjustments[slot])
                            injected.append(_shape_name(shape))
                    continue
                shape = shapes.get(slot)
                if shape is None:
                    if slot in required:
                        unresolved.append(slot)
                    continue
                if _write_shape_value(shape, value):
                    if slot in payload.font_size_adjustments:
                        _apply_font_size(shape, payload.font_size_adjustments[slot])
                    injected.append(slot)
            for table_slot, bindings in payload.table_cell_bindings.items():
                table_shape = shapes.get(table_slot)
                if table_shape is None:
                    unresolved.append(table_slot)
                    continue
                rows = _table_rows(table_shape)
                for binding in bindings:
                    try:
                        row_index = int(binding["row"])
                        col_index = int(binding["col"])
                        cell = rows[row_index][col_index]
                    except (KeyError, IndexError, TypeError, ValueError):
                        unresolved.append(f"{table_slot}[r{binding.get('row')}c{binding.get('col')}]")
                        continue
                    if _write_table_cell_value(cell, binding.get("value", "")):
                        injected.append(f"{table_slot}[r{row_index}c{col_index}]")
            # Runtime copies may still contain legacy footer identity text in
            # the frozen visual template.  Normalize only the application
            # identity; customer/source-material text is never blanket-
            # rewritten here.
            static_brand_replacements = {
                "READY CREW Proposal": "提案クエスト",
                "READY CREW Inc.": "提案クエスト",
                "READY CREW": "提案クエスト",
                "ProposalPilot": "提案クエスト",
                "AI営業秘書": "提案クエスト",
            }
            cleared.extend(_replace_or_clear_text(root, static_brand_replacements, ()))
            cleared.extend(_replace_or_clear_text(root, payload.text_replacements, payload.clear_matching_text))
            for clear_slot in payload.clear_slots:
                prefix = clear_slot[:-1] if clear_slot.endswith(".*") else clear_slot
                for shape_name, shape in shapes.items():
                    if not (shape_name == clear_slot or (clear_slot.endswith(".*") and shape_name.startswith(prefix))):
                        continue
                    nodes = _text_nodes(shape)
                    if not nodes:
                        continue
                    nodes[0].text = ""
                    for node in nodes[1:]:
                        node.text = ""
                    cleared.append(shape_name)
            slide_xml[name] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        with ZipFile(temp, "w", compression=ZIP_DEFLATED) as output:
            for name in names:
                output.writestr(name, slide_xml.get(name, package.read(name)))
    temp.replace(source)
    return {
        "injected_slots": sorted(set(injected)),
        "unresolved_required_slots": sorted(set(unresolved)),
        "cleared_optional_slots": sorted(set(cleared)),
    }


def render_native_role_dry_run(
    role: str,
    context: Any = None,
    *,
    data: Any = None,
    slide: Any = None,
    surface: str = "summary",
    slide_id: str | None = None,
    temporary_dir: str | Path | None = None,
) -> NativeRoleRenderResult:
    """Clone, adapt, inject, and validate one role without HTTP/production dispatch."""

    runtime_role = _canonical_runtime_role(role, surface)
    spec = get_runtime_native_role_spec(runtime_role, surface=surface, slide_id=slide_id)
    if spec is None:
        return NativeRoleRenderResult(False, role, slide_id, surface, None, reason="role is not registered", failure_reason=FailureReason.ROLE_NOT_REGISTERED.value)
    resolved_slide_id = str(spec.get("slide_id"))
    payload = adapt_role(role, data=data, context=context, slide=slide, surface=surface, slide_id=resolved_slide_id)
    result = NativeRoleRenderResult(
        success=False,
        role=role,
        slide_id=resolved_slide_id,
        surface=surface,
        template=str(spec.get("runtime_asset")),
        evidence_diagnostics=payload.diagnostics,
        reason=payload.reason,
        failure_reason=payload.failure_reason,
        payload=payload,
    )
    if not payload.renderable:
        return result
    contract = _contract_for(runtime_role, surface, resolved_slide_id) or {}
    source = REPO_ROOT / str(spec.get("runtime_asset"))
    text_fit = _text_fit_for_payload(payload, contract, source)
    result.text_fit = text_fit
    if not text_fit["valid"]:
        result.reason = "payload exceeds the approved text-fit contract"
        result.failure_reason = FailureReason.TEXT_OVERFLOW_RISK.value
        return result
    target_dir = Path(temporary_dir) if temporary_dir else Path(tempfile.mkdtemp(prefix="phase3f19b-native-"))
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{resolved_slide_id}_{role.lower()}.pptx"
    required_slots = contract.get("required_slots", [])
    try:
        clone_report = clone_template_package(
            source,
            target,
            approved_slide_id=resolved_slide_id,
            required_slots=required_slots,
            preserve_existing_slots=resolved_slide_id == "ROADMAP",
        )
        write_report = write_slot_payload(target, payload, required_slots=required_slots)
        validation = validate_injected_template_package(
            target,
            source_template=source,
            approved_slide_id=resolved_slide_id,
            required_slots=required_slots,
            unresolved_required_slots=write_report["unresolved_required_slots"],
            prohibited_sample_strings=payload.prohibited_sample_strings,
            text_fit_diagnostics=text_fit,
            evidence_diagnostics=payload.diagnostics,
            expected_source_sha256=sha256_file(source),
        )
    except (OSError, ValueError, KeyError, ET.ParseError) as exc:
        result.reason = f"native dry-run failed: {exc}"
        result.failure_reason = FailureReason.TEMPLATE_CLONE_FAILED.value
        return result
    result.package_path = str(target)
    result.pptx_bytes = target.read_bytes()
    result.injected_slots = write_report["injected_slots"]
    result.cleared_optional_slots = write_report["cleared_optional_slots"]
    result.unresolved_slots = write_report["unresolved_required_slots"]
    result.validation = {"clone": clone_report, "injected": validation}
    result.success = bool(validation.get("valid"))
    if not result.success:
        result.reason = "injected native package validation failed"
        result.failure_reason = (
            FailureReason.SAMPLE_CONTENT_LEAK.value
            if validation.get("prohibited_sample_strings_found")
            else FailureReason.VALIDATION_FAILED.value
        )
    return result


def adapter_registry_summary() -> dict[str, Any]:
    return {
        "registered_runtime_roles": len(RUNTIME_ROLES),
        "adapter_count": len(ROLE_ADAPTERS),
        "keys": [f"{surface}:{role}" for surface, role in sorted(ROLE_ADAPTERS)],
        "production_dispatch_connected": True,
    }
