from __future__ import annotations

import hashlib
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile

from app.services.pptx_parts.native_trace_content_adapter import ROLE_ADAPTERS
from app.services.pptx_parts.native_trace_registry import get_runtime_native_role_spec


ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DIR = ROOT / "backend" / "app" / "presentation_assets" / "native_trace" / "summary"

ASSETS = {
    "S03_current_state_16x9_retrace.pptx": ("05", "現状理解"),
    "S04_problem_analysis_16x9_retrace.pptx": ("06", "主要課題"),
    "S05_solution_concept_16x9_retrace.pptx": ("07", "提案コンセプト"),
    "S06_solution_approach_16x9_retrace.pptx": ("08", "導入戦略"),
}

FORBIDDEN_SAMPLE_TERMS = (
    "ProposalPilot",
    "AI営業秘書",
    "約70%削減",
    "約1.5倍",
    "約20%向上",
    "提案書自動生成AI",
    "ERP基盤",
    "統合DB",
    "マスタ管理",
)


def _xml_text(pptx: Path) -> str:
    with ZipFile(pptx) as archive:
        return "\n".join(
            archive.read(name).decode("utf-8", errors="ignore")
            for name in archive.namelist()
            if name.endswith(".xml")
        )


def test_latest_retrace_assets_are_single_slide_16x9_packages() -> None:
    for filename in ASSETS:
        path = RUNTIME_DIR / filename
        assert path.exists(), filename
        with ZipFile(path) as archive:
            names = set(archive.namelist())
            assert "[Content_Types].xml" in names
            assert "ppt/presentation.xml" in names
            assert "ppt/slides/slide1.xml" in names
            assert not any(name.startswith("ppt/media/") for name in names)
            presentation_xml = archive.read("ppt/presentation.xml").decode("utf-8")
            assert 'cx="12192000"' in presentation_xml
            assert 'cy="6858000"' in presentation_xml
            assert len([name for name in names if name.startswith("ppt/slides/slide") and name.endswith(".xml")]) == 1


def test_latest_retrace_assets_preserve_role_headers_and_native_slots() -> None:
    for filename, (page, title) in ASSETS.items():
        text = _xml_text(RUNTIME_DIR / filename)
        assert f">{page}<" in text, filename
        assert title in text, filename
        assert "trace:" in text, filename


def test_latest_retrace_assets_have_no_legacy_or_generic_sample_leak() -> None:
    text = "\n".join(_xml_text(RUNTIME_DIR / filename) for filename in ASSETS)
    for term in FORBIDDEN_SAMPLE_TERMS:
        assert term not in text, term


def test_latest_retrace_assets_preserve_approved_information_density() -> None:
    expected_terms = {
        "S03_current_state_16x9_retrace.pptx": (
            "業務プロセスの現状",
            "データ活用の現状",
            "判断基準のばらつき",
            "手入力・照合作業の負荷",
        ),
        "S04_problem_analysis_16x9_retrace.pptx": (
            "判断の標準化",
            "業務負荷の削減",
            "データ活用基盤の整備",
            "優先課題",
        ),
        "S05_solution_concept_16x9_retrace.pptx": (
            "人の判断を支援し、標準化と処理スピードを両立",
            "AIが候補を提示",
            "人が最終判断",
            "業務に馴染む運用設計",
        ),
        "S06_solution_approach_16x9_retrace.pptx": (
            "STEP 1",
            "STEP 2",
            "STEP 3",
            "小さく始め、運用条件を確認しながら次の範囲を定める",
        ),
    }
    for filename, terms in expected_terms.items():
        text = _xml_text(RUNTIME_DIR / filename)
        for term in terms:
            assert term in text, (filename, term)


def test_solution_concept_uses_editable_image_to_candidate_and_review_actions() -> None:
    text = _xml_text(RUNTIME_DIR / "S05_solution_concept_16x9_retrace.pptx")
    assert "候補結果" in text
    assert "AIの推定結果" in text
    assert "修正" in text
    assert "確定" in text
    assert "trace:S05:content.auto.22" in text


def test_latest_retrace_assets_are_self_contained_runtime_packages() -> None:
    expected_roles = {
        "S03_current_state_16x9_retrace.pptx": "CURRENT_STATE",
        "S04_problem_analysis_16x9_retrace.pptx": "PROBLEM_ANALYSIS",
        "S05_solution_concept_16x9_retrace.pptx": "SOLUTION_CONCEPT",
        "S06_solution_approach_16x9_retrace.pptx": "SOLUTION_APPROACH",
    }
    for filename, role in expected_roles.items():
        path = RUNTIME_DIR / filename
        spec = get_runtime_native_role_spec(role, surface="summary")
        assert spec is not None
        assert Path(str(spec["runtime_asset"])).name == filename
        assert hashlib.sha256(path.read_bytes()).hexdigest() == spec["runtime_checksum"]
        with ZipFile(path) as archive:
            names = set(archive.namelist())
            assert "[Content_Types].xml" in names
            assert "ppt/presentation.xml" in names
            slide_names = [
                name
                for name in names
                if name.startswith("ppt/slides/slide") and name.endswith(".xml")
            ]
            assert slide_names == ["ppt/slides/slide1.xml"]
            assert not any(name.startswith("ppt/media/") for name in names)
            slide_xml = archive.read("ppt/slides/slide1.xml").decode("utf-8")
            slide_root = ElementTree.fromstring(slide_xml)
            local_names = {
                element.tag.rsplit("}", 1)[-1]
                for element in slide_root.iter()
            }
            assert "sp" in local_names
            assert "t" in local_names
            assert "artifacts/" not in slide_xml


def test_latest_retrace_assets_are_runtime_wired_for_summary_roles() -> None:
    expected = {
        "CURRENT_STATE": "S03_current_state_16x9_retrace.pptx",
        "PROBLEM_ANALYSIS": "S04_problem_analysis_16x9_retrace.pptx",
        "SOLUTION_CONCEPT": "S05_solution_concept_16x9_retrace.pptx",
        "SOLUTION_APPROACH": "S06_solution_approach_16x9_retrace.pptx",
    }
    for role, filename in expected.items():
        spec = get_runtime_native_role_spec(role, surface="summary")
        assert spec is not None
        assert Path(str(spec["runtime_asset"])).name == filename
        assert ("summary", role) in ROLE_ADAPTERS
