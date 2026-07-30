"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, Loader2, ShieldCheck } from "lucide-react";

import { validateProposalForAcceptance, type ProposalValidationResult } from "@/lib/proposalValidation";
import type { PowerPointData } from "@/types/proposal";

type Props = {
  powerpointData: PowerPointData;
  proposalContext?: Record<string, unknown>;
};

const JUDGE_LABELS = {
  CUSTOMER_READY: "顧客へ提出可能",
  REVIEW_REQUIRED: "提出前に確認推奨",
  NOT_READY: "提出ブロック"
} as const;

export function ProposalValidationPanel({ powerpointData, proposalContext = {} }: Props) {
  const [result, setResult] = useState<ProposalValidationResult | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const validationKey = useMemo(
    () => `${powerpointData.deck_title}:${powerpointData.slides.length}:${powerpointData.slides.map((slide) => slide.title).join("|")}`,
    [powerpointData]
  );

  async function runValidation() {
    setIsLoading(true);
    setError("");
    try {
      const next = await validateProposalForAcceptance(powerpointData, proposalContext);
      setResult(next);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "提出可否チェックを完了できませんでした。");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError("");
    validateProposalForAcceptance(powerpointData, proposalContext)
      .then((next) => {
        if (!cancelled) setResult(next);
      })
      .catch((exc) => {
        if (!cancelled) setError(exc instanceof Error ? exc.message : "提出可否チェックを完了できませんでした。");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [validationKey]);

  const judge = result?.release_judge ?? "REVIEW_REQUIRED";
  const panelClass = result ? `proposal-validation-panel judge-${judge.toLowerCase().replaceAll("_", "-")}` : "proposal-validation-panel";

  return (
    <section className={panelClass} aria-label="顧客提出チェック">
      <div className="proposal-validation-heading">
        <div>
          <p className="eyebrow">顧客提出チェック</p>
          <h3>この提案書をそのまま出せるか確認</h3>
        </div>
        <button className="secondary-button compact" type="button" onClick={runValidation} disabled={isLoading}>
          {isLoading ? <Loader2 className="spin" size={16} aria-hidden="true" /> : <ShieldCheck size={16} aria-hidden="true" />}
          再チェック
        </button>
      </div>

      {isLoading && !result && (
        <div className="proposal-validation-loading" aria-live="polite">
          <Loader2 className="spin" size={18} aria-hidden="true" />
          営業・顧客・経営者の視点で確認しています。
        </div>
      )}

      {error && (
        <div className="proposal-validation-error" role="alert">
          <AlertTriangle size={18} aria-hidden="true" />
          <div>
            <strong>提出可否チェックを実行できませんでした</strong>
            <p>{error}</p>
          </div>
        </div>
      )}

      {result && (
        <>
          <div className="acceptance-hero">
            <div>
              <span className="acceptance-label">{JUDGE_LABELS[result.release_judge]}</span>
              <strong>{result.acceptance_scores.total_score}</strong>
              <small>総合100点満点</small>
            </div>
            <p>{result.summary}</p>
          </div>

          <div className="acceptance-score-grid">
            <Score label="経営者" value={result.acceptance_scores.executive_score} />
            <Score label="営業" value={result.acceptance_scores.sales_score} />
            <Score label="技術" value={result.acceptance_scores.technical_score} />
            <Score label="見せ方" value={result.acceptance_scores.presentation_score} />
            <Score label="ビジュアル" value={result.acceptance_scores.visual_score} />
            <Score label="事業価値" value={result.acceptance_scores.business_value_score} />
          </div>

          <div className="acceptance-prediction">
            <div>
              <span>修正なしで提出できる確率</span>
              <strong>{result.human_acceptance_prediction.no_revision_probability}%</strong>
            </div>
            <div>
              <span>30分以内の修正で提出できる確率</span>
              <strong>{result.human_acceptance_prediction.thirty_min_revision_probability}%</strong>
            </div>
          </div>

          {result.release_judge === "NOT_READY" && (
            <div className="proposal-validation-block" role="alert">
              <AlertTriangle size={18} aria-hidden="true" />
              <strong>この状態では顧客提出を止めてください。</strong>
            </div>
          )}

          <div className="validation-review-grid">
            <article>
              <strong>Red Team 指摘</strong>
              <ul>
                {(result.red_team_findings.length ? result.red_team_findings : [{ issue: "重大な指摘はありません。", improvement: "最終確認を行って提出できます。" }]).slice(0, 3).map((finding) => (
                  <li key={`${finding.issue}-${finding.improvement}`}>
                    <span>{finding.issue}</span>
                    <small>{finding.improvement}</small>
                  </li>
                ))}
              </ul>
            </article>
            <article>
              <strong>想定される顧客質問</strong>
              <ul>
                {result.customer_questions.slice(0, 4).map((item) => (
                  <li key={item.question}>
                    <span>{item.question}</span>
                    <small>{item.answer}</small>
                  </li>
                ))}
              </ul>
            </article>
          </div>

          <details className="validation-details">
            <summary>詳細レビューを見る</summary>
            <div className="validation-detail-section">
              <strong>コンサル提案書ベンチマーク</strong>
              <div className="persona-review-list">
                {result.benchmark_reviews.map((review) => (
                  <div key={review.benchmark}>
                    <CheckCircle2 size={16} aria-hidden="true" />
                    <span>{review.benchmark}</span>
                    <strong>{review.score}点</strong>
                    <small>構成{review.structure} / ストーリー{review.story} / 説得力{review.persuasion}</small>
                  </div>
                ))}
              </div>
            </div>
            <div className="validation-detail-section">
              <strong>ペルソナ別レビュー</strong>
            <div className="persona-review-list">
              {result.persona_reviews.map((review) => (
                <div key={review.persona}>
                  <CheckCircle2 size={16} aria-hidden="true" />
                  <span>{review.persona}</span>
                  <strong>{review.score}点</strong>
                  <small>{review.verdict}</small>
                </div>
              ))}
            </div>
            </div>
            <div className="validation-detail-section">
              <strong>スライド別レビュー</strong>
            <div className="slide-review-list">
              {result.slide_reviews.slice(0, 6).map((slide) => (
                <div key={`${slide.slide_no}-${slide.title}`}>
                  <span>{slide.slide_no}</span>
                  <p>{slide.title}</p>
                  <strong>{slide.persuasion_score}点</strong>
                </div>
              ))}
            </div>
            </div>
            <div className="validation-detail-section">
              <strong>Visual QA++</strong>
              <ul className="validation-compact-list">
                {(result.visual_qa_findings.length
                  ? result.visual_qa_findings.slice(0, 5)
                  : [{ category: "ok", severity: "info", message: "重大な視覚品質の懸念はありません。", recommendation: "最終確認を行って提出できます。" }]
                ).map((finding) => (
                  <li key={`${finding.category}-${finding.message}`}>
                    <span>{finding.severity}</span>
                    <p>{finding.message}</p>
                    <small>{finding.recommendation}</small>
                  </li>
                ))}
              </ul>
            </div>
            <div className="validation-detail-section">
              <strong>Version2.0からの品質改善</strong>
              <div className="acceptance-prediction">
                <div>
                  <span>平均改善率</span>
                  <strong>{result.regression_quality.average_improvement_rate}%</strong>
                </div>
                <div>
                  <span>基準</span>
                  <strong>{result.regression_quality.baseline}</strong>
                </div>
              </div>
            </div>
          </details>
        </>
      )}
    </section>
  );
}

function Score({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
