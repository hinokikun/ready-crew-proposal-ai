"use client";

import { AlertCircle, CheckCircle2 } from "lucide-react";
import { AdminAuditLogPanel } from "@/components/AdminAuditLogPanel";
import { AdminFeedbackPanel } from "@/components/AdminFeedbackPanel";
import { AdminImprovementDashboardPanel } from "@/components/AdminImprovementDashboardPanel";
import { AdminKnowledgePanel } from "@/components/AdminKnowledgePanel";
import { AdminOperationReadinessPanel } from "@/components/AdminOperationReadinessPanel";
import { AdminPilotDashboardPanel } from "@/components/AdminPilotDashboardPanel";
import { AdminProductAnalyticsPanel, type CandidateBoundaryDiagnosticState } from "@/components/AdminProductAnalyticsPanel";
import { AdminSalesAssistantPanel } from "@/components/AdminSalesAssistantPanel";
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
import { SystemDiagnosticsPanel } from "@/components/SystemDiagnosticsPanel";
import { SALES_ASSISTANT_FRONTEND_ENABLED } from "@/lib/config";
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
  candidateBoundaryDiagnostic: CandidateBoundaryDiagnosticState;
  onArmCandidateBoundaryDiagnostic: () => void;
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
  usageLogs,
  candidateBoundaryDiagnostic,
  onArmCandidateBoundaryDiagnostic
}: AdminSectionProps) {
  const readinessItems = [
    {
      label: "ログイン状態",
      detail: currentUser ? "管理者としてログイン中です" : "ログイン状態を確認してください",
      ok: Boolean(currentUser)
    },
    {
      label: "Backend接続",
      detail: healthSnapshot?.backendOk ? "Backendに接続できています" : "Backendの起動状態を確認してください",
      ok: Boolean(healthSnapshot?.backendOk)
    },
    {
      label: "DB接続",
      detail: healthSnapshot?.dbStatus || "未確認",
      ok: Boolean(healthSnapshot?.dbStatus && !healthSnapshot.dbStatus.includes("未"))
    },
    {
      label: "OpenAI設定",
      detail: healthSnapshot?.aiStatus || "未確認",
      ok: Boolean(healthSnapshot?.aiStatus && !healthSnapshot.aiStatus.includes("未"))
    },
    {
      label: "ユーザー管理",
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
  ];

  return (
    <details
      className="advanced-foldout admin-menu-foldout"
      data-testid="admin-menu"
      id="admin-menu-panel"
      open={isAdminMenuOpen}
      onToggle={(event) => setIsAdminMenuOpen(event.currentTarget.open)}
    >
      <summary>管理コンソールを開く</summary>
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
          <SystemDiagnosticsPanel />

          <section className="trial-check-panel" aria-label="管理者ダッシュボード">
            <div className="section-heading">
              <div>
                <p className="eyebrow">管理コンソール</p>
                <h2>管理者ダッシュボード</h2>
                <p>今日確認すべき接続、権限、ログ、利用状況をまとめています。秘密情報は表示しません。</p>
              </div>
              <span>管理者向け</span>
            </div>
            <div className="trial-check-grid">
              {readinessItems.map((item) => (
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

          <p className="admin-menu-category-label">ユーザーと組織</p>
          <details className="advanced-foldout" id="admin-users-panel">
            <summary>ユーザー管理</summary>
            <AdminUsersPanel
              users={managedUsers}
              onCreateUser={handleCreateUser}
              onDeleteUser={handleDeleteUser}
              onToggleUser={handleToggleUser}
              onTogglePilot={handleTogglePilot}
              onUpdateUser={handleUpdateUser}
            />
          </details>
          <details className="advanced-foldout">
            <summary>権限・Workspace設定</summary>
            <SettingsPanel
              health={healthSnapshot}
              isAuthenticated
              usageLogs={usageLogs}
              currentUser={currentUser}
              dbLogCount={dbLogCount}
            />
          </details>

          <p className="admin-menu-category-label">利用状況とレポート</p>
          <details className="advanced-foldout" id="admin-product-analytics-panel">
            <summary>Product Analytics</summary>
            <AdminProductAnalyticsPanel
              candidateBoundaryDiagnostic={candidateBoundaryDiagnostic}
              onArmCandidateBoundaryDiagnostic={onArmCandidateBoundaryDiagnostic}
            />
          </details>
          <details className="advanced-foldout">
            <summary>利用状況ダッシュボード</summary>
            <AdminUsageDashboardPanel
              dashboard={usageDashboard}
              isDownloadingCsv={isDownloadingUsageCsv}
              onDownloadCsv={() => void handleDownloadUsageCsv()}
            />
          </details>
          <details className="advanced-foldout">
            <summary>業務改善ダッシュボード</summary>
            <AdminImprovementDashboardPanel />
          </details>
          <details className="advanced-foldout" id="admin-pilot-dashboard-panel">
            <summary>Pilot Dashboard</summary>
            <AdminPilotDashboardPanel />
          </details>

          <p className="admin-menu-category-label">セキュリティと監査</p>
          <details className="advanced-foldout" id="admin-audit-log-panel">
            <summary>監査ログ</summary>
            <AdminAuditLogPanel logs={auditLogs} />
          </details>
          <details className="advanced-foldout">
            <summary>フィードバック一覧</summary>
            <AdminFeedbackPanel feedback={feedbackEntries} summary={feedbackSummary} />
          </details>

          <p className="admin-menu-category-label">外部連携と診断</p>
          <details className="advanced-foldout" id="admin-integration-panel">
            <summary>Beautiful.ai / OpenAI 診断</summary>
            <ExternalIntegrationsPanel currentRole={currentUser?.role} showSettings />
          </details>
          <details className="advanced-foldout">
            <summary>システム診断</summary>
            <SystemDiagnosticsPanel />
          </details>

          <p className="admin-menu-category-label">運用・リリース</p>
          <details className="advanced-foldout">
            <summary>運用準備チェック</summary>
            <AdminOperationReadinessPanel />
          </details>
          <details className="advanced-foldout">
            <summary>試験導入レポート</summary>
            <AdminTrialReportPanel />
          </details>

          <p className="admin-menu-category-label">AI運用・高度機能</p>
          <details className="advanced-foldout" id="admin-prompt-studio-panel">
            <summary>Prompt Studio</summary>
            <PromptStudio />
          </details>
          {SALES_ASSISTANT_FRONTEND_ENABLED && (
            <details className="advanced-foldout" id="admin-sales-assistant-panel">
              <summary>AI Sales Assistant</summary>
              <AdminSalesAssistantPanel />
            </details>
          )}
          <details className="advanced-foldout" id="admin-queue-monitor-panel">
            <summary>AI Queue Monitor</summary>
            <QueueMonitor />
          </details>
          <details className="advanced-foldout" id="admin-learning-panel">
            <summary>AI Learning Dashboard</summary>
            <LearningDashboard />
          </details>
          <details className="advanced-foldout" id="admin-knowledge-panel">
            <summary>Knowledge Intelligence</summary>
            <AdminKnowledgePanel />
          </details>
        </>
      )}
    </details>
  );
}
