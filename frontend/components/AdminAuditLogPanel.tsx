"use client";

import type { AuditLog } from "@/types/app";

type AdminAuditLogPanelProps = {
  logs: AuditLog[];
};

export function AdminAuditLogPanel({ logs }: AdminAuditLogPanelProps) {
  return (
    <details className="settings-panel admin-audit-panel">
      <summary>監査ログ</summary>
      {logs.length ? (
        <div className="usage-log-list">
          {logs.slice(0, 12).map((log) => (
            <article key={log.id}>
              <span>{new Date(log.created_at).toLocaleString("ja-JP")}</span>
              <strong>
                {labelEvent(log.event_type)} / {log.status === "success" ? "成功" : "失敗"}
              </strong>
              <small>
                操作者: {log.user_email || "システム"} / 対象: {log.target_type || "-"} {log.target_id || ""}
              </small>
            </article>
          ))}
        </div>
      ) : (
        <p>監査ログはまだありません。</p>
      )}
    </details>
  );
}

function labelEvent(eventType: string) {
  const labels: Record<string, string> = {
    login: "ログイン",
    generate: "作成",
    save: "保存",
    delete: "削除",
    settings_change: "設定変更"
  };
  return labels[eventType] ?? eventType;
}
