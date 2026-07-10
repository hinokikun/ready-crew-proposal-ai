"use client";

import type { UsageDashboardData } from "@/types/app";

type AdminUsageDashboardPanelProps = {
  dashboard: UsageDashboardData | null;
  isDownloadingCsv: boolean;
  onDownloadCsv: () => void;
};

const emptyDashboard: UsageDashboardData = {
  summary: {
    total_usage: 0,
    today_usage: 0,
    week_usage: 0,
    proposal_generation: 0,
    ppt_download: 0,
    error_count: 0,
    feedback_count: 0
  },
  error_analysis: {
    api_limit: 0,
    backend_unreachable: 0,
    input_missing: 0,
    ppt_generation_failed: 0,
    auth_error: 0
  },
  users: [],
  features: [],
  feedback_summary: {
    usable: 0,
    needs_revision: 0,
    hard_to_use: 0,
    comments: 0
  }
};

const summaryItems = [
  ["総利用回数", "total_usage"],
  ["今日の利用回数", "today_usage"],
  ["今週の利用回数", "week_usage"],
  ["提案書作成回数", "proposal_generation"],
  ["PPTダウンロード回数", "ppt_download"],
  ["エラー発生回数", "error_count"],
  ["フィードバック件数", "feedback_count"]
] as const;

const errorItems = [
  ["API上限", "api_limit"],
  ["Backend未接続", "backend_unreachable"],
  ["入力不足", "input_missing"],
  ["PPT生成失敗", "ppt_generation_failed"],
  ["認証エラー", "auth_error"]
] as const;

const feedbackItems = [
  ["使えそう", "usable"],
  ["修正すれば使えそう", "needs_revision"],
  ["使いにくい", "hard_to_use"],
  ["コメント件数", "comments"]
] as const;

export function AdminUsageDashboardPanel({ dashboard, isDownloadingCsv, onDownloadCsv }: AdminUsageDashboardPanelProps) {
  const data = dashboard ?? emptyDashboard;

  return (
    <section className="admin-usage-dashboard-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">社内試験導入</p>
          <h2>利用状況ダッシュボード</h2>
        </div>
        <button className="secondary-button csv-download-button" disabled={isDownloadingCsv} onClick={onDownloadCsv} type="button">
          {isDownloadingCsv ? "CSV作成中" : "CSV出力"}
        </button>
      </div>

      <div className="usage-dashboard-grid">
        {summaryItems.map(([label, key]) => (
          <article key={key}>
            <span>{label}</span>
            <strong>{data.summary[key]}件</strong>
          </article>
        ))}
      </div>

      <div className="usage-dashboard-columns">
        <section className="usage-dashboard-section">
          <h3>エラー分析</h3>
          <div className="usage-dashboard-list">
            {errorItems.map(([label, key]) => (
              <div key={key}>
                <span>{label}</span>
                <strong>{data.error_analysis[key]}件</strong>
              </div>
            ))}
          </div>
        </section>

        <section className="usage-dashboard-section">
          <h3>フィードバック集計</h3>
          <div className="usage-dashboard-list">
            {feedbackItems.map(([label, key]) => (
              <div key={key}>
                <span>{label}</span>
                <strong>{data.feedback_summary[key]}件</strong>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="usage-dashboard-section">
        <h3>機能別の利用集計</h3>
        <div className="usage-dashboard-table-wrap">
          <table className="usage-dashboard-table">
            <thead>
              <tr>
                <th>機能</th>
                <th>利用回数</th>
                <th>成功</th>
                <th>失敗</th>
              </tr>
            </thead>
            <tbody>
              {data.features.map((item) => (
                <tr key={item.feature_key}>
                  <td>{item.feature_name}</td>
                  <td>{item.usage_count}件</td>
                  <td>{item.success_count}件</td>
                  <td>{item.failure_count}件</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="usage-dashboard-section">
        <h3>利用者別の簡易集計</h3>
        <div className="usage-dashboard-table-wrap">
          <table className="usage-dashboard-table">
            <thead>
              <tr>
                <th>ユーザー</th>
                <th>ロール</th>
                <th>利用回数</th>
                <th>最終利用日時</th>
                <th>成功</th>
                <th>失敗</th>
              </tr>
            </thead>
            <tbody>
              {data.users.length ? (
                data.users.map((item) => (
                  <tr key={`${item.user_id ?? item.user_name}-${item.user_role}`}>
                    <td>{item.user_name}</td>
                    <td>{item.user_role}</td>
                    <td>{item.usage_count}件</td>
                    <td>{item.last_used_at ? new Date(item.last_used_at).toLocaleString("ja-JP") : "-"}</td>
                    <td>{item.success_count}件</td>
                    <td>{item.failure_count}件</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6}>まだ利用ログはありません。</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </section>
  );
}
