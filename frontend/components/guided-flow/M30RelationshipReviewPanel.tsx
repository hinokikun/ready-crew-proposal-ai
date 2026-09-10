import { useMemo, useState } from "react";
import { CheckCircle2, Pencil, X } from "lucide-react";
import { deriveActiveM30CanonicalCandidates } from "@/lib/m30StateEnvelope";
import type {
  M30CanonicalCandidateDto,
  M30CausalityRelationshipProposalDto,
  M30ReviewedCausalityRelationshipDto,
} from "@/types/m30Api";
import type { M30StateEnvelope } from "@/types/m30State";

type ReviewAction = "CONFIRM" | "CORRECT" | "REJECT";

type M30RelationshipReviewPanelProps = {
  state: M30StateEnvelope;
  onPropose: (requestedCount: number) => Promise<unknown>;
  onReview: (
    relationship: M30CausalityRelationshipProposalDto,
    action: ReviewAction,
    correctedFromId?: string,
    correctedToId?: string,
  ) => Promise<unknown>;
};

const roleLabels: Record<string, string> = {
  visible_issue: "見えている課題",
  root_cause: "根本原因",
  causal_state: "課題の状態",
  business_implication: "事業への影響",
  solution_direction: "解決の方向性",
};

function statusLabel(state: M30ReviewedCausalityRelationshipDto["review_state"] | undefined) {
  if (state === "CONFIRMED") return "確認済み";
  if (state === "CORRECTED") return "修正済み";
  if (state === "REJECTED") return "使用しない";
  return "未確認";
}

function latestReview(
  state: M30StateEnvelope,
  relationshipId: string,
): M30ReviewedCausalityRelationshipDto | null {
  for (let index = state.relationshipReviews.length - 1; index >= 0; index -= 1) {
    const review = state.relationshipReviews[index];
    if (review.original_relationship_id === relationshipId) return review;
  }
  return null;
}

function endpointLabel(candidate: M30CanonicalCandidateDto | undefined) {
  if (!candidate) return null;
  return `${roleLabels[candidate.semantic_role] || "確認項目"}: ${candidate.value}`;
}

export function M30RelationshipReviewPanel({ state, onPropose, onReview }: M30RelationshipReviewPanelProps) {
  const [isProposing, setIsProposing] = useState(false);
  const [pendingRelationshipId, setPendingRelationshipId] = useState<string | null>(null);
  const [editingRelationshipId, setEditingRelationshipId] = useState<string | null>(null);
  const [correctedFromId, setCorrectedFromId] = useState("");
  const [correctedToId, setCorrectedToId] = useState("");
  const [error, setError] = useState("");
  const activeNodes = useMemo(() => deriveActiveM30CanonicalCandidates(state), [state]);
  const nodeById = useMemo(() => new Map(activeNodes.map((node) => [node.candidate_id, node])), [activeNodes]);

  async function requestProposals() {
    if (isProposing || activeNodes.length === 0) return;
    setError("");
    setIsProposing(true);
    try {
      await onPropose(1);
    } catch {
      setError("因果関係の候補を取得できませんでした。通常の提案作成はそのまま進められます。");
    } finally {
      setIsProposing(false);
    }
  }

  async function submitReview(
    proposal: M30CausalityRelationshipProposalDto,
    action: ReviewAction,
  ) {
    if (pendingRelationshipId || latestReview(state, proposal.relationship_id)) return;
    if (action === "CORRECT" && (!correctedFromId || !correctedToId || correctedFromId === correctedToId)) return;
    setError("");
    setPendingRelationshipId(proposal.relationship_id);
    try {
      await onReview(
        proposal,
        action,
        action === "CORRECT" ? correctedFromId : undefined,
        action === "CORRECT" ? correctedToId : undefined,
      );
      setEditingRelationshipId(null);
      setCorrectedFromId("");
      setCorrectedToId("");
    } catch {
      setError("関係の確認結果を保存できませんでした。候補は未確認のままです。");
    } finally {
      setPendingRelationshipId(null);
    }
  }

  return (
    <section className="guided-semantic-confirmation" aria-labelledby="m30-relationship-review-heading" data-testid="m30-relationship-review">
      <div className="guided-semantic-confirmation__header">
        <div>
          <p className="eyebrow">追加確認</p>
          <h3 id="m30-relationship-review-heading">項目どうしの因果関係を確認する</h3>
          <p>確認済みの項目をもとに、AIが因果関係の候補を整理します。必要に応じて確認してください。ここで確認しなくても通常の提案作成は進められます。</p>
          <p>AIが提示した関係は候補です。確認・修正するまで承認済みにはなりません。</p>
        </div>
        {state.possiblyStale && <strong role="status">入力内容が変更されたため、この確認結果が古くなっている可能性があります。</strong>}
      </div>

      {activeNodes.length === 0 ? (
        <p className="guided-semantic-confirmation__hint" role="status">先に上の追加確認で、因果関係に使う項目を確認してください。</p>
      ) : (
        <div className="guided-semantic-card__actions">
          <button className="secondary-button" type="button" onClick={() => void requestProposals()} disabled={isProposing}>
            {isProposing ? "候補を取得中…" : "因果関係の候補を確認する"}
          </button>
        </div>
      )}

      {error && <p className="guided-semantic-confirmation__hint" role="alert">{error}</p>}

      {state.relationshipProposals.length > 0 && (
        <div className="guided-semantic-card-list">
          {state.relationshipProposals.map((proposal) => {
            const review = latestReview(state, proposal.relationship_id);
            const displayRelationship = review || proposal;
            const from = nodeById.get(displayRelationship.from_id);
            const to = nodeById.get(displayRelationship.to_id);
            const isPending = pendingRelationshipId === proposal.relationship_id;
            const isEditing = editingRelationshipId === proposal.relationship_id;
            const isReviewed = Boolean(review);

            return (
              <article className={`guided-semantic-card is-${(review?.review_state || proposal.review_state).toLowerCase()}`} key={proposal.relationship_id}>
                <div className="guided-semantic-card__topline">
                  <span className="guided-semantic-card__type">因果関係</span>
                  <span className="guided-semantic-card__status">{statusLabel(review?.review_state || proposal.review_state)}</span>
                </div>
                {!isReviewed && <span className="guided-semantic-card__ai-label">AIによる候補</span>}
                {from && to ? (
                  <div className="guided-semantic-handoff" aria-label="因果関係">
                    <span>{endpointLabel(from)}</span>
                    <span aria-hidden="true">→</span>
                    <span>{endpointLabel(to)}</span>
                  </div>
                ) : (
                  <p className="guided-semantic-confirmation__hint" role="status">この関係の項目を確認できないため、表示できません。</p>
                )}

                {isEditing && !isReviewed && (
                  <div className="guided-semantic-edit-row">
                    <label className="guided-semantic-field" htmlFor={`m30-relationship-from-${proposal.relationship_id}`}>
                      <span>起点</span>
                      <select id={`m30-relationship-from-${proposal.relationship_id}`} value={correctedFromId} onChange={(event) => setCorrectedFromId(event.target.value)} disabled={isPending}>
                        <option value="">項目を選択</option>
                        {activeNodes.map((node) => <option key={node.candidate_id} value={node.candidate_id}>{endpointLabel(node)}</option>)}
                      </select>
                    </label>
                    <label className="guided-semantic-field" htmlFor={`m30-relationship-to-${proposal.relationship_id}`}>
                      <span>終点</span>
                      <select id={`m30-relationship-to-${proposal.relationship_id}`} value={correctedToId} onChange={(event) => setCorrectedToId(event.target.value)} disabled={isPending}>
                        <option value="">項目を選択</option>
                        {activeNodes.map((node) => <option key={node.candidate_id} value={node.candidate_id}>{endpointLabel(node)}</option>)}
                      </select>
                    </label>
                  </div>
                )}

                {!isReviewed && from && to && !isEditing && (
                  <div className="guided-semantic-card__actions">
                    <button className="primary-button" type="button" onClick={() => void submitReview(proposal, "CONFIRM")} disabled={isPending}><CheckCircle2 size={15} aria-hidden="true" />この関係を確認</button>
                    <button className="secondary-button" type="button" onClick={() => { setEditingRelationshipId(proposal.relationship_id); setCorrectedFromId(proposal.from_id); setCorrectedToId(proposal.to_id); }} disabled={isPending}><Pencil size={15} aria-hidden="true" />関係を修正</button>
                    <button className="text-button" type="button" onClick={() => void submitReview(proposal, "REJECT")} disabled={isPending}><X size={15} aria-hidden="true" />この関係を使わない</button>
                  </div>
                )}
                {!isReviewed && isEditing && (
                  <div className="guided-semantic-card__actions">
                    <button className="primary-button" type="button" onClick={() => void submitReview(proposal, "CORRECT")} disabled={isPending || !correctedFromId || !correctedToId || correctedFromId === correctedToId}>修正内容を確定</button>
                    <button className="text-button" type="button" onClick={() => setEditingRelationshipId(null)} disabled={isPending}>キャンセル</button>
                  </div>
                )}
                {isReviewed && <span className="guided-semantic-card__ai-label">確認履歴として保存されています</span>}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
