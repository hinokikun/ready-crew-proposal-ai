"use client";

import { useEffect, useState } from "react";
import { getImprovementDashboard, type ImprovementDashboardData } from "@/lib/api";
import { toFriendlyError } from "@/lib/errorMessage";

const roadmapLabels = {
  now: "今すぐ対応",
  this_month: "今月対応",
  future: "将来対応"
} as const;

export function AdminImprovementDashboardPanel() {
  const [dashboard, setDashboard] = useState<ImprovementDashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [copyState, setCopyState] = useState<"idle" | "copied">("idle");
  const [error, setError] = useState("");

  useEffect(() => {
    void loadDashboard();
  }, []);

  async function loadDashboard() {
    setIsLoading(true);
    setError("");
    try {
      const response = await getImprovementDashboard();
      setDashboard(response.dashboard);
      setCopyState("idle");
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setError(`${friendly.title}。${friendly.action}`);
    } finally {
      setIsLoading(false);
    }
  }

  async function copyDashboard() {
    if (!dashboard) return;
    try {
      await navigator.clipboard.writeText(dashboard.markdown);
      setCopyState("copied");
      window.setTimeout(() => setCopyState("idle"), 1800);
    } catch {
      setError("改善案をコピーできませんでした。ブラウザのクリップボード権限を確認してください。");
    }
  }

  function downloadMarkdown() {
    if (!dashboard) return;
    const blob = new Blob([dashboard.markdown], { type: "text/markdown;charset=utf-8" });
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `AI営業秘書_改善提案_${new Date().toISOString().slice(0, 10)}.md`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.URL.revokeObjectURL(url);
  }

  return (
    <section className="admin-improvement-dashboard-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">試験導入後の改善判断</p>
          <h2>改善提案ダッシュボード</h2>
        </div>
        <button className="secondary-button" disabled={isLoading} onClick={() => void loadDashboard()} type="button">
          {isLoading ? "分析中" : "再分析"}
        </button>
      </div>

      <p className="improvement-dashboard-note">
        利用ログ、エラー、フィードバック、運用準備チェックから、次に改善すべきことを整理します。顧客本文や生成本文は含めません。
      </p>

      {error && <p className="improvement-dashboard-error">{error}</p>}

      {dashboard ? (
        <>
          <div className="improvement-summary-grid">
            <article><span>総利用回数</span><strong>{dashboard.summary.total_usage}件</strong></article>
            <article><span>エラー</span><strong>{dashboard.summary.error_count}件</strong></article>
            <article><span>フィードバック</span><strong>{dashboard.summary.feedback_count}件</strong></article>
            <article><span>使いにくい</span><strong>{dashboard.summary.hard_to_use}件</strong></article>
            <article><span>運用準備</span><strong>{dashboard.summary.readiness_score}点</strong></article>
          </div>

          <section className="improvement-executive-summary">
            <h3>上司報告用まとめ</h3>
            <p>{dashboard.executive_summary}</p>
          </section>

          <div className="improvement-actions">
            <button className="secondary-button" onClick={() => void copyDashboard()} type="button">
              {copyState === "copied" ? "コピーしました" : "コピー"}
            </button>
            <button className="secondary-button" onClick={downloadMarkdown} type="button">
              Markdown出力
            </button>
          </div>

          <section className="improvement-section">
            <h3>AI改善提案</h3>
            <div className="improvement-card-list">
              {dashboard.improvements.map((item) => (
                <article className={`priority-${item.priority}`} key={`${item.priority}-${item.category}-${item.title}`}>
                  <div className="improvement-card-head">
                    <span>{item.priority}</span>
                    <small>{item.category}</small>
                  </div>
                  <strong>{item.title}</strong>
                  <dl>
                    <div><dt>理由</dt><dd>{item.reason}</dd></div>
                    <div><dt>想定効果</dt><dd>{item.expected_effect}</dd></div>
                    <div><dt>対応難易度</dt><dd>{item.difficulty}</dd></div>
                    <div><dt>次にやること</dt><dd>{item.next_step}</dd></div>
                  </dl>
                </article>
              ))}
            </div>
          </section>

          <section className="improvement-section">
            <h3>改善ロードマップ</h3>
            <div className="improvement-roadmap">
              {(Object.keys(roadmapLabels) as Array<keyof typeof roadmapLabels>).map((key) => (
                <article key={key}>
                  <span>{roadmapLabels[key]}</span>
                  {dashboard.roadmap[key].length ? (
                    <ul>{dashboard.roadmap[key].map((item) => <li key={item}>{item}</li>)}</ul>
                  ) : (
                    <p>該当する改善案はありません。</p>
                  )}
                </article>
              ))}
            </div>
          </section>
        </>
      ) : (
        <p className="improvement-dashboard-empty">改善提案を読み込み中です。</p>
      )}
    </section>
  );
}
