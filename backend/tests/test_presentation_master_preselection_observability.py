from types import SimpleNamespace

from app.services.presentation_master.integration.engine_adapter import (
    _emit_preselection_snapshot,
    _emit_selection_diagnostics,
)
from app.services.presentation_master.integration.models import ProductionAdapterInput
from app.services.presentation_master.selection import MasterSelectionInput, select_master


def _adapter_input():
    payload = SimpleNamespace(candidate_boundary_correlation_id="corr-123")
    candidates = SimpleNamespace(
        candidates=(
            SimpleNamespace(review_state="CONFIRMED"),
            SimpleNamespace(review_state="CORRECTED"),
        ),
        unresolved_critical=lambda: (),
    )
    return ProductionAdapterInput(
        payload=payload,
        semantic_candidates=candidates,
        source_bindings=(object(),),
    )


def _selection_input():
    return MasterSelectionInput(
        decision_context="department_head",
        semantic_signals=frozenset({"responsibility", "approval", "execution", "secret-value"}),
        available_groups=frozenset({"preparation", "approval", "execution", "secret-group"}),
        relationship_types=frozenset({"dependency", "secret-relationship"}),
        content_counts={"preparation": 1, "approval": 1, "execution": 1, "secret-group": 1},
        evidence_states=frozenset({"source_backed", "secret-evidence"}),
        missing_information=("decision_context_unclear", "secret-gap"),
        confidence=0.8,
    )


def test_preselection_snapshot_is_bounded_and_correlated(caplog):
    selection_input = _selection_input()
    with caplog.at_level("INFO"):
        _emit_preselection_snapshot(selection_input, {"DIRECT": 3, "UNRESOLVED": 1}, _adapter_input(), None)

    record = next(record for record in caplog.records if record.getMessage() == "presentation_master_preselection_snapshot")
    assert record.correlation_id == "corr-123"
    assert record.decision_context == "department_head"
    assert "secret-value" not in record.semantic_signal_keys
    assert "secret-group" not in record.available_group_keys
    assert "secret-relationship" not in record.relationship_type_keys
    assert "secret-evidence" not in record.evidence_state_keys
    assert "secret-gap" not in record.unresolved_requirement_keys
    assert record.candidate_state_counts == {
        "confirmed": 1,
        "corrected": 1,
        "unconfirmed": 0,
        "rejected": 0,
        "unresolved": 0,
        "unresolved_critical": 0,
    }


def test_selection_diagnostics_use_existing_ranked_candidates(caplog):
    selection_input = _selection_input()
    selection = select_master(selection_input)
    with caplog.at_level("INFO"):
        _emit_selection_diagnostics(selection, _adapter_input(), None)

    record = next(record for record in caplog.records if record.getMessage() == "presentation_master_selection_diagnostics")
    assert record.correlation_id == "corr-123"
    assert [item["master_id"] for item in record.masters] == [item.master_id for item in selection.ranked_candidates]
    assert [item["score"] for item in record.masters] == [item.score for item in selection.ranked_candidates]
    assert all(item["master_id"] in {f"M{i}" for i in range(45, 55)} for item in record.masters)


def test_logging_failure_does_not_change_selection(monkeypatch):
    selection_input = _selection_input()
    expected = select_master(selection_input)

    def fail(*args, **kwargs):
        raise RuntimeError("logging failure")

    monkeypatch.setattr("app.services.presentation_master.integration.engine_adapter.logger.info", fail)
    _emit_preselection_snapshot(selection_input, {}, _adapter_input(), None)
    _emit_selection_diagnostics(expected, _adapter_input(), None)
    assert select_master(selection_input) == expected
