import { useState } from "react";
import type { M30CanonicalCandidateDto } from "@/types/m30Api";
import type { M30StateEnvelope } from "@/types/m30State";

type M30Role = "visible_issue" | "root_cause" | "causal_state" | "business_implication" | "solution_direction";
type ReviewAction = "CONFIRM" | "CORRECT" | "REJECT";

type M30CanonicalReviewPanelProps = {
  state: M30StateEnvelope;
  onPropose: (role: M30Role, requestedCount: number) => Promise<unknown>;
  onReview: (candidate: M30CanonicalCandidateDto, action: ReviewAction, correctedValue?: string) => Promise<unknown>;
};

const roleLabels: Record<M30Role, string> = {
  visible_issue: "見えている課題",
  root_cause: "根本原因",
  causal_state: "課題の状態",
  business_implication: "事業への影響",
  solution_direction: "解決の方向性"
};

const roleMaximums: Record<M30Role, number> = {
  visible_issue: 1,
  root_cause: 4,
  causal_state: 5,
  business_implication: 4,
  solution_direction: 1
};

const roles = Object.keys(roleLabels) as M30Role[];

function statusLabel(state: M30CanonicalCandidateDto["review_state"]) {
  if (state === "CONFIRMED") return "確認済み";
  if (state === "CORRECTED") return "修正済み";
  if (state === "REJECTED") return "使用しない";
  return "未確認";
}

function latestReview(state: M30StateEnvelope, candidateId: string) {
  for (let index = state.canonicalReviews.length - 1; index >= 0; index -= 1) {
    const review = state.canonicalReviews[index];
    if (review.original_candidate_id === candidateId) return review;
  }
  return null;
}

export function M30CanonicalReviewPanel({ state, onPropose, onReview }: M30CanonicalReviewPanelProps) {
  const [role, setRole] = useState<M30Role>("root_cause");
  const [pendingRole, setPendingRole] = useState<M30Role | null>(null);
  const [pendingCandidateId, setPendingCandidateId] = useState<string | null>(null);
  const [editingCandidateId, setEditingCandidateId] = useState<string | null>(null);
  const [editingValue, setEditingValue] = useState("");
  const [error, setError] = useState("");

  async function requestProposals() {
    if (pendingRole) return;
    setError("");
    setPendingRole(role);
    try {
      await onPropose(role, roleMaximums[role]);
    } catch {
      setError("候補の取得に失敗しました。必要な場合は、もう一度実行してください。");
    } finally {
      setPendingRole(null);
    }
  }

  async function submitReview(candidate: M30CanonicalCandidateDto, action: ReviewAction, correctedValue?: string) {
    if (pendingCandidateId || latestReview(state, candidate.candidate_id)) return;
    if (action === "CORRECT" && !correctedValue?.trim()) return;
    setError("");
    setPendingCandidateId(candidate.candidate_id);
    try {
      await onReview(candidate, action, action === "CORRECT" ? correctedValue : undefined);
      setEditingCandidateId(null);
      setEditingValue("");
    } catch {
      setError("確認結果を保存できませんでした。候補は未確認のままです。");
    } finally {
      setPendingCandidateId(null);
    }
  }

  return (
    <section className="guided-semantic-confirmation" aria-labelledby="m30-canonical-review-heading" data-testid="m30-canonical-review">
      <div className="guided-semantic-confirmation__header">
        <div>
          <p className="eyebrow">追加確認</p>
          <h3 id="m30-canonical-review-heading">提案内容をさらに整理する</h3>
          <p>必要に応じて、AI候補を追加で確認できます。ここで確認しなくても次へ進めます。</p>
          <p>AI候補は提案です。人が確定・修正・使用しないを選ぶまで、承認済みにはなりません。</p>
        </div>
        {state.possiblyStale && <strong role="status">入力内容が変更されたため、M30の確認結果が古くなっている可能性があります。</strong>}
      </div>
      <div className="guided-semantic-edit-row">
        <label className="guided-semantic-field" htmlFor="m30-canonical-role">
          <span>確認する項目</span>
          <select
            id="m30-canonical-role"
            className="guided-m30-role-select"
            value={role}
            onChange={(event) => setRole(event.target.value as M30Role)}
            disabled={Boolean(pendingRole)}
            style={{ border: "1px solid var(--border)", borderRadius: 10, minHeight: 42, padding: "0 12px", color: "var(--primary)", background: "#fff" }}
          >
            {roles.map((item) => <option key={item} value={item}>{roleLabels[item]}</option>)}
          </select>
        </label>
      </div>
      <div className="guided-semantic-card__actions">
        <button className="secondary-button" type="button" onClick={() => void requestProposals()} disabled={Boolean(pendingRole)}>
          {pendingRole ? "候補を取得中…" : "AI候補を確認する"}
        </button>
      </div>
      <p className="guided-semantic-confirmation__hint">この追加確認は任意です。AI候補の採用は、各項目への人の確認後にBackend結果で表示されます。</p>
      {error && <p className="guided-semantic-confirmation__hint" role="alert">{error}</p>}
      {state.canonicalProposals.length === 0 ? (
        <p className="guided-semantic-confirmation__hint">候補を取得すると、ここで一件ずつ確認できます。</p>
      ) : (
        <div className="guided-semantic-card-list">
          {state.canonicalProposals.map((proposal) => {
            const review = latestReview(state, proposal.candidate_id);
            const displayed = review ?? proposal;
            const isPending = pendingCandidateId === proposal.candidate_id;
            const isEditing = editingCandidateId === proposal.candidate_id;
            return (
              <article className={`guided-semantic-card is-${displayed.review_state.toLowerCase()}`} key={proposal.candidate_id}>
                <div className="guided-semantic-card__topline">
                  <span className="guided-semantic-card__type">{roleLabels[proposal.semantic_role as M30Role] || "M30確認項目"}</span>
                  <span className="guided-semantic-card__status">{statusLabel(displayed.review_state)}</span>
                </div>
                {!review && <span className="guided-semantic-card__ai-label">AIによる候補・要確認</span>}
                {isEditing ? (
                  <div className="guided-semantic-edit-row">
                    <label htmlFor={`m30-edit-${proposal.candidate_id}`}>修正内容</label>
                    <input id={`m30-edit-${proposal.candidate_id}`} value={editingValue} onChange={(event) => setEditingValue(event.target.value)} />
                    <button className="primary-button" type="button" onClick={() => void submitReview(proposal, "CORRECT", editingValue)} disabled={isPending}>内容を確定</button>
                    <button className="text-button" type="button" onClick={() => setEditingCandidateId(null)} disabled={isPending}>キャンセル</button>
                  </div>
                ) : <p className="guided-semantic-card__value">{displayed.value}</p>}
                {!review && (
                  <div className="guided-semantic-card__actions">
                    <button className="primary-button" type="button" onClick={() => void submitReview(proposal, "CONFIRM")} disabled={Boolean(pendingCandidateId)}>この内容で確定</button>
                    <button className="secondary-button" type="button" onClick={() => { setEditingCandidateId(proposal.candidate_id); setEditingValue(proposal.value); }} disabled={Boolean(pendingCandidateId)}>編集</button>
                    <button className="text-button" type="button" onClick={() => void submitReview(proposal, "REJECT")} disabled={Boolean(pendingCandidateId)}>この候補を使わない</button>
                  </div>
                )}
                {isPending && <small role="status">確認結果を保存中…</small>}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
