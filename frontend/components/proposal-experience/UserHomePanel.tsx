"use client";

import { BarChart3, Clock3, FileText, History, Sparkles } from "lucide-react";
import type { HistoryEntry } from "@/components/app-shell/types";

type UserHomePanelProps = {
  hasCurrentProposal: boolean;
  isGenerating: boolean;
  recentHistory: HistoryEntry[];
  onNewProposal: () => void;
  onOpenAnalytics: () => void;
  onOpenHistory: () => void;
  onResumeProposal: (entry: HistoryEntry) => void;
};

function formatDateTime(value?: string | null) {
  if (!value) return "日時未記録";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("ja-JP", { dateStyle: "short", timeStyle: "short" });
}

function statusLabel(entry: HistoryEntry) {
  if (entry.result?.powerpoint_generation_data) return "提案書作成済み";
  return "作成途中";
}

export function UserHomePanel({
  hasCurrentProposal,
  isGenerating,
  recentHistory,
  onNewProposal,
  onOpenAnalytics,
  onOpenHistory,
  onResumeProposal
}: UserHomePanelProps) {
  const visibleHistory = recentHistory.slice(0, 5);

  return (
    <section className="user-home-panel" aria-label="利用者ホーム" data-testid="user-home-panel">
      <div className="user-home-hero">
        <div>
          <p className="eyebrow">AI営業秘書</p>
          <h2>今日は何をしますか？</h2>
          <p>案件メール、議事録、ヒアリングメモを貼り付けるだけで、AIが提案書の初稿を作成します。</p>
        </div>
        <button className="primary-button user-home-main-cta" type="button" onClick={onNewProposal}>
          <Sparkles size={20} aria-hidden="true" />
          新しく提案書を作る
        </button>
      </div>

      <div className="user-home-priority-grid" aria-label="よく使う操作">
        <article>
          <FileText size={20} aria-hidden="true" />
          <span>1</span>
          <strong>新しい提案書を作る</strong>
          <p>案件情報を貼るだけで開始できます。</p>
        </article>
        <article>
          <Clock3 size={20} aria-hidden="true" />
          <span>2</span>
          <strong>作成途中を再開する</strong>
          <p>{hasCurrentProposal || isGenerating ? "現在の作成内容があります。" : "最近の履歴からすぐ再開できます。"}</p>
        </article>
        <article>
          <History size={20} aria-hidden="true" />
          <span>3</span>
          <strong>最近の提案書を見る</strong>
          <p>過去の出力やCSVは履歴にまとまります。</p>
        </article>
        <article>
          <BarChart3 size={20} aria-hidden="true" />
          <span>4</span>
          <strong>詳細分析を見る</strong>
          <p>効果測定やレポートは必要な時だけ開きます。</p>
        </article>
      </div>

      <div className="user-home-section-heading">
        <div>
          <p className="eyebrow">最近の作成</p>
          <h3>最近作成した提案書</h3>
        </div>
        <button className="secondary-button" type="button" onClick={onOpenHistory}>
          作成履歴をすべて見る
        </button>
      </div>

      {visibleHistory.length > 0 ? (
        <div className="user-home-recent-list">
          {visibleHistory.map((entry) => (
            <article className="user-home-recent-card" key={entry.id}>
              <div>
                <span>{formatDateTime(entry.createdAt)}</span>
                <strong>{entry.title || "提案書"}</strong>
                <p>{entry.clientName || "顧客名未設定"} / {statusLabel(entry)}</p>
              </div>
              <button className="secondary-button" type="button" onClick={() => onResumeProposal(entry)}>
                続きを開く
              </button>
            </article>
          ))}
        </div>
      ) : (
        <div className="user-home-empty">
          <strong>まだ提案書がありません</strong>
          <p>最初の提案書を作成すると、ここに最近の履歴が表示されます。</p>
          <button className="primary-button" type="button" onClick={onNewProposal}>
            新しく提案書を作る
          </button>
        </div>
      )}

      <details className="user-home-advanced">
        <summary>詳細分析を見る</summary>
        <div>
          <p>提案内容の評価、業務改善レポート、利用状況は「分析・レポート」にまとめています。</p>
          <button className="secondary-button" type="button" onClick={onOpenAnalytics}>
            分析・レポートを開く
          </button>
        </div>
      </details>
    </section>
  );
}
