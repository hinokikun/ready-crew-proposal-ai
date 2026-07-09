"use client";

import type { FeedbackEntry, FeedbackRating, FeedbackSummary } from "@/types/app";

type AdminFeedbackPanelProps = {
  feedback: FeedbackEntry[];
  summary: FeedbackSummary;
};

const ratingLabels: Record<FeedbackRating, string> = {
  usable: "使えそう",
  needs_revision: "修正すれば使えそう",
  hard_to_use: "使いにくい"
};

export function AdminFeedbackPanel({ feedback, summary }: AdminFeedbackPanelProps) {
  return (
    <section className="admin-feedback-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">フィードバック</p>
          <h2>フィードバック一覧</h2>
        </div>
      </div>
      <div className="feedback-summary-grid">
        <article><span>使えそう</span><strong>{summary.usable}件</strong></article>
        <article><span>修正すれば使えそう</span><strong>{summary.needs_revision}件</strong></article>
        <article><span>使いにくい</span><strong>{summary.hard_to_use}件</strong></article>
        <article><span>コメント</span><strong>{summary.comments}件</strong></article>
      </div>
      {feedback.length ? (
        <div className="admin-feedback-list">
          {feedback.slice(0, 50).map((item) => (
            <article key={item.id}>
              <div>
                <strong>{ratingLabels[item.rating] ?? item.rating}</strong>
                <span>{new Date(item.created_at).toLocaleString("ja-JP")} / ロール: {item.user_role || "未確認"}</span>
              </div>
              <p>{item.comment || "コメントなし"}</p>
            </article>
          ))}
        </div>
      ) : (
        <p className="admin-feedback-empty">まだフィードバックはありません。</p>
      )}
    </section>
  );
}
