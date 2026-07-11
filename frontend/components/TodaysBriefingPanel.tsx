"use client";

import { memo, useEffect, useMemo, useRef, useState } from "react";
import { CheckCircle2, Clock3, Sparkles } from "lucide-react";
import { getTodayBriefing, saveBriefingEvent, type DailyBriefingData, type DailyBriefingSuggestion } from "@/lib/api";
import { getAnalyticsSessionId } from "@/lib/analytics";
import { toFriendlyError } from "@/lib/errorMessage";

type TodaysBriefingPanelProps = {
  onOpenCrm?: () => void;
};

const priorityClass: Record<string, string> = {
  高: "is-high",
  中: "is-medium",
  低: "is-low"
};

export const TodaysBriefingPanel = memo(function TodaysBriefingPanel({ onOpenCrm }: TodaysBriefingPanelProps) {
  const [briefing, setBriefing] = useState<DailyBriefingData | null>(null);
  const [completedKeys, setCompletedKeys] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [message, setMessage] = useState("");
  const viewedRef = useRef(false);

  async function loadBriefing() {
    setIsLoading(true);
    setMessage("");
    try {
      const response = await getTodayBriefing();
      setBriefing(response.briefing);
      if (!viewedRef.current) {
        viewedRef.current = true;
        void saveBriefingEvent({ session_id: getAnalyticsSessionId(), event_type: "viewed" });
      }
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setMessage(`${friendly.title} ${friendly.action}`);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadBriefing();
  }, []);

  const recommendedTitle = useMemo(() => briefing?.recommended_project?.title ?? "まずは案件状況を確認しましょう", [briefing]);

  async function handleOpenProject(item: DailyBriefingSuggestion) {
    void saveBriefingEvent({
      session_id: getAnalyticsSessionId(),
      event_type: "priority_clicked",
      project_id: item.project_id,
      item_key: item.key
    });
    onOpenCrm?.();
  }

  async function handleComplete(item: DailyBriefingSuggestion) {
    setCompletedKeys((current) => (current.includes(item.key) ? current : [...current, item.key]));
    void saveBriefingEvent({
      session_id: getAnalyticsSessionId(),
      event_type: "item_completed",
      project_id: item.project_id,
      item_key: item.key
    });
  }

  if (isLoading) {
    return (
      <section className="todays-briefing-panel" aria-label="今日のAIブリーフィング">
        <div className="briefing-loading">
          <Sparkles size={22} aria-hidden="true" />
          <span>今日の優先案件を整理しています...</span>
        </div>
      </section>
    );
  }

  return (
    <section className="todays-briefing-panel" aria-label="今日のAIブリーフィング">
      <div className="briefing-hero">
        <div>
          <p className="eyebrow">Today's Briefing</p>
          <h2>今日のAIブリーフィング</h2>
          <p>営業開始前に、レビュー待ち・修正依頼・停滞案件・受注見込みをまとめました。</p>
        </div>
        <button className="secondary-button" type="button" onClick={() => void loadBriefing()}>
          更新
        </button>
      </div>

      {message ? <p className="status-note">{message}</p> : null}

      {briefing ? (
        <>
          <div className="briefing-summary-grid">
            <BriefingMetric label="今日対応" value={briefing.summary.action_required_count} />
            <BriefingMetric label="レビュー待ち" value={briefing.summary.review_waiting} />
            <BriefingMetric label="修正依頼" value={briefing.summary.changes_requested} />
            <BriefingMetric label="期限近い" value={briefing.summary.due_soon} />
            <BriefingMetric label="受注予定" value={briefing.summary.expected_wins} />
            <BriefingMetric label="停滞案件" value={briefing.summary.stagnant} />
          </div>

          <div className="briefing-recommendation">
            <span>今日はこの案件から</span>
            <strong>{recommendedTitle}</strong>
            <p>{briefing.recommended_project?.reason ?? "新しい優先案件がないため、CRMの未完了案件を確認してください。"}</p>
          </div>

          <div className="briefing-layout">
            <article className="briefing-card">
              <div className="briefing-card-heading">
                <h3>AIからの提案</h3>
                <small>優先度順</small>
              </div>
              <div className="briefing-suggestion-list">
                {briefing.suggestions.length ? (
                  briefing.suggestions.map((item) => (
                    <div className={`briefing-suggestion ${priorityClass[item.priority] ?? ""}`} key={item.key}>
                      <div>
                        <span>{item.priority}</span>
                        <strong>{item.title}</strong>
                      </div>
                      <p>{item.reason}</p>
                      <dl>
                        <div><dt>期限</dt><dd>{item.deadline || "今日中に確認"}</dd></div>
                        <div><dt>レビュー</dt><dd>{formatReviewStatus(item.review_status)}</dd></div>
                        <div><dt>受注確率</dt><dd>{item.win_probability}%</dd></div>
                      </dl>
                      <div className="briefing-action-row">
                        <button className="secondary-button compact-button" type="button" onClick={() => void handleOpenProject(item)}>
                          案件を確認
                        </button>
                        <button
                          className="secondary-button compact-button"
                          type="button"
                          disabled={completedKeys.includes(item.key)}
                          onClick={() => void handleComplete(item)}
                        >
                          {completedKeys.includes(item.key) ? "完了済み" : "完了"}
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="helper-text">今日の優先提案はありません。案件メールを貼るか、CRMを確認してください。</p>
                )}
              </div>
            </article>

            <article className="briefing-card">
              <div className="briefing-card-heading">
                <h3>今日のタイムライン</h3>
                <small>CRMから推定</small>
              </div>
              <div className="briefing-timeline">
                {briefing.timeline.map((item) => (
                  <div key={`${item.time}-${item.label}`}>
                    <time>{item.time}</time>
                    <span><Clock3 size={14} aria-hidden="true" />{item.label}</span>
                    <p>{item.description}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <details className="briefing-agent-comments">
            <summary>AI社員コメントを見る</summary>
            <div>
              {briefing.agent_comments.map((item) => (
                <p key={item.agent}>
                  <CheckCircle2 size={15} aria-hidden="true" />
                  <strong>{item.agent}</strong>
                  <span>{item.comment}</span>
                </p>
              ))}
            </div>
          </details>
        </>
      ) : null}
    </section>
  );
});

function BriefingMetric({ label, value }: { label: string; value: number }) {
  return (
    <article>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function formatReviewStatus(value: string) {
  const labels: Record<string, string> = {
    draft: "下書き",
    review_requested: "レビュー待ち",
    approved: "承認済み",
    changes_requested: "修正依頼",
    rejected: "却下",
    "": "未依頼"
  };
  return labels[value] ?? value;
}
