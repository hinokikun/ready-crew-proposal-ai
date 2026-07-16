"use client";

import { memo, useEffect, useMemo, useState } from "react";
import {
  convertExternalIntakeCandidate,
  createExternalIntake,
  getConnectorReadiness,
  getExternalIntakeCandidates,
  getIntegrationDryRunLogs,
  getIntegrationSettings,
  reviewExternalIntakeCandidate,
  runIntegrationDryRun,
  updateIntegrationSetting
} from "@/lib/api";
import { toFriendlyError } from "@/lib/errorMessage";
import type {
  ConnectorReadinessItem,
  DryRunLog,
  ExternalIntakeCandidate,
  ExternalIntakeSourceType,
  IntegrationDryRunResult,
  IntegrationDryRunTemplate,
  IntegrationSetting,
  IntegrationStatus,
  UserRole
} from "@/types/app";

type Props = {
  currentRole?: UserRole;
  showSettings?: boolean;
};

const statusOptions: IntegrationStatus[] = ["未接続", "接続準備中", "接続済み", "エラー"];
const roleOptions: UserRole[] = ["admin", "manager", "member", "viewer"];
const dryRunProviders = ["gmail", "outlook", "slack", "teams", "google_calendar", "google_drive"] as const;
const dryRunTemplates: Array<{ value: IntegrationDryRunTemplate; label: string }> = [
  { value: "case_email", label: "案件相談メール" },
  { value: "meeting_schedule", label: "商談予定" },
  { value: "slack_consultation", label: "Slack相談" },
  { value: "teams_request", label: "Teams依頼" },
  { value: "proposal_request_memo", label: "提案依頼書メモ" },
  { value: "document_share_memo", label: "資料共有メモ" }
];

const providerNotes: Record<string, string> = {
  gmail: "案件相談メールを要約して案件候補にする想定です。OAuthトークンは保存しません。",
  outlook: "営業メールを要約して案件候補にする想定です。本文全文は保存しません。",
  google_calendar: "商談予定の件名と要約から案件候補を作る想定です。",
  google_drive: "提案書や議事録の要約だけを参照する想定です。",
  slack: "相談スレッドの要約から案件候補を作る想定です。",
  teams: "チャットや会議メモの要約から案件候補を作る想定です。",
  notion: "社内メモの要約を案件候補へつなぐ想定です。",
  kintone: "既存案件管理のメタ情報を取り込む想定です。",
  hubspot: "CRMリードの要約を案件候補にする想定です。",
  salesforce: "商談メタ情報を案件候補にする想定です。"
};

function formatDate(value: string | null | undefined) {
  return value ? value.replace("T", " ").slice(0, 16) : "-";
}

function statusLabel(status: string) {
  if (status === "接続済み") return "is-connected";
  if (status === "接続準備中") return "is-preparing";
  if (status === "エラー") return "is-error";
  return "is-disconnected";
}

function providerLabel(provider: string) {
  return provider
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function candidateStatusLabel(status: string) {
  const labels: Record<string, string> = {
    received: "受信済み",
    pending_review: "レビュー待ち",
    approved: "承認済み",
    rejected: "却下",
    converted: "案件化済み",
    archived: "アーカイブ"
  };
  return labels[status] ?? status;
}

export const ExternalIntegrationsPanel = memo(function ExternalIntegrationsPanel({ currentRole, showSettings = true }: Props) {
  const [settings, setSettings] = useState<IntegrationSetting[]>([]);
  const [candidates, setCandidates] = useState<ExternalIntakeCandidate[]>([]);
  const [readiness, setReadiness] = useState<ConnectorReadinessItem[]>([]);
  const [dryRunLogs, setDryRunLogs] = useState<DryRunLog[]>([]);
  const [dryRunResult, setDryRunResult] = useState<IntegrationDryRunResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDryRunRunning, setIsDryRunRunning] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [testProvider, setTestProvider] = useState("gmail");
  const [testSourceType, setTestSourceType] = useState<ExternalIntakeSourceType>("email");
  const [testTitle, setTestTitle] = useState("AI-OCR導入相談");
  const [testSummary, setTestSummary] = useState("請求書処理の読み取り精度と会計システム連携を改善したいという案件相談。予算と納期は要確認。");
  const [dryRunProvider, setDryRunProvider] = useState<(typeof dryRunProviders)[number]>("gmail");
  const [dryRunTemplate, setDryRunTemplate] = useState<IntegrationDryRunTemplate>("case_email");
  const canManageSettings = currentRole === "admin";
  const canCreateCandidate = currentRole === "admin" || currentRole === "manager" || currentRole === "member";
  const canConvertCandidate = canCreateCandidate;

  const visibleSettings = useMemo(() => settings, [settings]);
  const activeCandidates = useMemo(
    () => candidates.filter((candidate) => candidate.candidate_status !== "archived"),
    [candidates]
  );

  async function loadPanel() {
    setIsLoading(true);
    setStatusMessage("");
    try {
      const candidateResponse = await getExternalIntakeCandidates();
      setCandidates(candidateResponse.candidates);
      if (showSettings && (currentRole === "admin" || currentRole === "manager")) {
        const [settingsResponse, readinessResponse, logsResponse] = await Promise.all([
          getIntegrationSettings(),
          getConnectorReadiness(),
          getIntegrationDryRunLogs()
        ]);
        setSettings(settingsResponse.settings);
        setReadiness(readinessResponse.readiness);
        setDryRunLogs(logsResponse.logs);
      }
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setStatusMessage(`${friendly.title} ${friendly.action}`);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadPanel();
  }, [currentRole, showSettings]);

  async function changeSetting(setting: IntegrationSetting, patch: Partial<IntegrationSetting>) {
    if (!canManageSettings) return;
    try {
      const response = await updateIntegrationSetting(setting.provider, {
        status: patch.status ?? setting.status,
        display_name: patch.display_name ?? setting.display_name,
        enabled: patch.enabled ?? setting.enabled,
        error_message: patch.error_message ?? setting.error_message,
        allowed_roles: patch.allowed_roles ?? setting.allowed_roles,
        requires_admin_approval: patch.requires_admin_approval ?? setting.requires_admin_approval,
        data_retention_days: patch.data_retention_days ?? setting.data_retention_days,
        security_note: patch.security_note ?? setting.security_note
      });
      setSettings((items) => items.map((item) => (item.provider === setting.provider ? response.setting : item)));
      setStatusMessage("外部連携設定を更新しました。");
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setStatusMessage(`${friendly.title} ${friendly.action}`);
    }
  }

  async function createTestCandidate() {
    if (!canCreateCandidate) return;
    try {
      const response = await createExternalIntake({
        source_provider: testProvider,
        source_type: testSourceType,
        title: testTitle,
        summary: testSummary,
        received_at: new Date().toISOString(),
        metadata: {
          company_name: testTitle.replace("相談", "").slice(0, 40),
          source_url: "https://example.com",
          provider_item_id: `demo-${Date.now()}`
        }
      });
      setCandidates((items) => [response.candidate, ...items]);
      setStatusMessage("案件化候補を作成しました。");
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setStatusMessage(`${friendly.title} ${friendly.action}`);
    }
  }

  async function convertCandidate(candidateId: number) {
    if (!canConvertCandidate) return;
    try {
      const response = await convertExternalIntakeCandidate(candidateId);
      setCandidates((items) => items.map((item) => (item.id === candidateId ? response.candidate : item)));
      setStatusMessage("案件化しました。CRMとAI Workspaceに引き継ぎました。");
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setStatusMessage(`${friendly.title} ${friendly.action}`);
    }
  }

  async function reviewCandidate(candidateId: number, status: "approved" | "rejected" | "archived") {
    if (!(currentRole === "admin" || currentRole === "manager")) return;
    try {
      const response = await reviewExternalIntakeCandidate(candidateId, {
        status,
        review_comment: status === "approved" ? "案件化前レビューで承認" : "管理者判断でステータス更新"
      });
      setCandidates((items) => items.map((item) => (item.id === candidateId ? response.candidate : item)));
      setStatusMessage("外部入力のレビュー状態を更新しました。");
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setStatusMessage(`${friendly.title} ${friendly.action}`);
    }
  }

  async function executeDryRun() {
    if (!(currentRole === "admin" || currentRole === "manager")) return;
    setIsDryRunRunning(true);
    setStatusMessage("");
    try {
      const response = await runIntegrationDryRun({
        provider: dryRunProvider,
        template_type: dryRunTemplate
      });
      setDryRunResult(response.dry_run);
      setCandidates((items) => [response.candidate, ...items]);
      const [readinessResponse, logsResponse] = await Promise.all([getConnectorReadiness(), getIntegrationDryRunLogs()]);
      setReadiness(readinessResponse.readiness);
      setDryRunLogs(logsResponse.logs);
      setStatusMessage("疑似連携テストが完了しました。外部入力はレビュー待ちとして登録されています。");
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setStatusMessage(`${friendly.title} ${friendly.action}`);
    } finally {
      setIsDryRunRunning(false);
    }
  }

  if (isLoading) {
    return (
      <section className="external-integrations-panel">
        <p className="helper-text">外部連携の状態を読み込んでいます。</p>
      </section>
    );
  }

  return (
    <section className="external-integrations-panel">
      <div className="section-heading-row">
        <div>
          <p className="eyebrow">Version 12.0</p>
          <h3>外部連携準備</h3>
          <p className="helper-text">Gmail / Slack / Calendar などから案件候補を受け取るための準備画面です。実接続やOAuthはまだ行いません。</p>
        </div>
        <button className="secondary-button" type="button" onClick={() => void loadPanel()}>
          再読み込み
        </button>
      </div>

      {statusMessage ? <p className="status-note">{statusMessage}</p> : null}

      {showSettings && (currentRole === "admin" || currentRole === "manager") ? (
        <details className="advanced-foldout" open>
          <summary>疑似連携テスト</summary>
          <div className="dry-run-panel">
            <div className="external-intake-form">
              <label className="field">
                <span>Provider</span>
                <select value={dryRunProvider} onChange={(event) => setDryRunProvider(event.target.value as (typeof dryRunProviders)[number])}>
                  {dryRunProviders.map((provider) => (
                    <option value={provider} key={provider}>{providerLabel(provider)}</option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>テンプレート</span>
                <select value={dryRunTemplate} onChange={(event) => setDryRunTemplate(event.target.value as IntegrationDryRunTemplate)}>
                  {dryRunTemplates.map((template) => (
                    <option value={template.value} key={template.value}>{template.label}</option>
                  ))}
                </select>
              </label>
              <button className="primary-button" type="button" onClick={() => void executeDryRun()} disabled={isDryRunRunning}>
                {isDryRunRunning ? "Dry Run実行中" : "Dry Run実行"}
              </button>
            </div>
            {dryRunResult ? (
              <div className="dry-run-result-card">
                <strong>Dry Run結果</strong>
                <p>{dryRunResult.result_summary}</p>
                <ul>
                  <li>{dryRunResult.checks.registered ? "OK" : "要確認"}: 外部入力として登録</li>
                  <li>{dryRunResult.checks.security_scanned ? "OK" : "要確認"}: セキュリティスキャン</li>
                  <li>{dryRunResult.checks.pending_review ? "OK" : "要確認"}: pending_reviewで保存</li>
                  <li>{dryRunResult.checks.can_convert_after_approval ? "OK" : "要確認"}: 承認後に案件化可能</li>
                  <li>{dryRunResult.checks.workspace_handoff_after_conversion ? "OK" : "要確認"}: AI Workspaceへ引き継ぎ可能</li>
                </ul>
              </div>
            ) : null}
          </div>
        </details>
      ) : null}

      {showSettings && (currentRole === "admin" || currentRole === "manager") ? (
        <details className="advanced-foldout" open>
          <summary>Connector Readiness Score</summary>
          <div className="readiness-grid">
            {readiness.map((item) => (
              <article className="readiness-card" key={item.provider}>
                <div>
                  <strong>{item.display_name}</strong>
                  <span className={`integration-status ${item.status === "ready" ? "is-connected" : "is-preparing"}`}>
                    {item.status === "ready" ? "準備OK" : "要確認"}
                  </span>
                </div>
                <b>{item.score}点</b>
                <ul>
                  {Object.entries(item.checks).map(([key, value]) => (
                    <li key={key}>{value ? "OK" : "未完了"}: {key}</li>
                  ))}
                </ul>
                <small>最終Dry Run: {formatDate(item.last_dry_run_at)}</small>
              </article>
            ))}
          </div>
          {dryRunLogs.length ? (
            <div className="dry-run-log-list">
              {dryRunLogs.slice(0, 5).map((log) => (
                <article key={log.id}>
                  <strong>{providerLabel(log.provider)} / {log.template_type}</strong>
                  <span>{log.status}</span>
                  <p>{log.result_summary}</p>
                  <small>{formatDate(log.created_at)} / flags {log.security_flags_count}</small>
                </article>
              ))}
            </div>
          ) : null}
        </details>
      ) : null}

      {showSettings && (currentRole === "admin" || currentRole === "manager") ? (
        <details className="advanced-foldout" open>
          <summary>外部連携一覧</summary>
          <div className="integration-provider-grid">
            {visibleSettings.map((setting) => (
              <article className="integration-provider-card" key={setting.provider}>
                <div className="integration-provider-header">
                  <div>
                    <strong>{setting.display_name || providerLabel(setting.provider)}</strong>
                    <small>{setting.provider}</small>
                  </div>
                  <span className={`integration-status ${statusLabel(setting.status)}`}>{setting.status}</span>
                </div>
                <p>{providerNotes[setting.provider] ?? "外部サービスから要約とメタ情報だけを受け取る想定です。"}</p>
                <div className="integration-control-row">
                  <label>
                    状態
                    <select
                      value={setting.status}
                      onChange={(event) => void changeSetting(setting, { status: event.target.value })}
                      disabled={!canManageSettings}
                    >
                      {statusOptions.map((option) => (
                        <option value={option} key={option}>{option}</option>
                      ))}
                    </select>
                  </label>
                  <label className="toggle-row">
                    <input
                      type="checkbox"
                      checked={Boolean(setting.enabled)}
                      onChange={(event) => void changeSetting(setting, { enabled: event.target.checked })}
                      disabled={!canManageSettings}
                    />
                    有効化準備
                  </label>
                </div>
                <div className="integration-governance-grid">
                  <label>
                    許可ロール
                    <select
                      multiple
                      value={setting.allowed_roles ?? []}
                      onChange={(event) =>
                        void changeSetting(setting, {
                          allowed_roles: Array.from(event.currentTarget.selectedOptions).map((option) => option.value as UserRole)
                        })
                      }
                      disabled={!canManageSettings}
                    >
                      {roleOptions.map((role) => (
                        <option value={role} key={role}>{role}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    保持期間（日）
                    <input
                      type="number"
                      min={1}
                      max={3650}
                      value={setting.data_retention_days ?? 90}
                      onChange={(event) => void changeSetting(setting, { data_retention_days: Number(event.target.value) })}
                      disabled={!canManageSettings}
                    />
                  </label>
                  <label className="toggle-row">
                    <input
                      type="checkbox"
                      checked={Boolean(setting.requires_admin_approval)}
                      onChange={(event) => void changeSetting(setting, { requires_admin_approval: event.target.checked })}
                      disabled={!canManageSettings}
                    />
                    管理者承認を必須にする
                  </label>
                  <label>
                    セキュリティメモ
                    <textarea
                      rows={2}
                      value={setting.security_note ?? ""}
                      onChange={(event) => void changeSetting(setting, { security_note: event.target.value })}
                      disabled={!canManageSettings}
                    />
                  </label>
                </div>
                <small>最終確認: {formatDate(setting.last_checked_at || setting.updated_at)}</small>
                <small>最終セキュリティ確認: {formatDate(setting.last_security_review_at)}</small>
              </article>
            ))}
          </div>
        </details>
      ) : null}

      {canCreateCandidate ? (
        <details className="advanced-foldout">
          <summary>連携テスト用に案件候補を作る</summary>
          <div className="external-intake-form">
            <label className="field">
              <span>連携元</span>
              <select value={testProvider} onChange={(event) => setTestProvider(event.target.value)}>
                {(settings.length ? settings : [{ provider: "gmail", display_name: "Gmail" } as IntegrationSetting]).map((setting) => (
                  <option value={setting.provider} key={setting.provider}>{setting.display_name || providerLabel(setting.provider)}</option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>種別</span>
              <select value={testSourceType} onChange={(event) => setTestSourceType(event.target.value as ExternalIntakeSourceType)}>
                <option value="email">メール</option>
                <option value="calendar">予定</option>
                <option value="chat">チャット</option>
                <option value="document">資料</option>
              </select>
            </label>
            <label className="field">
              <span>タイトル</span>
              <input value={testTitle} onChange={(event) => setTestTitle(event.target.value)} />
            </label>
            <label className="field">
              <span>要約</span>
              <textarea rows={3} value={testSummary} onChange={(event) => setTestSummary(event.target.value)} />
            </label>
            <button className="secondary-button" type="button" onClick={() => void createTestCandidate()}>
              案件候補を作成
            </button>
          </div>
        </details>
      ) : null}

      <details className="advanced-foldout" open>
        <summary>案件化候補一覧</summary>
        {activeCandidates.length ? (
          <div className="external-candidate-list">
            {activeCandidates.map((candidate) => (
              <article className="external-candidate-card" key={candidate.id}>
                <div>
                  <span>{providerLabel(candidate.source_provider)} / {candidate.source_type}</span>
                  <strong>{candidate.title}</strong>
                  <p>{candidate.summary || "要約は未入力です。"}</p>
                  <small>受付: {formatDate(candidate.received_at || candidate.created_at)}</small>
                  {candidate.security_flags?.length ? (
                    <div className="security-flag-list">
                      {candidate.security_flags.map((flag) => (
                        <span className={`security-flag is-${flag.severity}`} key={`${flag.type}-${flag.field}`}>
                          {flag.type} / {flag.field}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <small>セキュリティフラグ: なし</small>
                  )}
                  {candidate.review_comment ? <small>レビューコメント: {candidate.review_comment}</small> : null}
                </div>
                <div className="external-candidate-actions">
                  <span className={`integration-status ${candidate.candidate_status === "converted" || candidate.candidate_status === "approved" ? "is-connected" : "is-preparing"}`}>
                    {candidateStatusLabel(candidate.candidate_status)}
                  </span>
                  {candidate.project_id ? <small>案件ID: {candidate.project_id}</small> : null}
                  {(currentRole === "admin" || currentRole === "manager") && candidate.candidate_status === "pending_review" ? (
                    <div className="candidate-review-actions">
                      <button className="secondary-button compact-button" type="button" onClick={() => void reviewCandidate(candidate.id, "approved")}>
                        承認
                      </button>
                      <button className="secondary-button compact-button" type="button" onClick={() => void reviewCandidate(candidate.id, "rejected")}>
                        却下
                      </button>
                      <button className="secondary-button compact-button" type="button" onClick={() => void reviewCandidate(candidate.id, "archived")}>
                        アーカイブ
                      </button>
                    </div>
                  ) : null}
                  <button
                    className="primary-button compact-button"
                    type="button"
                    onClick={() => void convertCandidate(candidate.id)}
                    disabled={!canConvertCandidate || candidate.candidate_status !== "approved"}
                  >
                    案件にする
                  </button>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <p className="helper-text">まだ案件化候補はありません。将来の外部連携または連携テストから作成されます。</p>
        )}
      </details>
    </section>
  );
});
