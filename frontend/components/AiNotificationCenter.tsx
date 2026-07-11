"use client";

import { memo, useEffect, useMemo, useState } from "react";
import { Archive, Bell, CheckCircle2, Eye, RefreshCw } from "lucide-react";
import {
  archiveAiNotification,
  getAiNotifications,
  markAiNotificationActioned,
  markAiNotificationRead,
  runAiWatchEngine,
  type AiNotification,
  type AiNotificationCenterData
} from "@/lib/api";
import { toFriendlyError } from "@/lib/errorMessage";

type AiNotificationCenterProps = {
  onOpenCrm?: () => void;
};

const priorityClass: Record<string, string> = {
  高: "is-high",
  中: "is-medium",
  低: "is-low"
};

const emptyData: AiNotificationCenterData = {
  notifications: [],
  summary: {
    total: 0,
    unread: 0,
    high: 0,
    medium: 0,
    low: 0
  }
};

export const AiNotificationCenter = memo(function AiNotificationCenter({ onOpenCrm }: AiNotificationCenterProps) {
  const [data, setData] = useState<AiNotificationCenterData>(emptyData);
  const [isLoading, setIsLoading] = useState(true);
  const [message, setMessage] = useState("");

  async function loadNotifications(useWatch = false) {
    setIsLoading(true);
    setMessage("");
    try {
      const response = useWatch ? await runAiWatchEngine() : await getAiNotifications();
      setData(response);
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setMessage(`${friendly.title} ${friendly.action}`);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadNotifications(false);
  }, []);

  const topNotifications = useMemo(() => data.notifications.slice(0, 8), [data.notifications]);

  async function updateNotification(notification: AiNotification, action: "read" | "actioned" | "archive") {
    try {
      if (action === "read") {
        await markAiNotificationRead(notification.id);
      } else if (action === "actioned") {
        await markAiNotificationActioned(notification.id);
      } else {
        await archiveAiNotification(notification.id);
      }
      await loadNotifications(false);
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setMessage(`${friendly.title} ${friendly.action}`);
    }
  }

  function openRelatedProject(notification: AiNotification) {
    if (notification.status === "unread") {
      void updateNotification(notification, "read");
    }
    onOpenCrm?.();
  }

  return (
    <section className="ai-notification-center" aria-label="AI Notification Center">
      <div className="notification-center-header">
        <div className="notification-bell-wrap">
          <Bell size={22} aria-hidden="true" />
          {data.summary.unread > 0 ? <span>{data.summary.unread}</span> : null}
        </div>
        <div>
          <p className="eyebrow">AI Watch Engine</p>
          <h2>AI通知センター</h2>
          <p>AI社員が案件の停滞や確認漏れを見つけます。</p>
        </div>
        <button className="secondary-button compact-button" disabled={isLoading} onClick={() => void loadNotifications(true)} type="button">
          <RefreshCw size={15} aria-hidden="true" />
          更新
        </button>
      </div>

      <div className="notification-summary-row">
        <span>高 {data.summary.high}</span>
        <span>中 {data.summary.medium}</span>
        <span>低 {data.summary.low}</span>
      </div>

      {message ? <p className="status-note">{message}</p> : null}
      {isLoading ? <p className="helper-text">AIが通知を確認しています...</p> : null}

      <div className="notification-list">
        {topNotifications.length ? (
          topNotifications.map((notification) => (
            <article className={`notification-item ${priorityClass[notification.priority] ?? ""} ${notification.status === "unread" ? "is-unread" : ""}`} key={notification.id}>
              <div className="notification-item-head">
                <span>{notification.priority}</span>
                <strong>{notification.title}</strong>
              </div>
              <p>{notification.message}</p>
              <small>
                {notification.agent_name} / {notification.customer_name || notification.project_name || notification.source_type}
              </small>
              <div className="notification-action">
                <p>{notification.recommended_action}</p>
                <div>
                  <button className="icon-button" title="確認" type="button" onClick={() => openRelatedProject(notification)}>
                    <Eye size={15} aria-hidden="true" />
                  </button>
                  <button className="icon-button" title="対応済み" type="button" onClick={() => void updateNotification(notification, "actioned")}>
                    <CheckCircle2 size={15} aria-hidden="true" />
                  </button>
                  <button className="icon-button" title="アーカイブ" type="button" onClick={() => void updateNotification(notification, "archive")}>
                    <Archive size={15} aria-hidden="true" />
                  </button>
                </div>
              </div>
            </article>
          ))
        ) : (
          <p className="helper-text">現在、AIからの重要な通知はありません。</p>
        )}
      </div>
    </section>
  );
});
