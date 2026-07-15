"use client";

import { AlertCircle, CheckCircle2 } from "lucide-react";
import { AdminAuditLogPanel } from "@/components/AdminAuditLogPanel";
import { AdminFeedbackPanel } from "@/components/AdminFeedbackPanel";
import { AdminImprovementDashboardPanel } from "@/components/AdminImprovementDashboardPanel";
import { AdminKnowledgePanel } from "@/components/AdminKnowledgePanel";
import { AdminOperationReadinessPanel } from "@/components/AdminOperationReadinessPanel";
import { AdminPilotDashboardPanel } from "@/components/AdminPilotDashboardPanel";
import { AdminProductAnalyticsPanel } from "@/components/AdminProductAnalyticsPanel";
import { AdminTrialReportPanel } from "@/components/AdminTrialReportPanel";
import { AdminUsageDashboardPanel } from "@/components/AdminUsageDashboardPanel";
import { AdminUsersPanel } from "@/components/AdminUsersPanel";
import { ExternalIntegrationsPanel } from "@/components/ExternalIntegrationsPanel";
import { HealthStatus, type HealthSnapshot } from "@/components/HealthStatus";
import { LearningDashboard } from "@/components/LearningDashboard";
import { PermissionNotice } from "@/components/PermissionNotice";
import { PromptStudio } from "@/components/PromptStudio";
import { QueueMonitor } from "@/components/QueueMonitor";
import { SecurityNotice } from "@/components/SecurityNotice";
import { SettingsPanel } from "@/components/SettingsPanel";
import type { CreatableUserRole } from "@/lib/roles";

export type AdminSectionProps = {
  auditLogs: any[];
  currentUser: any;
  dbLogCount: number;
  feedbackEntries: any[];
  feedbackSummary: any;
  handleCreateUser: (payload: { email: string; password: string; role: CreatableUserRole; display_name?: string }) => Promise<void>;
  handleDeleteUser: (userId: number) => Promise<void>;
  handleDownloadUsageCsv: () => Promise<void> | void;
  handleUpdateUser: (
    userId: number,
    payload: Partial<{
      display_name: string;
      role: CreatableUserRole;
      password: string;
      password_change_required: boolean;
      is_active: boolean;
      pilot_enabled: boolean;
      pilot_completed: boolean;
      pilot_note: string;
    }>
  ) => Promise<void>;
  handleTogglePilot: (userId: number, enabled: boolean) => Promise<void>;
  handleToggleUser: (userId: number, isActive: boolean) => Promise<void>;
  healthSnapshot: HealthSnapshot | null;
  isAdminMenuOpen: boolean;
  isDownloadingUsageCsv: boolean;
  managedUsers: any[];
  setHealthSnapshot: (snapshot: HealthSnapshot) => void;
  setIsAdminMenuOpen: (isOpen: boolean) => void;
  usageDashboard: any;
  usageLogs: any[];
};

export function AdminSection({
  auditLogs,
  currentUser,
  dbLogCount,
  feedbackEntries,
  feedbackSummary,
  handleCreateUser,
  handleDeleteUser,
  handleDownloadUsageCsv,
  handleUpdateUser,
  handleTogglePilot,
  handleToggleUser,
  healthSnapshot,
  isAdminMenuOpen,
  isDownloadingUsageCsv,
  managedUsers,
  setHealthSnapshot,
  setIsAdminMenuOpen,
  usageDashboard,
  usageLogs
}: AdminSectionProps) {
  return (
    <details
      className="advanced-foldout admin-menu-foldout"
      data-testid="admin-menu"
      id="admin-menu-panel"
      open={isAdminMenuOpen}
      onToggle={(event) => setIsAdminMenuOpen(event.currentTarget.open)}
    >
      <summary>管理者メニュー・接続状態を開く</summary>
    {isAdminMenuOpen && (
      <>
    <SecurityNotice />
    <HealthStatus onChange={setHealthSnapshot} />
    <SettingsPanel
      health={healthSnapshot}
      isAuthenticated
      usageLogs={usageLogs}
      currentUser={currentUser}
      dbLogCount={dbLogCount}
    />
    <PermissionNotice role={currentUser?.role} />
      <section className="trial-check-panel" aria-label="試験導入チェック">
        <div className="section-heading">
          <div>
            <p className="eyebrow">試験導入</p>
            <h2>試験導入チェック</h2>
          </div>
          <span>管理者向け</span>
        </div>
        <div className="trial-check-grid">
          {[
            {
              label: "ログイン設定",
              detail: currentUser ? `${currentUser.email} でログイン中` : "ログイン状態を確認してください",
              ok: Boolean(currentUser)
            },
            {
              label: "Backend接続",
              detail: healthSnapshot?.backendOk ? "正常に接続しています" : "接続状態を確認してください",
              ok: Boolean(healthSnapshot?.backendOk)
            },
            {
              label: "DB接続",
              detail: healthSnapshot?.dbStatus || "未確認",
              ok: healthSnapshot?.dbStatus === "接続済み"
            },
            {
              label: "OpenAI API状態",
              detail: healthSnapshot?.aiStatus || "未確認",
              ok: healthSnapshot?.aiStatus === "利用可能"
            },
            {
              label: "権限管理",
              detail: `${managedUsers.length}件のユーザーを確認できます`,
              ok: managedUsers.length > 0
            },
            {
              label: "利用ログ",
              detail: `${Math.max(dbLogCount, usageLogs.length)}件のログを確認できます`,
              ok: dbLogCount > 0 || usageLogs.length > 0
            },
            {
              label: "監査ログ",
              detail: `${auditLogs.length}件の監査ログを確認できます`,
              ok: auditLogs.length > 0
            }
          ].map((item) => (
            <article className={item.ok ? "is-ok" : "is-alert"} key={item.label}>
              {item.ok ? <CheckCircle2 size={18} aria-hidden="true" /> : <AlertCircle size={18} aria-hidden="true" />}
              <div>
                <strong>{item.label}</strong>
                <p>{item.detail}</p>
              </div>
            </article>
          ))}
        </div>
      </section>
      <>
        <p className="admin-menu-category-label">運用管理</p>
        <details className="advanced-foldout">
          <summary>運用準備チェックを開く</summary>
          <AdminOperationReadinessPanel />
        </details>
        <details className="advanced-foldout" id="admin-users-panel">
          <summary>ユーザー管理を開く</summary>
          <AdminUsersPanel
            users={managedUsers}
            onCreateUser={handleCreateUser}
            onDeleteUser={handleDeleteUser}
            onToggleUser={handleToggleUser}
            onTogglePilot={handleTogglePilot}
            onUpdateUser={handleUpdateUser}
          />
        </details>
        <details className="advanced-foldout" id="admin-pilot-dashboard-panel">
          <summary>Pilot Dashboardを開く</summary>
          <AdminPilotDashboardPanel />
        </details>
        <details className="advanced-foldout" id="admin-audit-log-panel">
          <summary>監査ログを開く</summary>
          <AdminAuditLogPanel logs={auditLogs} />
        </details>
        <details className="advanced-foldout">
          <summary>フィードバック一覧を開く</summary>
          <AdminFeedbackPanel feedback={feedbackEntries} summary={feedbackSummary} />
        </details>
        <p className="admin-menu-category-label">改善分析</p>
        <details className="advanced-foldout">
          <summary>改善提案ダッシュボードを開く</summary>
          <AdminImprovementDashboardPanel />
        </details>
        <details className="advanced-foldout">
          <summary>利用状況ダッシュボードを開く</summary>
          <AdminUsageDashboardPanel
            dashboard={usageDashboard}
            isDownloadingCsv={isDownloadingUsageCsv}
            onDownloadCsv={() => void handleDownloadUsageCsv()}
          />
        </details>
        <details className="advanced-foldout" id="admin-product-analytics-panel">
          <summary>Product Analyticsを開く</summary>
          <AdminProductAnalyticsPanel />
        </details>
        <details className="advanced-foldout" id="admin-queue-monitor-panel">
          <summary>AI Queue Monitorを開く</summary>
          <QueueMonitor />
        </details>
        <details className="advanced-foldout" id="admin-learning-panel">
          <summary>AI Learning Dashboardを開く</summary>
          <LearningDashboard />
        </details>
        <p className="admin-menu-category-label">AI実験/Prompt管理</p>
        <details className="advanced-foldout" id="admin-prompt-studio-panel">
          <summary>Prompt Studioを開く</summary>
          <PromptStudio />
        </details>
        <p className="admin-menu-category-label">外部連携</p>
        <details className="advanced-foldout" id="admin-integration-panel">
          <summary>外部連携を開く</summary>
          <ExternalIntegrationsPanel currentRole={currentUser?.role} showSettings />
        </details>
        <p className="admin-menu-category-label">ナレッジ管理</p>
        <details className="advanced-foldout" id="admin-knowledge-panel">
          <summary>Knowledge Intelligenceを開く</summary>
          <AdminKnowledgePanel />
        </details>
        <p className="admin-menu-category-label">社内展開・監査</p>
        <details className="advanced-foldout">
          <summary>試験導入レポート作成を開く</summary>
          <AdminTrialReportPanel />
        </details>
      </>
      </>
    )}
    </details>
  );
}
