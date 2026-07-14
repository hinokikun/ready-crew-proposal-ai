"use client";

import { memo, useCallback, useEffect, useMemo, useState } from "react";
import { CheckCircle2, ExternalLink, Loader2, RotateCw, Sparkles, XCircle } from "lucide-react";
import {
  approvePresentationRevision,
  comparePresentationRevisions,
  createPresentationReview,
  createPresentationRevision,
  generateBeautifulAiRevision,
  getPresentationReviewTimeline,
  rejectPresentationRevision,
  type PresentationReview,
  type PresentationRevision,
  type PresentationRevisionChange
} from "@/lib/api";
import { toFriendlyError } from "@/lib/errorMessage";
import type { PresentationImprovement, UserRole } from "@/types/app";
import type { PowerPointData } from "@/types/proposal";

type PresentationReviewPanelProps = {
  projectId: string;
  projectName: string;
  powerpointData: PowerPointData | null;
  beautifulAiPresentationId?: string;
  beautifulAiPayload?: Record<string, unknown> | null;
  currentRole?: UserRole | string;
};

const STATUS_LABELS: Record<string, string> = {
  draft: "下書き",
  reviewing: "レビュー中",
  generation_requested: "生成依頼中",
  generating: "Beautiful.ai生成中",
  generated: "生成済み",
  approved: "承認済み",
  rejected: "却下",
  failed: "生成失敗",
  archived: "アーカイブ"
};

function canCreate(role?: string) {
  return role === "admin" || role === "member";
}

function canApprove(role?: string) {
  return role === "admin" || role === "manager";
}

function changeClass(changeType: string) {
  if (changeType === "追加") return "is-added";
  if (changeType === "削除") return "is-removed";
  if (changeType === "変更なし") return "is-neutral";
  return "is-modified";
}

function priorityLabel(priority?: string) {
  if (priority === "high") return "高";
  if (priority === "medium") return "中";
  return "低";
}

function statusLabel(status?: string) {
  return STATUS_LABELS[String(status || "")] || "未設定";
}

function actionKey(action: PresentationImprovement, index: number) {
  return action.action_id || `${action.type}-${action.target}-${index}`;
}

function upsertById<T extends { id: number }>(items: T[], nextItem: T) {
  return [nextItem, ...items.filter((item) => item.id !== nextItem.id)];
}

function PresentationReviewPanelBase({
  projectId,
  projectName,
  powerpointData,
  beautifulAiPresentationId = "",
  beautifulAiPayload = null,
  currentRole
}: PresentationReviewPanelProps) {
  const [reviews, setReviews] = useState<PresentationReview[]>([]);
  const [revisions, setRevisions] = useState<PresentationRevision[]>([]);
  const [changes, setChanges] = useState<PresentationRevisionChange[]>([]);
  const [selectedActionKeys, setSelectedActionKeys] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const latestReview = reviews[0] ?? null;
  const latestRevision = revisions[0] ?? null;
  const previousRevision = revisions[1] ?? null;
  const isReady = Boolean(projectId && powerpointData);
  const createAllowed = canCreate(String(currentRole || ""));
  const approveAllowed = canApprove(String(currentRole || ""));
  const actions = useMemo(
    () => latestReview?.actions?.length ? latestReview.actions : latestReview?.improvements ?? [],
    [latestReview]
  );

  const selectedActions = useMemo(
    () => actions.filter((action, index) => selectedActionKeys.has(actionKey(action, index))),
    [actions, selectedActionKeys]
  );

  const canCreateRevision = Boolean(latestReview && createAllowed && selectedActions.length > 0);
  const canGenerateBeautifulAi = Boolean(
    latestRevision &&
    approveAllowed &&
    beautifulAiPayload &&
    (latestRevision.approved || latestRevision.status === "approved" || latestRevision.status === "failed")
  );

  const loadTimeline = useCallback(async () => {
    if (!projectId) return;
    try {
      const response = await getPresentationReviewTimeline(projectId);
      setReviews(response.reviews);
      setRevisions(response.revisions);
      if (response.revisions.length) {
        const compared = await comparePresentationRevisions(projectId, response.revisions[1]?.id, response.revisions[0]?.id);
        setChanges(compared.changes);
      } else {
        setChanges([]);
      }
    } catch {
      setChanges([]);
    }
  }, [projectId]);

  useEffect(() => {
    void loadTimeline();
  }, [loadTimeline]);

  useEffect(() => {
    if (!actions.length) {
      setSelectedActionKeys(new Set());
      return;
    }
    setSelectedActionKeys(
      new Set(
        actions
          .map((action, index) => ({ action, index }))
          .filter(({ action }) => action.selected !== false && (action.priority === "high" || action.priority === "medium"))
          .map(({ action, index }) => actionKey(action, index))
      )
    );
  }, [actions]);

  const averageLabel = useMemo(() => {
    if (!latestReview) return "未レビュー";
    return `${Number(latestReview.average_score || latestReview.overall_score || 0).toFixed(1)} / 5.0`;
  }, [latestReview]);

  async function runReview() {
    if (!isReady || !powerpointData) return;
    setIsLoading(true);
    setError("");
    setNotice("");
    try {
      const response = await createPresentationReview({
        project_id: projectId,
        project_name: projectName,
        powerpoint_generation_data: powerpointData,
        beautiful_ai_presentation_id: beautifulAiPresentationId
      });
      setReviews((current) => upsertById(current, response.review));
      if (response.review.latest_revision) {
        setRevisions((current) => upsertById(current, response.review.latest_revision as PresentationRevision));
      }
      setNotice("AIレビューが完了しました。反映したい改善だけ選んでRevisionを作成してください。");
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setError(`${friendly.title}。${friendly.action}`);
    } finally {
      setIsLoading(false);
    }
  }

  async function createRevision() {
    if (!latestReview || !selectedActions.length) return;
    setIsLoading(true);
    setError("");
    setNotice("");
    try {
      await createPresentationRevision({
        review_id: latestReview.id,
        selected_actions: selectedActions,
        beautiful_ai_presentation_id: beautifulAiPresentationId || latestReview.beautiful_ai_presentation_id
      });
      await loadTimeline();
      setNotice("選択した改善をRevision下書きとして保存しました。管理者または上司の承認後にBeautiful.aiへ再生成できます。");
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setError(`${friendly.title}。${friendly.action}`);
    } finally {
      setIsLoading(false);
    }
  }

  async function approveLatestRevision() {
    if (!latestRevision) return;
    setIsLoading(true);
    setError("");
    setNotice("");
    try {
      await approvePresentationRevision(latestRevision.id);
      await loadTimeline();
      setNotice("Revisionを承認しました。Beautiful.aiで新しい版として再生成できます。");
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setError(`${friendly.title}。${friendly.action}`);
    } finally {
      setIsLoading(false);
    }
  }

  async function rejectLatestRevision() {
    if (!latestRevision) return;
    setIsLoading(true);
    setError("");
    setNotice("");
    try {
      await rejectPresentationRevision(latestRevision.id, "管理画面から却下");
      await loadTimeline();
      setNotice("Revisionを却下しました。");
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setError(`${friendly.title}。${friendly.action}`);
    } finally {
      setIsLoading(false);
    }
  }

  async function regenerateBeautifulAiRevision() {
    if (!latestRevision || !beautifulAiPayload) return;
    setIsLoading(true);
    setError("");
    setNotice("");
    try {
      const response = await generateBeautifulAiRevision(latestRevision.id, beautifulAiPayload);
      setRevisions((current) => upsertById(current, response.revision));
      await loadTimeline();
      setNotice("Beautiful.aiでRevisionを新規生成しました。既存プレゼンは上書きしていません。");
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setError(`${friendly.title}。${friendly.action}`);
    } finally {
      setIsLoading(false);
    }
  }

  function toggleAction(action: PresentationImprovement, index: number) {
    const key = actionKey(action, index);
    setSelectedActionKeys((current) => {
      const next = new Set(current);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  return (
    <section className="presentation-review-panel" aria-label="Presentation Review" data-testid="presentation-review-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Presentation Reviewer</p>
          <h2>Presentation Review</h2>
          <p>生成済み提案書を採点し、選択した改善だけをBeautiful.ai向けRevisionとして再生成します。</p>
        </div>
        <span>{averageLabel}</span>
      </div>

      {!isReady && <p className="status-note">提案書を作成すると、Presentation Reviewを実行できます。</p>}

      <div className="presentation-review-actions">
        <button className="primary-button" type="button" onClick={runReview} disabled={!isReady || !createAllowed || isLoading}>
          {isLoading ? <Loader2 className="spin" size={16} aria-hidden="true" /> : <Sparkles size={16} aria-hidden="true" />}
          AIレビュー
        </button>
        <button className="secondary-button" type="button" onClick={createRevision} disabled={!canCreateRevision || isLoading}>
          選択内容でRevision作成
        </button>
        {latestRevision && approveAllowed && (
          <>
            <button className="secondary-button" type="button" onClick={approveLatestRevision} disabled={isLoading || latestRevision.approved || latestRevision.status === "generated"}>
              <CheckCircle2 size={16} aria-hidden="true" />
              Revision承認
            </button>
            <button className="secondary-button" type="button" onClick={rejectLatestRevision} disabled={isLoading || latestRevision.status === "rejected" || latestRevision.status === "generated"}>
              <XCircle size={16} aria-hidden="true" />
              却下
            </button>
            <button className="secondary-button" type="button" onClick={regenerateBeautifulAiRevision} disabled={!canGenerateBeautifulAi || isLoading}>
              <RotateCw size={16} aria-hidden="true" />
              Beautiful.aiで再生成
            </button>
          </>
        )}
      </div>

      {!createAllowed && <p className="permission-note">viewerは閲覧のみです。レビュー作成やRevision作成はできません。</p>}
      {notice && <p className="success-note">{notice}</p>}
      {error && <p className="error-note">{error}</p>}

      {latestReview && (
        <div className="presentation-review-grid">
          <article className="presentation-review-card">
            <h3>AIレビュー項目</h3>
            <div className="score-list">
              {latestReview.scores.map((score) => (
                <div className="presentation-score-row" key={score.key}>
                  <p>
                    <span>{score.label}</span>
                    <strong>{"★".repeat(Math.max(1, Math.round(score.score)))} {Number(score.score).toFixed(1)}</strong>
                  </p>
                  {score.reason && <small>{score.reason}</small>}
                  {score.requires_human_review && <em>人の確認が必要</em>}
                </div>
              ))}
            </div>
          </article>

          <article className="presentation-review-card">
            <h3>改善候補を選択</h3>
            <p className="status-note">Beautiful.aiへは自動送信しません。反映したい改善だけ選んでください。</p>
            {actions.length ? (
              <ul className="presentation-improvement-list">
                {actions.slice(0, 12).map((item, index) => {
                  const key = actionKey(item, index);
                  const checked = selectedActionKeys.has(key);
                  return (
                    <li key={key}>
                      <label className="presentation-action-check">
                        <input type="checkbox" checked={checked} onChange={() => toggleAction(item, index)} />
                        <span className={changeClass(item.change_type)}>{item.change_type}</span>
                        <strong>{item.title || item.type}</strong>
                      </label>
                      <p>{item.instruction || item.summary}</p>
                      <small>優先度: {priorityLabel(item.priority)} / 対象: {item.target || "全体"}</small>
                    </li>
                  );
                })}
              </ul>
            ) : (
              <p>大きな改善候補はありません。</p>
            )}
          </article>
        </div>
      )}

      {revisions.length > 0 && (
        <details className="advanced-foldout presentation-revision-timeline" open>
          <summary>Revision Timeline</summary>
          <div className="revision-list">
            {revisions.map((revision, index) => (
              <article key={`${revision.id}-${index}`}>
                <strong>{revision.revision_label || `Proposal v${revision.revision_number}`}</strong>
                <span>
                  状態: {statusLabel(revision.status)} / Beautiful.ai: {revision.beautiful_ai_presentation_id || "未生成"}
                </span>
                <small>{revision.created_at} / {revision.approved ? "承認済み" : "未承認"}</small>
                {(revision.editor_url || revision.player_url) && (
                  <div className="presentation-link-row">
                    {revision.editor_url && (
                      <a href={revision.editor_url} target="_blank" rel="noreferrer">
                        Editor <ExternalLink size={14} aria-hidden="true" />
                      </a>
                    )}
                    {revision.player_url && (
                      <a href={revision.player_url} target="_blank" rel="noreferrer">
                        Player <ExternalLink size={14} aria-hidden="true" />
                      </a>
                    )}
                  </div>
                )}
              </article>
            ))}
          </div>
        </details>
      )}

      {(changes.length > 0 || (latestRevision && previousRevision)) && (
        <details className="advanced-foldout presentation-diff-panel" open>
          <summary>Revision差分</summary>
          {changes.length ? (
            <ul>
              {changes.map((change) => (
                <li className={changeClass(change.change_type)} key={change.id}>
                  <span>{change.change_type}</span>
                  <p>{change.change_summary}</p>
                  {(change.before_summary || change.after_summary) && (
                    <div className="presentation-diff-compare">
                      <small>Before: {change.before_summary || "-"}</small>
                      <small>After: {change.after_summary || "-"}</small>
                    </div>
                  )}
                  {change.human_action && <em>{change.human_action}</em>}
                </li>
              ))}
            </ul>
          ) : (
            <p>差分はまだありません。</p>
          )}
        </details>
      )}
    </section>
  );
}

export const PresentationReviewPanel = memo(PresentationReviewPanelBase);
