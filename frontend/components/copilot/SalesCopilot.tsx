"use client";

import { memo, useMemo } from "react";
import { Bot } from "lucide-react";
import { CopilotChat } from "./CopilotChat";
import { CopilotRecommendations } from "./CopilotRecommendations";
import { CopilotTodo } from "./CopilotTodo";
import type { CopilotModel, CopilotRecommendation, CopilotTodoItem, SalesCopilotInput } from "./types";

export const SalesCopilot = memo(function SalesCopilot(props: SalesCopilotInput) {
  const model = useMemo(() => buildCopilotModel(props), [props]);

  return (
    <aside className="sales-copilot-panel" data-testid="sales-copilot" aria-label="Sales Copilot">
      <div className="sales-copilot-header">
        <div className="sales-copilot-avatar">
          <Bot size={20} aria-hidden="true" />
        </div>
        <div>
          <p className="eyebrow">Sales Copilot</p>
          <h2>AI営業</h2>
          <p>{model.headline}</p>
        </div>
      </div>

      <div className="sales-copilot-summary">
        <strong>おすすめ</strong>
        <p>{model.recommendation}</p>
        <ul>
          {model.reasons.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      </div>

      <CopilotRecommendations recommendations={model.recommendations} onOpenPanel={props.onOpenPanel} />
      <CopilotTodo todos={model.todos} onOpenPanel={props.onOpenPanel} />
      <CopilotChat model={model} onOpenPanel={props.onOpenPanel} />
    </aside>
  );
});

function buildCopilotModel(input: SalesCopilotInput): CopilotModel {
  const activeProjects = input.projects.filter((project) => !["受注", "失注", "完了", "納品", "won", "lost"].some((status) => project.status.includes(status) || project.outcome === status));
  const reviewWaiting = input.projects.filter((project) => project.review_status === "review_requested" || project.status.includes("レビュー"));
  const qualityGateWaiting = input.qualityGateWaiting ? 1 : 0;
  const stagnant = activeProjects.filter((project) => daysSince(project.updated_at) >= 7);
  const lowWin = activeProjects.filter((project) => project.win_probability > 0 && project.win_probability < 45);
  const errorCount = input.usageDashboard?.summary.error_count ?? input.usageLogs.filter((log) => log.status === "failure").length;
  const feedbackIssues = input.feedbackSummary.hard_to_use + input.feedbackSummary.needs_revision;
  const knowledgeSignal = input.history.length > 0 ? "Knowledge一致: 過去提案履歴あり" : "Knowledge一致: 参照候補なし";
  const analyticsSignal = errorCount > 0 ? "Analytics一致: エラー傾向あり" : "Analytics一致: 安定稼働";
  const learningSignal = feedbackIssues > 0 ? "Learning一致: 改善余地あり" : "Learning一致: 肯定フィードバック中心";

  const recommendations = buildRecommendations({
    reviewWaiting: reviewWaiting.length,
    qualityGateWaiting,
    stagnant: stagnant.length,
    lowWin: lowWin.length,
    feedbackIssues,
    knowledgeSignal,
    analyticsSignal,
    learningSignal
  });
  const topRecommendation = recommendations[0];
  const reasons = [
    reviewWaiting.length ? `レビュー待ち ${reviewWaiting.length}件` : "レビュー待ちは少なめ",
    qualityGateWaiting ? "品質ゲート未完了 1件" : "品質ゲート未完了なし",
    stagnant.length ? `停滞案件 ${stagnant.length}件` : "停滞案件は少なめ",
    lowWin.length ? `受注確率低下リスク ${lowWin.length}件` : "低確度案件は目立ちません"
  ];
  const headline = topRecommendation
    ? `今日優先すべき対応は${recommendations.length}件です。`
    : "今日の営業対応は落ち着いています。新規案件の受付から始められます。";
  const recommendation = topRecommendation ? topRecommendation.title : "新規案件メールを貼り付けて、AI Workspaceを進めてください。";
  const todos: CopilotTodoItem[] = recommendations.slice(0, 5).map((item) => ({
    id: item.id,
    label: item.title,
    targetPanelId: item.targetPanelId
  }));
  const commandMap: Record<string, string> = {
    "レビュー一覧": input.isAdmin ? "review-menu-panel" : "result-sales-panel",
    "品質ゲート": "result-sales-panel",
    CRM: "dashboard-panel",
  };
  if (input.isAdmin) {
    commandMap.Knowledge = "admin-knowledge-panel";
    commandMap.Analytics = "admin-product-analytics-panel";
    commandMap["Prompt Studio"] = "admin-prompt-studio-panel";
    commandMap.通知 = "notifications-panel";
    commandMap.案件詳細 = "dashboard-panel";
  } else {
    commandMap.通知 = "real-operations-dashboard";
    commandMap.案件詳細 = "dashboard-panel";
  }

  return { headline, reasons, recommendation, recommendations, todos, commandMap };
}

function buildRecommendations(input: {
  reviewWaiting: number;
  qualityGateWaiting: number;
  stagnant: number;
  lowWin: number;
  feedbackIssues: number;
  knowledgeSignal: string;
  analyticsSignal: string;
  learningSignal: string;
}) {
  const items: CopilotRecommendation[] = [];
  if (input.reviewWaiting > 0) {
    items.push({
      id: "review-request",
      stars: "★★★★★",
      title: "レビュー待ちを先に完了してください",
      detail: `${input.reviewWaiting}件のレビュー待ちがあります。提出前の滞留を減らせます。`,
      actionLabel: "レビュー一覧",
      targetPanelId: "review-menu-panel",
      confidence: 92,
      reasons: ["Review一致: review_requestedあり", "提出前工程で詰まりやすい", input.analyticsSignal],
      signals: ["Review一致", "Analytics一致", "通知一致"]
    });
  }
  if (input.qualityGateWaiting > 0) {
    items.push({
      id: "quality-gate",
      stars: "★★★★★",
      title: "品質ゲートを確認してください",
      detail: "PPT/PDFの主要ダウンロード前に、人間の提出前確認が必要です。",
      actionLabel: "品質ゲート",
      targetPanelId: "result-sales-panel",
      confidence: 88,
      reasons: ["Quality Gate一致: 未完了", "社外提出前の安全確認が必要", "レビュー状態と合わせて確認"],
      signals: ["Quality Gate一致", "Review一致", "Security一致"]
    });
  }
  if (input.stagnant > 0) {
    items.push({
      id: "stagnant-contact",
      stars: "★★★★☆",
      title: "停滞案件へ連絡してください",
      detail: `${input.stagnant}件が7日以上更新されていません。返信待ち・次回日程を確認してください。`,
      actionLabel: "CRM",
      targetPanelId: "dashboard-panel",
      confidence: 84,
      reasons: ["CRM一致: 更新日が古い", "Notification一致: 停滞リスク", input.analyticsSignal],
      signals: ["CRM一致", "Notification一致", "Analytics一致"]
    });
  }
  if (input.lowWin > 0) {
    items.push({
      id: "low-win-risk",
      stars: "★★★★☆",
      title: "低確度案件の打ち手を確認してください",
      detail: `${input.lowWin}件で受注確率が低めです。価格・競合・納期の懸念を確認してください。`,
      actionLabel: "CRM",
      targetPanelId: "dashboard-panel",
      confidence: 80,
      reasons: ["CRM一致: 受注確率45%未満", input.knowledgeSignal, input.learningSignal],
      signals: ["CRM一致", "Knowledge一致", "Learning一致"]
    });
  }
  if (input.feedbackIssues > 0) {
    items.push({
      id: "knowledge-learning",
      stars: "★★★☆☆",
      title: "Knowledgeと改善候補を更新してください",
      detail: "修正要望や使いにくい評価があるため、次回提案に活かす候補があります。",
      actionLabel: "Knowledge",
      targetPanelId: "admin-menu-panel",
      confidence: 76,
      reasons: ["Learning一致: 改善フィードバックあり", "Knowledge更新候補あり", input.analyticsSignal],
      signals: ["Learning一致", "Knowledge一致", "Feedback一致"]
    });
  }
  if (!items.length) {
    items.push({
      id: "new-case",
      stars: "★★★☆☆",
      title: "新規案件の受付を進めてください",
      detail: "案件メールを貼るだけで、AI Workspaceが提案準備を進めます。",
      actionLabel: "新規案件",
      targetPanelId: "new-case",
      confidence: 72,
      reasons: ["Review/Quality Gateの滞留が少ない", "AI稼働状況は安定", "次の案件受付に進める状態"],
      signals: ["Analytics一致", "CRM一致", "Workspace一致"]
    });
  }
  return items.slice(0, 5);
}

function daysSince(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 0;
  return Math.floor((Date.now() - date.getTime()) / (24 * 60 * 60 * 1000));
}
