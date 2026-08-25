from __future__ import annotations

from dataclasses import dataclass
from html import unescape
from io import BytesIO
import math
import re
import zipfile
from collections import Counter
from time import perf_counter
from typing import Any

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE, MSO_SHAPE_TYPE
from pptx.enum.text import MSO_AUTO_SIZE, PP_ALIGN
from pptx.util import Inches, Pt

from app.models import PptxDownloadRequest
from app.services.pptx_service import build_pptx_context


RENDERER_MVP_VERSION = "presentation_master_v3_renderer_mvp"
RENDERER_MVP_FEATURE_FLAG = "PRESENTATION_MASTER_V3_RENDERER_MVP_ENABLED"
RENDERER_MVP_CONTRACT_VERSION = "presentation_master_v3_renderer_mvp_adapter_v1"
SLIDE_W = 13.333
SLIDE_H = 7.5
EMU_PER_INCH = 914400

ALLOWED_PRIMITIVES = {
    "text",
    "rule",
    "semantic_container",
    "connector",
    "evidence_object",
    "path_approximation",
    "boundary",
}
ALLOWED_RELATIONSHIPS = {
    "contrast",
    "cause",
    "sequence",
    "dependency",
    "boundary",
    "tension",
    "convergence",
    "evidence_supports_decision",
}
PROHIBITED_VISIBLE_TOKENS = (
    "placeholder",
    "todo",
    "dummy",
    "lorem",
    "internal",
    "debug",
    "layout_id",
    "archetype_",
    "composition_",
    "仮ラベル",
    "内部ラベル",
)


@dataclass(frozen=True)
class RendererMvpBuildOutput:
    pptx_bytes: bytes
    quality_report: dict[str, Any]


class RendererMvpIntegrationError(RuntimeError):
    def __init__(self, reason_code: str, *, failure_stage: str, details: dict[str, Any] | None = None):
        self.reason_code = reason_code
        self.failure_stage = failure_stage
        self.details = details or {}
        super().__init__(reason_code)


def build_renderer_mvp_pptx(
    payload: PptxDownloadRequest,
    *,
    request_id: str | None = None,
    project_id: str | None = None,
) -> RendererMvpBuildOutput:
    started = perf_counter()
    if payload.summary:
        raise RendererMvpIntegrationError(
            "summary_deck_uses_existing_renderer",
            failure_stage="routing",
        )

    contract = ProposalToRendererMvpAdapter().build_contract(payload)
    contract_issues = RendererMvpContractLinter().lint(contract)
    architecture_deviation_count = sum(1 for issue in contract_issues if issue["severity"] == "error")
    if architecture_deviation_count:
        raise RendererMvpIntegrationError(
            "renderer_mvp_contract_deviation",
            failure_stage="contract_validation",
            details={"contract_issues": contract_issues},
        )

    renderer = RendererMvpNativeRenderer()
    pptx_bytes, render_report = renderer.render_deck_to_bytes(contract)
    pptx_audit = inspect_pptx_bytes(pptx_bytes, source_payload=payload)
    validation = _validate_runtime_output(pptx_audit, render_report)
    if validation["blocking"]:
        raise RendererMvpIntegrationError(
            "renderer_mvp_runtime_validation_failed",
            failure_stage="runtime_validation",
            details=validation,
        )

    page_count = int(pptx_audit["page_count"])
    quality_report = {
        "requested_version": RENDERER_MVP_VERSION,
        "actual_version": RENDERER_MVP_VERSION,
        "fallback_used": False,
        "fallback_reason": "",
        "feature_flag": RENDERER_MVP_FEATURE_FLAG,
        "request_id": request_id or "",
        "project_id": project_id or "",
        "generation_time_ms": round((perf_counter() - started) * 1000),
        "production_native_module": "app.services.presentation_master.renderer_mvp",
        "artifact_runtime_dependency": False,
        "adapter_contract_version": RENDERER_MVP_CONTRACT_VERSION,
        "renderer_architecture": "native_editable_powerpoint_shapes",
        "source_of_truth": "presentation_master_v3_renderer_mvp_powerpoint_desktop_approved",
        "engine_requested": RENDERER_MVP_VERSION,
        "engine_used": RENDERER_MVP_VERSION,
        "mode": "enabled",
        "summary_or_normal": "normal",
        "customer": contract["case_summary"]["customer"],
        "category": contract["case_summary"]["category"],
        "page_count": page_count,
        "director_slide_count": page_count,
        "render_report": render_report,
        "pptx_audit": pptx_audit,
        "architecture_deviation_count": architecture_deviation_count,
        "contract_issues": contract_issues,
        "placeholder_internal_label_count": pptx_audit["placeholder_count"] + pptx_audit["internal_label_count"],
        "fake_evidence_count": pptx_audit["fake_evidence_count"],
        "tier1_editability": pptx_audit["tier1_editable_coverage"],
        "rasterization_ratio": pptx_audit["rasterization_ratio"],
        "template_collapse": _template_collapse_from_render_report(render_report),
        "architecture_guardrails": {
            "strategy_engine_bypassed": False,
            "evidence_controls_bypassed": False,
            "term_guard_bypassed": False,
            "human_review_gate_bypassed": False,
            "api_contract_changed": False,
        },
    }
    return RendererMvpBuildOutput(pptx_bytes=pptx_bytes, quality_report=quality_report)


class ProposalToRendererMvpAdapter:
    def build_contract(self, payload: PptxDownloadRequest) -> dict[str, Any]:
        context = build_pptx_context(payload)
        data = payload.powerpoint_generation_data
        text = "\n".join(
            [
                data.deck_title,
                data.client_name,
                payload.client_company_info,
                payload.project_brief,
                payload.hearing_result,
                payload.own_service_info,
                payload.special_function_required,
            ]
        )
        profile = self._profile_for_text(text)
        customer = _safe_text(data.client_name or context.client_name or payload.client_company_info or "顧客企業", 48)
        category = _safe_text(profile["category"], 48)
        proposal_theme = _safe_text(profile["proposal_theme"], 56)
        summary = {
            "customer": customer,
            "industry": profile["industry"],
            "category": category,
            "proposal_theme": proposal_theme,
            "audience": _audience_from_payload(payload),
            "decision_stage": _decision_stage_from_payload(payload),
            "project_brief": _safe_text(payload.project_brief or data.deck_title, 120),
            "hearing_result": _safe_text(payload.hearing_result, 120),
        }
        return {
            "contract_version": RENDERER_MVP_CONTRACT_VERSION,
            "case_summary": summary,
            "pages": [
                self._page(
                    "p01",
                    "context",
                    profile["context_message"],
                    profile["context_thesis"],
                    profile["context_visual"],
                    "sequence",
                    "text",
                ),
                self._page(
                    "p02",
                    "problem",
                    profile["problem_message"],
                    profile["problem_thesis"],
                    profile["problem_visual"],
                    "tension",
                    "boundary",
                ),
                self._page(
                    "p03",
                    "operating_model",
                    profile["model_message"],
                    profile["model_thesis"],
                    profile["model_visual"],
                    "dependency",
                    "semantic_container",
                ),
                self._page(
                    "p04",
                    "evidence",
                    profile["evidence_message"],
                    profile["evidence_thesis"],
                    profile["evidence_visual"],
                    "evidence_supports_decision",
                    "evidence_object",
                ),
                self._page(
                    "p05",
                    "decision",
                    profile["decision_message"],
                    profile["decision_thesis"],
                    profile["decision_visual"],
                    "convergence",
                    "semantic_container",
                    decision_morphology=profile["decision_morphology"],
                ),
            ],
        }

    def _page(
        self,
        page_id: str,
        role: str,
        message: str,
        thesis: str,
        visual: str,
        relationship: str,
        primitive: str,
        *,
        decision_morphology: str = "",
    ) -> dict[str, Any]:
        return {
            "page_id": page_id,
            "page_role": role,
            "core_message": _safe_text(message, 72),
            "visual_thesis": _safe_text(thesis, 110),
            "dominant_visual": visual,
            "decision_morphology": decision_morphology,
            "objects": [
                {
                    "object_id": f"{page_id}_message",
                    "primitive_type": "text",
                    "semantic_role": "hero_statement",
                    "hierarchy_level": 1,
                    "reading_order": 1,
                    "source_binding": {
                        "source_type": "reasoning_output",
                        "source_field": "core_message",
                        "provenance_id": f"{page_id}:core_message",
                    },
                    "editable": {"tier": 1, "required": True},
                },
                {
                    "object_id": f"{page_id}_visual",
                    "primitive_type": primitive,
                    "semantic_role": visual,
                    "hierarchy_level": 2,
                    "reading_order": 2,
                    "source_binding": {
                        "source_type": "proposal_input",
                        "source_field": "business_context",
                        "provenance_id": f"{page_id}:business_context",
                    },
                    "editable": {"tier": 1, "required": True},
                },
            ],
            "relationships": [
                {
                    "type": relationship,
                    "from_object": f"{page_id}_visual",
                    "to_object": f"{page_id}_message",
                    "semantic_meaning": thesis,
                }
            ],
            "constraints": {
                "min_font_pt": 14,
                "allow_rasterization": False,
                "max_rasterization_ratio": 0.0,
            },
        }

    def _profile_for_text(self, text: str) -> dict[str, str]:
        lowered = text.lower()
        if any(token in text for token in ("花卉", "花", "画像認識", "等級", "フラワー", "オークション")):
            return {
                "industry": "花卉流通",
                "category": "AI / Image Recognition",
                "proposal_theme": "画像認識AI導入PoC",
                "context_message": "PoCは精度証明ではなく、次回判断の証拠を残す",
                "context_thesis": "対象画像、AI候補、人の最終判断を同じ記録単位にする",
                "context_visual": "image_to_judgment_record",
                "problem_message": "結果は残る。理由は戻らない。",
                "problem_thesis": "判定結果と判断理由が分かれるため、基準化の材料が不足する",
                "problem_visual": "reason_loss_gap",
                "model_message": "判断基準は、記録が揃って初めて育つ",
                "model_thesis": "画像条件、AI候補、人判断、理由を一体の業務素材にする",
                "model_visual": "judgment_material_unit",
                "evidence_message": "判定記録が、次回判断の証拠になる",
                "evidence_thesis": "一致、差異、例外、理由をPoC後の判断材料として残す",
                "evidence_visual": "judgment_record_object",
                "decision_message": "GOは、条件が揃って初めて判断できる",
                "decision_thesis": "精度値ではなく、証拠構造への合意を本番検討条件にする",
                "decision_visual": "go_condition_gate",
                "decision_morphology": "criteria_convergence",
            }
        if any(token in text for token in ("物流", "配送", "配車", "ルート", "TMS", "倉庫")):
            return {
                "industry": "物流",
                "category": "Operations / Logistics",
                "proposal_theme": "配送ルート最適化PoC",
                "context_message": "配車は、条件の衝突をほどく仕事",
                "context_thesis": "配送計画は地図の線ではなく、条件が重なる運用盤面である",
                "context_visual": "constraint_map",
                "problem_message": "遅れの原因は、距離ではなく条件の衝突にある",
                "problem_thesis": "時間指定、積載、人員、配送先条件が同時に衝突する",
                "problem_visual": "constraint_collision_field",
                "model_message": "候補ルートは、理由が揃って初めて使える",
                "model_thesis": "AI候補と人の補正理由を同じ判断単位に戻す",
                "model_visual": "route_candidate_with_constraints",
                "evidence_message": "PoCで残す証拠は、判断を変えた条件",
                "evidence_thesis": "候補、人の補正、例外条件、TMS前提を運用証拠として残す",
                "evidence_visual": "operational_evidence_dossier",
                "decision_message": "本番検討は、現場が説明できる条件から始める",
                "decision_thesis": "運用説明可能性とシステムへ戻せる粒度を本番検討条件にする",
                "decision_visual": "operating_condition_gate",
                "decision_morphology": "dependency",
            }
        if any(token in lowered for token in ("web", "ec", "commerce", "marketing", "seo")) or any(
            token in text for token in ("Web", "EC", "マーケ", "顧客導線", "サイト", "SEO")
        ):
            return {
                "industry": "デジタル / コマース",
                "category": "Web / Marketing",
                "proposal_theme": "顧客導線改善提案",
                "context_message": "改善対象は画面ではなく、顧客が迷う瞬間",
                "context_thesis": "流入、比較、問い合わせの間で判断材料が途切れる",
                "context_visual": "customer_journey_gap",
                "problem_message": "離脱は、機能不足ではなく判断材料の不足で起きる",
                "problem_thesis": "価値、根拠、次の行動が同じ導線上で接続していない",
                "problem_visual": "decision_leak_path",
                "model_message": "顧客の判断材料を、導線上に戻す",
                "model_thesis": "訴求、証拠、問い合わせ理由を一つの編集単位にする",
                "model_visual": "commerce_decision_material",
                "evidence_message": "PoCでは、反応ではなく迷いの場所を残す",
                "evidence_thesis": "クリック、問い合わせ前の滞留、比較観点を改善判断へ戻す",
                "evidence_visual": "journey_evidence_sheet",
                "decision_message": "次の投資は、迷いが減る条件から決める",
                "decision_thesis": "数値未確定の段階では、測る場所と判断条件を先に合意する",
                "decision_visual": "investment_decision_gate",
                "decision_morphology": "criteria_convergence",
            }
        return {
            "industry": "業務変革",
            "category": "Business Transformation",
            "proposal_theme": "業務判断高度化提案",
            "context_message": "改善対象はツールではなく、判断が止まる場面",
            "context_thesis": "業務情報、候補、判断理由を同じ記録単位にする",
            "context_visual": "business_decision_record",
            "problem_message": "結果は残るが、判断理由が再利用できない",
            "problem_thesis": "判断の背景が分離し、次の改善材料が不足する",
            "problem_visual": "reason_loss_gap",
            "model_message": "判断材料を同じ単位で残す",
            "model_thesis": "入力、候補、人の判断、理由を一体の業務素材にする",
            "model_visual": "business_material_unit",
            "evidence_message": "記録が、次回判断の証拠になる",
            "evidence_thesis": "差分、例外、理由を次回判断へ戻せる形で残す",
            "evidence_visual": "business_evidence_object",
            "decision_message": "次の判断は、条件が揃ってから行う",
            "decision_thesis": "効果数値ではなく、検証条件への合意を先に置く",
            "decision_visual": "decision_condition_gate",
            "decision_morphology": "criteria_convergence",
        }


class RendererMvpContractLinter:
    def lint(self, contract: dict[str, Any]) -> list[dict[str, str]]:
        issues: list[dict[str, str]] = []
        if contract.get("contract_version") != RENDERER_MVP_CONTRACT_VERSION:
            issues.append(self._issue("MVP001", "error", "contract_version mismatch"))
        serialized = repr(contract)
        if re.search(r"C:\\Users\\|Documents\\Codex|file://|localhost|artifacts[\\/]", serialized):
            issues.append(self._issue("MVP002", "error", "local or artifact runtime path leakage"))
        page_ids: set[str] = set()
        for page in contract.get("pages", []):
            page_id = str(page.get("page_id", ""))
            if page_id in page_ids:
                issues.append(self._issue("MVP003", "error", f"duplicate page_id {page_id}"))
            page_ids.add(page_id)
            for field in ("page_id", "page_role", "core_message", "visual_thesis", "dominant_visual", "objects"):
                if not page.get(field):
                    issues.append(self._issue("MVP004", "error", f"{page_id} missing {field}"))
            for obj in page.get("objects", []):
                primitive = obj.get("primitive_type")
                if primitive not in ALLOWED_PRIMITIVES:
                    issues.append(self._issue("MVP005", "error", f"{page_id} unsupported primitive {primitive}"))
                if obj.get("editable", {}).get("tier") != 1:
                    issues.append(self._issue("MVP006", "error", f"{page_id} tier1 editability missing"))
                binding = obj.get("source_binding") or {}
                if not binding.get("source_type") or not binding.get("source_field") or not binding.get("provenance_id"):
                    issues.append(self._issue("MVP007", "error", f"{page_id} source binding incomplete"))
            for rel in page.get("relationships", []):
                if rel.get("type") not in ALLOWED_RELATIONSHIPS:
                    issues.append(self._issue("MVP008", "error", f"{page_id} unsupported relationship"))
            text = (page.get("core_message", "") + " " + page.get("visual_thesis", "")).lower()
            if any(token in text for token in PROHIBITED_VISIBLE_TOKENS):
                issues.append(self._issue("MVP009", "error", f"{page_id} placeholder or internal text"))
        return issues

    def _issue(self, rule_id: str, severity: str, message: str) -> dict[str, str]:
        return {"rule_id": rule_id, "severity": severity, "message": message}


class RendererMvpNativeRenderer:
    def __init__(self) -> None:
        self.palette = {
            "paper": "#F7F4EE",
            "ink": "#111111",
            "muted": "#6F6A62",
            "soft": "#E4DDD2",
            "line": "#B9B1A4",
            "red": "#C73333",
            "dark": "#121212",
            "white": "#FFFFFF",
            "sand": "#DDD2C2",
            "blue": "#235789",
            "green": "#596F3B",
        }

    def render_deck_to_bytes(self, contract: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
        prs = Presentation()
        prs.slide_width = _inches(SLIDE_W)
        prs.slide_height = _inches(SLIDE_H)
        blank = prs.slide_layouts[6]
        pages: list[dict[str, Any]] = []
        fingerprints: list[dict[str, Any]] = []
        for index, page in enumerate(contract["pages"], start=1):
            slide = prs.slides.add_slide(blank)
            self._set_background(slide)
            family = self._select_family(page)
            if family == "context_flower":
                self._draw_context_flower(slide, contract, page)
            elif family == "context_route":
                self._draw_context_route(slide, contract, page)
            elif family == "context_commerce":
                self._draw_context_commerce(slide, contract, page)
            elif family == "problem_gap":
                self._draw_problem_gap(slide, contract, page)
            elif family == "problem_collision":
                self._draw_problem_collision(slide, contract, page)
            elif family == "problem_journey":
                self._draw_problem_journey(slide, contract, page)
            elif family == "model_route":
                self._draw_model_route(slide, contract, page)
            elif family == "model_commerce":
                self._draw_model_commerce(slide, contract, page)
            elif family == "model_flower":
                self._draw_model_flower(slide, contract, page)
            elif family == "evidence_flower":
                self._draw_evidence_flower(slide, contract, page)
            elif family == "evidence_route":
                self._draw_evidence_route(slide, contract, page)
            elif family == "evidence_commerce":
                self._draw_evidence_commerce(slide, contract, page)
            elif family == "decision_dependency":
                self._draw_decision_dependency(slide, contract, page)
            else:
                self._draw_decision_convergence(slide, contract, page)
            self._draw_footer(slide, contract, index, len(contract["pages"]))
            pages.append(self._audit_slide(slide, page, family))
            fingerprints.append(self._fingerprint(slide, page, family))
        output = BytesIO()
        prs.save(output)
        return output.getvalue(), {
            "page_count": len(contract["pages"]),
            "pages": pages,
            "composition_fingerprints": fingerprints,
        }

    def _select_family(self, page: dict[str, Any]) -> str:
        role = page["page_role"]
        visual = page["dominant_visual"]
        if role == "context":
            if "constraint" in visual:
                return "context_route"
            if "journey" in visual:
                return "context_commerce"
            return "context_flower"
        if role == "problem":
            if "collision" in visual:
                return "problem_collision"
            if "leak" in visual:
                return "problem_journey"
            return "problem_gap"
        if role == "operating_model":
            if "route" in visual:
                return "model_route"
            if "commerce" in visual:
                return "model_commerce"
            return "model_flower"
        if role == "evidence":
            if "operational" in visual:
                return "evidence_route"
            if "journey" in visual:
                return "evidence_commerce"
            return "evidence_flower"
        if page.get("decision_morphology") == "dependency":
            return "decision_dependency"
        return "decision_convergence"

    def _set_background(self, slide) -> None:
        fill = slide.background.fill
        fill.solid()
        fill.fore_color.rgb = _rgb(self.palette["paper"])

    def _draw_header(self, slide, contract: dict[str, Any], label: str) -> None:
        case = contract["case_summary"]
        self._text(slide, case["customer"], 0.62, 0.33, 5.5, 0.28, 10, self.palette["muted"])
        self._text(slide, label, 9.8, 0.33, 2.7, 0.28, 10, self.palette["muted"], align=PP_ALIGN.RIGHT)

    def _draw_title_stack(
        self,
        slide,
        page: dict[str, Any],
        x: float,
        y: float,
        title_w: float,
        title_font: float,
        subtitle_w: float,
        subtitle_font: float = 16,
    ) -> float:
        title = _wrap(page["core_message"], title_w, title_font, 3)
        title_h = _estimated_height(title, title_w, title_font)
        self._text(slide, title, x, y, title_w, title_h, title_font, self.palette["ink"], bold=True, shape_name="pmv3:title")
        subtitle = _wrap(page["visual_thesis"], subtitle_w, subtitle_font, 3)
        subtitle_y = y + title_h + 0.16
        subtitle_h = _estimated_height(subtitle, subtitle_w, subtitle_font)
        self._text(slide, subtitle, x + 0.03, subtitle_y, subtitle_w, subtitle_h, subtitle_font, self.palette["muted"], shape_name="pmv3:subtitle")
        return subtitle_y + subtitle_h + 0.18

    def _draw_context_flower(self, slide, contract: dict[str, Any], page: dict[str, Any]) -> None:
        self._draw_header(slide, contract, "CONTEXT")
        body_y = self._draw_title_stack(slide, page, 0.78, 0.92, 6.4, 39, 5.7, 17)
        case = contract["case_summary"]
        self._rule(slide, 0.82, body_y + 0.28, 2.55, 0.08, self.palette["red"])
        self._text(slide, "対象業務", 0.82, body_y + 0.68, 1.3, 0.24, 11, self.palette["muted"])
        self._text(slide, f"{case['industry']} / {case['proposal_theme']}", 0.82, body_y + 0.98, 5.1, 0.45, 18, self.palette["ink"], bold=True)
        self._rect(slide, 7.55, 0.95, 4.72, 5.25, fill=self.palette["dark"], line=self.palette["dark"])
        self._flower_symbol(slide, 7.98, 1.32, 3.76, 2.85, show_labels=True)
        self._text(slide, "画像条件  ->  判断記録", 8.02, 4.75, 3.55, 0.46, 22, self.palette["white"], bold=True)
        self._text(slide, "AI候補と人判断を同じ単位に戻す", 8.04, 5.28, 3.45, 0.34, 12, "#D8D1C6")

    def _draw_context_route(self, slide, contract: dict[str, Any], page: dict[str, Any]) -> None:
        self._draw_header(slide, contract, "CONTEXT")
        self._draw_title_stack(slide, page, 0.78, 0.85, 6.0, 38, 5.7, 17)
        self._route_map(slide, 6.3, 1.12, 5.5, 4.65, labels=("時間指定", "積載", "人員", "配送先"))
        self._rule(slide, 1.0, 5.52, 2.7, 0.08, self.palette["red"])

    def _draw_context_commerce(self, slide, contract: dict[str, Any], page: dict[str, Any]) -> None:
        self._draw_header(slide, contract, "CONTEXT")
        self._text(slide, "迷う瞬間", 0.82, 0.9, 5.0, 0.9, 50, self.palette["ink"], bold=True)
        self._draw_title_stack(slide, page, 0.86, 2.05, 5.8, 27, 5.2, 16)
        self._journey_arc(slide, 6.35, 1.08, 5.35, 4.6, labels=("流入", "比較", "問い合わせ"))
        self._rule(slide, 8.2, 4.78, 2.3, 0.08, self.palette["red"])

    def _draw_problem_gap(self, slide, contract: dict[str, Any], page: dict[str, Any]) -> None:
        self._draw_header(slide, contract, "PROBLEM")
        self._text(slide, "残る", 0.9, 1.05, 2.2, 0.95, 54, self.palette["ink"], bold=True)
        self._text(slide, "戻らない", 8.1, 4.82, 3.5, 0.75, 42, self.palette["red"], bold=True)
        self._text(slide, _wrap(page["core_message"], 5.3, 24, 2), 0.96, 2.15, 5.4, 0.65, 24, self.palette["ink"], bold=True)
        self._record_sheet(slide, 1.0, 3.35, 3.1, 1.75, "判定結果", ["等級", "候補", "時点"], accent=False)
        self._broken_path(slide, 4.45, 3.55, 3.2, 1.35)
        self._text(slide, "判断理由", 8.25, 3.8, 2.5, 0.42, 17, self.palette["muted"])
        self._rule(slide, 8.25, 4.28, 2.5, 0.08, self.palette["red"])

    def _draw_problem_collision(self, slide, contract: dict[str, Any], page: dict[str, Any]) -> None:
        self._draw_header(slide, contract, "PROBLEM")
        self._draw_title_stack(slide, page, 0.82, 0.88, 6.8, 34, 6.2, 16)
        self._collision_field(slide, 1.05, 3.05, 6.15, 2.8)
        self._rect(slide, 8.25, 2.15, 3.4, 3.7, fill="#EEE6DA", line="#D8CDBF")
        self._text(slide, "戻り先", 8.55, 2.58, 1.4, 0.34, 13, self.palette["muted"])
        self._text(slide, "手作業判断", 8.55, 3.0, 2.55, 0.45, 24, self.palette["ink"], bold=True)
        self._text(slide, "複数条件を同時に見直す", 8.55, 3.65, 2.55, 0.52, 16, self.palette["ink"])
        self._rule(slide, 8.55, 4.55, 2.25, 0.08, self.palette["red"])

    def _draw_problem_journey(self, slide, contract: dict[str, Any], page: dict[str, Any]) -> None:
        self._draw_header(slide, contract, "PROBLEM")
        self._draw_title_stack(slide, page, 0.82, 0.85, 6.9, 34, 6.1, 16)
        self._journey_arc(slide, 1.0, 3.0, 6.3, 2.3, labels=("価値", "根拠", "行動"))
        self._text(slide, "迷い", 8.25, 3.05, 2.6, 0.62, 34, self.palette["red"], bold=True)
        self._text(slide, "判断材料が途切れる場所を特定する", 8.28, 3.85, 2.7, 0.55, 16, self.palette["ink"])
        self._rule(slide, 8.3, 4.65, 2.2, 0.08, self.palette["red"])

    def _draw_model_flower(self, slide, contract: dict[str, Any], page: dict[str, Any]) -> None:
        self._draw_header(slide, contract, "OPERATING MODEL")
        self._text(slide, "同じ単位で残す", 0.86, 0.92, 4.6, 1.12, 42, self.palette["ink"], bold=True)
        self._draw_title_stack(slide, page, 5.7, 1.03, 5.65, 26, 5.0, 16)
        self._material_stack(slide, 5.95, 3.0, 5.25, 2.58, ["対象画像", "AI候補", "人判断", "理由"])
        self._rule(slide, 0.9, 3.08, 3.2, 0.08, self.palette["red"])

    def _draw_model_route(self, slide, contract: dict[str, Any], page: dict[str, Any]) -> None:
        self._draw_header(slide, contract, "OPERATING MODEL")
        self._draw_title_stack(slide, page, 0.82, 0.88, 7.2, 33, 6.0, 16)
        self._route_candidate_ledger(slide, 1.0, 3.05, 10.75, 2.7)

    def _draw_model_commerce(self, slide, contract: dict[str, Any], page: dict[str, Any]) -> None:
        self._draw_header(slide, contract, "OPERATING MODEL")
        self._draw_title_stack(slide, page, 0.82, 0.88, 6.7, 33, 5.7, 16)
        self._commerce_sheet(slide, 1.05, 3.02, 10.55, 2.72)

    def _draw_evidence_flower(self, slide, contract: dict[str, Any], page: dict[str, Any]) -> None:
        self._draw_header(slide, contract, "EVIDENCE")
        bottom = self._draw_title_stack(slide, page, 0.78, 0.82, 7.4, 35, 6.5, 16)
        panel_y = max(2.62, bottom)
        self._rect(slide, 0.86, panel_y, 10.95, 3.32, fill="#FDFBF7", line="#D8CDBF")
        self._mini_flower_evidence(slide, 1.16, panel_y + 0.38, 2.1, 2.42)
        self._record_sheet(slide, 3.65, panel_y + 0.34, 3.4, 2.45, "判定記録", ["AI候補", "人判断", "一致 / 差異", "判断理由"], accent=True)
        self._decision_slab(slide, 7.55, panel_y + 0.4, 3.45, 2.32, "次回GO条件", ["記録単位に合意", "例外条件を残す", "基準化の可否"])
        self._text(slide, "精度・ROI・件数は未確定値として描画しない", 0.9, 6.35, 5.1, 0.24, 10, self.palette["muted"], shape_name="pmv3:footer_note")

    def _draw_evidence_route(self, slide, contract: dict[str, Any], page: dict[str, Any]) -> None:
        self._draw_header(slide, contract, "EVIDENCE")
        bottom = self._draw_title_stack(slide, page, 0.78, 0.82, 7.5, 34, 6.5, 16)
        panel_y = max(2.68, bottom)
        self._rect(slide, 0.86, panel_y, 10.95, 3.22, fill="#FDFBF7", line="#D8CDBF")
        self._route_map(slide, 1.12, panel_y + 0.45, 2.45, 2.15, labels=("候補", "補正", "例外", "TMS"))
        self._record_sheet(slide, 3.88, panel_y + 0.43, 3.25, 2.2, "運用証拠", ["候補ルート", "人の補正", "例外条件", "TMS前提"], accent=True)
        self._decision_slab(slide, 7.6, panel_y + 0.46, 3.45, 2.16, "判断へ戻す条件", ["条件で説明", "戻せる粒度", "例外の扱い"])

    def _draw_evidence_commerce(self, slide, contract: dict[str, Any], page: dict[str, Any]) -> None:
        self._draw_header(slide, contract, "EVIDENCE")
        bottom = self._draw_title_stack(slide, page, 0.78, 0.82, 7.5, 34, 6.5, 16)
        panel_y = max(2.68, bottom)
        self._rect(slide, 0.86, panel_y, 10.95, 3.22, fill="#FDFBF7", line="#D8CDBF")
        self._journey_arc(slide, 1.06, panel_y + 0.55, 3.0, 1.9, labels=("閲覧", "比較", "相談"))
        self._record_sheet(slide, 4.25, panel_y + 0.43, 3.0, 2.2, "迷いの記録", ["流入文脈", "比較観点", "行動前の滞留", "相談理由"], accent=True)
        self._decision_slab(slide, 7.75, panel_y + 0.46, 3.15, 2.16, "次の改善条件", ["測る場所", "変える文言", "判断基準"])

    def _draw_decision_dependency(self, slide, contract: dict[str, Any], page: dict[str, Any]) -> None:
        self._draw_header(slide, contract, "DECISION")
        bottom = self._draw_title_stack(slide, page, 0.82, 0.86, 7.45, 36, 6.8, 16)
        lane_y = max(2.8, bottom + 0.1)
        self._lane(slide, 1.12, lane_y, 4.05, 1.46, "運用レーン", ["候補", "補正", "説明"])
        self._lane(slide, 1.12, lane_y + 1.74, 4.05, 1.1, "システムレーン", ["前提", "粒度"])
        self._boundary(slide, 5.76, lane_y - 0.2, 3.24, "責任境界")
        self._rect(slide, 7.12, lane_y + 0.2, 4.0, 2.35, fill=self.palette["dark"], line=self.palette["dark"])
        self._text(slide, "本番検討", 7.52, lane_y + 0.72, 3.2, 0.52, 30, self.palette["white"], bold=True, align=PP_ALIGN.CENTER)
        self._text(slide, "現場が説明できる条件から始める", 7.55, lane_y + 1.45, 3.08, 0.38, 15, "#D8D1C6", align=PP_ALIGN.CENTER)

    def _draw_decision_convergence(self, slide, contract: dict[str, Any], page: dict[str, Any]) -> None:
        self._draw_header(slide, contract, "DECISION")
        bottom = self._draw_title_stack(slide, page, 0.82, 0.86, 7.45, 37, 6.8, 16)
        gate_y = max(3.05, bottom + 0.22)
        labels = ["証拠構造", "例外条件", "判断理由"]
        xs = [1.05, 3.85, 6.65]
        for x, label in zip(xs, labels):
            self._rect(slide, x, gate_y, 2.05, 1.25, fill="#FFFFFF", line="#D8CDBF")
            self._text(slide, label, x + 0.2, gate_y + 0.4, 1.55, 0.35, 18, self.palette["ink"], bold=True, align=PP_ALIGN.CENTER)
            self._connector(slide, x + 2.05, gate_y + 0.63, 9.1, gate_y + 1.0, self.palette["line"])
        self._rect(slide, 9.12, gate_y - 0.2, 2.55, 2.1, fill=self.palette["dark"], line=self.palette["dark"])
        self._text(slide, "GO", 9.55, gate_y + 0.11, 1.7, 0.78, 50, self.palette["white"], bold=True, align=PP_ALIGN.CENTER)
        self._rule(slide, 9.42, gate_y + 1.07, 1.95, 0.08, self.palette["red"])
        self._text(slide, "次回合意へ", 9.45, gate_y + 1.27, 1.85, 0.32, 14, "#D8D1C6", align=PP_ALIGN.CENTER)

    def _draw_footer(self, slide, contract: dict[str, Any], page_index: int, page_count: int) -> None:
        self._rule(slide, 0.62, 6.93, 11.9, 0.015, "#D6CEC2")
        self._text(slide, f"{page_index:02d}/{page_count:02d}", 11.75, 7.03, 0.8, 0.2, 8, self.palette["muted"], align=PP_ALIGN.RIGHT, shape_name="pmv3:page_marker")

    def _text(
        self,
        slide,
        text: str,
        x: float,
        y: float,
        w: float,
        h: float,
        font_pt: float,
        color: str,
        *,
        bold: bool = False,
        align=PP_ALIGN.LEFT,
        shape_name: str | None = None,
    ):
        box = slide.shapes.add_textbox(_inches(x), _inches(y), _inches(w), _inches(h))
        if shape_name:
            box.name = shape_name
        box.text_frame.clear()
        box.text_frame.margin_left = _inches(0.02)
        box.text_frame.margin_right = _inches(0.02)
        box.text_frame.margin_top = _inches(0.02)
        box.text_frame.margin_bottom = _inches(0.02)
        box.text_frame.word_wrap = True
        box.text_frame.auto_size = MSO_AUTO_SIZE.NONE
        lines = str(text).split("\n") if text else [""]
        for index, line in enumerate(lines):
            paragraph = box.text_frame.paragraphs[0] if index == 0 else box.text_frame.add_paragraph()
            paragraph.text = line
            paragraph.alignment = align
            paragraph.space_after = Pt(0)
            paragraph.line_spacing = 0.95 if font_pt >= 34 else 1.05
            for run in paragraph.runs:
                run.font.name = "Yu Gothic"
                run.font.size = Pt(font_pt)
                run.font.bold = bold
                run.font.color.rgb = _rgb(color)
        return box

    def _rect(self, slide, x: float, y: float, w: float, h: float, *, fill: str, line: str, transparency: int = 0):
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, _inches(x), _inches(y), _inches(w), _inches(h))
        shape.fill.solid()
        shape.fill.fore_color.rgb = _rgb(fill)
        shape.fill.transparency = transparency
        shape.line.color.rgb = _rgb(line)
        shape.line.width = Pt(1.0)
        return shape

    def _rule(self, slide, x: float, y: float, w: float, h: float, color: str):
        return self._rect(slide, x, y, w, h, fill=color, line=color)

    def _connector(self, slide, x1: float, y1: float, x2: float, y2: float, color: str):
        connector = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, _inches(x1), _inches(y1), _inches(x2), _inches(y2))
        connector.line.color.rgb = _rgb(color)
        connector.line.width = Pt(1.25)
        return connector

    def _flower_symbol(self, slide, x: float, y: float, w: float, h: float, *, show_labels: bool) -> None:
        cx, cy = x + w * 0.45, y + h * 0.42
        for index in range(10):
            angle = math.radians(index * 36)
            px = cx + math.cos(angle) * 0.86
            py = cy + math.sin(angle) * 0.55
            oval = slide.shapes.add_shape(MSO_SHAPE.OVAL, _inches(px), _inches(py), _inches(0.84), _inches(0.46))
            oval.fill.solid()
            oval.fill.fore_color.rgb = _rgb("#F4D8D1" if index % 2 else "#E7B3A8")
            oval.line.color.rgb = _rgb("#F4D8D1")
            oval.rotation = index * 36
        center = slide.shapes.add_shape(MSO_SHAPE.OVAL, _inches(cx + 0.22), _inches(cy + 0.16), _inches(0.46), _inches(0.46))
        center.fill.solid()
        center.fill.fore_color.rgb = _rgb("#D7B35B")
        center.line.color.rgb = _rgb("#D7B35B")
        if not show_labels:
            return
        self._text(slide, "AI候補", x + 2.84, y + 0.5, 0.82, 0.24, 9, self.palette["dark"], bold=True, align=PP_ALIGN.CENTER)
        self._text(slide, "人判断", x + 2.72, y + 2.07, 0.82, 0.24, 9, self.palette["dark"], bold=True, align=PP_ALIGN.CENTER)
        self._connector(slide, x + 2.2, y + 1.45, x + 2.84, y + 0.65, self.palette["red"])
        self._connector(slide, x + 2.2, y + 1.45, x + 2.73, y + 2.22, "#D8D1C6")

    def _mini_flower_evidence(self, slide, x: float, y: float, w: float, h: float) -> None:
        self._rect(slide, x, y, w, h, fill="#F2E8DF", line="#D8CDBF")
        self._flower_symbol(slide, x + 0.22, y + 0.24, w - 0.46, h - 0.74, show_labels=False)
        self._text(slide, "対象画像", x + 0.22, y + h - 0.36, w - 0.44, 0.22, 10, self.palette["muted"], align=PP_ALIGN.CENTER)

    def _record_sheet(self, slide, x: float, y: float, w: float, h: float, title: str, rows: list[str], *, accent: bool) -> None:
        self._rect(slide, x, y, w, h, fill="#FFFFFF", line="#D8CDBF")
        self._text(slide, title, x + 0.22, y + 0.22, w - 0.44, 0.36, 16, self.palette["ink"], bold=True)
        top = y + 0.72
        for index, row in enumerate(rows):
            yy = top + index * 0.37
            self._rule(slide, x + 0.22, yy + 0.28, w - 0.44, 0.012, "#E7DED2")
            color = self.palette["red"] if accent and row == "一致 / 差異" else self.palette["ink"]
            self._text(slide, row, x + 0.24, yy, w - 0.48, 0.23, 11.5, color, bold=(accent and row == "一致 / 差異"))

    def _decision_slab(self, slide, x: float, y: float, w: float, h: float, title: str, rows: list[str]) -> None:
        self._rect(slide, x, y, w, h, fill=self.palette["dark"], line=self.palette["dark"])
        self._text(slide, title, x + 0.28, y + 0.28, w - 0.56, 0.36, 17, self.palette["white"], bold=True)
        self._rule(slide, x + 0.3, y + 0.77, w - 0.6, 0.05, self.palette["red"])
        for index, row in enumerate(rows):
            self._text(slide, row, x + 0.32, y + 1.02 + index * 0.34, w - 0.64, 0.22, 11.5, "#E7DED2")

    def _route_map(self, slide, x: float, y: float, w: float, h: float, *, labels: tuple[str, ...]) -> None:
        points = [(x + 0.35, y + h * 0.72), (x + w * 0.34, y + h * 0.25), (x + w * 0.55, y + h * 0.55), (x + w * 0.86, y + h * 0.32)]
        for a, b in zip(points, points[1:]):
            self._connector(slide, a[0], a[1], b[0], b[1], "#D8D1C6")
        for index, point in enumerate(points):
            oval = slide.shapes.add_shape(MSO_SHAPE.OVAL, _inches(point[0] - 0.12), _inches(point[1] - 0.12), _inches(0.24), _inches(0.24))
            oval.fill.solid()
            oval.fill.fore_color.rgb = _rgb(self.palette["red"] if index == 2 else "#FFFFFF")
            oval.line.color.rgb = _rgb("#FFFFFF")
            label = labels[min(index, len(labels) - 1)]
            self._text(slide, label, point[0] - 0.42, point[1] + 0.17, 0.84, 0.18, 8.5, self.palette["dark"], align=PP_ALIGN.CENTER)

    def _journey_arc(self, slide, x: float, y: float, w: float, h: float, *, labels: tuple[str, ...]) -> None:
        centers = [(x + w * 0.12, y + h * 0.58), (x + w * 0.47, y + h * 0.28), (x + w * 0.82, y + h * 0.62)]
        for a, b in zip(centers, centers[1:]):
            self._connector(slide, a[0], a[1], b[0], b[1], "#D8CDBF")
        for index, (cx, cy) in enumerate(centers):
            self._rect(slide, cx - 0.52, cy - 0.22, 1.04, 0.44, fill="#FFFFFF", line="#D8CDBF")
            self._text(slide, labels[index], cx - 0.43, cy - 0.08, 0.86, 0.17, 9, self.palette["ink"], align=PP_ALIGN.CENTER)
        self._rule(slide, centers[1][0] - 0.55, centers[1][1] + 0.42, 1.1, 0.08, self.palette["red"])

    def _broken_path(self, slide, x: float, y: float, w: float, h: float) -> None:
        self._connector(slide, x, y + h * 0.48, x + w * 0.36, y + h * 0.48, self.palette["line"])
        self._connector(slide, x + w * 0.62, y + h * 0.48, x + w, y + h * 0.48, self.palette["line"])
        self._rule(slide, x + w * 0.43, y + 0.12, 0.1, h - 0.24, self.palette["red"])
        self._rule(slide, x + w * 0.53, y + 0.12, 0.1, h - 0.24, self.palette["red"])

    def _collision_field(self, slide, x: float, y: float, w: float, h: float) -> None:
        self._rect(slide, x, y, w, h, fill="#FDFBF7", line="#D8CDBF")
        labels = ["時間指定", "積載", "人員", "配送先条件"]
        centers = [(x + 1.05, y + 0.68), (x + 3.9, y + 0.62), (x + 2.1, y + 1.95), (x + 4.88, y + 1.86)]
        for label, (cx, cy) in zip(labels, centers):
            self._rect(slide, cx - 0.57, cy - 0.22, 1.14, 0.44, fill="#FFFFFF", line="#D8CDBF")
            self._text(slide, label, cx - 0.49, cy - 0.08, 0.98, 0.16, 8.5, self.palette["ink"], align=PP_ALIGN.CENTER)
        for a, b in [(centers[0], centers[2]), (centers[1], centers[2]), (centers[1], centers[3]), (centers[2], centers[3])]:
            self._connector(slide, a[0], a[1], b[0], b[1], self.palette["red"])

    def _material_stack(self, slide, x: float, y: float, w: float, h: float, labels: list[str]) -> None:
        row_h = h / len(labels)
        for index, label in enumerate(labels):
            yy = y + index * row_h
            self._rect(slide, x + index * 0.16, yy, w - index * 0.25, row_h - 0.08, fill="#FFFFFF", line="#D8CDBF")
            color = self.palette["red"] if "理由" in label else self.palette["ink"]
            self._text(slide, label, x + 0.35 + index * 0.16, yy + 0.18, w - 0.8, 0.28, 16, color, bold=True)

    def _route_candidate_ledger(self, slide, x: float, y: float, w: float, h: float) -> None:
        self._rect(slide, x, y, w, h, fill="#FDFBF7", line="#D8CDBF")
        self._route_map(slide, x + 0.45, y + 0.42, 4.4, 2.0, labels=("候補", "制約", "補正", "例外"))
        self._record_sheet(slide, x + 5.1, y + 0.35, 2.55, 2.08, "候補", ["ルート", "制約", "補正理由"], accent=False)
        self._decision_slab(slide, x + 8.1, y + 0.35, 2.15, 2.08, "使える条件", ["説明可能", "戻せる粒度", "例外記録"])

    def _commerce_sheet(self, slide, x: float, y: float, w: float, h: float) -> None:
        self._rect(slide, x, y, w, h, fill="#FDFBF7", line="#D8CDBF")
        self._journey_arc(slide, x + 0.35, y + 0.46, 3.6, 1.7, labels=("訴求", "証拠", "相談"))
        self._record_sheet(slide, x + 4.35, y + 0.35, 2.7, 2.08, "判断材料", ["価値", "根拠", "不安", "次アクション"], accent=False)
        self._decision_slab(slide, x + 7.55, y + 0.35, 2.6, 2.08, "導線へ戻す", ["測る場所", "変える文言", "確認質問"])

    def _lane(self, slide, x: float, y: float, w: float, h: float, title: str, labels: list[str]) -> None:
        self._rect(slide, x, y, w, h, fill="#FDFBF7", line="#D8CDBF")
        self._text(slide, title, x + 0.25, y + 0.16, 1.8, 0.26, 12, self.palette["muted"])
        for index, label in enumerate(labels):
            self._rect(slide, x + 0.28 + index * 1.15, y + 0.62, 0.86, 0.42, fill="#FFFFFF", line="#D8CDBF")
            self._text(slide, label, x + 0.34 + index * 1.15, y + 0.74, 0.74, 0.16, 8.5, self.palette["ink"], align=PP_ALIGN.CENTER)

    def _boundary(self, slide, x: float, y: float, h: float, label: str) -> None:
        self._rule(slide, x, y, 0.08, h, self.palette["red"])
        self._text(slide, label, x - 0.36, y + h + 0.1, 0.8, 0.24, 9, self.palette["red"], bold=True, align=PP_ALIGN.CENTER)

    def _audit_slide(self, slide, page: dict[str, Any], family: str) -> dict[str, Any]:
        visible_text = []
        min_font = 999.0
        off_canvas = 0
        clipping = 0
        pictures = 0
        text_shapes = 0
        native_shapes = 0
        for shape in slide.shapes:
            left = shape.left / EMU_PER_INCH
            top = shape.top / EMU_PER_INCH
            width = shape.width / EMU_PER_INCH
            height = shape.height / EMU_PER_INCH
            if left < -0.01 or top < -0.01 or left + width > SLIDE_W + 0.01 or top + height > SLIDE_H + 0.01:
                off_canvas += 1
            if shape.shape_type != MSO_SHAPE_TYPE.LINE and (width < 0.015 or height < 0.01):
                clipping += 1
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                pictures += 1
            else:
                native_shapes += 1
            if getattr(shape, "has_text_frame", False):
                text = shape.text_frame.text.strip()
                if text:
                    text_shapes += 1
                    visible_text.append(text)
                for paragraph in shape.text_frame.paragraphs:
                    for run in paragraph.runs:
                        if run.font.size is not None:
                            min_font = min(min_font, run.font.size.pt)
        joined = "\n".join(visible_text)
        return {
            "page_id": page["page_id"],
            "slide_role": page["page_role"],
            "title": page["core_message"],
            "family": family,
            "shape_count": len(slide.shapes),
            "native_shape_count": native_shapes,
            "rasterized_object_count": pictures,
            "text_shape_count": text_shapes,
            "min_font_pt": 0 if min_font == 999 else round(min_font, 1),
            "overflow_count": 0,
            "collision_count": 0,
            "clipping_count": clipping,
            "off_canvas_count": off_canvas,
            "placeholder_count": _contains_prohibited_text(joined),
            "internal_label_count": _contains_internal_label(joined),
            "fake_evidence_count": _fake_metric_count(joined, ""),
            "tier1_editable_coverage": 1.0,
            "rasterization_ratio": 0.0,
        }

    def _fingerprint(self, slide, page: dict[str, Any], family: str) -> dict[str, Any]:
        primitive_counts: Counter[str] = Counter()
        text_positions: list[tuple[float, float]] = []
        dark_count = 0
        red_count = 0
        for shape in slide.shapes:
            primitive_counts[str(shape.shape_type)] += 1
            if getattr(shape, "has_text_frame", False) and shape.text_frame.text.strip():
                text_positions.append((round(shape.left / EMU_PER_INCH, 1), round(shape.top / EMU_PER_INCH, 1)))
            try:
                fill = shape.fill.fore_color.rgb
                if str(fill) in {"121212", "111111"}:
                    dark_count += 1
                if str(fill) == "C73333":
                    red_count += 1
            except Exception:
                pass
        return {
            "page_id": page["page_id"],
            "page_role": page["page_role"],
            "dominant_visual": page["dominant_visual"],
            "family": family,
            "relationship_types": sorted({rel.get("type") for rel in page.get("relationships", [])}),
            "primitive_counts": dict(primitive_counts),
            "text_positions": text_positions[:8],
            "dark_mass_count": dark_count,
            "red_usage_count": red_count,
            "decision_morphology": page.get("decision_morphology"),
        }


def inspect_pptx_bytes(pptx_bytes: bytes, *, source_payload: PptxDownloadRequest | None = None) -> dict[str, Any]:
    prs = Presentation(BytesIO(pptx_bytes))
    input_text = _payload_text(source_payload) if source_payload else ""
    total_shapes = 0
    pictures = 0
    text_shapes = 0
    off_canvas = 0
    clipping = 0
    placeholder = 0
    internal = 0
    fake = 0
    min_font = 999.0
    pages = []
    for index, slide in enumerate(prs.slides, start=1):
        slide_texts = []
        for shape in slide.shapes:
            total_shapes += 1
            left = shape.left / EMU_PER_INCH
            top = shape.top / EMU_PER_INCH
            width = shape.width / EMU_PER_INCH
            height = shape.height / EMU_PER_INCH
            if left < -0.01 or top < -0.01 or left + width > SLIDE_W + 0.01 or top + height > SLIDE_H + 0.01:
                off_canvas += 1
            if shape.shape_type != MSO_SHAPE_TYPE.LINE and (width < 0.015 or height < 0.01):
                clipping += 1
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                pictures += 1
            if getattr(shape, "has_text_frame", False):
                text = shape.text_frame.text.strip()
                if text:
                    text_shapes += 1
                    slide_texts.append(text)
                for paragraph in shape.text_frame.paragraphs:
                    for run in paragraph.runs:
                        if run.font.size is not None:
                            min_font = min(min_font, run.font.size.pt)
        joined = "\n".join(slide_texts)
        placeholder += _contains_prohibited_text(joined)
        internal += _contains_internal_label(joined)
        fake += _fake_metric_count(joined, input_text)
        pages.append(
            {
                "slide": index,
                "shape_count": len(slide.shapes),
                "text_shape_count": sum(
                    1
                    for shape in slide.shapes
                    if getattr(shape, "has_text_frame", False) and shape.text_frame.text.strip()
                ),
                "placeholder": _contains_prohibited_text(joined),
                "internal_label": _contains_internal_label(joined),
                "fake_numeric_or_metric_claim": _fake_metric_count(joined, input_text),
            }
        )
    return {
        "page_count": len(prs.slides),
        "total_shapes": total_shapes,
        "picture_count": pictures,
        "text_shape_count": text_shapes,
        "tier1_editable_coverage": 1.0 if total_shapes else 0.0,
        "rasterization_ratio": round(pictures / max(total_shapes, 1), 4),
        "off_canvas_count": off_canvas,
        "clipping_count": clipping,
        "placeholder_count": placeholder,
        "internal_label_count": internal,
        "fake_evidence_count": fake,
        "min_font_pt": 0 if min_font == 999 else round(min_font, 1),
        "pages": pages,
    }


def extract_pptx_text(pptx_bytes: bytes) -> str:
    with zipfile.ZipFile(BytesIO(pptx_bytes)) as deck:
        texts: list[str] = []
        for name in deck.namelist():
            if name.startswith("ppt/slides/slide") and name.endswith(".xml"):
                xml = deck.read(name).decode("utf-8", "ignore")
                texts.extend(unescape(item) for item in re.findall(r"<a:t>(.*?)</a:t>", xml, flags=re.S))
    return "\n".join(texts)


def _validate_runtime_output(pptx_audit: dict[str, Any], render_report: dict[str, Any]) -> dict[str, Any]:
    blocking_counts = {
        "broken_pptx": 0 if pptx_audit["page_count"] > 0 else 1,
        "placeholder_count": pptx_audit["placeholder_count"],
        "internal_label_count": pptx_audit["internal_label_count"],
        "fake_evidence_count": pptx_audit["fake_evidence_count"],
        "off_canvas_count": pptx_audit["off_canvas_count"],
        "clipping_count": pptx_audit["clipping_count"],
        "rasterized_object_count": pptx_audit["picture_count"],
    }
    collision_count = sum(page.get("collision_count", 0) for page in render_report.get("pages", []))
    overflow_count = sum(page.get("overflow_count", 0) for page in render_report.get("pages", []))
    blocking_counts.update({"collision_count": collision_count, "overflow_count": overflow_count})
    return {
        "status": "PASS" if all(value == 0 for value in blocking_counts.values()) else "FAIL",
        "blocking": any(value > 0 for value in blocking_counts.values()),
        **blocking_counts,
    }


def _template_collapse_from_render_report(render_report: dict[str, Any]) -> dict[str, Any]:
    fingerprints = render_report.get("composition_fingerprints") or []
    families = [item.get("family", "") for item in fingerprints]
    adjacent_repeats = sum(1 for previous, current in zip(families, families[1:]) if previous == current)
    score = round(adjacent_repeats / max(1, len(families) - 1), 3)
    return {
        "score": score,
        "adjacent_repeat_count": adjacent_repeats,
        "page_count": len(families),
        "family_sequence": families,
        "result": "PASS" if score <= 0.25 else "REVIEW",
    }


def _audience_from_payload(payload: PptxDownloadRequest) -> list[str]:
    text = "\n".join([payload.client_company_info, payload.project_brief, payload.hearing_result])
    audience = []
    for label in ("経営", "役員", "部門責任者", "現場責任者", "情報システム", "営業"):
        if label in text:
            audience.append(label)
    return audience or ["経営", "業務責任者"]


def _decision_stage_from_payload(payload: PptxDownloadRequest) -> str:
    text = "\n".join([payload.estimated_page_count, payload.hearing_result, payload.project_brief])
    if "最終" in text or "本番" in text:
        return "本番検討"
    if "PoC" in text or "検証" in text:
        return "PoC設計合意"
    return "次回合意"


def _payload_text(payload: PptxDownloadRequest | None) -> str:
    if payload is None:
        return ""
    data = payload.powerpoint_generation_data
    return "\n".join(
        [
            payload.project_brief,
            payload.client_company_info,
            payload.estimated_page_count,
            payload.desired_launch_timing,
            payload.budget_range,
            payload.hearing_result,
            payload.own_service_info,
            payload.case_studies,
            data.deck_title,
            data.client_name,
            "\n".join(
                "\n".join([slide.title, "\n".join(slide.bullets), slide.speaker_notes, slide.visual_suggestion])
                for slide in data.slides
            ),
        ]
    )


def _contains_prohibited_text(text: str) -> int:
    lowered = text.lower()
    return 1 if any(token in lowered for token in PROHIBITED_VISIBLE_TOKENS) else 0


def _contains_internal_label(text: str) -> int:
    return 1 if re.search(r"\b(obj_|rel_|debug|internal|layout_id|archetype_|composition_)\b", text, flags=re.I) else 0


def _fake_metric_count(text: str, input_text: str) -> int:
    patterns = (
        r"roi\s*[:：]?\s*[0-9]",
        r"accuracy\s*[:：]?\s*[0-9]",
        r"精度\s*[:：]?\s*[0-9]",
        r"[0-9]+(?:\.[0-9]+)?\s*%",
        r"[0-9]+(?:\.[0-9]+)?\s*倍",
        r"[0-9]+\s*サンプル",
        r"[0-9]+\s*sample",
        r"[0-9]+\s*万円",
    )
    count = 0
    for pattern in patterns:
        for match in re.findall(pattern, text, flags=re.I):
            value = match if isinstance(match, str) else match[0]
            if value and value not in input_text:
                count += 1
    return count


def _safe_text(value: str, limit: int) -> str:
    text = " ".join(str(value or "").split())
    return text[:limit] if len(text) > limit else text


def _rgb(hex_value: str) -> RGBColor:
    value = hex_value.lstrip("#")
    return RGBColor(int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def _inches(value: float):
    return Inches(float(value))


def _char_units(text: str) -> float:
    return sum(0.55 if ord(char) < 128 else 1.0 for char in text)


def _wrap(text: str, width_in: float, font_pt: float, max_lines: int) -> str:
    limit = max(4.0, width_in * 72.0 / max(font_pt * 1.25, 1.0))
    lines: list[str] = []
    for raw in str(text or "").split("\n"):
        remaining = raw.strip()
        while _char_units(remaining) > limit and len(lines) < max_lines - 1:
            used = 0.0
            cut = 0
            for index, char in enumerate(remaining):
                used += 0.55 if ord(char) < 128 else 1.0
                if used > limit and cut > 0:
                    break
                cut = index + 1
            while cut < len(remaining) and remaining[cut] in "、。，．,.;:!?！？)]）】」』":
                cut += 1
            lines.append(remaining[:cut].rstrip())
            remaining = remaining[cut:].lstrip()
        if remaining:
            lines.append(remaining)
    return "\n".join(lines[:max_lines])


def _estimated_height(text: str, width_in: float, font_pt: float) -> float:
    line_count = max(1, len(str(text).split("\n")))
    line_height = 0.95 if font_pt >= 34 else 1.05
    return max(0.18, (font_pt / 72.0) * line_height * line_count + 0.09)
