"use client";

import { useEffect, useState } from "react";
import { getOperationReadiness, type OperationReadinessData, type OperationReadinessStatus } from "@/lib/api";
import { toFriendlyError } from "@/lib/errorMessage";

const statusLabels: Record<OperationReadinessStatus, string> = {
  ok: "OK",
  warning: "要確認",
  missing: "未設定"
};

export function AdminOperationReadinessPanel() {
  const [readiness, setReadiness] = useState<OperationReadinessData | null>(null);
  const [isChecking, setIsChecking] = useState(false);
  const [copyState, setCopyState] = useState<"idle" | "copied">("idle");
  const [error, setError] = useState("");

  useEffect(() => {
    void runCheck();
  }, []);

  async function runCheck() {
    setIsChecking(true);
    setError("");
    try {
      const response = await getOperationReadiness();
      setReadiness(response.readiness);
      setCopyState("idle");
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setError(`${friendly.title}。${friendly.action}`);
    } finally {
      setIsChecking(false);
    }
  }

  async function copyResult() {
    if (!readiness) return;
    try {
      await navigator.clipboard.writeText(readiness.markdown);
      setCopyState("copied");
      window.setTimeout(() => setCopyState("idle"), 1800);
    } catch {
      setError("チェック結果をコピーできませんでした。ブラウザのクリップボード権限を確認してください。");
    }
  }

  function downloadMarkdown() {
    if (!readiness) return;
    const blob = new Blob([readiness.markdown], { type: "text/markdown;charset=utf-8" });
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `AI営業秘書_運用準備チェック_${new Date().toISOString().slice(0, 10)}.md`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.URL.revokeObjectURL(url);
  }

  const scoreClass = readiness ? (readiness.score >= 85 ? "is-ok" : readiness.score >= 70 ? "is-warning" : "is-missing") : "";

  return (
    <section className="admin-operation-readiness-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">社内案内前チェック</p>
          <h2>運用準備チェック</h2>
        </div>
        <button className="secondary-button" disabled={isChecking} onClick={() => void runCheck()} type="button">
          {isChecking ? "確認中" : "再チェック"}
        </button>
      </div>

      <p className="operation-readiness-note">
        社内メンバーへ案内する前に、設定・接続・権限・セキュリティ面の準備状況を確認します。顧客本文や生成本文は含めません。
      </p>

      {error && <p className="operation-readiness-error">{error}</p>}

      {readiness ? (
        <>
          <div className={`operation-readiness-score ${scoreClass}`}>
            <span>運用準備スコア</span>
            <strong>{readiness.score}点</strong>
            <p>{readiness.score_label}</p>
          </div>

          <div className="operation-readiness-actions">
            <button className="secondary-button" onClick={() => void copyResult()} type="button">
              {copyState === "copied" ? "コピーしました" : "チェック結果をコピー"}
            </button>
            <button className="secondary-button" onClick={downloadMarkdown} type="button">
              Markdownで出力
            </button>
          </div>

          <section className="operation-readiness-section">
            <h3>自動チェック項目</h3>
            <div className="operation-readiness-list">
              {readiness.checks.map((item) => (
                <article className={`is-${item.status}`} key={item.key}>
                  <span>{statusLabels[item.status]}</span>
                  <div>
                    <strong>{item.label}</strong>
                    <p>{item.detail}</p>
                    {item.status !== "ok" && item.next_action && <small>{item.next_action}</small>}
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className="operation-readiness-section">
            <h3>セキュリティチェック</h3>
            <div className="operation-readiness-list">
              {readiness.security_checks.map((item) => (
                <article className={`is-${item.status}`} key={item.key}>
                  <span>{statusLabels[item.status]}</span>
                  <div>
                    <strong>{item.label}</strong>
                    <p>{item.detail}</p>
                    {item.status !== "ok" && item.next_action && <small>{item.next_action}</small>}
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className="operation-readiness-section">
            <h3>次にやること</h3>
            {readiness.next_actions.length ? (
              <ul>{readiness.next_actions.map((action) => <li key={action}>{action}</li>)}</ul>
            ) : (
              <p>主要な準備項目は整っています。少人数で試験利用を開始できます。</p>
            )}
          </section>
        </>
      ) : (
        <p className="operation-readiness-empty">運用準備チェックを読み込み中です。</p>
      )}
    </section>
  );
}
