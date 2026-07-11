import { expect, test } from "@playwright/test";
import type { Page, Route } from "@playwright/test";

const adminEmail = "admin@example.com";
const memberEmail = "member@example.com";

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.clear();
    window.localStorage.setItem("ready-crew-guide-tutorial-seen-v1", "true");
    window.localStorage.setItem("ai-sales-secretary-pilot-checklist-v1-1", "true");
    window.localStorage.setItem("ai-sales-secretary-pilot-checklist-v1-2", "true");
  });
  page.on("pageerror", (error) => {
    console.log(`Page error: ${error.message}`);
  });
  page.on("console", (message) => {
    if (message.type() === "error") {
      console.log(`Console error: ${message.text()}`);
    }
  });
  await mockApi(page);
});

test("ログイン画面が表示される", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /AI Workspace|AI営業秘書/ })).toBeVisible();
  await expect(page.getByLabel("アクセスパスワード")).toBeVisible();
});

test("ログイン後にDashboardが表示される", async ({ page }) => {
  await login(page, memberEmail);
  await expect(page.getByRole("heading", { name: "営業AIオペレーションセンター" })).toBeVisible();
  await expect(page.getByText("まだ案件がありません。案件メールを貼り付けて開始してください。")).toBeVisible();
});

test("案件入力欄へ入力できる", async ({ page }) => {
  await login(page, memberEmail);
  const input = page.getByTestId("project-source-input");
  await input.waitFor({ state: "visible" });
  await setTextareaValue(page, "project-source-input", "株式会社サンプル様。Webサイトリニューアルの相談。予算300万円、納期3か月。");
  await expect(input).toHaveValue(/株式会社サンプル/);
});

test("Maintenance中の503メッセージを表示できる", async ({ page }) => {
  await mockApi(page, { analyzeError: "maintenance" });
  await login(page, memberEmail);
  await page.getByRole("button", { name: "まずはサンプルで体験" }).click();
  await expect(page.getByLabel("AIウィザード").getByText("現在、新規作成は一時停止中です")).toBeVisible({ timeout: 25000 });
});

test("Rate Limitの429メッセージを表示できる", async ({ page }) => {
  await mockApi(page, { analyzeError: "rate" });
  await login(page, memberEmail);
  await page.getByRole("button", { name: "まずはサンプルで体験" }).click();
  await expect(page.getByLabel("AIウィザード").getByText("AI APIの利用上限に達した可能性があります")).toBeVisible({ timeout: 25000 });
});

test("推定値やデモ値はラベルで誤認を防ぐ", async ({ page }) => {
  await mockApi(page, { hasUsageData: true });
  await login(page, adminEmail);
  await expect(page.getByText(/推定|デモ表示/).first()).toBeVisible();
});

test("memberに管理者メニューが表示されない", async ({ page }) => {
  await login(page, memberEmail);
  await expect(page.getByText("管理者メニュー・接続状態を開く")).toHaveCount(0);
  await expect(page.getByText("Prompt Studioを開く")).toHaveCount(0);
});

test("adminに管理者メニューが表示される", async ({ page }) => {
  await login(page, adminEmail);
  await expect(page.getByTestId("admin-menu")).toBeVisible();
});

test("Sales CopilotのQuick Commandが対象画面へ移動する", async ({ page }) => {
  await login(page, adminEmail);
  await page.getByTestId("copilot-command-Analytics").waitFor({ state: "visible" });
  await clickByTestId(page, "copilot-command-Analytics");
  await expect(page.locator("#admin-product-analytics-panel")).toBeVisible();
});

test("存在しないページでアプリ全体が落ちない", async ({ page }) => {
  await page.goto("/not-found-for-e2e");
  await expect(page.locator("body")).toBeVisible();
});

test("adminがPilot Dashboardを開きIssue登録できる", async ({ page }) => {
  await login(page, adminEmail);
  await openAdminPilotDashboard(page);
  await expect(page.getByTestId("pilot-dashboard-panel")).toBeVisible();
  await page.getByTestId("pilot-issue-title").fill("要約PPTの確認課題");
  await page.getByTestId("pilot-issue-create").click();
  await expect(page.getByText("Issueを登録しました。")).toBeVisible();
});

test("adminがMaintenance警告と終了判定を確認できる", async ({ page }) => {
  await login(page, adminEmail);
  await openAdminPilotDashboard(page);
  await expect(page.getByTestId("pilot-judgment-result")).toBeVisible();
  await page.getByTestId("pilot-maintenance-enable").click();
  await expect(page.getByText("Maintenance Modeを有効化しました。")).toBeVisible();
});

test("Pilot終了レポートをコピーできる", async ({ page, context }) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await login(page, adminEmail);
  await openAdminPilotDashboard(page);
  await page.getByRole("button", { name: "Pilot終了レポートを作成" }).click();
  await expect(page.getByText("Pilot終了レポート", { exact: true })).toBeVisible();
  await page.getByTestId("pilot-report-copy").click();
  await expect(page.getByText("レポートをコピーしました。")).toBeVisible();
});

test("Beautiful.ai未設定時は既存PPTXの導線を残す", async ({ page }) => {
  await mockApi(page, { beautifulEnabled: false });
  await login(page, memberEmail);
  await page.getByRole("button", { name: "まずはサンプルで体験" }).click();
  await scrollToOutputs(page);
  const wizard = page.getByLabel("AIウィザード");
  await expect(wizard.getByText("Beautiful.ai連携は未設定です。")).toBeVisible({ timeout: 25000 });
  await expect(wizard.getByRole("button", { name: /要約PPTをダウンロード/ })).toBeVisible();
});

test("Beautiful.ai作成後に編集と表示リンクが出る", async ({ page }) => {
  await login(page, memberEmail);
  await page.getByRole("button", { name: "まずはサンプルで体験" }).click();
  await scrollToOutputs(page);
  const wizard = page.getByLabel("AIウィザード");
  const button = wizard.getByRole("button", { name: /Beautiful.aiで提案書を作成/ });
  await expect(button).toBeEnabled({ timeout: 25000 });
  await button.click();
  await expect(wizard.getByText("Beautiful.ai提案書を作成しました")).toBeVisible();
  await expect(wizard.getByRole("button", { name: "Beautiful.aiで編集" })).toBeVisible();
  await expect(wizard.getByRole("button", { name: "プレゼンテーションを表示" })).toBeVisible();
});

test("Beautiful.ai利用上限時も既存PPTXを利用できる", async ({ page }) => {
  await mockApi(page, { beautifulError: 429 });
  await login(page, memberEmail);
  await page.getByRole("button", { name: "まずはサンプルで体験" }).click();
  await scrollToOutputs(page);
  const wizard = page.getByLabel("AIウィザード");
  const button = wizard.getByRole("button", { name: /Beautiful.aiで提案書を作成/ });
  await expect(button).toBeEnabled({ timeout: 25000 });
  await button.click();
  await expect(wizard.getByText("Beautiful.aiの利用上限に達しました", { exact: true })).toBeVisible();
  await expect(wizard.getByRole("button", { name: /要約PPTをダウンロード/ })).toBeVisible();
});

test("品質ゲート未完了ではBeautiful.ai作成ボタンを押せない", async ({ page }) => {
  await mockApi(page, { qualityGateComplete: false });
  await login(page, memberEmail);
  await page.getByRole("button", { name: "まずはサンプルで体験" }).click();
  await scrollToOutputs(page);
  await expect(page.getByLabel("AIウィザード").getByRole("button", { name: /Beautiful.aiで提案書を作成/ })).toBeDisabled({ timeout: 25000 });
});

test("Beautiful.ai Status CardでEnabledとMockを確認できる", async ({ page }) => {
  await login(page, memberEmail);
  const card = page.getByTestId("beautiful-ai-status-card");
  await expect(card).toBeVisible();
  await expect(card.getByText("Enabled")).toBeVisible();
  await expect(card.getByText("有効")).toBeVisible();
  await expect(card.getByText("Mock")).toBeVisible();
  await expect(card.getByText("ON", { exact: true })).toBeVisible();
  await expect(card.getByText("API reachable")).toBeVisible();
  await expect(card.getByText("到達")).toBeVisible();
  await expect(card.getByText("Route found")).toBeVisible();
  await expect(card.getByText("検出")).toBeVisible();
});

test("Beautiful.ai Disabled時も状態と無効ボタンを確認できる", async ({ page }) => {
  await mockApi(page, { beautifulStatus: "disabled", beautifulEnabled: false });
  await login(page, memberEmail);
  await expect(page.getByTestId("beautiful-ai-status-card").getByText("無効")).toBeVisible();
  await page.locator(".wizard-sample-experience .primary-button").click();
  await scrollToOutputs(page);
  await expect(page.getByTestId("beautiful-ai-create-button").first()).toBeDisabled({ timeout: 25000 });
  await expect(page.getByText("Beautiful.ai連携は未設定です。").first()).toBeVisible();
});

test("Beautiful.ai statusが404の場合はUIでRender未反映を確認できる", async ({ page }) => {
  await mockApi(page, { beautifulStatus: "not_found" });
  await login(page, memberEmail);
  const card = page.getByTestId("beautiful-ai-status-card");
  await expect(card.getByText("Route found")).toBeVisible();
  await expect(card.getByText("未検出")).toBeVisible();
  await expect(card.getByText(/Beautiful.ai APIルートが見つかりません/)).toBeVisible();
});

test("FrontendとBackendのバージョン不一致を検出できる", async ({ page }) => {
  await mockApi(page, { backendCommit: "different-backend-commit" });
  await login(page, memberEmail);
  await expect(page.getByTestId("beautiful-ai-status-card").getByText(/FrontendとBackendのバージョンが一致していません/)).toBeVisible();
});

async function login(page: Page, email: string) {
  await page.goto("/");
  await page.getByLabel("メールアドレス").fill(email);
  await page.getByLabel("アクセスパスワード").fill("test-password");
  await page.getByRole("button", { name: "ログイン" }).click();
  await expect(page.getByRole("heading", { name: "営業AIオペレーションセンター" })).toBeVisible();
  const pilotConfirm = page.getByRole("button", { name: "確認して開始する" });
  if (await pilotConfirm.waitFor({ state: "visible", timeout: 1500 }).then(() => true).catch(() => false)) {
    await pilotConfirm.click();
  }
  await expect(page.getByTestId("sales-copilot")).toBeVisible();
}

async function openAdminPilotDashboard(page: Page) {
  await page.locator("#admin-menu-panel").evaluate((element) => {
    (element as HTMLDetailsElement).open = true;
  });
  await page.locator("#admin-pilot-dashboard-panel").evaluate((element) => {
    (element as HTMLDetailsElement).open = true;
  });
  await page.getByTestId("pilot-dashboard-panel").waitFor({ state: "visible" });
  await page.getByTestId("pilot-dashboard-panel").evaluate((element) => {
    element.querySelectorAll("details").forEach((details) => {
      (details as HTMLDetailsElement).open = true;
    });
  });
}

async function setTextareaValue(page: Page, testId: string, value: string) {
  await page.evaluate(
    ({ testId: id, value: nextValue }) => {
      const element = document.querySelector(`[data-testid="${id}"]`) as HTMLTextAreaElement | null;
      if (!element) throw new Error(`Missing textarea: ${id}`);
      const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value")?.set;
      setter?.call(element, nextValue);
      element.dispatchEvent(new Event("input", { bubbles: true }));
    },
    { testId, value }
  );
}

async function clickByTestId(page: Page, testId: string) {
  await page.evaluate((id) => {
    const element = document.querySelector(`[data-testid="${id}"]`) as HTMLButtonElement | null;
    if (!element) throw new Error(`Missing button: ${id}`);
    element.click();
  }, testId);
}

async function scrollToOutputs(page: Page) {
  const summaryButton = page.getByLabel("AIウィザード").getByRole("button", { name: /要約PPTをダウンロード/ });
  await summaryButton.waitFor({ state: "visible", timeout: 25000 });
  await summaryButton.scrollIntoViewIfNeeded();
  await page.mouse.wheel(0, 500);
}

type MockOptions = {
  analyzeError?: "maintenance" | "rate";
  hasUsageData?: boolean;
  beautifulEnabled?: boolean;
  beautifulStatus?: "enabled" | "disabled" | "mock" | "not_found" | "unauthorized" | "forbidden" | "server_error";
  beautifulError?: 403 | 429;
  qualityGateComplete?: boolean;
  backendCommit?: string;
};

async function mockApi(page: Page, options: MockOptions = {}) {
  await page.route("**/health", async (route) =>
    json(route, {
      status: "ok",
      ai_api: "mock",
      mock_mode: true,
      db_connected: true,
      db_type: "sqlite",
      db_tables_count: 0,
      auth_configured: true,
      pptx: "available",
      pdf: "available",
      app_version: "17.3-e2e",
      git: {
        commit: options.backendCommit ?? "e2e-frontend-commit",
        commit_short: (options.backendCommit ?? "e2e-frontend-commit").slice(0, 7),
        branch: "main"
      },
      routes: {
        beautiful_ai_status: "/api/beautiful-ai/status",
        beautiful_ai_status_registered: options.beautifulStatus !== "not_found"
      },
      beautiful_ai: {
        enabled: options.beautifulEnabled ?? options.beautifulStatus !== "disabled",
        configured: options.beautifulEnabled ?? options.beautifulStatus !== "disabled",
        mock: true,
        route_registered: options.beautifulStatus !== "not_found"
      }
    })
  );

  await page.route("**/api/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    if (path.endsWith("/api/analyze") && options.analyzeError === "maintenance") {
      return json(
        route,
        {
          error_type: "maintenance_mode",
          message: "現在メンテナンス中のため、新規作成を停止しています。",
          request_id: "e2e-maintenance"
        },
        503
      );
    }
    if (path.endsWith("/api/analyze") && options.analyzeError === "rate") {
      return json(
        route,
        {
          error_type: "rate_limit",
          message: "短時間に操作が集中しています。少し時間を置いてから再実行してください。",
          request_id: "e2e-rate",
          retry_after_seconds: 30
        },
        429
      );
    }
    if (path.endsWith("/api/analyze")) {
      return json(route, proposalResponse());
    }
    if (path.endsWith("/api/beautiful-ai/status")) {
      return beautifulStatusJson(route, options);
    }
    if (path.includes("/api/beautiful-ai/presentations") && options.beautifulError === 403) {
      return json(
        route,
        {
          detail: {
            error_type: "beautiful_ai_forbidden",
            message: "Beautiful.ai APIの利用権限が有効になっていません",
            fallback_available: true
          }
        },
        403
      );
    }
    if (path.includes("/api/beautiful-ai/presentations") && options.beautifulError === 429) {
      return json(
        route,
        {
          detail: {
            error_type: "beautiful_ai_rate_limit",
            message: "Beautiful.aiの利用上限に達しました。時間を置くか既存PPTXをご利用ください",
            fallback_available: true
          }
        },
        429
      );
    }
    if (path.endsWith("/api/auth/login")) {
      let body: { email?: string } = {};
      try {
        body = route.request().postDataJSON() as { email?: string };
      } catch {
        body = {};
      }
      const role = body.email === adminEmail ? "admin" : "member";
      return json(route, {
        authenticated: true,
        token: `${role}-token`,
        expires_in_seconds: 3600,
        message: "ok",
        user: { id: role === "admin" ? 1 : 2, email: body.email || memberEmail, role, is_active: true }
      });
    }
    if (path.endsWith("/api/auth/status")) {
      const token = route.request().headers().authorization || "";
      const role = token.includes("admin") ? "admin" : "member";
      return json(route, {
        user: { id: role === "admin" ? 1 : 2, email: role === "admin" ? adminEmail : memberEmail, role, is_active: true }
      });
    }
    return json(route, mockResponse(path, options));
  });
}

function json(route: Route, body: unknown, status = 200) {
  return route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body)
  });
}

function beautifulStatusJson(route: Route, options: MockOptions) {
  if (options.beautifulStatus === "not_found") {
    return json(route, { detail: "Not Found" }, 404);
  }
  if (options.beautifulStatus === "unauthorized") {
    return json(route, { detail: "Unauthorized" }, 401);
  }
  if (options.beautifulStatus === "forbidden") {
    return json(route, { detail: "Forbidden" }, 403);
  }
  if (options.beautifulStatus === "server_error") {
    return json(route, { detail: "Internal Server Error" }, 500);
  }
  const enabled = options.beautifulEnabled ?? options.beautifulStatus !== "disabled";
  return json(route, {
    enabled,
    configured: enabled,
    mock: true,
    provider: "beautiful.ai",
    message: enabled ? "Beautiful.ai連携は利用可能です。" : "Beautiful.ai連携は未設定です。"
  });
}

function mockResponse(path: string, options: MockOptions = {}) {
  if (path.includes("/beautiful-ai/status")) {
    const enabled = options.beautifulEnabled ?? true;
    return {
      enabled,
      configured: enabled,
      mock: true,
      provider: "beautiful.ai",
      message: enabled ? "Beautiful.ai連携は利用可能です。" : "Beautiful.ai連携は未設定です。"
    };
  }
  if (path.includes("/beautiful-ai/presentations") && path.includes("/editor-opened")) return { ok: true };
  if (path.includes("/beautiful-ai/presentations")) {
    if (options.beautifulError === 403) {
      return {
        detail: {
          error_type: "beautiful_ai_forbidden",
          message: "Beautiful.ai APIの利用権限が有効になっていません",
          fallback_available: true
        }
      };
    }
    if (options.beautifulError === 429) {
      return {
        detail: {
          error_type: "beautiful_ai_rate_limit",
          message: "Beautiful.aiの利用上限に達しました。時間を置くか既存PPTXをご利用ください",
          fallback_available: true
        }
      };
    }
    return {
      presentation_id: "mock-beautiful-e2e",
      status: "mock",
      title: "Beautiful.ai mock proposal",
      editor_url: "https://www.beautiful.ai/editor/mock-beautiful-e2e",
      player_url: "https://www.beautiful.ai/player/mock-beautiful-e2e",
      created_at: new Date().toISOString(),
      provider: "beautiful.ai",
      fallback_available: true
    };
  }
  if (path.includes("/projects/crm")) return { customers: [], projects: [] };
  if (path.includes("/logs/usage-dashboard")) {
    return {
      dashboard: {
        summary: {
          total_usage: options.hasUsageData ? 3 : 0,
          today_usage: options.hasUsageData ? 1 : 0,
          week_usage: options.hasUsageData ? 3 : 0,
          proposal_generation: options.hasUsageData ? 1 : 0,
          ppt_download: options.hasUsageData ? 1 : 0,
          error_count: 0,
          feedback_count: 0
        },
        error_analysis: { api_limit: 0, backend_unreachable: 0, input_missing: 0, ppt_generation_failed: 0, auth_error: 0 },
        users: [],
        features: [],
        feedback_summary: { usable: 0, needs_revision: 0, hard_to_use: 0, comments: 0 }
      }
    };
  }
  if (path.includes("/logs/audit")) return { logs: [] };
  if (path.includes("/logs")) return { logs: [] };
  if (path.includes("/releases")) return { releases: [] };
  if (path.includes("/users")) return { users: [] };
  if (path.includes("/pilot/issues/from-feedback")) {
    return {
      issue: pilotIssue(),
      duplicate_candidates: []
    };
  }
  if (path.includes("/pilot/issues")) {
    return { issue: pilotIssue(), issues: [pilotIssue()] };
  }
  if (path.includes("/pilot/maintenance")) {
    return { maintenance: { env_enabled: false, runtime_enabled: true, effective: true, reason: "重大障害候補の確認中", updated_at: new Date().toISOString(), updated_by: 1 } };
  }
  if (path.includes("/pilot/end")) return { report: pilotReport() };
  if (path.includes("/pilot/dashboard")) return { dashboard: pilotDashboard() };
  if (path.includes("/pilot/status")) {
    return {
      pilot: {
        pilot_mode: true,
        maintenance_mode: false,
        pilot_start_date: "2026-07-01",
        pilot_end_date: "2026-07-15",
        pilot_max_users: 5,
        days_remaining: 4,
        notice: "社内試験利用中です。"
      }
    };
  }
  if (path.includes("/feedback")) return { feedback: [], summary: { usable: 0, needs_revision: 0, hard_to_use: 0, comments: 0 } };
  if (path.includes("/notifications")) return { notifications: [], summary: { unread: 0, high: 0, medium: 0, low: 0 }, analytics: { total: 0, read_rate: 0, actioned_rate: 0, ignored_rate: 0 } };
  if (path.includes("/knowledge/entries")) return { entries: [] };
  if (path.includes("/knowledge/templates")) return { templates: [] };
  if (path.includes("/knowledge/best-practices")) {
    return {
      best_practices: {
        winning_structures: [],
        frequent_proposals: [],
        industry_success_examples: []
      }
    };
  }
  if (path.includes("/learning/dashboard")) return { dashboard: emptyLearningDashboard() };
  if (path.includes("/prompts/dashboard")) return { dashboard: emptyPromptStudioDashboard() };
  if (path.includes("/integrations/settings")) return { settings: [] };
  if (path.includes("/integrations/candidates")) return { candidates: [] };
  if (path.includes("/integrations/readiness")) return { readiness: [] };
  if (path.includes("/integrations/dry-run/logs")) return { logs: [] };
  if (path.includes("/integrations")) return { ok: true };
  if (path.includes("/briefing")) {
    return {
      briefing: {
        generated_at: new Date().toISOString(),
        summary: { action_required_count: 0, review_waiting: 0, changes_requested: 0, due_soon: 0, expected_wins: 0, stagnant: 0 },
        suggestions: [],
        timeline: [],
        recommended_project: null,
        agent_comments: []
      }
    };
  }
  if (path.includes("/quality-gates")) {
    const complete = options.qualityGateComplete ?? true;
    return {
      gate: complete
        ? { project_id: "e2e", checklist_items: ["company", "budget"], completed: true, bypassed: false, download_unlocked: true }
        : { project_id: "e2e", checklist_items: [], completed: false, bypassed: false, download_unlocked: false }
    };
  }
  if (path.includes("/reviews")) return { reviews: [], review: null, revisions: [] };
  if (path.includes("/orchestrator/queue")) return { queue: [] };
  if (path.includes("/orchestrator/analytics")) {
    return {
      orchestrator: {
        average_processing_seconds: 0,
        retry_rate: 0,
        autonomous_completion_rate: 0,
        human_intervention_rate: 0,
        agent_durations: []
      }
    };
  }
  if (path.includes("/analytics/release-notes")) return { release_notes: [] };
  if (path.includes("/analytics")) return { dashboard: emptyProductAnalyticsDashboard(), notes: [] };
  return { ok: true };
}

function proposalResponse() {
  const powerpoint_generation_data = {
    deck_title: "株式会社サンプル不動産 Webサイト制作ご提案書",
    client_name: "株式会社サンプル不動産",
    slides: [
      {
        slide_no: 1,
        layout: "cover",
        title: "Webサイト制作ご提案",
        bullets: ["問い合わせ増加", "SEO改善", "CMS運用改善"],
        speaker_notes: "提案概要を説明します。",
        visual_suggestion: "clean corporate cover"
      },
      {
        slide_no: 2,
        layout: "summary",
        title: "提案サマリー",
        bullets: ["問い合わせ導線を改善", "物件情報を整理", "更新しやすいCMSを構築"],
        speaker_notes: "主要提案を説明します。",
        visual_suggestion: "three value cards"
      }
    ]
  };
  return {
    markdown: "# 提案サマリー\n\n- 問い合わせ導線を改善します\n- SEOとCMS運用を強化します",
    powerpoint_generation_data,
    analysis: {
      project_summary: "Webサイトリニューアル案件",
      assumed_customer_issues: [],
      issue_priorities: [],
      win_probability: {
        rank: "B",
        probability: 60,
        label: "Bランク",
        reason: "予算と目的が整理されています。",
        risk_score: 3,
        risk_label: "★★★☆☆",
        positive_factors: ["目的が明確"],
        risk_factors: ["納期確認が必要"],
        recommended_next_actions: ["予算と納期を確認"],
        improvement_actions: ["決裁者確認"],
        projected_probability_after_actions: 75
      },
      proposal_policy: "問い合わせ増加を軸に提案します。",
      proposal_story: "現状課題から導線改善へつなげます。",
      proposal_structure: [],
      slide_scripts: [],
      expected_questions_and_answers: [],
      quality_check: {
        logical_consistency: "OK",
        typos: "OK",
        proposal_coverage: "OK",
        competitive_differentiation: "OK",
        alignment_with_customer_issues: "OK",
        human_review_notes: "提出前に人が確認してください。"
      },
      powerpoint_generation_data
    }
  };
}

function pilotIssue() {
  return {
    id: 1,
    issue_id: "PILOT-TEST01",
    category: "PPT/PDF",
    severity: "high",
    title: "要約PPTの確認課題",
    summary: "要約PPTの生成確認が必要です。",
    reproduction_steps: "要約PPTを押す",
    status: "reported",
    reported_by: 1,
    reported_by_email: adminEmail,
    assigned_to: "",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    resolved_at: null,
    resolution_note: ""
  };
}

function pilotDashboard() {
  return {
    status: {
      pilot_mode: true,
      maintenance_mode: false,
      pilot_start_date: "2026-07-01",
      pilot_end_date: "2026-07-15",
      pilot_max_users: 5,
      days_remaining: 4,
      notice: "社内試験利用中です。"
    },
    summary: {
      enabled_users: 5,
      started_users: 4,
      active_this_week: 4,
      usage_rate: 80,
      proposal_count: 5,
      proposal_generations: 5,
      downloads: 3,
      success_rate: 100,
      error_count: 0,
      feedback_count: 2,
      feedback_average: 4.5,
      critical_issue_count: 0,
      unresolved_issue_count: 1,
      issue_count: 1,
      average_processing_ms: 1200,
      unused_users: 1,
      max_users: 5,
      days_remaining: 4,
      days_to_end: 4
    },
    users: [],
    unused_users: [],
    success_criteria: [
      { key: "usage", label: "対象者の80%以上が利用", value: 80, target: 80, met: true, unit: "%" },
      { key: "proposal_success", label: "提案書作成成功率90%以上", value: 100, target: 90, met: true, unit: "%" }
    ],
    feedback_metrics: {
      average_usability: 4.5,
      practical_usability_rate: 100,
      time_saved_rate: 100,
      continue_intent_rate: 100,
      score_count: 2
    },
    issues: [pilotIssue()],
    incidents: [{ key: "proposal_failures", severity: "high", title: "重大障害候補", detail: "テスト用の警告です。" }],
    judgment: {
      result: "条件付き合格",
      criteria: [
        { key: "usage", label: "対象者の80%以上が利用", value: 80, target: 80, met: true, unit: "%" }
      ],
      reasons: ["未解決Issueを確認してください。"],
      feedback_metrics: {
        average_usability: 4.5,
        practical_usability_rate: 100,
        time_saved_rate: 100,
        continue_intent_rate: 100,
        score_count: 2
      }
    },
    maintenance: {
      env_enabled: false,
      runtime_enabled: false,
      effective: false,
      reason: "",
      updated_at: "",
      updated_by: null
    },
    recent_feedback: [
      {
        id: 1,
        rating: "usable",
        comment_summary: "操作は分かりやすい",
        feature_name: "pilot",
        user_role: "member",
        created_at: new Date().toISOString()
      }
    ],
    retention_preview: {
      pilot_events: 5,
      pilot_feedback: 2,
      pilot_users: 5,
      pilot_issues: 1,
      production_projects: 0,
      knowledge_entries: 0,
      audit_logs: 0
    }
  };
}

function pilotReport() {
  return {
    dashboard: pilotDashboard(),
    feedback_summary: { usable: 2, needs_revision: 0, hard_to_use: 0, comments: 2 },
    next_improvements: ["未解決Issueを確認する"],
    issues: [pilotIssue()],
    resolved_issues: [],
    unresolved_issues: [pilotIssue()],
    judgment: pilotDashboard().judgment,
    markdown: "# AI営業秘書 Pilot 終了レポート\n\n- Pilot終了判定: 条件付き合格\n"
  };
}

function emptyProductAnalyticsDashboard() {
  return {
    summary: {
      total_sessions: 0,
      total_events: 0,
      total_errors: 0,
      average_session_seconds: 0
    },
    funnel: [],
    sessions: [],
    errors: [],
    feature_usage: [],
    improvement_candidates: []
  };
}

function emptyLearningDashboard() {
  return {
    run: null,
    improvements: [],
    release_candidate: { version: "未作成", summary: "Learningデータはまだありません。" },
    analytics: {
      learning_runs: 0,
      improvement_adoption_rate: 0,
      average_expected_win_rate_delta: 0,
      prompt_improvements: 0,
      workflow_improvements: 0,
      total_improvements: 0
    }
  };
}

function emptyPromptStudioDashboard() {
  return {
    versions: [],
    experiments: [],
    analytics: {
      prompt_versions_count: 0,
      experiments_count: 0,
      active_experiments_count: 0,
      assignments_count: 0,
      metrics_count: 0,
      prompt_metrics: [],
      winner_recommendations: []
    },
    winner_recommendations: []
  };
}
