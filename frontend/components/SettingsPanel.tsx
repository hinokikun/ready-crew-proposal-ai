"use client";

import { API_BASE_URL } from "@/lib/config";
import type { HealthSnapshot } from "@/components/HealthStatus";
import type { UsageLogEntry } from "@/lib/storage";
import type { AuthUser } from "@/lib/auth";

type SettingsPanelProps = {
  health: HealthSnapshot | null;
  isAuthenticated: boolean;
  usageLogs?: UsageLogEntry[];
  currentUser?: AuthUser | null;
  dbLogCount?: number;
};

export function SettingsPanel({ health, isAuthenticated, usageLogs = [], currentUser = null, dbLogCount = 0 }: SettingsPanelProps) {
  const vercelUrl = typeof window !== "undefined" ? window.location.origin : "";

  return (
    <details className="settings-panel">
      <summary>設定</summary>
      <div className="settings-grid">
        <SettingItem label="Backend URL" value={API_BASE_URL} />
        <SettingItem label="ログイン状態" value={isAuthenticated ? "ログイン済み" : "未ログイン"} />
        <SettingItem label="ログインユーザー" value={currentUser?.email || "未確認"} />
        <SettingItem label="ロール" value={currentUser?.role || "未確認"} />
        <SettingItem label="DB接続状態" value={health?.dbStatus || "未確認"} />
        <SettingItem label="モックモード状態" value={health?.mockMode === null ? "未確認" : health?.mockMode ? "ON" : "OFF"} />
        <SettingItem label="最終接続確認日時" value={health?.checkedAt || "未確認"} />
        <SettingItem label="Vercel URL" value={vercelUrl || "未確認"} />
        <SettingItem label="Render URL" value={API_BASE_URL} />
        <SettingItem label="DB利用ログ件数" value={`${dbLogCount}件`} />
      </div>
      <div className="settings-note">
        <strong>注意事項</strong>
        <p>APIキー、APP_ACCESS_PASSWORD、個人情報、顧客の機密情報はこの画面に表示しません。環境変数はVercel/Renderの管理画面で確認してください。</p>
      </div>
      <div className="role-prep-panel">
        <strong>ユーザー権限</strong>
        <div className="role-prep-grid">
          <article><span>admin</span><p>全機能利用、ユーザー管理、ログ確認ができます。</p></article>
          <article><span>member</span><p>提案書生成、PPTX/PDF出力、業務AI利用ができます。</p></article>
          <article><span>viewer</span><p>Dashboardと履歴閲覧のみ。生成・出力はできません。</p></article>
        </div>
      </div>
      <div className="usage-log-panel">
        <strong>直近の利用ログ</strong>
        {usageLogs.length ? (
          <div className="usage-log-list">
            {usageLogs.slice(0, 8).map((log) => (
              <article key={log.id}>
                <span>{new Date(log.createdAt).toLocaleString("ja-JP")}</span>
                <strong>{log.featureName}</strong>
                <small>
                  入力文字数: {log.inputLength} / 出力: {log.outputType} / {log.status === "success" ? "成功" : `失敗 ${log.errorType}`}
                </small>
              </article>
            ))}
          </div>
        ) : (
          <p>まだ利用ログはありません。</p>
        )}
      </div>
    </details>
  );
}

function SettingItem({ label, value }: { label: string; value: string }) {
  return (
    <article>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}
