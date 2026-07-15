"use client";

import { lazy, memo, Suspense, useMemo } from "react";
import { ActionCenter } from "./ActionCenter";
import { ActivityFeed } from "./ActivityFeed";
import { ExecutiveCards } from "./ExecutiveCards";
import { KpiCards } from "./KpiCards";
import { QuickActions } from "./QuickActions";
import { SearchBar } from "./SearchBar";
import type {
  ActionItem,
  ActivityItem,
  ExecutiveMetric,
  KpiMetric,
  OperationsDashboardData,
  OperationsDashboardInput,
  QuickAction
} from "./types";

type RealOperationsDashboardProps = OperationsDashboardInput & {
  isAdmin: boolean;
  onOpenPanel: (panelId: string) => void;
  onFocusNewCase: () => void;
};

const SalesCopilot = lazy(() =>
  import("@/components/copilot/SalesCopilot").then((module) => ({ default: module.SalesCopilot }))
);

const terminalStatuses = ["受注", "失注", "納品", "完了", "won", "lost", "completed"];

export const RealOperationsDashboard = memo(function RealOperationsDashboard(props: RealOperationsDashboardProps) {
  const data = useMemo(() => buildOperationsDashboard(props), [props]);
  const hasAnyData = props.projects.length > 0 || props.history.length > 0 || props.usageLogs.length > 0;

  return (
    <section className="real-operations-dashboard" data-testid="operations-dashboard" id="real-operations-dashboard" aria-label="ProposalPilotホーム">
      <div className="operations-dashboard-header">
        <div>
          <p className="eyebrow">ProposalPilot</p>
          <h2>お客様の案件について教えてください。ProposalPilotが提案づくりをお手伝いします。</h2>
          <p>今日やること、作業中の案件、最近作成した提案書をひとつの画面で確認できます。</p>
          <p className="dashboard-note">KPIには推定値を含みます。詳細な分析や管理機能は、管理者メニューまたは詳細モードで確認できます。</p>
        </div>
      </div>

      {!hasAnyData && (
        <div className="operations-empty-state">
          <p>まだ案件がありません。案件メールや議事録を貼り付けて、新しい提案を作成してください。</p>
          <button className="primary-button" onClick={props.onFocusNewCase} type="button">
            新しい提案を作成
          </button>
        </div>
      )}

      <QuickActions actions={data.quickActions} isAdmin={props.isAdmin} onOpenPanel={props.onOpenPanel} />
      <SearchBar projects={props.projects} onOpenProject={() => props.onOpenPanel("dashboard-panel")} />
      <ExecutiveCards metrics={data.executiveMetrics} />

      <div className="operations-copilot-layout">
        <div className="operations-primary-column">
          <div className="operations-dashboard-main">
            <ActionCenter actions={data.actionItems} onOpenPanel={props.onOpenPanel} />
            <ActivityFeed activities={data.activities} />
          </div>
          <KpiCards metrics={data.kpiMetrics} />
        </div>

        <Suspense fallback={<div className="sales-copilot-skeleton">Sales Copilotを準備しています...</div>}>
          <SalesCopilot
            projects={props.projects}
            history={props.history}
            usageLogs={props.usageLogs}
            auditLogs={props.auditLogs}
            usageDashboard={props.usageDashboard}
            feedbackSummary={props.feedbackSummary}
            qualityGateWaiting={props.qualityGateWaiting}
            hasProposalResult={props.hasProposalResult}
            onOpenPanel={props.onOpenPanel}
            isAdmin={props.isAdmin}
          />
        </Suspense>
      </div>
    </section>
  );
});

function buildOperationsDashboard(input: RealOperationsDashboardProps): OperationsDashboardData {
  const today = new Date();
  const todayKey = toDateKey(today);
  const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
  const projects = input.projects;
  const activeProjects = projects.filter((project) => !isTerminalProject(project.status, project.outcome));
  const todayProjects = projects.filter((project) => toDateKey(new Date(project.updated_at)) === todayKey);
  const reviewWaiting = projects.filter((project) => project.review_status === "review_requested" || project.status.includes("レビュー"));
  const qualityGateWaiting = input.qualityGateWaiting ? 1 : 0;
  const stagnant = activeProjects.filter((project) => daysSince(project.updated_at) >= 7);
  const overdue = activeProjects.filter((project) => /期限|超過|遅延|至急|今日/.test(`${project.status} ${project.next_action}`));
  const won = projects.filter((project) => project.outcome === "won" || project.status === "受注").length;
  const lost = projects.filter((project) => project.outcome === "lost" || project.status === "失注").length;
  const winRate = won + lost > 0 ? Math.round((won / (won + lost)) * 100) : Math.round(average(projects.map((project) => project.win_probability)));
  const weeklyProposals = input.history.filter((item) => new Date(item.createdAt) >= weekAgo).length || input.usageDashboard?.summary.proposal_generation || 0;
  const totalUsage = input.usageDashboard?.summary.total_usage ?? input.usageLogs.length;
  const errorCount = input.usageDashboard?.summary.error_count ?? input.usageLogs.filter((log) => log.status === "failure").length;
  const aiUtilization = totalUsage > 0 ? Math.max(0, Math.round(((totalUsage - errorCount) / totalUsage) * 100)) : 0;
  const hasAnyData = projects.length > 0 || input.history.length > 0 || input.usageLogs.length > 0;

  const executiveMetrics: ExecutiveMetric[] = hasAnyData
    ? [
        { label: "今日の案件数", value: `${todayProjects.length}件`, note: "本日更新された案件", tone: todayProjects.length ? "success" : "normal" },
        { label: "レビュー待ち", value: `${reviewWaiting.length}件`, note: reviewWaiting.length ? "上司確認が必要です" : "レビュー待ちはありません", tone: reviewWaiting.length ? "warning" : "success" },
        { label: "提出前チェック待ち", value: `${qualityGateWaiting}件`, note: qualityGateWaiting ? "出力前の確認が必要です" : "チェック待ちはありません", tone: qualityGateWaiting ? "warning" : "success" },
        { label: "停滞案件", value: `${stagnant.length}件`, note: stagnant.length ? "7日以上更新がありません" : "停滞案件はありません", tone: stagnant.length ? "danger" : "success" },
        { label: "期限超過", value: `${overdue.length}件`, note: overdue.length ? "早めの確認が必要です" : "期限超過はありません", tone: overdue.length ? "danger" : "success" },
        { label: "受注率", value: `${Number.isFinite(winRate) ? winRate : 0}%`, note: won + lost > 0 ? "受注/失注から計算" : "受注確率の平均", tone: "normal" },
        { label: "今週の提案数", value: `${weeklyProposals}件`, note: "作成履歴または利用ログから計算", tone: weeklyProposals ? "success" : "normal" },
        { label: "AI稼働率", value: `${aiUtilization}%`, note: "成功したAI処理の割合", tone: aiUtilization >= 80 ? "success" : aiUtilization >= 50 ? "warning" : "normal" }
      ]
    : [
        { label: "案件", value: "未作成", note: "案件情報を貼り付けると表示されます", tone: "normal" },
        { label: "レビュー", value: "待ちなし", note: "レビュー待ちの案件はありません", tone: "success" },
        { label: "通知", value: "対応なし", note: "現在、対応が必要な通知はありません", tone: "success" },
        { label: "Analytics", value: "蓄積前", note: "利用データが蓄積されると表示されます", tone: "normal" }
      ];

  const actionItems = buildActionItems(reviewWaiting.length, qualityGateWaiting, stagnant.length, overdue.length, input.hasProposalResult);
  const activities = buildActivities(input).slice(0, 20);
  const kpiMetrics = buildKpiMetrics(input, winRate, aiUtilization, reviewWaiting.length, hasAnyData);
  const quickActions: QuickAction[] = [
    { label: "新規案件", target: "new-case" },
    { label: "案件検索", target: "operations-search" },
    { label: "レビュー", target: "review-menu-panel" },
    { label: "CRM", target: "dashboard-panel" },
    { label: "Knowledge", target: "admin-knowledge-panel", adminOnly: true },
    { label: "Analytics", target: "admin-product-analytics-panel", adminOnly: true },
    { label: "Prompt Studio", target: "admin-prompt-studio-panel", adminOnly: true }
  ];

  return { executiveMetrics, actionItems, activities, kpiMetrics, quickActions };
}

function buildActionItems(reviewWaiting: number, qualityGateWaiting: number, stagnant: number, overdue: number, hasProposalResult: boolean): ActionItem[] {
  const actions: ActionItem[] = [];
  if (reviewWaiting > 0) {
    actions.push({
      id: "review-waiting",
      priority: "high",
      stars: "★★★★★",
      title: "レビュー待ち案件があります",
      detail: `${reviewWaiting}件のレビュー依頼を確認してください。`,
      actionLabel: "レビューする",
      targetPanelId: "review-menu-panel"
    });
  }
  if (qualityGateWaiting > 0) {
    actions.push({
      id: "quality-gate",
      priority: "high",
      stars: "★★★★☆",
      title: "提出前チェックが未完了です",
      detail: "提出前チェックを完了すると、PPTX/PDFの確認へ進めます。",
      actionLabel: "確認する",
      targetPanelId: "result-sales-panel"
    });
  }
  if (overdue > 0) {
    actions.push({
      id: "overdue",
      priority: "high",
      stars: "★★★★☆",
      title: "期限超過の可能性があります",
      detail: `${overdue}件の案件で期限や至急対応の記録があります。`,
      actionLabel: "案件を見る",
      targetPanelId: "dashboard-panel"
    });
  }
  if (stagnant > 0) {
    actions.push({
      id: "stagnant",
      priority: "medium",
      stars: "★★★☆☆",
      title: "停滞案件があります",
      detail: `${stagnant}件が7日以上更新されていません。`,
      actionLabel: "案件を見る",
      targetPanelId: "dashboard-panel"
    });
  }
  if (!hasProposalResult) {
    actions.push({
      id: "new-proposal",
      priority: "low",
      stars: "★★★☆☆",
      title: "案件情報を貼り付けて開始できます",
      detail: "案件メールや議事録を貼り付けると、AI Workspaceが提案づくりを支援します。",
      actionLabel: "入力する",
      targetPanelId: "new-case"
    });
  }
  return actions.slice(0, 5);
}

function buildActivities(input: OperationsDashboardInput): ActivityItem[] {
  const auditActivities = input.auditLogs.map<ActivityItem>((log) => ({
    id: `audit-${log.id}`,
    agent: pickAgent(log.event_type),
    title: formatAuditTitle(log.event_type),
    detail: `${log.target_type || "操作"} / ${log.status}`,
    time: formatTime(log.created_at)
  }));
  const usageActivities = input.usageLogs.map<ActivityItem>((log) => ({
    id: `usage-${log.id}`,
    agent: pickAgent(log.featureName),
    title: `${log.featureName} ${log.status === "success" ? "完了" : "失敗"}`,
    detail: log.errorType || log.outputType || "AI処理ログ",
    time: formatTime(log.createdAt)
  }));
  const historyActivities = input.history.map<ActivityItem>((item) => ({
    id: `history-${item.id}`,
    agent: "AI営業",
    title: "提案書作成完了",
    detail: item.clientName || item.title,
    time: formatTime(item.createdAt)
  }));
  return [...auditActivities, ...usageActivities, ...historyActivities].sort((a, b) => sortableTime(b.time) - sortableTime(a.time));
}

function buildKpiMetrics(input: OperationsDashboardInput, winRate: number, aiUtilization: number, reviewCount: number, hasAnyData: boolean): KpiMetric[] {
  if (!hasAnyData) {
    return [
      { label: "受注率", value: "-", note: "案件が登録されると表示されます" },
      { label: "平均提案時間", value: "-", note: "提案作成後に確認できます" },
      { label: "レビュー回数", value: "-", note: "レビュー依頼後に表示されます" },
      { label: "提出前チェック通過率", value: "-", note: "提出前チェック後に表示されます" }
    ];
  }
  const totalUsage = input.usageDashboard?.summary.total_usage ?? input.usageLogs.length;
  const proposalCount = input.usageDashboard?.summary.proposal_generation ?? input.history.length;
  const qualityGatePassRate = input.hasProposalResult && !input.qualityGateWaiting ? 100 : input.hasProposalResult ? 0 : 0;
  const feedbackTotal = input.feedbackSummary.usable + input.feedbackSummary.needs_revision + input.feedbackSummary.hard_to_use;
  const learningAdoptionRate = feedbackTotal > 0
    ? Math.round(((input.feedbackSummary.usable + input.feedbackSummary.needs_revision) / Math.max(1, feedbackTotal)) * 100)
    : 0;
  return [
    { label: "受注率", value: `${Number.isFinite(winRate) ? winRate : 0}%`, note: "CRM登録値から推定" },
    { label: "平均提案時間", value: proposalCount ? "20〜40分" : "-", note: "実測Analytics蓄積後に更新" },
    { label: "レビュー回数", value: `${reviewCount}件`, note: "レビュー待ちを含む" },
    { label: "提出前チェック通過率", value: `${qualityGatePassRate}%`, note: "現在の提案書状態" },
    { label: "AI自律率", value: `${aiUtilization}%`, note: "成功したAI処理の割合" },
    { label: "人間介入率", value: `${Math.max(0, 100 - aiUtilization)}%`, note: "エラー・確認対応の目安" },
    { label: "Learning改善採用率", value: `${learningAdoptionRate}%`, note: "フィードバック集計から推定" },
    { label: "総AI処理", value: `${totalUsage}件`, note: "利用ログ集計" }
  ];
}

function pickAgent(value: string) {
  if (/review|品質|quality|gate|監査|audit/i.test(value)) return "AIディレクター";
  if (/pdf|ppt|schedule|pm|見積|納期/i.test(value)) return "AI PM";
  if (/release|approve|承認|社長/i.test(value)) return "AI社長";
  if (/proposal|提案|営業|analysis/i.test(value)) return "AI営業";
  return "AI秘書";
}

function formatAuditTitle(value: string) {
  if (!value) return "操作ログ";
  if (/login/i.test(value)) return "ログイン確認";
  if (/review/i.test(value)) return "レビュー処理";
  if (/quality/i.test(value)) return "提出前チェック処理";
  if (/release/i.test(value)) return "リリース確認";
  return value.replace(/_/g, " ");
}

function isTerminalProject(status: string, outcome?: string) {
  return terminalStatuses.some((item) => status.includes(item) || outcome === item);
}

function daysSince(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 0;
  return Math.floor((Date.now() - date.getTime()) / (24 * 60 * 60 * 1000));
}

function average(values: number[]) {
  const validValues = values.filter((value) => Number.isFinite(value));
  if (!validValues.length) return 0;
  return validValues.reduce((sum, value) => sum + value, 0) / validValues.length;
}

function toDateKey(date: Date) {
  return `${date.getFullYear()}-${date.getMonth() + 1}-${date.getDate()}`;
}

function formatTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleString("ja-JP", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

function sortableTime(value: string) {
  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? 0 : parsed;
}
