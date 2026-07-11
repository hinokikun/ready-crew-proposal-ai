"use client";

import { memo, useCallback, useEffect, useMemo, useState } from "react";
import {
  completeProject,
  generateProjectHandoff,
  getProjectLifecycle,
  registerProjectOutcome,
  updateProjectStatus,
  type CrmCustomer,
  type CrmProject,
  type ProjectLifecycleDetail,
  type ProjectLifecycleStatus,
  type ProjectLostReason,
  type UserRole
} from "@/lib/api";
import { toFriendlyError } from "@/lib/errorMessage";

type CrmPanelProps = {
  customers: CrmCustomer[];
  projects: CrmProject[];
  currentRole?: UserRole;
  onChanged?: () => void;
};

const fallbackStatuses: ProjectLifecycleStatus[] = [
  "受付",
  "ヒアリング",
  "提案中",
  "レビュー中",
  "提出済み",
  "商談中",
  "受注",
  "失注",
  "制作中",
  "納品",
  "完了"
];

const reviewLabels: Record<string, string> = {
  draft: "下書き",
  review_requested: "レビュー依頼中",
  approved: "承認済み",
  changes_requested: "修正依頼",
  rejected: "却下"
};

const eventLabels: Record<string, string> = {
  project_received: "案件受付",
  status_changed: "ステータス変更",
  project_won: "受注登録",
  project_lost: "失注登録",
  handoff_created: "制作引継ぎ作成",
  project_completed: "案件完了"
};

const lostReasonLabels: Record<ProjectLostReason, string> = {
  price: "価格",
  competitor: "競合",
  deadline: "納期",
  proposal: "提案内容",
  other: "その他",
  "": "未選択"
};

export const CrmPanel = memo(function CrmPanel({ customers, projects, currentRole, onChanged }: CrmPanelProps) {
  const canEdit = currentRole === "admin" || currentRole === "manager" || currentRole === "member";
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(projects[0]?.id ?? null);
  const [lifecycle, setLifecycle] = useState<ProjectLifecycleDetail | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<ProjectLifecycleStatus>("受付");
  const [statusNote, setStatusNote] = useState("");
  const [lostReason, setLostReason] = useState<ProjectLostReason>("price");
  const [outcomeNote, setOutcomeNote] = useState("");
  const [handoffDeadline, setHandoffDeadline] = useState("");
  const [handoffOwner, setHandoffOwner] = useState("");
  const [handoffCms, setHandoffCms] = useState("");
  const [handoffFunctions, setHandoffFunctions] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState("");

  const statuses = lifecycle?.statuses?.length ? lifecycle.statuses : fallbackStatuses;
  const currentProject = lifecycle?.project ?? projects.find((project) => project.id === selectedProjectId) ?? null;
  const currentStatus = currentProject?.status && currentProject.status !== "draft" ? currentProject.status : "受付";
  const activeStatusIndex = Math.max(statuses.indexOf(currentStatus as ProjectLifecycleStatus), 0);

  const selectedProjectSummary = useMemo(() => {
    if (!currentProject) return "";
    return currentProject.summary || currentProject.next_action || "案件概要はまだ登録されていません。";
  }, [currentProject]);

  const loadLifecycle = useCallback(
    async (projectId: number) => {
      setIsLoading(true);
      setMessage("");
      try {
        const response = await getProjectLifecycle(projectId);
        setLifecycle(response.lifecycle);
        const nextStatus = response.lifecycle.project.status === "draft" ? "受付" : response.lifecycle.project.status;
        setSelectedStatus((nextStatus as ProjectLifecycleStatus) || "受付");
      } catch (caught) {
        const friendly = toFriendlyError(caught);
        setMessage(`${friendly.title} ${friendly.action}`);
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    if (selectedProjectId) {
      void loadLifecycle(selectedProjectId);
    }
  }, [loadLifecycle, selectedProjectId]);

  const refreshLifecycle = useCallback(
    async (projectId: number) => {
      await loadLifecycle(projectId);
      onChanged?.();
    },
    [loadLifecycle, onChanged]
  );

  async function handleStatusUpdate() {
    if (!selectedProjectId || !canEdit) return;
    setIsLoading(true);
    try {
      const response = await updateProjectStatus(selectedProjectId, { status: selectedStatus, note: statusNote });
      setLifecycle(response.lifecycle);
      setStatusNote("");
      setMessage("ステータスを更新しました。");
      onChanged?.();
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setMessage(`${friendly.title} ${friendly.action}`);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleOutcome(outcome: "won" | "lost") {
    if (!selectedProjectId || !canEdit) return;
    setIsLoading(true);
    try {
      const response = await registerProjectOutcome(selectedProjectId, {
        outcome,
        lost_reason: outcome === "lost" ? lostReason : "",
        note: outcomeNote
      });
      setLifecycle(response.lifecycle);
      setOutcomeNote("");
      setMessage(outcome === "won" ? "受注として登録しました。" : "失注として登録しました。");
      onChanged?.();
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setMessage(`${friendly.title} ${friendly.action}`);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleHandoff() {
    if (!selectedProjectId || !canEdit) return;
    setIsLoading(true);
    try {
      const response = await generateProjectHandoff(selectedProjectId, {
        proposal_summary: selectedProjectSummary,
        deadline: handoffDeadline,
        owner: handoffOwner,
        special_functions: handoffFunctions,
        cms: handoffCms
      });
      setLifecycle(response.lifecycle);
      setMessage("制作チーム向け引継ぎを作成しました。");
      await refreshLifecycle(selectedProjectId);
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setMessage(`${friendly.title} ${friendly.action}`);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleComplete() {
    if (!selectedProjectId || !canEdit) return;
    setIsLoading(true);
    try {
      const response = await completeProject(selectedProjectId, {
        success_factors: "提案から引継ぎまでの情報を一元管理できたこと。",
        improvements: "次回は決裁者、予算、納期の確認をより早い段階で行います。",
        next_learnings: "完了案件の振り返りをKnowledge候補として活用します。"
      });
      setLifecycle(response.lifecycle);
      setMessage("案件を完了し、振り返りをKnowledge候補に追加しました。");
      onChanged?.();
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setMessage(`${friendly.title} ${friendly.action}`);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className="crm-panel" aria-label="CRM">
      <div className="section-heading">
        <p className="eyebrow">CRM / Project Lifecycle</p>
        <h2>案件ライフサイクル管理</h2>
        <p>案件の受付から受注、制作引継ぎ、納品、完了、Knowledge化までを時系列で確認します。</p>
      </div>

      {message ? <p className="status-note">{message}</p> : null}

      <div className="crm-grid">
        <article>
          <strong>顧客一覧</strong>
          <div className="crm-list">
            {customers.length ? (
              customers.map((customer) => (
                <div key={customer.id}>
                  <span>{customer.company_name}</span>
                  <small>
                    業種: {customer.industry || "未設定"} / 担当: {customer.contact_person || "未設定"} / 更新: {formatDate(customer.updated_at)}
                  </small>
                </div>
              ))
            ) : (
              <p>まだ顧客は保存されていません。</p>
            )}
          </div>
        </article>

        <article>
          <strong>案件一覧</strong>
          <div className="crm-list">
            {projects.length ? (
              projects.map((project) => (
                <button
                  className={`crm-project-button ${selectedProjectId === project.id ? "is-active" : ""}`}
                  key={project.id}
                  onClick={() => setSelectedProjectId(project.id)}
                  type="button"
                >
                  <span>{project.name}</span>
                  <small>
                    顧客: {project.customer_name || "未設定"} / 状態: {project.status === "draft" ? "受付" : project.status} / レビュー:{" "}
                    {formatReviewStatus(project.review_status)} / 受注確率: {project.win_probability}%
                  </small>
                  <p>{project.next_action || project.summary || "次回アクションは未設定です。"}</p>
                </button>
              ))
            ) : (
              <p>まだ案件は保存されていません。</p>
            )}
          </div>
        </article>
      </div>

      {currentProject ? (
        <div className="project-dashboard">
          <div className="project-dashboard-header">
            <div>
              <p className="eyebrow">Project Dashboard</p>
              <h3>{currentProject.name}</h3>
              <p>{currentProject.customer_name || "顧客名未設定"} / 現在: {currentStatus}</p>
            </div>
            <button className="secondary-button" disabled={isLoading || !selectedProjectId} onClick={() => selectedProjectId && void loadLifecycle(selectedProjectId)} type="button">
              再読み込み
            </button>
          </div>

          <div className="project-timeline" aria-label="案件ステータス">
            {statuses.map((status, index) => (
              <div
                className={`lifecycle-step ${index < activeStatusIndex ? "is-done" : ""} ${index === activeStatusIndex ? "is-current" : ""}`}
                key={status}
              >
                <span>{index < activeStatusIndex ? "✓" : index === activeStatusIndex ? "●" : ""}</span>
                <strong>{status}</strong>
              </div>
            ))}
          </div>

          <div className="project-action-grid">
            <article className="project-action-panel">
              <h4>ステータス変更</h4>
              <label>
                次の状態
                <select disabled={!canEdit || isLoading} value={selectedStatus} onChange={(event) => setSelectedStatus(event.target.value as ProjectLifecycleStatus)}>
                  {statuses.map((status) => (
                    <option key={status} value={status}>
                      {status}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                メモ
                <textarea value={statusNote} onChange={(event) => setStatusNote(event.target.value)} placeholder="例：7/12に提案書を提出済み" />
              </label>
              <button className="primary-button" disabled={!canEdit || isLoading} onClick={() => void handleStatusUpdate()} type="button">
                ステータスを更新
              </button>
              {!canEdit ? <p className="helper-text">閲覧権限のため、変更はできません。</p> : null}
            </article>

            <article className="project-action-panel">
              <h4>受注・失注登録</h4>
              <label>
                失注理由
                <select disabled={!canEdit || isLoading} value={lostReason} onChange={(event) => setLostReason(event.target.value as ProjectLostReason)}>
                  {Object.entries(lostReasonLabels).filter(([key]) => key !== "").map(([key, label]) => (
                    <option key={key} value={key}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                メモ
                <textarea value={outcomeNote} onChange={(event) => setOutcomeNote(event.target.value)} placeholder="例：価格差により競合へ決定" />
              </label>
              <div className="project-button-row">
                <button className="primary-button" disabled={!canEdit || isLoading} onClick={() => void handleOutcome("won")} type="button">
                  受注登録
                </button>
                <button className="secondary-button" disabled={!canEdit || isLoading} onClick={() => void handleOutcome("lost")} type="button">
                  失注登録
                </button>
              </div>
              {lifecycle?.outcome ? (
                <p className="helper-text">
                  登録済み: {lifecycle.outcome.outcome === "won" ? "受注" : "失注"}{" "}
                  {lifecycle.outcome.lost_reason ? `(${lostReasonLabels[lifecycle.outcome.lost_reason as ProjectLostReason] ?? lifecycle.outcome.lost_reason})` : ""}
                </p>
              ) : null}
            </article>

            <article className="project-action-panel">
              <h4>制作引継ぎ</h4>
              <div className="handoff-input-grid">
                <input value={handoffDeadline} onChange={(event) => setHandoffDeadline(event.target.value)} placeholder="納期（例：2026年9月末）" />
                <input value={handoffOwner} onChange={(event) => setHandoffOwner(event.target.value)} placeholder="担当（例：営業 山田）" />
                <input value={handoffCms} onChange={(event) => setHandoffCms(event.target.value)} placeholder="CMS（例：WordPress）" />
                <input value={handoffFunctions} onChange={(event) => setHandoffFunctions(event.target.value)} placeholder="特殊機能（例：物件検索）" />
              </div>
              <button className="secondary-button" disabled={!canEdit || isLoading} onClick={() => void handleHandoff()} type="button">
                引継ぎ資料を作成
              </button>
              {lifecycle?.handoff?.handoff_text ? <pre className="handoff-box">{lifecycle.handoff.handoff_text}</pre> : null}
            </article>

            <article className="project-action-panel">
              <h4>案件完了・振り返り</h4>
              <p className="helper-text">完了時に成功要因、改善点、次回活かすことをKnowledge候補へ追加します。</p>
              <button className="secondary-button" disabled={!canEdit || isLoading} onClick={() => void handleComplete()} type="button">
                完了して振り返り作成
              </button>
              {lifecycle?.retrospective ? (
                <div className="retrospective-grid">
                  <p><strong>成功要因</strong>{lifecycle.retrospective.success_factors}</p>
                  <p><strong>改善点</strong>{lifecycle.retrospective.improvements}</p>
                  <p><strong>次回活かすこと</strong>{lifecycle.retrospective.next_learnings}</p>
                </div>
              ) : null}
            </article>
          </div>

          <details className="advanced-foldout" open>
            <summary>案件タイムライン</summary>
            <div className="project-event-list">
              {lifecycle?.timeline.length ? (
                lifecycle.timeline.map((event) => (
                  <div key={event.id}>
                    <time>{formatDate(event.created_at)}</time>
                    <strong>{eventLabels[event.event_type] ?? event.event_type}</strong>
                    <span>
                      {event.from_status ? `${event.from_status} → ` : ""}
                      {event.to_status || "記録"}
                    </span>
                    <p>{event.note}</p>
                  </div>
                ))
              ) : (
                <p>まだタイムラインはありません。</p>
              )}
            </div>
          </details>
        </div>
      ) : null}
    </section>
  );
});

function formatDate(value: string) {
  if (!value) return "未設定";
  return new Date(value).toLocaleString("ja-JP");
}

function formatReviewStatus(value?: string) {
  return value ? reviewLabels[value] ?? value : "未依頼";
}
