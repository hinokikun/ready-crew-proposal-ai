import { memo } from "react";
import { AlertCircle, CheckCircle2, Clock3, Loader2, RotateCcw } from "lucide-react";
import type { ActionQueueItem } from "@/types/app";

type ActionTimelineProps = {
  actions: ActionQueueItem[];
  onRetry?: (actionId: number) => void;
  retryingActionId?: number | null;
};

const statusLabel: Record<string, string> = {
  pending: "実行待ち",
  running: "実行中",
  success: "成功",
  failure: "失敗",
  retry_waiting: "リトライ待ち",
  needs_human: "人間確認"
};

function StatusIcon({ status }: { status: string }) {
  if (status === "success") return <CheckCircle2 size={17} aria-hidden="true" />;
  if (status === "running") return <Loader2 className="spin" size={17} aria-hidden="true" />;
  if (status === "failure" || status === "needs_human") return <AlertCircle size={17} aria-hidden="true" />;
  return <Clock3 size={17} aria-hidden="true" />;
}

function ActionTimelineBase({ actions, onRetry, retryingActionId }: ActionTimelineProps) {
  if (!actions.length) {
    return <p className="queue-empty">まだAI Orchestratorのキューはありません。</p>;
  }

  return (
    <div className="action-timeline" aria-label="AI Orchestrator action queue">
      {actions.map((action) => (
        <article className={`action-timeline-item is-${action.status}`} key={action.id}>
          <div className="action-timeline-icon">
            <StatusIcon status={action.status} />
          </div>
          <div className="action-timeline-body">
            <div className="action-timeline-main">
              <div>
                <strong>{action.action_label || action.action_type}</strong>
                <span>{action.agent}</span>
              </div>
              <em>{statusLabel[action.status] ?? action.status}</em>
            </div>
            <p>{action.result_summary || action.reason || "AI社長の判断待ちです。"}</p>
            <div className="action-timeline-meta">
              <span>{action.customer_name || "顧客未設定"}</span>
              <span>{action.project_name || `Project #${action.project_id ?? "-"}`}</span>
              {action.next_agent && <span>次: {action.next_agent}</span>}
              {action.retry_count > 0 && <span>Retry {action.retry_count}</span>}
            </div>
          </div>
          {onRetry && (action.status === "failure" || action.status === "retry_waiting") && (
            <button
              className="secondary-button queue-retry-button"
              type="button"
              onClick={() => onRetry(action.id)}
              disabled={retryingActionId === action.id}
            >
              {retryingActionId === action.id ? <Loader2 className="spin" size={15} aria-hidden="true" /> : <RotateCcw size={15} aria-hidden="true" />}
              再実行
            </button>
          )}
        </article>
      ))}
    </div>
  );
}

export const ActionTimeline = memo(ActionTimelineBase);
