"use client";

import { memo, useCallback, useEffect, useMemo, useState } from "react";
import { Loader2, RefreshCw } from "lucide-react";
import { ActionTimeline } from "@/components/orchestrator/ActionTimeline";
import { getActionQueue, retryQueueAction } from "@/lib/api";
import type { ActionQueueItem } from "@/types/app";

const statusOrder = ["pending", "running", "success", "failure", "retry_waiting", "needs_human"];
const statusLabels: Record<string, string> = {
  pending: "実行待ち",
  running: "実行中",
  success: "成功",
  failure: "失敗",
  retry_waiting: "リトライ待ち",
  needs_human: "人の確認待ち"
};

function QueueMonitorBase() {
  const [queue, setQueue] = useState<ActionQueueItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [retryingActionId, setRetryingActionId] = useState<number | null>(null);
  const [notice, setNotice] = useState("");

  const counts = useMemo(() => {
    const next: Record<string, number> = {};
    queue.forEach((item) => {
      next[item.status] = (next[item.status] ?? 0) + 1;
    });
    return next;
  }, [queue]);

  const loadQueue = useCallback(async () => {
    setIsLoading(true);
    setNotice("");
    try {
      const response = await getActionQueue({ limit: 120 });
      setQueue(Array.isArray(response.queue) ? response.queue : []);
    } catch {
      setQueue([]);
      setNotice("AI Queue Monitorを読み込めませんでした。Backend接続と権限を確認してください。");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const retryAction = useCallback(
    async (actionId: number) => {
      setRetryingActionId(actionId);
      setNotice("");
      try {
        await retryQueueAction(actionId);
        setNotice("対象アクションを再実行待ちに戻しました。");
        await loadQueue();
      } catch {
        setNotice("再実行に失敗しました。権限またはBackendログを確認してください。");
      } finally {
        setRetryingActionId(null);
      }
    },
    [loadQueue]
  );

  useEffect(() => {
    void loadQueue();
  }, [loadQueue]);

  return (
    <section className="queue-monitor-panel">
      <div className="section-heading-row">
        <div>
          <p className="eyebrow">Version 13.0</p>
          <h3>AI Queue Monitor</h3>
          <p className="helper-text">AI社員の自律実行キューを確認します。本文や機密情報は保存しません。</p>
        </div>
        <button className="secondary-button" type="button" onClick={() => void loadQueue()} disabled={isLoading}>
          {isLoading ? <Loader2 className="spin" size={16} aria-hidden="true" /> : <RefreshCw size={16} aria-hidden="true" />}
          更新
        </button>
      </div>

      <div className="queue-summary-grid">
        {statusOrder.map((status) => (
          <article key={status}>
            <span>{statusLabels[status] ?? status}</span>
            <strong>{counts[status] ?? 0}</strong>
          </article>
        ))}
      </div>

      {notice ? <p className="status-note">{notice}</p> : null}
      {isLoading && !queue.length ? <p className="queue-loading">AI Queueを読み込み中です。</p> : null}
      <ActionTimeline actions={queue} onRetry={(actionId) => void retryAction(actionId)} retryingActionId={retryingActionId} />
    </section>
  );
}

export const QueueMonitor = memo(QueueMonitorBase);
