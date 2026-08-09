"""Offline refinement loop for generated V9 design decks."""

from __future__ import annotations

from dataclasses import replace

from .density_optimizer import normalize_visible_text, visible_character_count
from .models import DesignDeck, DesignSlideContract, RefinementIssue, RefinementReport
from .validators import INTERNAL_LABEL_PATTERN, validate_design_deck


def refine_design_deck(deck: DesignDeck, *, max_iterations: int = 3) -> tuple[DesignDeck, RefinementReport]:
    current = deck
    issues: list[RefinementIssue] = []
    changes: list[str] = []
    iterations = 0
    for iteration in range(1, max_iterations + 1):
        iterations = iteration
        validation = validate_design_deck(current)
        density_issues = _density_issues(current)
        all_issues = validation + density_issues
        if not all_issues:
            break
        current, new_issues, new_changes = _apply_contract_fixes(current, all_issues, iteration)
        issues.extend(new_issues)
        changes.extend(new_changes)
    final_validation = validate_design_deck(current) + _density_issues(current)
    status = "clean" if not final_validation else "human_review_required"
    return current, RefinementReport(iterations=iterations, issues=tuple(issues), final_status=status, changes_applied=tuple(changes))


def _density_issues(deck: DesignDeck) -> list[str]:
    issues: list[str] = []
    for contract in deck.slide_contracts:
        count = visible_character_count(contract.action_title, contract.core_message, contract.takeaway, *contract.supporting_evidence)
        if count > 170:
            issues.append(f"{contract.slide_id}_visible_density_too_high")
    return issues


def _apply_contract_fixes(
    deck: DesignDeck,
    issue_keys: list[str],
    iteration: int,
) -> tuple[DesignDeck, list[RefinementIssue], list[str]]:
    issues: list[RefinementIssue] = []
    changes: list[str] = []
    fixed_contracts: list[DesignSlideContract] = []
    issue_text = " ".join(issue_keys)
    for contract in deck.slide_contracts:
        fixed = contract
        if f"{contract.slide_id}_action_title_too_long" in issue_text:
            fixed = replace(fixed, action_title=normalize_visible_text(fixed.action_title, 40))
            issues.append(_issue(contract.slide_id, "action_title", "P1", "Action title was too long.", "Shortened to fit two lines.", iteration))
            changes.append(f"{contract.slide_id}: shortened action title")
        if f"{contract.slide_id}_visible_density_too_high" in issue_text:
            fixed = replace(
                fixed,
                core_message=normalize_visible_text(fixed.core_message, 52),
                takeaway=normalize_visible_text(fixed.takeaway, 34),
                supporting_evidence=tuple(normalize_visible_text(item, 30) for item in fixed.supporting_evidence[:3]),
            )
            issues.append(_issue(contract.slide_id, "content_density", "P1", "Visible copy was too dense.", "Compressed visible text and kept detail in notes.", iteration))
            changes.append(f"{contract.slide_id}: compressed visible content")
        visible = " ".join([fixed.action_title, fixed.core_message, fixed.takeaway, *fixed.supporting_evidence])
        if INTERNAL_LABEL_PATTERN.search(visible):
            fixed = replace(
                fixed,
                core_message=INTERNAL_LABEL_PATTERN.sub("design element", fixed.core_message),
                takeaway=INTERNAL_LABEL_PATTERN.sub("design element", fixed.takeaway),
            )
            issues.append(_issue(contract.slide_id, "internal_label", "P0", "Internal label appeared in visible text.", "Removed internal label.", iteration))
            changes.append(f"{contract.slide_id}: removed internal label")
        fixed_contracts.append(fixed)

    current = DesignDeck(
        version=deck.version,
        design_version=deck.design_version,
        case_id=deck.case_id,
        case_name=deck.case_name,
        client_name=deck.client_name,
        feature_flag_enabled=deck.feature_flag_enabled,
        information_architecture=deck.information_architecture,
        slide_contracts=tuple(fixed_contracts),
        design_language=deck.design_language,
        design_plan_fingerprint=deck.design_plan_fingerprint,
        fallback_count=deck.fallback_count,
        native_fallback_count=deck.native_fallback_count,
        render_warnings=deck.render_warnings,
    )
    return current, issues, changes


def _issue(slide_id: str, category: str, severity: str, finding: str, correction: str, iteration: int) -> RefinementIssue:
    return RefinementIssue(
        slide_id=slide_id,
        category=category,
        severity=severity,  # type: ignore[arg-type]
        finding=finding,
        correction=correction,
        iteration=iteration,
    )
