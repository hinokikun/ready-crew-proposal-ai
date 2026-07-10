"use client";

import { useState } from "react";
import { createTrialReport, type TrialReportData } from "@/lib/api";
import { toFriendlyError } from "@/lib/errorMessage";

const numericLabels: Array<[keyof TrialReportData["numeric_summary"], string]> = [
  ["total_usage", "総利用回数"],
  ["proposal_generation", "提案書作成回数"],
  ["ppt_download", "PPTダウンロード回数"],
  ["error_count", "エラー発生回数"],
  ["feedback_count", "フィードバック件数"]
];

const feedbackLabels: Array<[keyof TrialReportData["feedback_summary"], string]> = [
  ["usable", "使えそう"],
  ["needs_revision", "修正すれば使えそう"],
  ["hard_to_use", "使いにくい"],
  ["comments", "コメント件数"]
];

export function AdminTrialReportPanel() {
  const [adminComment, setAdminComment] = useState("");
  const [report, setReport] = useState<TrialReportData | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [copyState, setCopyState] = useState<"idle" | "copied">("idle");
  const [error, setError] = useState("");

  async function generateReport() {
    setIsCreating(true);
    setError("");
    try {
      const response = await createTrialReport({ admin_comment: adminComment });
      setReport(response.report);
      setCopyState("idle");
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setError(`${friendly.title}。${friendly.action}`);
    } finally {
      setIsCreating(false);
    }
  }

  async function copyReport() {
    if (!report) return;
    try {
      await navigator.clipboard.writeText(report.markdown);
      setCopyState("copied");
      window.setTimeout(() => setCopyState("idle"), 1800);
    } catch {
      setError("レポートをコピーできませんでした。ブラウザのクリップボード権限を確認してください。");
    }
  }

  function downloadMarkdown() {
    if (!report) return;
    const blob = new Blob([report.markdown], { type: "text/markdown;charset=utf-8" });
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `AI営業秘書_試験導入レポート_${new Date().toISOString().slice(0, 10)}.md`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.URL.revokeObjectURL(url);
  }

  return (
    <section className="admin-trial-report-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">社内試験導入</p>
          <h2>試験導入レポート作成</h2>
        </div>
      </div>

      <p className="trial-report-note">
        利用状況・エラー・フィードバックの集計から、上司報告やAI研修報告に使える文章を作成します。顧客本文や生成本文は含めません。
      </p>

      <label className="field trial-report-comment">
        <span>管理者コメント欄</span>
        <textarea
          value={adminComment}
          onChange={(event) => setAdminComment(event.target.value)}
          placeholder="例：営業部3名で1週間試験利用。要約PPTの社内共有がしやすく、提案書初稿の作成時間短縮が見込めた。"
          rows={4}
        />
      </label>

      <div className="trial-report-actions">
        <button className="primary-button" disabled={isCreating} onClick={() => void generateReport()} type="button">
          {isCreating ? "レポート作成中" : "レポートを作成"}
        </button>
        <button className="secondary-button" disabled={!report} onClick={() => void copyReport()} type="button">
          {copyState === "copied" ? "コピーしました" : "レポートをコピー"}
        </button>
        <button className="secondary-button" disabled={!report} onClick={downloadMarkdown} type="button">
          Markdownで出力
        </button>
      </div>

      {error && <p className="trial-report-error">{error}</p>}

      {report ? (
        <div className="trial-report-preview">
          <section>
            <h3>要約</h3>
            <p>{report.summary_text}</p>
          </section>

          <section>
            <h3>数値サマリー</h3>
            <div className="trial-report-metrics">
              <article>
                <span>試験導入期間</span>
                <strong>{report.period.label}</strong>
              </article>
              {numericLabels.map(([key, label]) => (
                <article key={key}>
                  <span>{label}</span>
                  <strong>{report.numeric_summary[key]}件</strong>
                </article>
              ))}
            </div>
          </section>

          <section>
            <h3>フィードバック傾向</h3>
            <div className="trial-report-metrics">
              {feedbackLabels.map(([key, label]) => (
                <article key={key}>
                  <span>{label}</span>
                  <strong>{report.feedback_summary[key]}件</strong>
                </article>
              ))}
            </div>
          </section>

          <section>
            <h3>良かった点</h3>
            <ul>{report.good_points.map((item) => <li key={item}>{item}</li>)}</ul>
          </section>

          <section>
            <h3>課題</h3>
            <ul>{report.issues.map((item) => <li key={item}>{item}</li>)}</ul>
          </section>

          <section>
            <h3>次回改善案</h3>
            <ul>{report.next_actions.map((item) => <li key={item}>{item}</li>)}</ul>
          </section>

          <section>
            <h3>社内展開可否の所感</h3>
            <p>{report.rollout_opinion}</p>
          </section>

          <section>
            <h3>管理者コメント</h3>
            <p>{report.admin_comment || "未入力"}</p>
          </section>
        </div>
      ) : (
        <p className="trial-report-empty">管理者コメントを入力し、「レポートを作成」を押してください。</p>
      )}
    </section>
  );
}
