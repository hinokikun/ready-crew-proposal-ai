"""Registry and safety gate for Human-approved native proposal slides.

The registry is deliberately small and explicit.  A role is only eligible for
the native path when it is listed here and all runtime safety checks pass.  All
other roles continue through the existing slide renderer.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
RUNTIME_REGISTRY_PATH = REPO_ROOT / "backend" / "app" / "presentation_assets" / "native_trace" / "registry.json"


@dataclass(frozen=True)
class NativeRoleSpec:
    role: str
    renderer_id: str
    template_version: str
    source_artifact: str
    human_approved: bool
    data_contract: str
    fallback_renderer: str = "existing_pptx_renderer"
    classification: str = "B"
    human_approval_source: str = "Phase3F-14 sanitized existing asset Human PASS"
    alias_of: str | None = None
    production_use: str = "Summary/Detail"

    @property
    def source_path(self) -> Path:
        return REPO_ROOT / self.source_artifact

    @property
    def template_available(self) -> bool:
        return self.source_path.is_file()

    def as_dict(self) -> dict[str, Any]:
        return {
            "ROLE": self.role,
            "RENDERER_ID": self.renderer_id,
            "TEMPLATE_VERSION": self.template_version,
            "SOURCE_ARTIFACT": self.source_artifact,
            "VISUAL_ASSET": self.source_artifact,
            "HUMAN_APPROVED": self.human_approved,
            "DATA_CONTRACT": self.data_contract,
            "FALLBACK_RENDERER": self.fallback_renderer,
            "CLASSIFICATION": self.classification,
            "HUMAN_APPROVAL_SOURCE": self.human_approval_source,
            "ALIAS_OF": self.alias_of,
            "PRODUCTION_USE": self.production_use,
        }


NEW_NATIVE_TRACE_ROLES = frozenset(
    {
        "ESTIMATE",
        "KPI",
        "COMPETITIVE_COMPARISON",
        "WIN_PROBABILITY",
        "SCHEDULE",
        "ROADMAP",
    }
)

ROLE_PRODUCTION_USE = {
    "CLOSING": "Detail closing",
    "SUPPORT": "Detail conditional",
    "RISK": "Detail conditional",
    "COMPETITIVE_COMPARISON": "Detail conditional",
    "WIN_PROBABILITY": "Detail conditional",
    "ROADMAP": "Detail conditional",
}

# Production-facing role vocabulary has a few names that are intentionally
# more descriptive than the compact runtime registry identities.  Keep this
# normalization in one place so approval, contract, adapter, and renderer
# lookups cannot drift apart.
RUNTIME_ROLE_ALIASES = {
    "COMPETITIVE_COMPARISON": "COMPETITION",
    "SCHEDULE_GOVERNANCE": "SCHEDULE",
    "IMPLEMENTATION_SCHEDULE": "ROADMAP",
}


def canonical_runtime_role(role: str | None) -> str | None:
    return RUNTIME_ROLE_ALIASES.get(role or "", role)


def _spec(
    role: str,
    renderer_id: str,
    source_artifact: str,
    data_contract: str,
    *,
    alias_of: str | None = None,
) -> NativeRoleSpec:
    is_new_trace = role in NEW_NATIVE_TRACE_ROLES
    return NativeRoleSpec(
        role=role,
        renderer_id=renderer_id,
        template_version="phase3f-approved-v1",
        source_artifact=source_artifact,
        human_approved=True,
        data_contract=data_contract,
        classification="A" if is_new_trace else ("C" if alias_of else "B"),
        human_approval_source=(
            "Phase3F-09–13 Human-approved Native Trace"
            if is_new_trace
            else "Phase3F-14 sanitized existing asset Human PASS"
        ),
        alias_of=alias_of,
        production_use=ROLE_PRODUCTION_USE.get(role, "Summary/Detail"),
    )


APPROVED_NATIVE_REGISTRY: dict[str, NativeRoleSpec] = {
    # Human-approved sanitized legacy/native assets.
    "PROPOSAL_SUMMARY": _spec(
        "PROPOSAL_SUMMARY",
        "sanitized-p27-summary",
        "artifacts/phase3f10e_sanitized_native_assets/P27/sanitized_native.pptx",
        "role_data_contract.proposal_summary",
    ),
    "SOLUTION_CONCEPT": _spec(
        "SOLUTION_CONCEPT",
        "sanitized-p31-solution",
        "artifacts/phase3f10e_sanitized_native_assets/P31/sanitized_native.pptx",
        "role_data_contract.solution_concept",
    ),
    "COVER": _spec(
        "COVER",
        "sanitized-p29-cover",
        "artifacts/phase3f10e_sanitized_native_assets/P29/sanitized_native.pptx",
        "role_data_contract.cover",
    ),
    "CLOSING": _spec(
        "CLOSING",
        "sanitized-p29-closing",
        "artifacts/phase3f10e_sanitized_native_assets/P29/sanitized_native.pptx",
        "role_data_contract.closing",
        alias_of="COVER",
    ),
    "CURRENT_STATE": _spec(
        "CURRENT_STATE",
        "sanitized-p30-current-state",
        "artifacts/phase3f10e_sanitized_native_assets/P30/sanitized_native.pptx",
        "role_data_contract.current_state",
    ),
    "PROBLEM_ANALYSIS": _spec(
        "PROBLEM_ANALYSIS",
        "sanitized-p30-problem-analysis",
        "artifacts/phase3f10e_sanitized_native_assets/P30/sanitized_native.pptx",
        "role_data_contract.problem_analysis",
        alias_of="CURRENT_STATE",
    ),
    "SOLUTION_APPROACH": _spec(
        "SOLUTION_APPROACH",
        "sanitized-p31-solution-approach",
        "artifacts/phase3f10e_sanitized_native_assets/P31/sanitized_native.pptx",
        "role_data_contract.solution_approach",
        alias_of="SOLUTION_CONCEPT",
    ),
    "OPERATING_MODEL": _spec(
        "OPERATING_MODEL",
        "sanitized-p34-operating-model",
        "artifacts/phase3f10e_sanitized_native_assets/P34/sanitized_native.pptx",
        "role_data_contract.operating_model",
    ),
    "SYSTEM_ARCHITECTURE": _spec(
        "SYSTEM_ARCHITECTURE",
        "sanitized-p33-architecture",
        "artifacts/phase3f10e_sanitized_native_assets/P33/sanitized_native.pptx",
        "role_data_contract.system_architecture",
    ),
    "SUPPORT": _spec(
        "SUPPORT",
        "sanitized-p34-support",
        "artifacts/phase3f10e_sanitized_native_assets/P34/sanitized_native.pptx",
        "role_data_contract.support",
        alias_of="OPERATING_MODEL",
    ),
    "RISK": _spec(
        "RISK",
        "sanitized-p38-risk",
        "artifacts/phase3f10e_sanitized_native_assets/P38/sanitized_native.pptx",
        "role_data_contract.risk",
    ),
    "NEXT_ACTION": _spec(
        "NEXT_ACTION",
        "sanitized-p39-next-action",
        "artifacts/phase3f10e_sanitized_native_assets/P39/sanitized_native.pptx",
        "role_data_contract.next_action",
    ),
    # Human-approved Phase3F native traces.
    "ESTIMATE": _spec(
        "ESTIMATE",
        "native-trace-estimate-v1",
        "artifacts/phase3f08_native_trace_gap/01_estimate/native_trace.pptx",
        "native_slide_binding_01_estimate",
    ),
    "KPI": _spec(
        "KPI",
        "native-trace-kpi-v1",
        "artifacts/phase3f08_native_trace_gap/02_kpi/native_trace.pptx",
        "native_slide_binding_02_kpi",
    ),
    "COMPETITIVE_COMPARISON": _spec(
        "COMPETITIVE_COMPARISON",
        "native-trace-competitive-v1",
        "artifacts/phase3f08_native_trace_gap/03_competitive_comparison/native_trace.pptx",
        "native_slide_binding_03_competitive",
    ),
    "WIN_PROBABILITY": _spec(
        "WIN_PROBABILITY",
        "native-trace-win-probability-v1",
        "artifacts/phase3f08_native_trace_gap/04_win_probability/native_trace.pptx",
        "native_slide_binding_04_win_probability",
    ),
    "SCHEDULE": _spec(
        "SCHEDULE",
        "native-trace-schedule-governance-v1",
        "artifacts/phase3f08_native_trace_gap/05_schedule_governance/native_trace.pptx",
        "native_slide_binding_05_schedule_governance",
    ),
    "ROADMAP": _spec(
        "ROADMAP",
        "native-trace-implementation-schedule-v1",
        "artifacts/phase3f08_native_trace_gap/06_implementation_schedule/native_trace.pptx",
        "native_slide_binding_06_implementation_schedule",
    ),
}

# Stable aliases for callers that prefer registry-style naming.
NATIVE_TRACE_REGISTRY = APPROVED_NATIVE_REGISTRY
APPROVED_NATIVE_ROLES = frozenset(APPROVED_NATIVE_REGISTRY)


# Explicitly retained as existing-renderer-only roles.  Keeping this list in
# one place prevents a broad title heuristic from accidentally enabling them.
UNAPPROVED_NATIVE_ROLES = frozenset(
    {"CASE_STUDY", "ROI_OR_EFFECT", "MARKET_ANALYSIS", "TARGET_ANALYSIS"}
)

# Approved alternate assets remain isolated from the unapproved families.  The
# role resolver selects the primary sanitized asset; these are available for a
# later template-selection policy without changing the role contract.
APPROVED_NATIVE_ALTERNATES = {
    "SOLUTION_CONCEPT": "artifacts/phase3f10e_sanitized_native_assets/P28/sanitized_native.pptx",
    "COVER": "artifacts/phase3f10e_sanitized_native_assets/P28/sanitized_native.pptx",
    "OPERATING_MODEL": "artifacts/phase3f10e_sanitized_native_assets/P32/sanitized_native.pptx",
}


def _normalized(value: object) -> str:
    return re.sub(r"\s+", "", str(value or "")).lower()


def resolve_approved_native_role(slide_data: object, index: int = 0) -> str | None:
    """Resolve the existing slide model to an approved role, if any.

    This is intentionally conservative: ambiguous titles return ``None`` and
    therefore use the existing renderer.
    """

    title = _normalized(getattr(slide_data, "title", ""))
    layout = _normalized(getattr(slide_data, "layout", ""))

    # Explicitly deny the four not-yet-approved families before positive rules.
    if any(token in title or token in layout for token in ("事例", "ケース", "roi", "費用対効果", "市場", "マーケット", "ターゲット", "ユーザー分析")):
        return None

    # The quality layouts are already an explicit role signal from the
    # existing slide pipeline, so use them after the unapproved-role deny list.
    quality_layout_roles = {
        "quality_kpi": "KPI",
        "quality_comparison": "COMPETITIVE_COMPARISON",
        "quality_timeline": "SCHEDULE",
        "quality_roadmap": "ROADMAP",
    }
    if layout in quality_layout_roles:
        return quality_layout_roles[layout]

    if index == 0 or layout == "title":
        return "COVER"
    if "概算見積" in title or "見積と判断" in title or "費用概算" in title or "概算費用" in title:
        return "ESTIMATE"
    # Only the approved KPI slide titles are eligible for the KPI Native
    # template.  Detail helper slides can mention KPI in a broader sentence
    # (for example, a next-action or current-state slide) without becoming a
    # second KPI role.
    if title in {"kpi設計", "kpi設計と効果測定"}:
        return "KPI"
    if "競合比較" in title or "差別化ポイント" in title:
        return "COMPETITIVE_COMPARISON"
    if "受注確度" in title or "受注確率" in title:
        return "WIN_PROBABILITY"
    if "導入ステップ" in title or "ロードマップ" in title:
        return "ROADMAP"
    if "スケジュール" in title or "推進体制" in title:
        return "SCHEDULE"
    if "提案サマリー" in title or layout in {"summary", "proposal_summary"}:
        return "PROPOSAL_SUMMARY"
    if "提案コンセプト" in title or "solution_concept" in layout:
        return "SOLUTION_CONCEPT"
    if title == "現状理解":
        return "CURRENT_STATE"
    # Keep related-but-distinct Detail slides on the existing renderer.  The
    # Human-approved Problem Analysis Native asset is reserved for the
    # explicit primary problem slide.
    if "主要課題" in title or title in {"課題分析", "問題分析"}:
        return "PROBLEM_ANALYSIS"
    if "web戦略" in title or "導入戦略" in title or "solution_approach" in layout:
        return "SOLUTION_APPROACH"
    if "サイトマップ" in title or "システム構成" in title or "アーキテクチャ" in title:
        return "SYSTEM_ARCHITECTURE"
    if "リスク" in title or "懸念" in title:
        return "RISK"
    if "サポート" in title:
        return "SUPPORT"
    if title in {"運用体制", "運用モデル", "オペレーティングモデル"}:
        return "OPERATING_MODEL"
    if title in {"次のアクション", "今後の進め方", "nextaction"}:
        return "NEXT_ACTION"
    if "クロージング" in title or "まとめ" in title:
        return "CLOSING"
    return None


def get_native_role_spec(role: str | None) -> NativeRoleSpec | None:
    return APPROVED_NATIVE_REGISTRY.get(role or "")


def native_role_gate(
    role: str | None,
    *,
    template_available: bool | None = None,
    data_contract_valid: bool = True,
    text_fit_valid: bool = True,
    renderer_available: bool = True,
) -> tuple[bool, dict[str, bool]]:
    """Return eligibility and the individual safety-gate checks."""

    spec = get_native_role_spec(role)
    checks = {
        "HUMAN_APPROVED": bool(spec and spec.human_approved),
        "TEMPLATE_AVAILABLE": bool(spec and (spec.template_available if template_available is None else template_available)),
        "DATA_CONTRACT_VALID": bool(data_contract_valid),
        "TEXT_FIT_VALID": bool(text_fit_valid),
        "RENDERER_AVAILABLE": bool(renderer_available),
    }
    return all(checks.values()), checks


def is_native_role_eligible(role: str | None, **kwargs: bool) -> bool:
    return native_role_gate(role, **kwargs)[0]


def load_runtime_native_registry() -> dict[str, Any]:
    """Load the Phase3F-19A runtime registry without activating dispatch.

    The existing ``APPROVED_NATIVE_REGISTRY`` above remains the legacy
    feature-flag registry used by the pre-existing dispatcher.  This separate
    loader makes the new runtime asset set available to foundation validation
    and the future content-adapter phase while keeping this phase fail-closed.
    """

    if not RUNTIME_REGISTRY_PATH.is_file():
        return {"version": "phase3f19a-runtime-v1", "roles": [], "errors": ["runtime_registry_missing"]}
    with RUNTIME_REGISTRY_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_runtime_native_role_specs(
    role: str | None,
    *,
    surface: str | None = None,
    slide_id: str | None = None,
) -> list[dict[str, Any]]:
    runtime_role = canonical_runtime_role(role)
    return [
        spec
        for spec in load_runtime_native_registry().get("roles", [])
        if spec.get("role") == runtime_role
        and (surface is None or spec.get("surface") == surface)
        and (slide_id is None or spec.get("slide_id") == slide_id)
    ]


def get_runtime_native_role_spec(
    role: str | None,
    *,
    surface: str | None = None,
    slide_id: str | None = None,
) -> dict[str, Any] | None:
    specs = get_runtime_native_role_specs(role, surface=surface, slide_id=slide_id)
    return specs[0] if specs else None


def runtime_native_role_gate(
    role: str | None,
    *,
    surface: str | None = None,
    slide_id: str | None = None,
    template_available: bool | None = None,
    data_contract_valid: bool = True,
    text_fit_valid: bool = True,
    renderer_available: bool = True,
) -> tuple[bool, dict[str, bool]]:
    """Evaluate the isolated runtime registry safety gate only."""

    runtime_role = canonical_runtime_role(role)
    spec = get_runtime_native_role_spec(runtime_role, surface=surface, slide_id=slide_id)
    if template_available is None:
        template_available = bool(spec and (REPO_ROOT / str(spec.get("runtime_asset", ""))).is_file())
    checks = {
        "HUMAN_APPROVED": bool(spec and spec.get("human_approved") is True),
        "TEMPLATE_AVAILABLE": bool(template_available),
        "DATA_CONTRACT_VALID": bool(data_contract_valid),
        "TEXT_FIT_VALID": bool(text_fit_valid),
        "RENDERER_AVAILABLE": bool(renderer_available),
    }
    return all(checks.values()), checks
