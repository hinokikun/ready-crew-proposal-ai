import { expect, test } from "@playwright/test";
import type { Page, Route } from "@playwright/test";

const admin = "admin@example.com";

type Relationship = {
  relationship_id: string;
  from_id: string;
  to_id: string;
  relationship_type: "causality";
  authority: "AI_PROPOSED" | "USER_EXPLICIT";
  review_state: "UNCONFIRMED" | "CONFIRMED" | "CORRECTED" | "REJECTED";
  confirmation_authority: "USER_EXPLICIT" | null;
  inferred: boolean;
  provenance: string;
  original_relationship_id?: string;
};

function json(route: Route, body: unknown, status = 200) {
  return route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
}

function canonicalCandidate(id: string, value: string) {
  return {
    candidate_id: id,
    semantic_role: "root_cause",
    value,
    source_type: "product",
    source_field: "project_brief",
    source_reference: "Step1.project_brief",
    source_references: ["Step1.project_brief"],
    source_identities: [{ source_id: "product.step1.project_brief", source_field: "project_brief", source_reference: "Step1.project_brief" }],
    source_fingerprint: "a".repeat(64),
    authority: "USER_EXPLICIT",
    review_state: "CONFIRMED",
    confirmation_authority: "USER_EXPLICIT",
    inferred: true,
    acquisition_revision: "v1",
    original_candidate_id: id
  };
}

function proposalRelationship(id: string, from = "node-a", to = "node-b"): Relationship {
  return {
    relationship_id: id,
    from_id: from,
    to_id: to,
    relationship_type: "causality",
    authority: "AI_PROPOSED",
    review_state: "UNCONFIRMED",
    confirmation_authority: null,
    inferred: true,
    provenance: "M30 canonical proposal v1"
  };
}

function reviewedRelationship(proposal: Relationship, state: "CONFIRMED" | "CORRECTED" | "REJECTED", from = proposal.from_id, to = proposal.to_id): Relationship {
  return {
    ...proposal,
    relationship_id: state === "CORRECTED" ? `reviewed-${proposal.relationship_id}` : proposal.relationship_id,
    original_relationship_id: proposal.relationship_id,
    from_id: from,
    to_id: to,
    authority: state === "REJECTED" ? "AI_PROPOSED" : "USER_EXPLICIT",
    review_state: state,
    confirmation_authority: state === "REJECTED" ? null : "USER_EXPLICIT"
  };
}

async function installMocks(page: Page, options: { activeCanonical?: boolean; relationships?: Relationship[]; reviewState?: "CONFIRMED" | "CORRECTED" | "REJECTED" } = {}) {
  let canonicalReviewed = options.activeCanonical ?? false;
  let proposalCalls = 0;
  const proposalRequests: unknown[] = [];
  const reviewRequests: unknown[] = [];
  let holdProposal: (() => void) | null = null;
  let proposalPending = false;
  let holdReview: (() => void) | null = null;
  let reviewPending = false;
  const relationshipProposals = options.relationships ?? [proposalRelationship("relationship-a")];

  await page.addInitScript(() => {
    window.localStorage.clear();
    window.sessionStorage.clear();
    window.localStorage.setItem("ready-crew-guide-tutorial-seen-v1", "true");
    window.localStorage.setItem("ai-sales-secretary-pilot-checklist-v1-1", "true");
    window.localStorage.setItem("ai-sales-secretary-pilot-checklist-v1-2", "true");
  });

  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/api/auth/login")) {
      return json(route, { authenticated: true, token: "mock-admin-token", expires_in_seconds: 3600, login_mode: "admin", user: { id: 1, email: admin, role: "admin", is_active: true } });
    }
    if (path.endsWith("/api/auth/status")) return json(route, { user: { id: 1, email: admin, role: "admin", is_active: true } });
    if (path.endsWith("/api/organizations/context")) return json(route, { current: { organization_id: 1, organization_name: "Ready Crew", workspace_id: 101, workspace_name: "営業部", membership_role: "system_admin", user_id: 1, system_role: "admin", scope: "admin" }, available: [] });
    if (path.endsWith("/api/system/diagnostics")) return json(route, { overall_status: "ok", backend: { reachable: true }, database: { connected: true }, auth: { available: true }, openai: { enabled: true, configured: true }, beautiful_ai: { enabled: false, configured: false, mock: true } });
    if (path.endsWith("/api/beautiful-ai/status")) return json(route, { enabled: false, configured: false, mock: true, message: "disabled" });
    if (path.endsWith("/api/sales-assistant/status")) return json(route, { enabled: false, version: "50", requires_admin: true, persistence_enabled: false, external_ai_enabled: false, proposal_preview_enabled: false, proposal_export_enabled: false, beautiful_ai_export_enabled: false });
    if (path.endsWith("/api/analytics/events")) return json(route, { ok: true });
    if (path.endsWith("/api/pilot/status")) return json(route, { pilot: { pilot_mode: false, maintenance_mode: false, days_remaining: 0, notice: "" } });
    if (path.endsWith("/api/pilot/checklist-confirmed")) return json(route, { ok: true });
    if (path.endsWith("/api/pilot/dashboard")) return json(route, { dashboard: { summary: {}, issues: [], timeline: [] } });
    if (path.endsWith("/api/notifications")) return json(route, { notifications: [], summary: { unread: 0, high: 0, medium: 0, low: 0 } });
    if (path.endsWith("/api/feedback")) return json(route, { feedback: [], summary: { usable: 0, needs_revision: 0, hard_to_use: 0, comments: 0 } });
    if (path.includes("/api/presentation-review/projects")) return json(route, { reviews: [], revisions: [] });
    if (path.endsWith("/api/logs/creation-history")) return json(route, { history: [] });
    if (path.includes("/api/proposal-optimization/recommendations")) return json(route, { recommendations: [], dashboard: {}, note: "" });
    if (path.endsWith("/api/briefing/today")) return json(route, { briefing: { summary: {}, suggestions: [], timeline: [] } });
    if (path.endsWith("/api/workspace/conversations")) return json(route, { conversations: [] });
    if (path.endsWith("/api/projects")) return json(route, { projects: [] });
    if (path.endsWith("/api/quality-gates/")) return json(route, { gate: { completed: true, bypassed: false, download_unlocked: true } });
    if (path.endsWith("/api/analyze")) {
      return json(route, {
        markdown: "# 提案サマリー\n\n- 目的整理",
        powerpoint_generation_data: { deck_title: "検証提案", client_name: "株式会社サンプル", slides: [{ slide_no: 1, layout: "cover", title: "検証提案", bullets: ["目的整理"] }] },
        analysis: { project_summary: "検証案件", assumed_customer_issues: [], issue_priorities: [], win_probability: { rank: "B", probability: 60, label: "Bランク", reason: "確認済み", risk_score: 1, risk_label: "★☆☆☆☆", positive_factors: [], risk_factors: [], recommended_next_actions: [], improvement_actions: [], projected_probability_after_actions: 70 }, proposal_policy: "確認", proposal_story: "確認", proposal_structure: [], slide_scripts: [], expected_questions_and_answers: [], quality_check: { logical_consistency: "OK", typos: "OK", proposal_coverage: "OK", competitive_differentiation: "OK", alignment_with_customer_issues: "OK", human_review_notes: "確認してください" }, powerpoint_generation_data: { deck_title: "検証提案", client_name: "株式会社サンプル", slides: [{ slide_no: 1, layout: "cover", title: "検証提案", bullets: ["目的整理"] }] } }, human_review_required: true, human_review_reasons: ["確認してください"], generation_metadata: { schema_version: "e2e", persistence_enabled: false, pptx_enabled: false, beautiful_ai_enabled: false }, semantic_candidates: { candidates: [] }
      });
    }
    if (path.endsWith("/api/m30/canonical/proposals")) {
      canonicalReviewed = false;
      return json(route, { candidates: [canonicalCandidate("node-a", "根本原因の候補") , canonicalCandidate("node-b", "結果につながる状態")] });
    }
    if (path.endsWith("/api/m30/canonical/reviews")) {
      canonicalReviewed = true;
      const body = route.request().postDataJSON() as { original_candidate?: { candidate_id?: string } };
      const id = body.original_candidate?.candidate_id ?? "node-a";
      return json(route, { candidate: canonicalCandidate(id, id === "node-a" ? "根本原因の候補" : "結果につながる状態") });
    }
    if (path.endsWith("/api/m30/causality/proposals")) {
      proposalCalls += 1;
      proposalRequests.push(route.request().postDataJSON());
      if (proposalPending) await new Promise<void>((resolve) => { holdProposal = resolve; });
      return json(route, { relationships: relationshipProposals });
    }
    if (path.endsWith("/api/m30/causality/reviews")) {
      const body = route.request().postDataJSON() as { original_relationship?: Relationship; decision?: { action: "CONFIRM" | "CORRECT" | "REJECT"; corrected_from_id: string | null; corrected_to_id: string | null } };
      reviewRequests.push(body);
      if (reviewPending) await new Promise<void>((resolve) => { holdReview = resolve; });
      const original = body.original_relationship ?? relationshipProposals[0];
      const decision = body.decision ?? { action: "CONFIRM" as const, corrected_from_id: null, corrected_to_id: null };
      return json(route, { relationship: reviewedRelationship(original, decision.action === "CORRECT" ? "CORRECTED" : decision.action === "REJECT" ? "REJECTED" : "CONFIRMED", decision.corrected_from_id || original.from_id, decision.corrected_to_id || original.to_id) });
    }
    return json(route, {});
  });
  await page.route("**/health", async (route) => json(route, { status: "ok", db_connected: true }));

  return {
    get proposalCalls() { return proposalCalls; },
    proposalRequests,
    reviewRequests,
    setProposalPending(value: boolean) { proposalPending = value; },
    releaseProposal() { holdProposal?.(); holdProposal = null; },
    setReviewPending(value: boolean) { reviewPending = value; },
    releaseReview() { holdReview?.(); holdReview = null; },
    isCanonicalReviewed() { return canonicalReviewed; }
  };
}

async function openStep3(page: Page) {
  await page.goto("/");
  await page.getByTestId("login-mode-admin").click();
  await page.getByLabel("メールアドレス").fill(admin);
  await page.getByLabel("アクセスパスワード").fill("test-password");
  await page.getByTestId("login-submit").click();
  await expect(page.getByTestId("user-home-panel")).toBeVisible();
  const pilotConfirm = page.getByTestId("pilot-checklist-confirm");
  if (await pilotConfirm.isVisible().catch(() => false)) {
    await pilotConfirm.click();
    await expect(page.locator(".pilot-checklist-overlay")).toHaveCount(0);
  }
  const sidebarProposal = page.getByTestId("v80-sidebar").getByRole("button", { name: /提案書を作る/ });
  if (!(await sidebarProposal.isVisible().catch(() => false))) {
    const mobileMenu = page.locator(".v80-mobile-menu-button");
    if (await mobileMenu.isVisible().catch(() => false)) await mobileMenu.click();
  }
  await sidebarProposal.click();
  await expect(page.getByTestId("guided-flow")).toBeVisible();
  await page.getByTestId("project-source-input").fill("業務改善の確認案件です。");
  await page.getByRole("button", { name: "AIで提案書を作成" }).click();
  await expect(page.getByRole("button", { name: "内容を確認しました。提出前チェックへ進む" })).toBeVisible({ timeout: 25_000 });
}

async function activateCanonicalNodes(page: Page) {
  const canonical = page.getByTestId("m30-canonical-review");
  await canonical.getByRole("button", { name: "AI候補を確認する" }).click();
  await expect(canonical.getByText("根本原因の候補")).toBeVisible();
  const cards = canonical.locator(".guided-semantic-card");
  for (let index = 0; index < 2; index += 1) {
    await cards.nth(index).getByRole("button", { name: "この内容で確定" }).click();
  }
}

test.describe("M30 C3B relationship review contract", () => {
  test("no active canonical nodes does not call proposal and does not block normal flow", async ({ page }) => {
    const mock = await installMocks(page);
    await openStep3(page);
    const panel = page.getByTestId("m30-relationship-review");
    await expect(panel.getByText("先に上の追加確認で、因果関係に使う項目を確認してください。")).toBeVisible();
    await expect(panel.getByRole("button", { name: "因果関係の候補を確認する" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "内容を確認しました。提出前チェックへ進む" })).toBeEnabled();
    expect(mock.proposalCalls).toBe(0);
  });

  test("proposal is explicit, single-shot, and loading disables the CTA", async ({ page }) => {
    const mock = await installMocks(page);
    await openStep3(page);
    await activateCanonicalNodes(page);
    const panel = page.getByTestId("m30-relationship-review");
    const cta = panel.getByRole("button", { name: /因果関係の候補を確認する|候補を取得中/ });
    await expect(cta).toBeVisible();
    expect(mock.proposalCalls).toBe(0);
    mock.setProposalPending(true);
    await cta.click();
    await expect(cta).toBeDisabled();
    await expect.poll(() => mock.proposalCalls).toBe(1);
    await cta.click({ force: true });
    expect(mock.proposalCalls).toBe(1);
    mock.releaseProposal();
    await expect(panel.getByText("根本原因の候補")).toBeVisible();
  });

  test("confirm sends null correction endpoints and commits only after the response", async ({ page }) => {
    const mock = await installMocks(page);
    await openStep3(page);
    await activateCanonicalNodes(page);
    const panel = page.getByTestId("m30-relationship-review");
    await panel.getByRole("button", { name: "因果関係の候補を確認する" }).click();
    const card = panel.locator(".guided-semantic-card").first();
    await card.getByRole("button", { name: "この関係を確認" }).click();
    await expect.poll(() => mock.reviewRequests.length).toBe(1);
    const request = mock.reviewRequests[0] as { decision: { action: string; corrected_from_id: string | null; corrected_to_id: string | null }; original_relationship: Relationship };
    expect(request.decision).toEqual({ original_relationship_id: "relationship-a", action: "CONFIRM", corrected_from_id: null, corrected_to_id: null });
    expect(request.original_relationship.relationship_id).toBe("relationship-a");
    await expect(card.getByText("確認済み")).toBeVisible();
    await expect(card.getByRole("button", { name: "この関係を確認" })).toHaveCount(0);
  });

  test("confirm does not commit before the review response", async ({ page }) => {
    const mock = await installMocks(page);
    await openStep3(page);
    await activateCanonicalNodes(page);
    const panel = page.getByTestId("m30-relationship-review");
    await panel.getByRole("button", { name: "因果関係の候補を確認する" }).click();
    const card = panel.locator(".guided-semantic-card").first();
    mock.setReviewPending(true);
    await card.getByRole("button", { name: "この関係を確認" }).click();
    await expect.poll(() => mock.reviewRequests.length).toBe(1);
    await expect(card.getByText("確認済み")).toHaveCount(0);
    await expect(card.getByText("未確認")).toBeVisible();
    mock.releaseReview();
    await expect(card.getByText("確認済み")).toBeVisible();
  });

  test("reviewed relationship cannot be submitted again", async ({ page }) => {
    const mock = await installMocks(page);
    await openStep3(page);
    await activateCanonicalNodes(page);
    const panel = page.getByTestId("m30-relationship-review");
    await panel.getByRole("button", { name: "因果関係の候補を確認する" }).click();
    const card = panel.locator(".guided-semantic-card").first();
    await card.getByRole("button", { name: "この関係を確認" }).click();
    await expect(card.getByText("確認済み")).toBeVisible();
    expect(mock.reviewRequests).toHaveLength(1);
    await expect(card.getByRole("button", { name: /関係を確認|関係を修正|関係を使わない/ })).toHaveCount(0);
    expect(mock.reviewRequests).toHaveLength(1);
  });

  test("correct uses active node IDs and keeps causality identity", async ({ page }) => {
    const mock = await installMocks(page);
    await openStep3(page);
    await activateCanonicalNodes(page);
    const panel = page.getByTestId("m30-relationship-review");
    await panel.getByRole("button", { name: "因果関係の候補を確認する" }).click();
    const card = panel.locator(".guided-semantic-card").first();
    await card.getByRole("button", { name: "関係を修正" }).click();
    await card.locator("select").nth(0).selectOption("node-b");
    await card.locator("select").nth(1).selectOption("node-a");
    await card.getByRole("button", { name: "修正内容を確定" }).click();
    const request = mock.reviewRequests[0] as { decision: { action: string; corrected_from_id: string | null; corrected_to_id: string | null }; original_relationship: Relationship };
    expect(request.decision).toEqual({ original_relationship_id: "relationship-a", action: "CORRECT", corrected_from_id: "node-b", corrected_to_id: "node-a" });
    expect(request.original_relationship.relationship_type).toBe("causality");
    expect((request as { relationship_id?: string }).relationship_id).toBeUndefined();
    await expect(card.getByText("修正済み")).toBeVisible();
  });

  test("reject is retained as audit-only and cannot be resubmitted", async ({ page }) => {
    const mock = await installMocks(page);
    await openStep3(page);
    await activateCanonicalNodes(page);
    const panel = page.getByTestId("m30-relationship-review");
    await panel.getByRole("button", { name: "因果関係の候補を確認する" }).click();
    const card = panel.locator(".guided-semantic-card").first();
    await card.getByRole("button", { name: "この関係を使わない" }).click();
    const request = mock.reviewRequests[0] as { decision: { action: string; corrected_from_id: string | null; corrected_to_id: string | null } };
    expect(request.decision).toEqual({ original_relationship_id: "relationship-a", action: "REJECT", corrected_from_id: null, corrected_to_id: null });
    await expect(card.getByText("使用しない")).toBeVisible();
    await expect(card.getByRole("button", { name: /関係を確認|関係を修正|関係を使わない/ })).toHaveCount(0);
  });

  test("unresolved endpoints are safe and non-destructive", async ({ page }) => {
    const unresolved = proposalRelationship("relationship-unresolved", "missing-node", "node-b");
    await installMocks(page, { relationships: [unresolved] });
    await openStep3(page);
    await activateCanonicalNodes(page);
    await page.getByTestId("m30-relationship-review").getByRole("button", { name: "因果関係の候補を確認する" }).click();
    const panel = page.getByTestId("m30-relationship-review");
    const card = panel.locator(".guided-semantic-card").first();
    await expect(card.getByText("この関係の項目を確認できないため、表示できません。")).toBeVisible();
    await expect(card.getByRole("button", { name: /関係を確認|関係を修正|関係を使わない/ })).toHaveCount(0);
  });

  test("relationship identity follows IDs when display order differs", async ({ page }) => {
    const relationships = [
      proposalRelationship("relationship-z", "node-a", "node-b"),
      proposalRelationship("relationship-a", "node-b", "node-a")
    ];
    const mock = await installMocks(page, { relationships });
    await openStep3(page);
    await activateCanonicalNodes(page);
    const panel = page.getByTestId("m30-relationship-review");
    await panel.getByRole("button", { name: "因果関係の候補を確認する" }).click();
    const second = panel.locator(".guided-semantic-card").nth(1);
    await second.getByRole("button", { name: "この関係を確認" }).click();
    const request = mock.reviewRequests[0] as { original_relationship: Relationship; decision: { original_relationship_id: string } };
    expect(request.original_relationship.relationship_id).toBe("relationship-a");
    expect(request.decision.original_relationship_id).toBe("relationship-a");
  });
});
