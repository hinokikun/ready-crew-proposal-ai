"""Focused Phase3F-22A tests for the isolated ROADMAP runtime foundation."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import hashlib
import tempfile
import unittest
from zipfile import ZipFile

from app.services.pptx_parts.native_trace_content_adapter import (
    FailureReason,
    adapt_role,
    render_native_role_dry_run,
)
from app.services.pptx_parts.native_trace_registry import (
    REPO_ROOT,
    get_runtime_native_role_spec,
    resolve_approved_native_role,
)
from app.services.pptx_parts.native_trace_validation import inspect_template_package


SOURCE = REPO_ROOT / "artifacts/phase3f08_native_trace_gap/06_implementation_schedule/native_trace.pptx"
RUNTIME = REPO_ROOT / "backend/app/presentation_assets/native_trace/conditional/ROADMAP.pptx"


def roadmap_data(phase_count: int = 5) -> dict:
    phases = []
    for index in range(1, phase_count + 1):
        phases.append(
            {
                "number": index,
                "name": ["企画・設計", "環境構築", "トライアル運用", "本格展開", "継続的な改善", "追加展開"][index - 1],
                "duration": ["4週間", "5週間", "6週間", "8週間", "継続", "4週間"][index - 1],
                "description": f"現行業務を確認し、第{index}段階の実施内容を整理します。",
                "actions": [f"実施項目{index}-{action_index}" for action_index in range(1, 5)],
            }
        )
    milestones = [
        {"title": title, "timing": timing}
        for title, timing in zip(
            ["準備完了", "環境確認", "試行完了", "展開開始", "定着確認", "追加確認"],
            ["Week 2", "Week 7", "Week 8", "Week 22", "継続確認", "Week 25"],
        )
    ][:phase_count]
    return {
        "phases": phases,
        "milestones": milestones,
        "success_factors": [
            {"title": "経営層の関与", "body": "判断と支援を継続します。"},
            {"title": "現場との連携", "body": "利用者の声を反映します。"},
            {"title": "小さく始める", "body": "段階的に展開します。"},
            {"title": "継続的な改善", "body": "成果を定期確認します。"},
        ],
        "objective": "確実な導入と継続的な改善により、持続的な価値を創出します。",
    }


def context_for(phase_count: int = 5, *, generated: bool = False, long_text: bool = False) -> SimpleNamespace:
    data = roadmap_data(phase_count)
    if long_text:
        data["phases"][0]["actions"][0] = "長文" * 40
    source_type = "ai_generated" if generated else "user_input"
    candidate = {
        "semantic_type": "roadmap implementation schedule",
        "source_field": "context.verified_roadmap",
        "source_type": source_type,
        "authority": "AI_PROPOSED" if generated else "USER_PROVIDED",
        "review_state": "confirmed",
        "value": "current roadmap",
    }
    return SimpleNamespace(
        verified_roadmap=data,
        semantic_candidates=[candidate],
    )


def slide() -> SimpleNamespace:
    return SimpleNamespace(title="導入ステップとスケジュール")


class RoadmapRuntimeFoundationTests(unittest.TestCase):
    def test_role_resolution_and_runtime_registration(self) -> None:
        self.assertEqual(resolve_approved_native_role(slide(), index=1), "ROADMAP")
        spec = get_runtime_native_role_spec("ROADMAP", surface="conditional")
        self.assertIsNotNone(spec)
        self.assertTrue(spec["human_approved"])
        self.assertEqual(spec["registry_status"], "FOUNDATION_ONLY_NOT_ACTIVATED")
        self.assertTrue(SOURCE.is_file())
        self.assertTrue(RUNTIME.is_file())
        self.assertEqual(hashlib.sha256(SOURCE.read_bytes()).hexdigest(), spec["source_checksum"])
        self.assertEqual(hashlib.sha256(RUNTIME.read_bytes()).hexdigest(), spec["runtime_checksum"])

    def test_template_is_native_and_source_is_unchanged(self) -> None:
        source_before = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        report = inspect_template_package(RUNTIME)
        self.assertEqual(report["full_slide_raster_count"], 0)
        self.assertGreater(report["editable_text_shape_count"], 0)
        self.assertGreater(report["editable_shape_count"], 0)
        self.assertEqual(hashlib.sha256(SOURCE.read_bytes()).hexdigest(), source_before)

    def test_three_four_and_five_phase_plans_are_eligible(self) -> None:
        for count in (3, 4, 5):
            result = adapt_role("ROADMAP", surface="conditional", slide_id="ROADMAP", context=context_for(count), slide=slide())
            self.assertTrue(result.renderable, result.reason)
            self.assertEqual(result.evidence_status["roadmap.phases"], "VERIFIED")

    def test_six_plus_phases_require_continuation(self) -> None:
        result = adapt_role("ROADMAP", surface="conditional", slide_id="ROADMAP", context=context_for(6), slide=slide())
        self.assertFalse(result.renderable)
        self.assertEqual(result.failure_reason, FailureReason.TEXT_OVERFLOW_RISK.value)
        self.assertTrue(any(item.get("status") == "CONTINUATION_REQUIRED" for item in result.diagnostics))

    def test_missing_duration_or_milestone_fails_closed(self) -> None:
        context = context_for(5)
        context.verified_roadmap["phases"][1]["duration"] = None
        result = adapt_role("ROADMAP", surface="conditional", slide_id="ROADMAP", context=context, slide=slide())
        self.assertFalse(result.renderable)
        self.assertEqual(result.failure_reason, FailureReason.EVIDENCE_REQUIRED.value)

        context = context_for(5)
        context.verified_roadmap["milestones"] = context.verified_roadmap["milestones"][:3]
        result = adapt_role("ROADMAP", surface="conditional", slide_id="ROADMAP", context=context, slide=slide())
        self.assertFalse(result.renderable)
        self.assertEqual(result.failure_reason, FailureReason.EVIDENCE_REQUIRED.value)

    def test_generated_only_data_is_rejected(self) -> None:
        result = adapt_role("ROADMAP", surface="conditional", slide_id="ROADMAP", context=context_for(generated=True), slide=slide())
        self.assertFalse(result.renderable)
        self.assertEqual(result.failure_reason, FailureReason.EVIDENCE_REQUIRED.value)

    def test_dry_render_replaces_dynamic_sample_content_without_leak(self) -> None:
        with tempfile.TemporaryDirectory(prefix="phase3f22a-roadmap-") as temporary_dir:
            result = render_native_role_dry_run(
                "ROADMAP",
                surface="conditional",
                slide_id="ROADMAP",
                context=context_for(5),
                slide=slide(),
                temporary_dir=temporary_dir,
            )
            self.assertTrue(result.success, result.reason)
            self.assertEqual(result.failure_reason, None)
            validation = result.validation["injected"]
            self.assertEqual(validation["prohibited_sample_strings_found"], [])
            self.assertEqual(validation["full_slide_raster_count"], 0)
            self.assertTrue(validation["shape_bounds_unchanged"])
            self.assertTrue(validation["image_relationships_preserved"])
            self.assertTrue(validation["valid"])
            self.assertTrue(result.package_path)
            with ZipFile(result.package_path) as package:
                xml = package.read("ppt/slides/slide1.xml").decode("utf-8")
            for sample in ("2026.06.22", "1ヶ月", "1〜2ヶ月", "Week 1", "Week 6", "Week 12", "Week 20"):
                self.assertNotIn(sample, xml)

    def test_long_text_is_rejected_by_text_fit_before_render(self) -> None:
        with tempfile.TemporaryDirectory(prefix="phase3f22a-roadmap-long-") as temporary_dir:
            result = render_native_role_dry_run(
                "ROADMAP",
                surface="conditional",
                slide_id="ROADMAP",
                context=context_for(5, long_text=True),
                slide=slide(),
                temporary_dir=temporary_dir,
            )
            self.assertFalse(result.success)
            self.assertEqual(result.failure_reason, FailureReason.TEXT_OVERFLOW_RISK.value)


if __name__ == "__main__":
    unittest.main()
