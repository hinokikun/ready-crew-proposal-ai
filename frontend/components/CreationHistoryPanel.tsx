"use client";

import { FormEvent, useState } from "react";
import { BusinessImprovementReportPanel } from "@/components/BusinessImprovementReportPanel";
import { downloadCreationHistoryCsv, getCreationHistory, type CreationHistoryItem } from "@/lib/api";

function formatDateTime(value?: string | null) {
  if (!value) return "-";
  return value.replace("T", " ").slice(0, 19);
}

export function CreationHistoryPanel() {
  const [items, setItems] = useState<CreationHistoryItem[]>([]);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isDownloadingCsv, setIsDownloadingCsv] = useState(false);
  const [error, setError] = useState("");
  const [loaded, setLoaded] = useState(false);

  async function loadHistory() {
    setIsLoading(true);
    setError("");
    try {
      const response = await getCreationHistory({ q: query, status, limit: 100 });
      setItems(response.items);
      setLoaded(true);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "作成履歴を取得できませんでした。");
    } finally {
      setIsLoading(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void loadHistory();
  }

  async function downloadCsv() {
    setIsDownloadingCsv(true);
    setError("");
    try {
      const blob = await downloadCreationHistoryCsv({ q: query, status, limit: 500 });
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "proposal-generation-history.csv";
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(url);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "CSVを出力できませんでした。");
    } finally {
      setIsDownloadingCsv(false);
    }
  }

  return (
    <details
      className="dashboard-details creation-history-panel"
      id="creation-history-panel"
      onToggle={(event) => {
        if (event.currentTarget.open && !loaded && !isLoading) void loadHistory();
      }}
    >
      <summary>作成履歴を開く</summary>
      <div className="section-heading">
        <div>
          <p className="eyebrow">History</p>
          <h2>作成履歴</h2>
        </div>
        <span>{items.length}件</span>
      </div>
      <form className="admin-user-form" onSubmit={handleSubmit}>
        <input
          aria-label="案件名、顧客名、作成者で検索"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="案件名、顧客名、作成者で検索"
        />
        <select aria-label="ステータス" value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="">すべて</option>
          <option value="success">成功</option>
          <option value="failure">失敗</option>
        </select>
        <button className="secondary-button" type="submit" disabled={isLoading}>
          {isLoading ? "検索中" : "検索"}
        </button>
        <button className="secondary-button" type="button" onClick={() => void downloadCsv()} disabled={isDownloadingCsv}>
          {isDownloadingCsv ? "CSV作成中" : "履歴CSV"}
        </button>
      </form>
      {error && <p className="status-note error">{error}</p>}
      {!isLoading && loaded && items.length === 0 && (
        <p className="history-empty">作成履歴はまだありません。案件を作成するとここに表示されます。</p>
      )}
      <div className="history-list">
        {items.map((item) => (
          <article className="history-item" key={item.id}>
            <div>
              <span>{formatDateTime(item.created_at)}</span>
              <strong>{item.project_name || item.feature_name || "案件名未設定"}</strong>
              <p>{item.customer_name || "顧客名未設定"} / {item.status === "success" ? "成功" : "失敗"}</p>
              <small>
                作成者: {item.created_by_name || item.created_by_email || "-"} / Organization: {item.organization_name || item.organization_id} / Workspace: {item.workspace_name || item.workspace_id}
              </small>
              <small>出力形式: {item.output_formats || item.output_type || "-"}</small>
              <small>合計生成時間: {Math.round(((item.total_generation_duration_ms ?? 0) / 1000) * 10) / 10}秒</small>
              {item.error_type && <small>エラー: {item.error_type}</small>}
            </div>
            <div className="history-actions">
              {item.beautiful_ai_url ? (
                <button className="secondary-button" type="button" onClick={() => window.open(item.beautiful_ai_url || "", "_blank", "noopener,noreferrer")}>
                  Beautiful.aiを開く
                </button>
              ) : (
                <span className="status-note">成果物URLがない場合は再出力してください。</span>
              )}
            </div>
          </article>
        ))}
      </div>
      <BusinessImprovementReportPanel />
    </details>
  );
}
