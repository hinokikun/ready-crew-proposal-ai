"use client";

import { memo, useCallback, useEffect, useState } from "react";
import { CheckCircle2, Loader2, XCircle } from "lucide-react";
import { listProposalReviews, updateProposalReview, type ProposalReviewEntry, type ProposalReviewStatus } from "@/lib/api";

const statusLabels: Record<string, string> = {
  draft: "下書き",
  review_requested: "レビュー依頼中",
  approved: "承認済み",
  changes_requested: "修正依頼",
  rejected: "却下"
};

export const AdminReviewPanel = memo(function AdminReviewPanel() {
  const [reviews, setReviews] = useState<ProposalReviewEntry[]>([]);
  const [comments, setComments] = useState<Record<number, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState("");

  const loadReviews = useCallback(async () => {
    setIsLoading(true);
    setMessage("");
    try {
      const response = await listProposalReviews();
      setReviews(response.reviews);
    } catch {
      setMessage("レビュー依頼一覧を読み込めませんでした。Backend接続を確認してください。");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadReviews();
  }, [loadReviews]);

  async function updateReview(review: ProposalReviewEntry, status: Extract<ProposalReviewStatus, "approved" | "changes_requested" | "rejected">) {
    setIsLoading(true);
    setMessage("");
    try {
      await updateProposalReview(review.id, {
        status,
        review_comment: comments[review.id] ?? review.review_comment ?? ""
      });
      setMessage(status === "approved" ? "承認しました。" : status === "changes_requested" ? "修正依頼を送信しました。" : "却下しました。");
      await loadReviews();
    } catch {
      setMessage("レビュー状態を更新できませんでした。権限またはBackend接続を確認してください。");
      setIsLoading(false);
    }
  }

  return (
    <section className="admin-review-panel" aria-label="レビュー依頼一覧">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Review</p>
          <h2>レビュー依頼一覧</h2>
          <p>上司・管理者が、提案内容の承認・修正依頼・却下を行います。</p>
        </div>
        <button type="button" className="secondary-button" onClick={() => void loadReviews()} disabled={isLoading}>
          {isLoading ? <Loader2 className="spin" size={16} aria-hidden="true" /> : null}
          更新
        </button>
      </div>

      {message && <p className="workspace-history-note">{message}</p>}

      <div className="review-request-list">
        {reviews.length ? reviews.map((review) => (
          <article className={`review-request-card is-${review.status}`} key={review.id}>
            <div>
              <strong>{review.project_name || "AI Workspace提案"}</strong>
              <span>{statusLabels[review.status] ?? review.status}</span>
            </div>
            <p>作成者: {review.creator_email || "未確認"} / 依頼: {formatDate(review.review_requested_at)} / 更新: {formatDate(review.updated_at)}</p>
            {review.review_comment && <small>コメント: {review.review_comment}</small>}
            <textarea
              value={comments[review.id] ?? review.review_comment ?? ""}
              onChange={(event) => setComments((current) => ({ ...current, [review.id]: event.target.value }))}
              placeholder="レビューコメントを入力"
            />
            <div className="review-action-row">
              <button type="button" onClick={() => void updateReview(review, "approved")} disabled={isLoading}>
                <CheckCircle2 size={16} aria-hidden="true" />
                承認
              </button>
              <button type="button" onClick={() => void updateReview(review, "changes_requested")} disabled={isLoading}>
                修正依頼
              </button>
              <button type="button" className="danger-button" onClick={() => void updateReview(review, "rejected")} disabled={isLoading}>
                <XCircle size={16} aria-hidden="true" />
                却下
              </button>
            </div>
          </article>
        )) : <p>レビュー依頼はまだありません。</p>}
      </div>
    </section>
  );
});

function formatDate(value: string | null) {
  if (!value) return "未設定";
  return new Date(value).toLocaleString("ja-JP");
}
