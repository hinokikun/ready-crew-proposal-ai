import { expect, test } from "@playwright/test";
import type { Page, Route } from "@playwright/test";

const adminEmail = "admin@example.com";
const memberEmail = "member@example.com";
const viewerEmail = "viewer@example.com";
const inactiveEmail = "inactive@example.com";

test.setTimeout(60_000);

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    if (!window.sessionStorage.getItem("ready-crew-e2e-storage-initialized")) {
      window.localStorage.clear();
      window.sessionStorage.setItem("ready-crew-e2e-storage-initialized", "true");
    }
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
  await expect(page.getByTestId("login-mode-user")).toBeVisible();
  await expect(page.getByTestId("login-mode-admin")).toBeVisible();
  await expect(page.getByLabel("アクセスパスワード")).toBeVisible();
});

test("利用者ログインと管理者ログインを切り替えられる", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("login-mode-user")).toHaveAttribute("aria-selected", "true");
  await page.getByTestId("login-mode-admin").click();
  await expect(page.getByTestId("login-mode-admin")).toHaveAttribute("aria-selected", "true");
  await expect(page.getByText("現在選択中: 管理者ログイン")).toBeVisible();
});

test("adminは管理者ログインで成功し利用者ログインでは案内される", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("login-mode-user").click();
  await page.getByLabel("メールアドレス").fill(adminEmail);
  await page.getByLabel("アクセスパスワード").fill("test-password");
  await page.getByTestId("login-submit").click();
  await expect(page.getByText("管理者ログインからログインしてください")).toBeVisible();

  await page.getByTestId("login-mode-admin").click();
  await page.getByTestId("login-submit").click();
  await expect(page.getByRole("heading", { name: "営業AIオペレーションセンター" })).toBeVisible();
});

test("memberは利用者ログインで成功し管理者ログインでは拒否される", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("login-mode-admin").click();
  await page.getByLabel("メールアドレス").fill(memberEmail);
  await page.getByLabel("アクセスパスワード").fill("test-password");
  await page.getByTestId("login-submit").click();
  await expect(page.getByText("このアカウントには管理者権限がありません")).toBeVisible();

  await page.getByTestId("login-mode-user").click();
  await page.getByTestId("login-submit").click();
  await expect(page.getByRole("heading", { name: "営業AIオペレーションセンター" })).toBeVisible();
});

test("viewerは利用者ログインで成功し管理者メニューは表示されない", async ({ page }) => {
  await login(page, viewerEmail);
  await expect(page.getByRole("heading", { name: "営業AIオペレーションセンター" })).toBeVisible();
  await expect(page.getByTestId("admin-menu")).toHaveCount(0);
});

test("ログアウト後は直前のログイン入口に戻る", async ({ page }) => {
  await login(page, adminEmail);
  await page.getByRole("button", { name: "ログアウト" }).click();
  await expect(page.getByLabel("メールアドレス")).toBeVisible();
  await expect(page.getByTestId("login-mode-admin")).toHaveAttribute("aria-selected", "true");
});

test("スマートフォン幅でもログイン入口をキーボード操作できる", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 800 });
  await page.goto("/");
  await page.getByTestId("login-mode-admin").focus();
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("login-mode-admin")).toHaveAttribute("aria-selected", "true");
});

test("inactive userと間違ったパスワードとrate limitを日本語で表示する", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("メールアドレス").fill(inactiveEmail);
  await page.getByLabel("アクセスパスワード").fill("test-password");
  await page.getByTestId("login-submit").click();
  await expect(page.getByText("このアカウントは現在無効です")).toBeVisible();

  await page.getByLabel("メールアドレス").fill(memberEmail);
  await page.getByLabel("アクセスパスワード").fill("wrong-password");
  await page.getByTestId("login-submit").click();
  await expect(page.getByText("メールアドレスまたはパスワードが正しくありません")).toBeVisible();

  await page.getByLabel("メールアドレス").fill("rate-limit@example.com");
  await page.getByLabel("アクセスパスワード").fill("test-password");
  await page.getByTestId("login-submit").click();
  await expect(page.getByText("試行回数が多いため、しばらく待ってから再度お試しください")).toBeVisible();
});

test("ログイン後にDashboardが表示される", async ({ page }) => {
  await login(page, memberEmail);
  await expect(page.getByRole("heading", { name: "営業AIオペレーションセンター" })).toBeVisible();
  await expect(page.getByText("まだ案件がありません")).toBeVisible();
});

test("案件入力欄へ入力できる", async ({ page }) => {
  await login(page, memberEmail);
  const input = page.getByTestId("project-source-input");
  await input.waitFor({ state: "visible" });
  await setTextareaValue(page, "project-source-input", "株式会社サンプル様。Webサイトリニューアルの相談。予算300万円、納期3か月。");
  await expect(input).toHaveValue(/株式会社サンプル/);
});

test("通常モードは7ステップのかんたん操作フローを初期表示する", async ({ page }) => {
  await login(page, memberEmail);
  await expect(page.getByTestId("guided-flow")).toBeVisible();
  for (const label of ["案件入力", "AI作成", "内容確認", "品質確認", "出力", "改善", "完了"]) {
    await expect(page.getByRole("button", { name: new RegExp(label) })).toBeVisible();
  }
  await expect(page.getByText("Current backend version")).toHaveCount(0);
  await expect(page.getByText("Git Commit")).toHaveCount(0);
  await expect(page.getByText("Prompt Studioを開く")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "詳細モード" })).toHaveCount(0);
});

test("提出前チェックは未チェック数を表示し全チェック後に完了できる", async ({ page }) => {
  await mockApi(page, { qualityGateComplete: false });
  await login(page, memberEmail);
  await page.getByRole("button", { name: "サンプルを使う" }).click();
  await clickGuidedGenerate(page);
  await page.getByRole("button", { name: "内容を確認しました。品質確認へ進む" }).waitFor({ state: "visible", timeout: 25000 });
  await page.getByRole("button", { name: "内容を確認しました。品質確認へ進む" }).click();
  const completeButton = page.getByRole("button", { name: "提出前チェックを完了する" });
  await expect(completeButton).toBeVisible();
  await expect(completeButton).toBeDisabled();
  await expect(page.getByText("あと6項目の確認が必要です")).toBeVisible();
  for (const label of ["会社名に誤りがない", "金額が正しい", "納期が現実的", "提案内容に不足がない", "AI推測の項目を確認した", "社外提出前に上長確認した"]) {
    await page.getByLabel(label).check();
  }
  await expect(page.getByText("すべて確認済みです")).toBeVisible();
  await expect(completeButton).toBeEnabled();
  await completeButton.click();
  await expect(page.getByText("提出前チェックが完了しました")).toBeVisible();
  await page.getByRole("button", { name: "出力方法を選ぶ" }).click();
  await expect(page.getByRole("heading", { name: "提案書を出力する" })).toBeVisible();
});

test("Beautiful.aiが押せない理由を通常モードで日本語表示する", async ({ page }) => {
  await mockApi(page, { beautifulEnabled: false });
  await login(page, memberEmail);
  await page.getByRole("button", { name: "サンプルを使う" }).click();
  await scrollToOutputs(page);
  await page.getByRole("button", { name: "Beautiful.ai" }).click();
  await expect(page.getByTestId("beautiful-ai-create-button")).toBeDisabled();
  await expect(page.getByText("Beautiful.aiの設定が完了していません").first()).toBeVisible();
});

test("かんたん操作フローはモバイル幅でも1カラムで操作できる", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 800 });
  await login(page, memberEmail);
  await expect(page.getByTestId("guided-flow")).toBeVisible();
  await expect(page.getByTestId("project-source-input")).toBeVisible();
  await page.getByTestId("project-source-input").focus();
  await page.keyboard.type("株式会社サンプル様。Webサイトリニューアルの相談。予算300万円、納期3か月。");
  await expect(page.getByRole("button", { name: "この内容で提案書を作る" })).toBeVisible();
});

test("Maintenance中の503メッセージを表示できる", async ({ page }) => {
  await mockApi(page, { analyzeError: "maintenance" });
  await login(page, memberEmail);
  await page.getByRole("button", { name: "サンプルを使う" }).click();
  await clickGuidedGenerate(page);
  await expect(page.getByLabel("AIウィザード").getByText("現在、新規作成は一時停止中です").first()).toBeVisible({ timeout: 25000 });
});

test("Rate Limitの429メッセージを表示できる", async ({ page }) => {
  await mockApi(page, { analyzeError: "rate" });
  await login(page, memberEmail);
  await page.getByRole("button", { name: "サンプルを使う" }).click();
  await clickGuidedGenerate(page);
  await expect(page.getByLabel("AIウィザード").getByText("AI APIの利用上限に達した可能性があります").first()).toBeVisible({ timeout: 25000 });
});

test("推定値やデモ値はラベルで誤認を防ぐ", async ({ page }) => {
  await mockApi(page, { hasUsageData: true });
  await login(page, adminEmail);
  await page.getByRole("button", { name: "詳細モード" }).click();
  await expect(page.getByText(/推定|デモ表示/).first()).toBeVisible();
});

test("memberに管理者メニューが表示されない", async ({ page }) => {
  await login(page, memberEmail);
  await expect(page.getByText("管理者メニュー・接続状態を開く")).toHaveCount(0);
  await expect(page.getByText("Prompt Studioを開く")).toHaveCount(0);
  await expect(page.getByTestId("uat-mode-panel")).toHaveCount(0);
});

test("adminに管理者メニューが表示される", async ({ page }) => {
  await login(page, adminEmail);
  await page.getByRole("button", { name: "詳細モード" }).click();
  await expect(page.getByTestId("admin-menu")).toBeVisible();
});

test("ブラウザ確認モードでUAT状態を確認できる", async ({ page, context }) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await login(page, adminEmail);
  await page.getByRole("button", { name: "詳細モード" }).click();
  await page.getByTestId("uat-mode-toggle").click();
  const diagnostics = page.getByTestId("uat-diagnostics");
  await expect(diagnostics).toBeVisible();
  await expect(diagnostics.getByText("17.3-e2e")).toBeVisible();
  await expect(diagnostics.getByText("営業部")).toBeVisible();
  await expect(page.getByTestId("uat-result-card")).toBeVisible();
  await expect(diagnostics.getByText("Backend Version")).toBeVisible();
  await expect(diagnostics.getByText("Beautiful.ai Configured")).toBeVisible();
  await expect(page.getByText("UAT結果")).toBeVisible();
  await expect(page.locator("#admin-menu-panel")).toHaveJSProperty("open", true);
  await page.getByTestId("uat-result-dashboard-pass").click();
  await page.getByTestId("uat-comment-dashboard").fill("正常に表示できました");
  await expect(page.getByTestId("uat-progress").getByText("完了数")).toBeVisible();
  await page.getByTestId("uat-result-admin-login-fail").click();
  await expect(page.getByTestId("uat-critical-alert")).toContainText("本番利用不可");
  await page.getByTestId("uat-copy-markdown").click();
  await expect(page.getByText("UAT結果Markdownをコピーしました。")).toBeVisible();
  const clipboardText = await page.evaluate(() => navigator.clipboard.readText());
  expect(clipboardText).toContain("重大不具合");
  await expect(page.getByTestId("uat-jump-real-operations-dashboard")).toBeVisible();
  await page.getByTestId("uat-mode-toggle").click();
  await expect(page.getByTestId("uat-diagnostics")).toHaveCount(0);
  await page.reload();
  await login(page, adminEmail);
  await page.getByRole("button", { name: "詳細モード" }).click();
  await page.getByTestId("uat-mode-toggle").click();
  await expect(page.getByTestId("uat-diagnostics").getByText("17.3-e2e")).toBeVisible();
  await expect(page.getByTestId("uat-diagnostics").getByText("営業部")).toBeVisible();
  await expect(page.getByTestId("uat-comment-dashboard")).toHaveValue("正常に表示できました");
  await expect(page.getByTestId("uat-result-dashboard-pass")).toHaveClass(/is-selected/);
});

test("UAT結果はOrganizationとWorkspaceごとに分離保存される", async ({ page }) => {
  await login(page, adminEmail);
  await page.getByRole("button", { name: "詳細モード" }).click();
  await page.getByTestId("uat-mode-toggle").click();
  await expect(page.getByTestId("uat-diagnostics").getByText("17.3-e2e")).toBeVisible();
  await expect(page.getByTestId("uat-diagnostics").getByText("営業部")).toBeVisible();
  await page.getByTestId("uat-result-dashboard-pass").click();
  await page.getByTestId("uat-comment-dashboard").fill("営業Workspaceで確認");
  await page.locator(".workspace-context-card select").selectOption("1:202");
  await expect(page.getByTestId("uat-diagnostics").getByText("制作部")).toBeVisible();
  await expect(page.getByTestId("uat-comment-dashboard")).toHaveValue("");
  await expect(page.getByTestId("uat-result-dashboard-pass")).not.toHaveClass(/is-selected/);
  await page.locator(".workspace-context-card select").selectOption("1:101");
  await expect(page.getByTestId("uat-diagnostics").getByText("営業部")).toBeVisible();
  await expect(page.getByTestId("uat-comment-dashboard")).toHaveValue("営業Workspaceで確認");
  await expect(page.getByTestId("uat-result-dashboard-pass")).toHaveClass(/is-selected/);
});

test("ブラウザ確認モードはモバイル幅でも確認できる", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 800 });
  await login(page, adminEmail);
  await page.getByRole("button", { name: "詳細モード" }).click();
  await page.getByTestId("uat-mode-toggle").click();
  await expect(page.getByTestId("uat-diagnostics")).toBeVisible();
  await expect(page.getByTestId("uat-result-card")).toBeVisible();
});

test("Sales CopilotのQuick Commandが対象画面へ移動する", async ({ page }) => {
  await login(page, adminEmail);
  await page.getByRole("button", { name: "詳細モード" }).click();
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
  await page.getByRole("button", { name: "サンプルを使う" }).click();
  await scrollToOutputs(page);
  await page.getByRole("button", { name: "Beautiful.ai" }).click();
  const wizard = page.getByLabel("AIウィザード");
  await expect(wizard.getByText("Beautiful.aiの設定が完了していません").first()).toBeVisible({ timeout: 25000 });
  await page.getByRole("button", { name: "要約PowerPoint" }).click();
  await expect(wizard.getByRole("button", { name: "選択した形式で出力する" })).toBeVisible();
});

test("Beautiful.ai作成後に編集と表示リンクが出る", async ({ page }) => {
  await login(page, memberEmail);
  await page.getByRole("button", { name: "サンプルを使う" }).click();
  await scrollToOutputs(page);
  await page.getByRole("button", { name: "Beautiful.ai" }).click();
  const wizard = page.getByLabel("AIウィザード");
  const button = wizard.getByTestId("beautiful-ai-create-button");
  await expect(button).toBeEnabled({ timeout: 25000 });
  await button.click();
  await expect(wizard.getByText("Beautiful.ai提案書を作成しました").first()).toBeVisible();
  await expect(wizard.getByRole("button", { name: "Beautiful.aiで編集" })).toBeVisible();
  await expect(wizard.getByRole("button", { name: "プレゼンテーションを表示" })).toBeVisible();
});

test("Beautiful.ai利用上限時も既存PPTXを利用できる", async ({ page }) => {
  await mockApi(page, { beautifulError: 429 });
  await login(page, memberEmail);
  await page.getByRole("button", { name: "サンプルを使う" }).click();
  await scrollToOutputs(page);
  await page.getByRole("button", { name: "Beautiful.ai" }).click();
  const wizard = page.getByLabel("AIウィザード");
  const button = wizard.getByTestId("beautiful-ai-create-button");
  await expect(button).toBeEnabled({ timeout: 25000 });
  await button.click();
  await expect(wizard.getByText(/Beautiful\.aiの利用上限に達しました/).first()).toBeVisible();
  await page.getByRole("button", { name: "要約PowerPoint" }).click();
  await expect(wizard.getByRole("button", { name: "選択した形式で出力する" })).toBeVisible();
});

test("品質ゲート未完了ではBeautiful.ai作成ボタンを押せない", async ({ page }) => {
  await mockApi(page, { qualityGateComplete: false });
  await login(page, memberEmail);
  await page.getByRole("button", { name: "サンプルを使う" }).click();
  await clickGuidedGenerate(page);
  await page.getByRole("button", { name: "内容を確認しました。品質確認へ進む" }).waitFor({ state: "visible", timeout: 25000 });
  await page.getByRole("button", { name: "内容を確認しました。品質確認へ進む" }).click();
  await expect(page.getByText(/あと\d+項目の確認が必要です/)).toBeVisible();
  await expect(page.getByRole("button", { name: "提出前チェックを完了する" })).toBeDisabled();
});

test("Beautiful.ai Status Cardは管理者の詳細モードでEnabledとMockを確認できる", async ({ page }) => {
  await login(page, adminEmail);
  await page.getByRole("button", { name: "詳細モード" }).click();
  const card = page.getByTestId("beautiful-ai-status-card");
  await expect(card).toBeVisible();
  await expect(card.getByText("Enabled", { exact: true })).toBeVisible();
  await expect(card.getByText("有効", { exact: true }).first()).toBeVisible();
  await expect(card.getByText("Mock")).toBeVisible();
  await expect(card.getByText("ON", { exact: true })).toBeVisible();
  await expect(card.getByText("API mode", { exact: true })).toBeVisible();
  await expect(card.getByText("Prompt API", { exact: true }).first()).toBeVisible();
  await expect(card.getByText("https://www.beautiful.ai/api/v1/generatePresentation").first()).toBeVisible();
  await expect(card.getByText("API reachable")).toBeVisible();
  await expect(card.getByText("到達")).toBeVisible();
  await expect(card.getByText("Route found")).toBeVisible();
  await expect(card.getByText("検出")).toBeVisible();
});

test("Beautiful.ai Disabled時も状態と無効ボタンを確認できる", async ({ page }) => {
  await mockApi(page, { beautifulStatus: "disabled", beautifulEnabled: false });
  await login(page, memberEmail);
  await expect(page.getByTestId("beautiful-ai-status-card")).toHaveCount(0);
  await page.getByRole("button", { name: "サンプルを使う" }).click();
  await scrollToOutputs(page);
  await page.getByRole("button", { name: "Beautiful.ai" }).click();
  await expect(page.getByTestId("beautiful-ai-create-button").first()).toBeDisabled({ timeout: 25000 });
  await expect(page.getByText("Beautiful.aiの設定が完了していません").first()).toBeVisible();
});

test("Beautiful.ai statusが404の場合はUIでRender未反映を確認できる", async ({ page }) => {
  await mockApi(page, { beautifulStatus: "not_found" });
  await login(page, adminEmail);
  await page.getByRole("button", { name: "詳細モード" }).click();
  const card = page.getByTestId("beautiful-ai-status-card");
  await expect(card.getByText("Route found")).toBeVisible();
  await expect(card.getByText("未検出")).toBeVisible();
  await expect(card.getByText(/Beautiful.ai APIルートが見つかりません/)).toBeVisible();
});

test("FrontendとBackendのバージョン不一致を検出できる", async ({ page }) => {
  await mockApi(page, { backendCommit: "different-backend-commit" });
  await login(page, adminEmail);
  await page.getByRole("button", { name: "詳細モード" }).click();
  await expect(page.getByTestId("beautiful-ai-status-card").getByText(/FrontendとBackendのバージョンが一致していません/)).toBeVisible();
});

test("Beautiful.ai診断は管理者詳細モードで確認でき、member通常モードには表示されない", async ({ page }) => {
  await login(page, memberEmail);
  await expect(page.getByTestId("beautiful-ai-disabled-reasons")).toHaveCount(0);
  await page.getByRole("button", { name: "ログアウト" }).click();
  await expect(page.getByLabel("メールアドレス")).toBeVisible();
  await login(page, adminEmail);
  await page.getByRole("button", { name: "詳細モード" }).click();
  await page.getByRole("button", { name: "サンプルを使う" }).click();
  await scrollToOutputs(page);
  const diagnostics = page.getByTestId("beautiful-ai-disabled-reasons-detail").first();
  await expect(diagnostics).toBeVisible({ timeout: 25000 });
  await expect(diagnostics.locator("article").filter({ hasText: "Admin" }).getByText("true")).toBeVisible();
  await expect(diagnostics.locator("article").filter({ hasText: "Role Allowed" }).getByText("true")).toBeVisible();
  await expect(diagnostics.locator("article").filter({ hasText: "Quality Gate" }).getByText("true")).toBeVisible();
});

test("Beautiful.ai診断はmock=falseでも作成ボタンを有効にする", async ({ page }) => {
  await mockApi(page, { beautifulMock: false });
  await login(page, memberEmail);
  await page.getByRole("button", { name: "サンプルを使う" }).click();
  await scrollToOutputs(page);
  await page.getByRole("button", { name: "Beautiful.ai" }).click();
  await expect(page.getByTestId("beautiful-ai-create-button")).toBeEnabled();
});

test("Presentation Review can create a revision", async ({ page }) => {
  await login(page, memberEmail);
  await page.getByRole("button", { name: "サンプルを使う" }).click();
  await scrollToOutputs(page);
  await page.getByRole("button", { name: "AIレビューと改善へ進む" }).click();
  const panel = page.getByTestId("guided-flow").getByTestId("presentation-review-panel");
  await expect(panel).toBeVisible({ timeout: 25000 });
  await panel.getByRole("button", { name: "AIレビュー" }).click();
  await expect(panel.getByText("AIレビューが完了しました。反映したい改善だけ選んでRevisionを作成してください。")).toBeVisible({ timeout: 25000 });
  await expect(panel.getByText("ROI追加")).toBeVisible();
  await panel.getByRole("button", { name: "選択内容でRevision作成" }).click();
  await expect(panel.getByText("Proposal v2").first()).toBeVisible({ timeout: 25000 });
  await expect(panel.getByText("Revision差分")).toBeVisible();
});

test("Presentation Review admin can approve and regenerate Beautiful.ai revision", async ({ page }) => {
  await login(page, adminEmail);
  await page.getByRole("button", { name: "サンプルを使う" }).click();
  await scrollToOutputs(page);
  await page.getByRole("button", { name: "AIレビューと改善へ進む" }).click();
  const panel = page.getByTestId("presentation-review-panel");
  await panel.getByRole("button", { name: "AIレビュー" }).click();
  await panel.getByRole("button", { name: "選択内容でRevision作成" }).click();
  await expect(panel.getByText("Proposal v2").first()).toBeVisible({ timeout: 25000 });
  await panel.getByRole("button", { name: "Revision承認" }).click();
  await expect(panel.getByText("Revisionを承認しました。Beautiful.aiで新しい版として再生成できます。")).toBeVisible({ timeout: 25000 });
  await panel.getByRole("button", { name: "Beautiful.aiで再生成" }).click();
  await expect(panel.getByText("Beautiful.aiでRevisionを新規生成しました。既存プレゼンは上書きしていません。")).toBeVisible({ timeout: 25000 });
  await expect(panel.getByText("mock-revision-e2e")).toBeVisible();
});

test("Proposal Optimization shows recommendations and can adopt an item", async ({ page }) => {
  await login(page, memberEmail);
  await page.getByRole("button", { name: "サンプルを使う" }).click();
  await scrollToOutputs(page);
  await page.getByRole("button", { name: "AIレビューと改善へ進む" }).click();
  const panel = page.getByTestId("guided-flow").getByTestId("proposal-optimization-panel");
  await expect(panel).toBeVisible({ timeout: 25000 });
  await panel.getByRole("button", { name: "Update backlog" }).click();
  await expect(panel.getByText("ROI improvement")).toBeVisible({ timeout: 25000 });
  await expect(panel.getByText("AI reference estimate, not a guaranteed result.")).toBeVisible();
  await panel.getByRole("button", { name: "Select" }).first().click();
  await expect(panel.getByText("Improvement selected. Reflect it in the next Presentation Revision.")).toBeVisible();
});

async function login(page: Page, email: string) {
  await page.goto("/");
  const firstVisible = await Promise.race([
    page.getByRole("heading", { name: "営業AIオペレーションセンター" }).waitFor({ state: "visible", timeout: 8000 }).then(() => "dashboard").catch(() => "none"),
    page.getByLabel("メールアドレス").waitFor({ state: "visible", timeout: 8000 }).then(() => "login").catch(() => "none")
  ]);
  if (firstVisible === "dashboard") {
    await expect(page.getByTestId("sales-copilot")).toBeVisible();
    return;
  }
  const loginMode = email === adminEmail ? "admin" : "user";
  await page.getByTestId(`login-mode-${loginMode}`).click();
  await page.getByLabel("メールアドレス").fill(email);
  await page.getByLabel("アクセスパスワード").fill("test-password");
  await page.getByTestId("login-submit").click();
  await expect(page.getByRole("heading", { name: "営業AIオペレーションセンター" })).toBeVisible();
  const pilotConfirm = page.getByRole("button", { name: "確認して開始する" });
  if (await pilotConfirm.waitFor({ state: "visible", timeout: 1500 }).then(() => true).catch(() => false)) {
    await pilotConfirm.click();
  }
  const pilotConfirmByTestId = page.getByTestId("pilot-checklist-confirm");
  if (await pilotConfirmByTestId.waitFor({ state: "visible", timeout: 5000 }).then(() => true).catch(() => false)) {
    await pilotConfirmByTestId.click();
    await expect(pilotConfirmByTestId).toHaveCount(0);
  }
  await expect(page.getByTestId("sales-copilot")).toBeVisible();
}

async function openAdminPilotDashboard(page: Page) {
  if (await page.getByRole("button", { name: "詳細モード" }).isVisible().catch(() => false)) {
    await page.getByRole("button", { name: "詳細モード" }).click();
  }
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
  await clickGuidedGenerate(page);
  const confirmButton = page.getByRole("button", { name: "内容を確認しました。品質確認へ進む" });
  await confirmButton.waitFor({ state: "visible", timeout: 25000 });
  await confirmButton.click();
  const qualityNext = page.getByRole("button", { name: /提出前チェックを完了する|出力方法を選ぶ/ });
  await qualityNext.waitFor({ state: "visible", timeout: 10000 });
  if (await page.getByText(/あと\d+項目の確認が必要です/).isVisible().catch(() => false)) {
    for (const label of ["会社名に誤りがない", "金額が正しい", "納期が現実的", "提案内容に不足がない", "AI推測の項目を確認した", "社外提出前に上長確認した"]) {
      await page.getByLabel(label).check();
    }
  }
  await qualityNext.click();
  await page.getByRole("heading", { name: "提案書を出力する" }).waitFor({ state: "visible", timeout: 10000 });
  await page.getByRole("heading", { name: "提案書を出力する" }).scrollIntoViewIfNeeded();
  await page.mouse.wheel(0, 500);
}

async function clickGuidedGenerate(page: Page) {
  const input = page.getByTestId("project-source-input");
  await expect(input).not.toHaveValue("");
  const button = page.getByRole("button", { name: "この内容で提案書を作る" });
  await expect(button).toBeEnabled();
  await button.click();
}

type MockOptions = {
  analyzeError?: "maintenance" | "rate";
  hasUsageData?: boolean;
  beautifulEnabled?: boolean;
  beautifulMock?: boolean;
  beautifulStatus?: "enabled" | "disabled" | "mock" | "not_found" | "unauthorized" | "forbidden" | "server_error";
  beautifulError?: 403 | 429;
  qualityGateComplete?: boolean;
  backendCommit?: string;
};

async function mockApi(page: Page, options: MockOptions = {}) {
  const presentationState = {
    status: "draft",
    approved: false,
    generated: false
  };
  let activeWorkspaceId = 101;
  let qualityGateCompleted = options.qualityGateComplete ?? true;
  const workspaceItems = [
    { organization_id: 1, organization_name: "Ready Crew", workspace_id: 101, workspace_name: "営業部", membership_role: "system_admin" },
    { organization_id: 1, organization_name: "Ready Crew", workspace_id: 202, workspace_name: "制作部", membership_role: "system_admin" }
  ];

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
        mock: options.beautifulMock ?? true,
        api_mode: "prompt",
        resolved_endpoint: "https://www.beautiful.ai/api/v1/generatePresentation",
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
    if (path.endsWith("/api/organizations/context")) {
      if (route.request().method() === "PATCH") {
        try {
          const body = route.request().postDataJSON() as { workspace_id?: number };
          if (body.workspace_id) activeWorkspaceId = body.workspace_id;
        } catch {
          activeWorkspaceId = 101;
        }
      }
      const current = workspaceItems.find((item) => item.workspace_id === activeWorkspaceId) ?? workspaceItems[0];
      return json(route, {
        current: { ...current, user_id: 1, system_role: "admin", scope: "admin" },
        available: workspaceItems
      });
    }
    if (path.endsWith("/api/beautiful-ai/diagnostics/test")) {
      return json(route, {
        ok: true,
        http_status: 400,
        error_type: "",
        message: "Beautiful.aiへの通信と認証を確認できました。診断用にpromptなしで送信したため、プレゼンは作成されていません。",
        response_text: "{\"error\":\"prompt is required\"}",
        checked_at: new Date().toISOString()
      });
    }
    if (path.endsWith("/api/beautiful-ai/diagnostics")) {
      return json(route, beautifulDiagnosticsJson(options));
    }
    if (path.endsWith("/api/beautiful-ai/status")) {
      return beautifulStatusJson(route, options);
    }
    if (path.includes("/api/beautiful-ai/presentations") && options.beautifulError === 403) {
      return json(
        route,
        {
          detail: {
            error_type: "beautiful_ai_access_not_enabled",
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
      let body: { email?: string; password?: string; login_mode?: "user" | "admin" } = {};
      try {
        body = route.request().postDataJSON() as { email?: string; password?: string; login_mode?: "user" | "admin" };
      } catch {
        body = {};
      }
      if (body.email === "rate-limit@example.com") {
        return json(route, { detail: "試行回数が多いため、しばらく待ってから再度お試しください" }, 429);
      }
      if (body.email === inactiveEmail) {
        return json(route, { detail: "このアカウントは現在無効です" }, 403);
      }
      if (body.password !== "test-password") {
        return json(route, { detail: "メールアドレスまたはパスワードが正しくありません" }, 401);
      }
      const role = body.email === adminEmail ? "admin" : body.email === viewerEmail ? "viewer" : "member";
      if (body.login_mode === "admin" && role !== "admin") {
        return json(route, { detail: "このアカウントには管理者権限がありません" }, 403);
      }
      if (body.login_mode === "user" && role === "admin") {
        return json(route, { detail: "このアカウントは利用者ログイン対象ではありません。管理者ログインからログインしてください" }, 403);
      }
      return json(route, {
        authenticated: true,
        token: `${role}-token`,
        expires_in_seconds: 3600,
        message: "ok",
        login_mode: body.login_mode,
        user: { id: role === "admin" ? 1 : role === "viewer" ? 3 : 2, email: body.email || memberEmail, role, is_active: true }
      });
    }
    if (path.endsWith("/api/auth/logout")) {
      return json(route, { ok: true });
    }
    if (path.endsWith("/api/auth/status")) {
      const token = route.request().headers().authorization || "";
      const role = token.includes("admin") ? "admin" : token.includes("viewer") ? "viewer" : "member";
      return json(route, {
        user: {
          id: role === "admin" ? 1 : role === "viewer" ? 3 : 2,
          email: role === "admin" ? adminEmail : role === "viewer" ? viewerEmail : memberEmail,
          role,
          is_active: true
        }
      });
    }
    if (path.includes("/quality-gates")) {
      if (path.endsWith("/complete")) {
        qualityGateCompleted = true;
      }
      const parts = path.split("/");
      const qualityGateIndex = parts.indexOf("quality-gates");
      const projectId = qualityGateIndex >= 0 ? decodeURIComponent(parts[qualityGateIndex + 1] || "e2e") : "e2e";
      return json(route, {
        gate: qualityGateCompleted
          ? { project_id: projectId, checklist_items: ["company", "budget"], completed: true, bypassed: false, download_unlocked: true, completed_at: new Date().toISOString(), updated_at: new Date().toISOString() }
          : { project_id: projectId, checklist_items: [], completed: false, bypassed: false, download_unlocked: false }
      });
    }
    return json(route, mockResponse(path, options, presentationState));
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
    mock: options.beautifulMock ?? true,
    api_mode: "prompt",
    resolved_endpoint: "https://www.beautiful.ai/api/v1/generatePresentation",
    provider: "beautiful.ai",
    message: enabled ? "Beautiful.ai連携は利用可能です。" : "Beautiful.ai連携は未設定です。"
  });
}

function beautifulDiagnosticsJson(options: MockOptions) {
  const enabled = options.beautifulEnabled ?? options.beautifulStatus !== "disabled";
  return {
    enabled,
    configured: enabled,
    mock: options.beautifulMock ?? true,
    api_mode: "prompt",
    resolved_endpoint: "https://www.beautiful.ai/api/v1/generatePresentation",
    workspace_id: "workspace-e2e",
    theme_id: "minimal",
    last_http_status: enabled ? 400 : 0,
    last_error_type: "",
    last_response_text: enabled ? "{\"error\":\"prompt is required\"}" : "",
    last_run_at: new Date().toISOString(),
    history: enabled
      ? [
          {
            id: 1,
            project_id: "__diagnostic__",
            title: "Beautiful.ai connection test",
            status: "diagnostic_ok",
            http_status: 400,
            error_type: "",
            response_text: "{\"error\":\"prompt is required\"}",
            endpoint: "https://www.beautiful.ai/api/v1/generatePresentation",
            api_mode: "prompt",
            theme_id: "minimal",
            workspace_config_id: "workspace-e2e",
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          }
        ]
      : []
  };
}

function mockResponse(path: string, options: MockOptions = {}, presentationState = { status: "draft", approved: false, generated: false }) {
  if (path.includes("/beautiful-ai/diagnostics/test")) {
    return {
      ok: true,
      http_status: 400,
      error_type: "",
      message: "Beautiful.aiへの通信と認証を確認できました。診断用にpromptなしで送信したため、プレゼンは作成されていません。",
      response_text: "{\"error\":\"prompt is required\"}",
      checked_at: new Date().toISOString()
    };
  }
  if (path.includes("/beautiful-ai/diagnostics")) {
    return beautifulDiagnosticsJson(options);
  }
  if (path.includes("/beautiful-ai/status")) {
    const enabled = options.beautifulEnabled ?? true;
    return {
      enabled,
      configured: enabled,
      mock: options.beautifulMock ?? true,
      api_mode: "prompt",
      resolved_endpoint: "https://www.beautiful.ai/api/v1/generatePresentation",
      provider: "beautiful.ai",
      message: enabled ? "Beautiful.ai連携は利用可能です。" : "Beautiful.ai連携は未設定です。"
    };
  }
  if (path.includes("/beautiful-ai/presentations") && path.includes("/editor-opened")) return { ok: true };
  if (path.includes("/beautiful-ai/presentations")) {
    if (options.beautifulError === 403) {
      return {
        detail: {
          error_type: "beautiful_ai_access_not_enabled",
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
    const parts = path.split("/");
    const qualityGateIndex = parts.indexOf("quality-gates");
    const projectId = qualityGateIndex >= 0 ? decodeURIComponent(parts[qualityGateIndex + 1] || "e2e") : "e2e";
    return {
      gate: complete
        ? { project_id: projectId, checklist_items: ["company", "budget"], completed: true, bypassed: false, download_unlocked: true }
        : { project_id: projectId, checklist_items: [], completed: false, bypassed: false, download_unlocked: false }
    };
  }
  if (path.includes("/presentation-review/projects") && path.includes("/compare")) {
    return {
      from_revision: presentationRevision(1),
      to_revision: presentationRevision(2),
      changes: [
        {
          id: 1,
          project_id: "e2e",
          from_revision_id: 1,
          to_revision_id: 2,
          change_type: "追加",
          change_summary: "ROI説明スライドを追加します。",
          change_reason: "ROIのスコアが低いため。",
          before_summary: "ROI説明なし",
          after_summary: "費用対効果スライドを追加",
          field_name: "slide_outline",
          human_action: "adopted",
          action_id: "a04_roi",
          created_at: new Date().toISOString()
        },
        {
          id: 2,
          project_id: "e2e",
          from_revision_id: 1,
          to_revision_id: 2,
          change_type: "修正",
          change_summary: "競合比較の見出しを修正します。",
          change_reason: "競合比較が弱いため。",
          before_summary: "競合比較が抽象的",
          after_summary: "比較表として明確化",
          field_name: "slide_outline",
          human_action: "adopted",
          action_id: "a05_competition",
          created_at: new Date().toISOString()
        }
      ]
    };
  }
  if (path.includes("/presentation-review/projects")) {
    return { reviews: [presentationReview()], revisions: [presentationRevision(2, presentationState.status, presentationState.approved, presentationState.generated), presentationRevision(1)] };
  }
  if (path.includes("/presentation-review/reviews")) {
    return { review: { ...presentationReview(), latest_revision: presentationRevision(1) } };
  }
  if (path.includes("/presentation-review/revisions") && path.includes("/generate-beautiful-ai")) {
    presentationState.status = "generated";
    presentationState.approved = true;
    presentationState.generated = true;
    return { revision: presentationRevision(2, presentationState.status, presentationState.approved, presentationState.generated) };
  }
  if (path.includes("/presentation-review/revisions") && path.includes("/approve")) {
    presentationState.status = "approved";
    presentationState.approved = true;
    return { revision: presentationRevision(2, presentationState.status, presentationState.approved, presentationState.generated) };
  }
  if (path.includes("/presentation-review/revisions") && path.includes("/reject")) {
    presentationState.status = "rejected";
    presentationState.approved = false;
    return { revision: presentationRevision(2, presentationState.status, presentationState.approved, presentationState.generated) };
  }
  if (path.includes("/presentation-review/revisions")) {
    presentationState.status = "draft";
    presentationState.approved = false;
    presentationState.generated = false;
    return { revision: presentationRevision(2, presentationState.status, presentationState.approved, presentationState.generated) };
  }
  if (path.includes("/proposal-optimization/backlog") && path.includes("/approve")) {
    return { item: { ...proposalOptimizationItem(), status: "approved" } };
  }
  if (path.includes("/proposal-optimization/backlog")) {
    return { item: { ...proposalOptimizationItem(), status: "selected" } };
  }
  if (path.includes("/proposal-optimization")) {
    return proposalOptimizationResponse();
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

function presentationReview() {
  return {
    id: 1,
    project_id: "e2e",
    project_name: "E2E Presentation",
    average_score: 3.7,
    scores: [
      { key: "story", label: "ストーリー", score: 4.2, reason: "流れは概ね整理済み", evidence: "keyword_hits=2", confidence: 0.7, requires_human_review: false },
      { key: "roi", label: "ROI", score: 2.5, reason: "費用対効果が不足", evidence: "keyword_hits=0", confidence: 0.6, requires_human_review: true },
      { key: "competitor", label: "競合比較", score: 3.0, reason: "競合比較の具体性不足", evidence: "keyword_hits=1", confidence: 0.6, requires_human_review: true }
    ],
    issues: [{ category: "ROI", severity: "high", summary: "ROI説明が不足しています。" }],
    improvements: [
      { action_id: "a04_roi", action_type: "add_roi", type: "ROI追加", title: "ROI追加", change_type: "追加", priority: "high", summary: "費用対効果の説明を1枚追加します。", instruction: "費用対効果の説明を1枚追加します。", target: "ROI", selected: true },
      { action_id: "a05_competition", action_type: "add_competitor_comparison", type: "競合比較追加", title: "競合比較追加", change_type: "修正", priority: "medium", summary: "競合比較の見出しを明確にします。", instruction: "競合比較の見出しを明確にします。", target: "競合比較", selected: true }
    ],
    actions: [
      { action_id: "a04_roi", action_type: "add_roi", type: "ROI追加", title: "ROI追加", change_type: "追加", priority: "high", summary: "費用対効果の説明を1枚追加します。", instruction: "費用対効果の説明を1枚追加します。", target: "ROI", selected: true },
      { action_id: "a05_competition", action_type: "add_competitor_comparison", type: "競合比較追加", title: "競合比較追加", change_type: "修正", priority: "medium", summary: "競合比較の見出しを明確にします。", instruction: "競合比較の見出しを明確にします。", target: "競合比較", selected: true }
    ],
    improvement_summary: "平均レビュー点は3.7点です。追加候補1件、修正候補1件を検出しました。",
    improvement_count: 2,
    unresolved_issue_count: 1,
    overall_score: 3.7,
    outline: { presentation_title: "E2E Presentation", version: "v1", slides: [] },
    approved: false,
    beautiful_ai_presentation_id: "mock-beautiful-e2e",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  };
}

function presentationRevision(number: number, status?: string, approved?: boolean, generated?: boolean) {
  const revisionStatus = number === 1 ? "generated" : status || "draft";
  const revisionGenerated = Boolean(generated);
  return {
    id: number,
    project_id: "e2e",
    review_id: 1,
    revision_number: number,
    revision_label: `Proposal v${number}`,
    slide_count: number === 1 ? 2 : 4,
    added_slide_count: number === 1 ? 0 : 1,
    removed_slide_count: 0,
    modified_slide_count: number === 1 ? 0 : 1,
    improvement_summary: number === 1 ? "初回Revision" : "ROIと競合比較を補強します。",
    beautiful_ai_presentation_id: number === 1 ? "mock-beautiful-e2e" : revisionGenerated ? "mock-revision-e2e" : "",
    editor_url: revisionGenerated ? "https://www.beautiful.ai/editor/mock-revision-e2e" : "",
    player_url: revisionGenerated ? "https://www.beautiful.ai/player/mock-revision-e2e" : "",
    status: revisionStatus,
    approved: number === 1 ? false : Boolean(approved),
    selected_actions: presentationReview().actions,
    outline: { presentation_title: "E2E Presentation", version: `v${number}`, slides: [] },
    diff: [],
    created_by: 2,
    created_by_email: memberEmail,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  };
}

function proposalOptimizationItem() {
  return {
    id: 1,
    project_id: "e2e",
    category: "roi",
    title: "ROI improvement",
    summary: "Adding ROI explanation is expected to improve proposal persuasiveness.",
    priority: "High",
    impact: 88,
    confidence: 0.82,
    expected_improvement: 12,
    effort: 3,
    importance: 5,
    adoption_rate: 66,
    predicted_win_rate_delta: 12,
    composite_score: 91,
    status: "suggested",
    owner: null,
    source_type: "optimization_engine",
    explanation: "ROI gaps appeared in review metadata and adopted improvements performed well.",
    evidence_type: "workspace_history",
    sample_size: 12,
    is_estimate: true,
    calculation_method: "weighted_score_v20_1",
    measurement_status: "pending",
    measured_effect: {},
    requires_human_review: false,
    evidence_summary: "Uses safe metadata only.",
    evidence_period: "latest_safe_workspace_metadata",
    simulation: {
      win_rate_delta: 12,
      review_count_delta: -18,
      proposal_time_delta: -10,
      quality_gate_delta: 8,
      is_estimated: true,
      is_estimate: true,
      note: "推測値です。",
      confidence: 0.82,
      sample_size: 12,
      evidence_type: "workspace_history",
      calculation_method: "weighted_score_v20_1",
      generated_at: new Date().toISOString(),
      requires_human_review: false
    },
    created_by: 1,
    approved_by: null,
    approved_at: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  };
}

function proposalOptimizationResponse() {
  const item = proposalOptimizationItem();
  return {
    recommendations: [item],
    backlog: [item],
    dashboard: {
      backlog_count: 1,
      improvement_adoption_rate: 0,
      improvement_success_rate: 0,
      improvement_rejection_rate: 0,
      average_improvements: 12,
      average_revisions: 1,
      revision_success_rate: 100,
      predicted_win_rate_improvement: 12,
      estimated_improvement_count: 1,
      measured_improvement_count: 0,
      insufficient_sample_count: 0,
      human_review_required_count: 0,
      best_practice_approval_rate: 0,
      revision_link_rate: 100,
      prediction_measurement_gap: null,
      measurement_uncertainty_rate: 0,
      average_prediction_error: null,
      confidence_success_rate: 82
    },
    note: "Effects are AI reference estimates from safe metadata. They are not guaranteed results."
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
    improvement_candidates: [],
    proposal_optimization: proposalOptimizationResponse().dashboard
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
