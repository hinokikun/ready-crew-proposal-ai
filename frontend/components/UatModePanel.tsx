"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, Clipboard, ClipboardCheck, ExternalLink, MinusCircle, XCircle } from "lucide-react";
import { FRONTEND_BUILD_INFO } from "@/lib/buildInfo";
import type { HealthSnapshot } from "@/components/HealthStatus";
import type { BackendHealthProbe, BeautifulAiStatusProbe } from "@/lib/beautifulAi";
import type { AuthUser, WorkspaceContext } from "@/types/app";

type UatResultValue = "untested" | "pass" | "partial" | "fail";
type StatusTone = "success" | "warning" | "error" | "neutral";

type UatRecord = {
  checklist_item_id: string;
  result: UatResultValue;
  comment: string;
  checked_at: string;
  checked_by: string;
};

type UatModePanelProps = {
  enabled: boolean;
  onToggle: () => void;
  currentUser: AuthUser | null;
  workspaceContext: WorkspaceContext | null;
  healthSnapshot: HealthSnapshot | null;
  beautifulAiStatusProbe: BeautifulAiStatusProbe | null;
  beautifulAiHealthProbe: BackendHealthProbe | null;
  maintenanceMode: boolean;
  canEditResults: boolean;
  onOpenAdminMenu: () => void;
  onJump: (target: string) => void;
};

type JumpTarget = {
  label: string;
  target: string;
  selectors: readonly string[];
  admin?: boolean;
  manager?: boolean;
};

const UAT_STORAGE_PREFIX = "ai-sales-secretary-uat-results-v20-3";

const resultLabels: Record<UatResultValue, string> = {
  untested: "未確認",
  pass: "○",
  partial: "△",
  fail: "×"
};

const uatItems = [
  { id: "admin-login", label: "管理者ログイン", critical: true },
  { id: "member-login", label: "一般利用者ログイン", critical: true },
  { id: "dashboard", label: "Dashboard", critical: false },
  { id: "workspace-display", label: "Organization / Workspace表示", critical: true },
  { id: "workspace-switch", label: "Workspace切替", critical: true },
  { id: "project-input", label: "案件入力", critical: true },
  { id: "proposal-generation", label: "AI提案書生成", critical: true },
  { id: "summary-pptx", label: "要約PPTX", critical: true },
  { id: "detail-pptx", label: "詳細PPTX", critical: true },
  { id: "estimate-pdf", label: "見積PDF", critical: true },
  { id: "quality-gate", label: "Quality Gate", critical: true },
  { id: "beautiful-status", label: "Beautiful.ai Status", critical: true },
  { id: "beautiful-generation", label: "Beautiful.ai新規生成", critical: true },
  { id: "presentation-review", label: "Presentation Review", critical: false },
  { id: "proposal-optimization", label: "Proposal Optimization", critical: false },
  { id: "revision-v2", label: "Revision v2", critical: false },
  { id: "beautiful-revision", label: "Beautiful.ai Revision", critical: false },
  { id: "best-practice", label: "Best Practice", critical: false },
  { id: "analytics", label: "Analytics", critical: false },
  { id: "permissions", label: "権限制御", critical: true },
  { id: "workspace-isolation", label: "Organization / Workspace分離", critical: true },
  { id: "mobile", label: "モバイル表示", critical: false },
  { id: "error-display", label: "エラー表示", critical: false },
  { id: "maintenance", label: "Maintenance", critical: true },
  { id: "health", label: "Health", critical: true },
  { id: "migration-ready", label: "Migration Ready", critical: true }
] as const;

const jumpTargets: readonly JumpTarget[] = [
  { label: "Dashboard", target: "real-operations-dashboard", selectors: ['#real-operations-dashboard', '[data-testid="operations-dashboard"]'] },
  { label: "案件入力", target: "project-source-input", selectors: ['[data-testid="project-source-input"]'] },
  { label: "AI Workspace", target: "ai-wizard-shell", selectors: [".ai-wizard-shell"] },
  { label: "出力", target: "result-sales-panel", selectors: ["#result-sales-panel"] },
  { label: "Quality Gate", target: "quality-gate", selectors: [".workspace-quality-gate-card"] },
  { label: "Beautiful.ai", target: "beautiful-ai-status-card", selectors: ['[data-testid="beautiful-ai-status-card"]'] },
  { label: "Presentation Review", target: "presentation-review-panel", selectors: ['[data-testid="presentation-review-panel"]'] },
  { label: "Proposal Optimization", target: "proposal-optimization-panel", selectors: ['[data-testid="proposal-optimization-panel"]'] },
  { label: "Revision", target: "presentation-review-panel", selectors: ['[data-testid="presentation-review-panel"]'] },
  { label: "CRM", target: "dashboard-panel", selectors: ["#dashboard-panel"] },
  { label: "Analytics", target: "admin-product-analytics-panel", selectors: ["#admin-product-analytics-panel"], admin: true },
  { label: "User Management", target: "admin-users-panel", selectors: ["#admin-users-panel"], admin: true },
  { label: "Knowledge", target: "admin-knowledge-panel", selectors: ["#admin-knowledge-panel"], admin: true },
  { label: "Prompt Studio", target: "admin-prompt-studio-panel", selectors: ["#admin-prompt-studio-panel"], admin: true },
  { label: "Learning", target: "admin-learning-panel", selectors: ["#admin-learning-panel"], admin: true },
  { label: "Pilot", target: "admin-pilot-dashboard-panel", selectors: ["#admin-pilot-dashboard-panel"], admin: true },
  { label: "Integrations", target: "admin-integration-panel", selectors: ["#admin-integration-panel"], admin: true },
  { label: "Release", target: "release-management-panel", selectors: ["#release-management-panel"], manager: true },
  { label: "Audit Log", target: "admin-audit-log-panel", selectors: ["#admin-audit-log-panel"], admin: true }
] as const;

function normalizeSegment(value: string | number | undefined | null) {
  return String(value || "none").replace(/[^a-zA-Z0-9._-]/g, "_");
}

function buildStorageKey(
  user: AuthUser | null,
  workspaceContext: WorkspaceContext | null,
  backendVersion: string
) {
  const current = workspaceContext?.current;
  return [
    UAT_STORAGE_PREFIX,
    `user_${normalizeSegment(user?.id)}`,
    `org_${normalizeSegment(current?.organization_id)}`,
    `workspace_${normalizeSegment(current?.workspace_id)}`,
    `frontend_${normalizeSegment(FRONTEND_BUILD_INFO.appVersion)}_${normalizeSegment(FRONTEND_BUILD_INFO.gitCommitShort)}`,
    `backend_${normalizeSegment(backendVersion)}`
  ].join(":");
}

function readStoredResults(storageKey: string) {
  if (typeof window === "undefined") return {};
  try {
    return JSON.parse(window.localStorage.getItem(storageKey) || "{}") as Record<string, UatRecord>;
  } catch {
    return {};
  }
}

function openParentDetails(element: Element) {
  let parentDetails = element.parentElement?.closest("details") as HTMLDetailsElement | null;
  while (parentDetails) {
    parentDetails.open = true;
    parentDetails = parentDetails.parentElement?.closest("details") as HTMLDetailsElement | null;
  }
}

function statusValue(value: boolean | null | undefined, ok: string, ng: string) {
  if (value === true) return ok;
  if (value === false) return ng;
  return "未取得";
}

function statusTone(value: boolean | null | undefined): StatusTone {
  if (value === true) return "success";
  if (value === false) return "error";
  return "neutral";
}

function isAdminRoleValue(role?: string) {
  return role === "admin";
}

function isManagerRoleValue(role?: string) {
  return role === "admin" || role === "manager";
}

function findJumpElement(target: JumpTarget) {
  for (const selector of target.selectors) {
    const element = document.querySelector(selector);
    if (element) return element;
  }
  return null;
}

function buildEmptyRecord(itemId: string, checkedBy: string): UatRecord {
  return {
    checklist_item_id: itemId,
    result: "untested",
    comment: "",
    checked_at: "",
    checked_by: checkedBy
  };
}

export function UatModePanel({
  enabled,
  onToggle,
  currentUser,
  workspaceContext,
  healthSnapshot,
  beautifulAiStatusProbe,
  beautifulAiHealthProbe,
  maintenanceMode,
  canEditResults,
  onOpenAdminMenu,
  onJump
}: UatModePanelProps) {
  const role = currentUser?.role || "";
  const isAdmin = isAdminRoleValue(role);
  const [results, setResults] = useState<Record<string, UatRecord>>({});
  const [loadedStorageKey, setLoadedStorageKey] = useState("");
  const [copyMessage, setCopyMessage] = useState("");
  const [availableJumpTargets, setAvailableJumpTargets] = useState<JumpTarget[]>([]);

  const backendVersion = beautifulAiStatusProbe?.status?.backend_version || beautifulAiHealthProbe?.appVersion || "";
  const backendCommit = beautifulAiHealthProbe?.gitCommit || "";
  const storageKey = useMemo(
    () => buildStorageKey(currentUser, workspaceContext, backendVersion || "unknown"),
    [backendVersion, currentUser, workspaceContext]
  );

  useEffect(() => {
    setResults(readStoredResults(storageKey));
    setLoadedStorageKey(storageKey);
  }, [storageKey]);

  useEffect(() => {
    if (typeof window !== "undefined" && loadedStorageKey === storageKey) {
      window.localStorage.setItem(storageKey, JSON.stringify(results));
    }
  }, [loadedStorageKey, results, storageKey]);

  useEffect(() => {
    if (!enabled || typeof window === "undefined") return;
    const timer = window.setTimeout(() => {
      setAvailableJumpTargets(
        jumpTargets.filter((target) => {
          if (target.admin && !isAdmin) return false;
          if (target.manager && !isManagerRoleValue(role)) return false;
          return Boolean(findJumpElement(target));
        })
      );
    }, isAdmin ? 180 : 60);
    return () => window.clearTimeout(timer);
  }, [enabled, isAdmin, role]);

  const statusRows = useMemo(() => {
    const current = workspaceContext?.current;
    const beautifulStatus = beautifulAiStatusProbe?.status;
    const routeFound = beautifulAiHealthProbe?.beautifulAiRouteRegistered ?? beautifulAiStatusProbe?.routeFound ?? null;
    const databaseReady = Boolean(healthSnapshot?.backendOk && healthSnapshot.dbType && healthSnapshot.dbType !== "未確認");
    const migrationReady: boolean | null = null;
    return [
      {
        label: "Frontend Build Version",
        value: FRONTEND_BUILD_INFO.appVersion || "未取得",
        tone: FRONTEND_BUILD_INFO.appVersion ? "success" : "neutral"
      },
      {
        label: "Frontend Git Commit",
        value: FRONTEND_BUILD_INFO.gitCommitShort || "未取得",
        tone: FRONTEND_BUILD_INFO.gitCommitShort ? "success" : "neutral"
      },
      {
        label: "Backend Version",
        value: backendVersion || "未取得",
        tone: beautifulAiHealthProbe?.reachable ? "success" : "neutral"
      },
      {
        label: "Backend Git Commit",
        value: beautifulAiHealthProbe?.gitCommitShort || "未取得",
        tone: beautifulAiHealthProbe?.gitCommitShort ? "success" : "neutral"
      },
      {
        label: "Migration Ready",
        value: migrationReady === null ? "未取得" : statusValue(migrationReady, "正常", "異常"),
        tone: migrationReady === null ? "neutral" : statusTone(migrationReady)
      },
      {
        label: "Database Ready",
        value: databaseReady ? `${healthSnapshot?.dbType || "DB"} / ${healthSnapshot?.dbTablesCount ?? 0} tables` : "未取得",
        tone: databaseReady ? "success" : "neutral"
      },
      {
        label: "Health",
        value: statusValue(Boolean(healthSnapshot?.backendOk || beautifulAiHealthProbe?.reachable), "正常", "異常"),
        tone: statusTone(Boolean(healthSnapshot?.backendOk || beautifulAiHealthProbe?.reachable))
      },
      {
        label: "Maintenance",
        value: maintenanceMode ? "停止中" : "通常稼働",
        tone: maintenanceMode ? "error" : "success"
      },
      {
        label: "OpenAI Mode",
        value: healthSnapshot?.mockMode ? "Mock" : healthSnapshot?.aiStatus || "未取得",
        tone: healthSnapshot?.mockMode === null && !healthSnapshot?.aiStatus ? "neutral" : "success"
      },
      {
        label: "Beautiful.ai Enabled",
        value: statusValue(beautifulStatus?.enabled, "正常", "要確認"),
        tone: beautifulStatus?.enabled === false ? "warning" : statusTone(beautifulStatus?.enabled)
      },
      {
        label: "Beautiful.ai Configured",
        value: statusValue(beautifulStatus?.configured, "正常", "要確認"),
        tone: beautifulStatus?.configured === false ? "warning" : statusTone(beautifulStatus?.configured)
      },
      {
        label: "Beautiful.ai Route",
        value: statusValue(routeFound, "正常", "異常"),
        tone: statusTone(routeFound)
      },
      {
        label: "Beautiful.ai Mock",
        value: statusValue(beautifulStatus?.mock ?? beautifulAiHealthProbe?.beautifulAiMock, "Mock", "Real"),
        tone: beautifulStatus?.mock ?? beautifulAiHealthProbe?.beautifulAiMock ? "warning" : "success"
      },
      {
        label: "Organization",
        value: current?.organization_name || "未取得",
        tone: current?.organization_name ? "success" : "neutral"
      },
      {
        label: "Workspace",
        value: current?.workspace_name || "未取得",
        tone: current?.workspace_name ? "success" : "neutral"
      },
      {
        label: "Role",
        value: currentUser?.role || "未取得",
        tone: currentUser?.role ? "success" : "neutral"
      }
    ] satisfies { label: string; value: string; tone: StatusTone }[];
  }, [backendVersion, beautifulAiHealthProbe, beautifulAiStatusProbe, currentUser?.role, healthSnapshot, maintenanceMode, workspaceContext]);

  const versionWarning = useMemo(() => {
    const frontendCommit = FRONTEND_BUILD_INFO.gitCommit;
    if (!frontendCommit || !backendCommit) {
      return {
        tone: "neutral" as StatusTone,
        message: "FrontendまたはBackendのGit Commitを確認できません。Vercel / RenderのBuild情報を確認してください。"
      };
    }
    if (frontendCommit.slice(0, 12) !== backendCommit.slice(0, 12)) {
      return {
        tone: "warning" as StatusTone,
        message: "FrontendとBackendのバージョンが一致していません。VercelとRenderの最新デプロイを確認してください。"
      };
    }
    return {
      tone: "success" as StatusTone,
      message: "FrontendとBackendのGit Commitは一致しています。"
    };
  }, [backendCommit]);

  const checkedBy = currentUser?.email || currentUser?.role || "unknown";

  const normalizedResults = useMemo(() => {
    return uatItems.map((item) => results[item.id] || buildEmptyRecord(item.id, checkedBy));
  }, [checkedBy, results]);

  const progress = useMemo(() => {
    const passCount = normalizedResults.filter((item) => item.result === "pass").length;
    const partialCount = normalizedResults.filter((item) => item.result === "partial").length;
    const failCount = normalizedResults.filter((item) => item.result === "fail").length;
    const untestedCount = normalizedResults.filter((item) => item.result === "untested").length;
    const completedCount = normalizedResults.length - untestedCount;
    const score = normalizedResults.reduce((total, item) => {
      if (item.result === "pass") return total + 1;
      if (item.result === "partial") return total + 0.5;
      return total;
    }, 0);
    const criticalDefects = uatItems.filter((item) => item.critical && results[item.id]?.result === "fail");
    const completion = Math.round((score / uatItems.length) * 100);
    const verdict = criticalDefects.length
      ? "本番利用不可"
      : completion >= 90
        ? "条件付きで試験利用可能"
        : "追加確認が必要";
    return { passCount, partialCount, failCount, untestedCount, completedCount, criticalDefects, completion, verdict };
  }, [normalizedResults, results]);

  function updateResult(itemId: string, result: UatResultValue) {
    if (!canEditResults) return;
    setResults((current) => ({
      ...persistResults({
        ...current,
        [itemId]: {
          ...(current[itemId] || buildEmptyRecord(itemId, checkedBy)),
          result,
          checked_at: new Date().toISOString(),
          checked_by: checkedBy
        }
      })
    }));
  }

  function updateComment(itemId: string, comment: string) {
    if (!canEditResults) return;
    setResults((current) => ({
      ...persistResults({
        ...current,
        [itemId]: {
          ...(current[itemId] || buildEmptyRecord(itemId, checkedBy)),
          comment,
          checked_at: new Date().toISOString(),
          checked_by: checkedBy
        }
      })
    }));
  }

  function persistResults(nextResults: Record<string, UatRecord>) {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(storageKey, JSON.stringify(nextResults));
    }
    return nextResults;
  }

  function jumpTo(target: JumpTarget) {
    if (target.admin) onOpenAdminMenu();
    window.setTimeout(() => {
      const element = findJumpElement(target);
      if (element) {
        openParentDetails(element);
        element.scrollIntoView({ behavior: "smooth", block: "start" });
        if (element instanceof HTMLElement) element.focus?.();
        return;
      }
      onJump(target.target);
    }, target.admin ? 160 : 0);
  }

  function buildMarkdown() {
    const current = workspaceContext?.current;
    const nextFixItems = uatItems
      .filter((item) => {
        const result = results[item.id]?.result || "untested";
        return result === "partial" || result === "fail";
      })
      .map((item) => `- ${item.label}: ${resultLabels[results[item.id]?.result || "untested"]}${results[item.id]?.comment ? ` / ${results[item.id]?.comment}` : ""}`);
    return [
      "# UAT結果",
      "",
      `- 実施日時: ${new Date().toLocaleString("ja-JP")}`,
      `- 実施者: ${checkedBy}`,
      `- Organization: ${current?.organization_name || "未取得"}`,
      `- Workspace: ${current?.workspace_name || "未取得"}`,
      `- Frontend Version: ${FRONTEND_BUILD_INFO.appVersion} / ${FRONTEND_BUILD_INFO.gitCommitShort || "未取得"}`,
      `- Backend Version: ${backendVersion || "未取得"} / ${beautifulAiHealthProbe?.gitCommitShort || "未取得"}`,
      `- 完成度: ${progress.completion}%`,
      `- ○: ${progress.passCount}件`,
      `- △: ${progress.partialCount}件`,
      `- ×: ${progress.failCount}件`,
      `- 未確認: ${progress.untestedCount}件`,
      `- 重大不具合: ${progress.criticalDefects.length}件`,
      `- 判定: ${progress.verdict}`,
      "",
      "## チェック結果",
      ...uatItems.map((item, index) => {
        const record = results[item.id] || buildEmptyRecord(item.id, checkedBy);
        return `${index + 1}. ${item.label}: ${resultLabels[record.result]}${record.comment ? ` - ${record.comment}` : ""}`;
      }),
      "",
      "## 次に直す項目",
      ...(nextFixItems.length ? nextFixItems : ["- なし"])
    ].join("\n");
  }

  async function copyMarkdown() {
    if (!canEditResults) return;
    try {
      await navigator.clipboard.writeText(buildMarkdown());
      setCopyMessage("UAT結果Markdownをコピーしました。");
    } catch {
      setCopyMessage("クリップボードへコピーできませんでした。ブラウザ権限を確認してください。");
    }
  }

  return (
    <section className={enabled ? "uat-mode-panel is-enabled" : "uat-mode-panel"} data-testid="uat-mode-panel" aria-label="ブラウザ確認モード">
      <div className="uat-mode-header">
        <div>
          <p className="eyebrow">UAT</p>
          <h2>ブラウザ確認モード</h2>
          <p>Version 20.1の完成度を、人がブラウザで確認するための補助表示です。</p>
        </div>
        <button className={enabled ? "secondary-button" : "primary-button"} type="button" onClick={onToggle} data-testid="uat-mode-toggle">
          <ClipboardCheck size={16} aria-hidden="true" />
          {enabled ? "確認モードOFF" : "確認モードON"}
        </button>
      </div>

      {!enabled ? (
        <p className="uat-mode-off-note">通常画面です。UAT時だけONにすると、状態・ジャンプ・結果入力をまとめて確認できます。</p>
      ) : (
        <>
          {!canEditResults && <p className="uat-readonly-note">managerは閲覧のみです。UAT結果の入力・コピーはadminで実施してください。</p>}
          <div className={`uat-version-warning is-${versionWarning.tone}`} role={versionWarning.tone === "warning" ? "alert" : undefined}>
            {versionWarning.tone === "success" ? <CheckCircle2 size={16} aria-hidden="true" /> : <AlertTriangle size={16} aria-hidden="true" />}
            <span>{versionWarning.message}</span>
          </div>

          <div className="uat-legend" aria-label="表示凡例">
            <span className="is-success"><CheckCircle2 size={14} aria-hidden="true" />正常</span>
            <span className="is-warning"><AlertTriangle size={14} aria-hidden="true" />要確認</span>
            <span className="is-error"><XCircle size={14} aria-hidden="true" />異常</span>
            <span className="is-neutral"><MinusCircle size={14} aria-hidden="true" />未取得</span>
          </div>

          <div className="uat-diagnostics-grid" data-testid="uat-diagnostics">
            {statusRows.map((row) => (
              <article className={`is-${row.tone}`} key={row.label}>
                <span>{row.label}</span>
                <strong>{row.value}</strong>
              </article>
            ))}
          </div>

          <p className="uat-security-note">
            UATコメントにはAPIキー、Password、Token、顧客本文全文、個人情報、機密情報を入力しないでください。
          </p>

          <div className="uat-jump-card">
            <div>
              <strong>確認ジャンプ</strong>
              <small>実在するパネルだけを表示します。折りたたみ内のパネルは開いてから移動します。</small>
            </div>
            <div className="uat-jump-grid" data-testid="uat-jump-grid">
              {availableJumpTargets.map((item) => (
                <button
                  className="secondary-button compact-button"
                  type="button"
                  key={`${item.label}-${item.target}`}
                  onClick={() => jumpTo(item)}
                  data-testid={`uat-jump-${item.target}`}
                >
                  <ExternalLink size={13} aria-hidden="true" />
                  {item.label}
                </button>
              ))}
              {!availableJumpTargets.length && <span className="uat-empty-note">現在表示中のジャンプ先はありません。</span>}
            </div>
          </div>

          <div className="uat-result-card" data-testid="uat-result-card">
            <div className="uat-result-heading">
              <div>
                <p className="eyebrow">UAT結果</p>
                <h3>ブラウザ確認結果</h3>
              </div>
              <div className="uat-verdict">
                <strong>完成度 {progress.completion}%</strong>
                <span className={progress.criticalDefects.length ? "is-error" : progress.completion >= 90 ? "is-success" : "is-warning"}>
                  {progress.verdict}
                </span>
              </div>
            </div>

            <div className="uat-progress-grid" data-testid="uat-progress">
              <article><span>完了数</span><strong>{progress.completedCount}</strong></article>
              <article><span>未確認数</span><strong>{progress.untestedCount}</strong></article>
              <article><span>○件数</span><strong>{progress.passCount}</strong></article>
              <article><span>△件数</span><strong>{progress.partialCount}</strong></article>
              <article><span>×件数</span><strong>{progress.failCount}</strong></article>
              <article className={progress.criticalDefects.length ? "is-error" : "is-success"}><span>重大不具合数</span><strong>{progress.criticalDefects.length}</strong></article>
            </div>

            {progress.criticalDefects.length > 0 && (
              <div className="uat-critical-alert" role="alert" data-testid="uat-critical-alert">
                <strong>本番利用不可</strong>
                <p>重大項目に×があります: {progress.criticalDefects.map((item) => item.label).join("、")}</p>
              </div>
            )}

            <div className="uat-result-actions">
              <button className="secondary-button compact-button" type="button" onClick={() => void copyMarkdown()} disabled={!canEditResults} data-testid="uat-copy-markdown">
                <Clipboard size={14} aria-hidden="true" />
                Markdownをコピー
              </button>
              {copyMessage && <span>{copyMessage}</span>}
            </div>

            <div className="uat-result-list">
              {uatItems.map((item, index) => {
                const record = results[item.id] || buildEmptyRecord(item.id, checkedBy);
                return (
                  <article key={item.id} data-testid={`uat-item-${item.id}`} className={item.critical ? "is-critical" : ""}>
                    <div className="uat-item-title">
                      <span>{index + 1}. {item.label}</span>
                      {item.critical && <small>重大項目</small>}
                    </div>
                    <div className="uat-result-buttons" role="group" aria-label={`${item.label}の結果`}>
                      {(["pass", "partial", "fail"] as const).map((value) => (
                        <button
                          className={record.result === value ? "is-selected" : ""}
                          type="button"
                          key={value}
                          onClick={() => updateResult(item.id, value)}
                          disabled={!canEditResults}
                          data-testid={`uat-result-${item.id}-${value}`}
                        >
                          {resultLabels[value]}
                        </button>
                      ))}
                    </div>
                    <label className="uat-comment-field">
                      <span>コメント</span>
                      <input
                        value={record.comment}
                        onChange={(event) => updateComment(item.id, event.target.value)}
                        disabled={!canEditResults}
                        placeholder="例: 正常に動作 / 文言が分かりにくい / 500エラー"
                        data-testid={`uat-comment-${item.id}`}
                      />
                    </label>
                  </article>
                );
              })}
            </div>
          </div>
        </>
      )}
    </section>
  );
}
