"use client";

import type { ReactNode } from "react";
import {
  Clipboard,
  Download,
  FileCheck2,
  FileDown,
  FileText,
  History,
  Loader2,
  Mail,
  RotateCcw,
  Sparkles
} from "lucide-react";

export type ProposalResultSectionProps = {
  aiMinutes: { minutes: string[]; todos: string[]; nextActions: string[] };
  aiRecommendations: string[];
  beautifulAiError: string;
  beautifulAiResult: any;
  canCreateBeautifulAiOutput: boolean;
  canDownloadMainOutputs: boolean;
  chatReadiness: any;
  clearHistory: () => void;
  copyMarkdown: () => void;
  copyState: string;
  createBeautifulAiCurrent: () => void;
  currentGuideStep: number;
  dealEvaluation: { riskLabel: string; probability: number; positives: string[]; decision: string };
  displayedMarkdown: string;
  displayedProbability: number;
  displayedWin: {
    rank: string;
    label: string;
    riskLabel: string;
    riskScore: number;
    probability: number;
    projectedProbability: number;
    reason: string;
    riskFactors: string[];
    improvementActions: string[];
  };
  downloadEstimatePdfCurrent: () => void;
  downloadEstimatePdfFor: (result: any, form: any) => void;
  downloadMarkdown: (result?: any, form?: any) => void;
  downloadPowerPoint: () => void;
  downloadPowerPointFor: (result: any, form: any, summary: boolean) => void;
  downloadSummaryPowerPoint: () => void;
  draftEmail: any;
  editablePreviewSlides: any[];
  estimateSummary: any;
  form: any;
  formatDateTime: (value: string) => string;
  history: any[];
  isBeautifulAiReady: boolean;
  isCreatingBeautifulAi: boolean;
  isDownloadingEstimatePdf: boolean;
  isDownloadingPowerPoint: boolean;
  isDownloadingSummaryPowerPoint: boolean;
  isGuideEnabled: boolean;
  isLoading: boolean;
  liveProjectSummary: Array<{ title: string; items: string[] }>;
  openBeautifulAiUrl: (url: string) => void;
  outputDigest: Array<{ title: string; items: string[] }>;
  qualityScore: {
    total: number;
    proposal: number;
    persuasion: number;
    roi: number;
    differentiation: number;
    readability: number;
    improvements: string[];
  };
  renderBeautifulAiDiagnosticsPanel: (variant: "primary" | "detail") => ReactNode;
  restoreHistory: (entry: any) => void;
  result: {
    knowledge_insights?: {
      similar?: {
        matches: unknown[];
        recommendation: string;
        success_patterns: string[];
        lost_patterns: string[];
      };
    };
    powerpoint_generation_data: {
      deck_title: string;
      slides: Array<{ slide_no: number; title: string }>;
    };
  } | null;
  salesIndicators: any[];
  salesOpportunityScore: any;
  setShowEmailDraft: (updater: (current: boolean) => boolean) => void;
  setShowMinutes: (updater: (current: boolean) => boolean) => void;
  showEmailDraft: boolean;
  showMinutes: boolean;
  similarCases: Array<{ entry: any; score: number }>;
  strategyCards: Array<{ title: string; reason: string }>;
  updatePreviewSlide: (index: number, field: "title" | "body", value: string) => void;
  winRateImprovements: string[];
};

export function ProposalResultSection({
  aiMinutes,
  aiRecommendations,
  beautifulAiError,
  beautifulAiResult,
  canCreateBeautifulAiOutput,
  canDownloadMainOutputs,
  chatReadiness,
  clearHistory,
  copyMarkdown,
  copyState,
  createBeautifulAiCurrent,
  currentGuideStep,
  dealEvaluation,
  displayedMarkdown,
  displayedProbability,
  displayedWin,
  downloadEstimatePdfCurrent,
  downloadEstimatePdfFor,
  downloadMarkdown,
  downloadPowerPoint,
  downloadPowerPointFor,
  downloadSummaryPowerPoint,
  draftEmail,
  editablePreviewSlides,
  estimateSummary,
  form,
  formatDateTime,
  history,
  isBeautifulAiReady,
  isCreatingBeautifulAi,
  isDownloadingEstimatePdf,
  isDownloadingPowerPoint,
  isDownloadingSummaryPowerPoint,
  isGuideEnabled,
  isLoading,
  liveProjectSummary,
  openBeautifulAiUrl,
  outputDigest,
  qualityScore,
  renderBeautifulAiDiagnosticsPanel,
  restoreHistory,
  result,
  salesIndicators,
  salesOpportunityScore,
  setShowEmailDraft,
  setShowMinutes,
  showEmailDraft,
  showMinutes,
  similarCases,
  strategyCards,
  updatePreviewSlide,
  winRateImprovements
}: ProposalResultSectionProps) {
  return (
    <section className="result-panel" aria-label="生成結果">
      <section className="live-brief-panel" aria-label="現在整理された案件概要">
        <div className="live-brief-header">
          <div>
            <p className="eyebrow">案件概要</p>
            <h2>現在整理された案件概要</h2>
          </div>
          <span className={`decision-pill ${chatReadiness.ready ? "rank-a" : "rank-c"}`}>
            {chatReadiness.ready ? "作成可能" : "整理中"}
          </span>
        </div>
        <div className="live-brief-grid">
          {liveProjectSummary.map((section) => (
            <article className="live-brief-card" key={section.title}>
              <strong>{section.title}</strong>
              <ul>
                {section.items.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </article>
          ))}
        </div>
        <div className="next-action-panel compact-next-action">
          <strong>次にやること</strong>
          <ol>
            <li>案件概要を確認</li>
            <li>不足情報を追記</li>
            <li>提案書を作成</li>
            <li>要約PPT・見積PDFを確認</li>
          </ol>
        </div>
        <details className="analysis-foldout">
          <summary>詳細分析を開く</summary>
        <div className="win-prediction-card">
          <div>
            <span>AI受注予測</span>
            <strong>{dealEvaluation.riskLabel}</strong>
          </div>
          <div>
            <span>受注確率</span>
            <strong>{dealEvaluation.probability}%</strong>
          </div>
          <ul>
            {dealEvaluation.positives.slice(0, 3).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
        <div className="live-status-row">
          <div>
            <span>受注確率</span>
            <strong>{dealEvaluation.probability}%</strong>
          </div>
          <div>
            <span>予算適合</span>
            <strong>{estimateSummary.budgetFit}</strong>
          </div>
          <div>
            <span>競合分析</span>
            <strong>{form.competitor_site_url.trim() || form.competitor_company_name.trim() ? "反映済み" : "未確認"}</strong>
          </div>
        </div>
        <div className="recommendation-panel">
          <div className="opportunity-card">
            <span>案件化しやすさ</span>
            <strong>{salesOpportunityScore.stars}</strong>
            <p>{salesOpportunityScore.reasons.slice(0, 2).join(" / ")}</p>
          </div>
          <div className="recommendation-list">
            <strong>この案件ならこんな提案が刺さります</strong>
            <ol>
              {aiRecommendations.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ol>
          </div>
        </div>
        <div className="strategy-grid" aria-label="AI提案戦略">
          {strategyCards.map((strategy) => (
            <article className="strategy-card" key={strategy.title}>
              <span>AI提案戦略</span>
              <strong>{strategy.title}</strong>
              <p>{strategy.reason}</p>
            </article>
          ))}
        </div>
        <section className="preview-panel" aria-label="PowerPoint風プレビュー">
          <div className="preview-heading">
            <div>
              <p className="eyebrow">プレビュー</p>
              <h3>提案書プレビュー</h3>
            </div>
            <span>{editablePreviewSlides.length}枚</span>
          </div>
          <div className="preview-slide-grid">
            {editablePreviewSlides.map((slide, index) => (
              <article className="preview-slide" key={`${slide.title}-${index}`}>
                <span>{index + 1}</span>
                <input
                  value={slide.title}
                  onChange={(event) => updatePreviewSlide(index, "title", event.target.value)}
                  aria-label={`スライド${index + 1}タイトル`}
                />
                <textarea
                  value={slide.body}
                  onChange={(event) => updatePreviewSlide(index, "body", event.target.value)}
                  aria-label={`スライド${index + 1}本文`}
                  rows={4}
                />
              </article>
            ))}
          </div>
        </section>
        </details>
      </section>

      <div className="panel-heading">
        <div>
          <p className="eyebrow">作成結果</p>
          <h2>作成結果</h2>
        </div>
        <div className="toolbar">
          <button className="icon-button" type="button" onClick={copyMarkdown} disabled={!result} title="Markdownをコピー">
            <Clipboard size={18} aria-hidden="true" />
          </button>
          <button className="icon-button" type="button" onClick={() => downloadMarkdown()} disabled={!result} title="Markdownをダウンロード">
            <Download size={18} aria-hidden="true" />
          </button>
        </div>
      </div>

      {copyState === "copied" && <p className="copy-note">Markdownをコピーしました。</p>}

      {!result && !isLoading && (
        <div className="empty-state">
          <FileText size={40} aria-hidden="true" />
          <p>案件概要を入力して生成すると、提案書初稿がここに表示されます。</p>
        </div>
      )}

      {isLoading && (
        <div className="loading-state" aria-live="polite">
          <Loader2 className="spin" size={42} aria-hidden="true" />
          <strong>提案書初稿を作成しています</strong>
          <p>入力内容をもとに、営業提案で使える叩き台を整理しています。</p>
          <div className="progress-steps">
            <div className="is-active">
              <span>1</span>
              <strong>案件分析中</strong>
              <small>目的・課題・不足情報を確認</small>
            </div>
            <div>
              <span>2</span>
              <strong>提案構成作成中</strong>
              <small>ストーリーと章立てを整理</small>
            </div>
            <div>
              <span>3</span>
              <strong>資料作成準備中</strong>
              <small>PPTX・PDF出力データを準備</small>
            </div>
          </div>
        </div>
      )}

      {result && (
        <div className="output-layout">
          <section className="output-summary-panel" aria-label="生成結果サマリー">
            {outputDigest.map((section) => (
              <article className="output-summary-card" key={section.title}>
                <strong>{section.title}</strong>
                <ul>
                  {section.items.slice(0, 4).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
            ))}
            {result.knowledge_insights?.similar && (
              <article className="output-summary-card knowledge-output-card">
                <strong>過去の類似案件</strong>
                <ul>
                  <li>{result.knowledge_insights.similar.matches.length}件ヒット</li>
                  <li>{result.knowledge_insights.similar.recommendation}</li>
                  {(result.knowledge_insights.similar.success_patterns[0] || result.knowledge_insights.similar.lost_patterns[0]) && (
                    <li>{result.knowledge_insights.similar.success_patterns[0] || result.knowledge_insights.similar.lost_patterns[0]}</li>
                  )}
                </ul>
              </article>
            )}
          </section>

          <article className="markdown-preview">
            <pre>{displayedMarkdown}</pre>
          </article>

          <aside className="ppt-panel">
            <p className="eyebrow">出力</p>
            <h3>{result.powerpoint_generation_data.deck_title}</h3>
            <p className="ppt-help">おすすめ順です。まずは要約版で共有し、必要に応じて詳細版と見積書を確認します。</p>
            <div className="ppt-button-stack">
              <button
                className={`ppt-download-button summary ${isGuideEnabled && currentGuideStep === 5 ? "guide-target" : ""}`}
                type="button"
                onClick={downloadSummaryPowerPoint}
                disabled={!canDownloadMainOutputs || isDownloadingPowerPoint || isDownloadingSummaryPowerPoint || isDownloadingEstimatePdf || isCreatingBeautifulAi}
              >
                {isGuideEnabled && currentGuideStep === 5 && <span className="guide-label button-guide-label">次はこちら</span>}
                {isDownloadingSummaryPowerPoint ? (
                  <Loader2 className="spin" size={18} aria-hidden="true" />
                ) : (
                  <FileDown size={18} aria-hidden="true" />
                )}
                <span>
                  <strong>{isDownloadingSummaryPowerPoint ? "要約版作成中" : "要約PPTをダウンロード"}</strong>
                  <small>発表用</small>
                </span>
              </button>
              <button
                className="ppt-download-button beautiful-ai"
                type="button"
                onClick={createBeautifulAiCurrent}
                data-testid="beautiful-ai-create-button-detail"
                disabled={!canCreateBeautifulAiOutput}
              >
                {isCreatingBeautifulAi ? (
                  <Loader2 className="spin" size={18} aria-hidden="true" />
                ) : (
                  <Sparkles size={18} aria-hidden="true" />
                )}
                <span>
                  <strong>
                    {isCreatingBeautifulAi
                      ? "Beautiful.aiでスライドをデザインしています"
                      : isBeautifulAiReady
                        ? "Beautiful.aiで提案書を作成"
                        : "Beautiful.aiは未設定"}
                  </strong>
                  <small>外部デザイン編集用</small>
                </span>
              </button>
              {renderBeautifulAiDiagnosticsPanel("detail")}
              {beautifulAiResult && (
                <div className="beautiful-ai-result" aria-live="polite">
                  <strong>Beautiful.ai提案書を作成しました</strong>
                  <div>
                    {beautifulAiResult.editor_url && (
                      <button className="text-button" type="button" onClick={() => openBeautifulAiUrl(beautifulAiResult.editor_url)}>
                        Beautiful.aiで編集
                      </button>
                    )}
                    {beautifulAiResult.player_url && (
                      <button className="text-button" type="button" onClick={() => openBeautifulAiUrl(beautifulAiResult.player_url)}>
                        プレゼンテーションを表示
                      </button>
                    )}
                  </div>
                  <small>共有権限はBeautiful.ai側で確認してください。</small>
                </div>
              )}
              {beautifulAiError && <p className="beautiful-ai-error">{beautifulAiError}</p>}
              <button
                className="ppt-download-button"
                type="button"
                onClick={downloadPowerPoint}
                disabled={!canDownloadMainOutputs || isDownloadingPowerPoint || isDownloadingSummaryPowerPoint || isDownloadingEstimatePdf || isCreatingBeautifulAi}
              >
                {isDownloadingPowerPoint ? (
                  <Loader2 className="spin" size={18} aria-hidden="true" />
                ) : (
                  <FileDown size={18} aria-hidden="true" />
                )}
                <span>
                  <strong>{isDownloadingPowerPoint ? "作成中" : "詳細PPTをダウンロード"}</strong>
                  <small>詳細提案用</small>
                </span>
              </button>
              <button
                className="ppt-download-button pdf"
                type="button"
                onClick={downloadEstimatePdfCurrent}
                disabled={!canDownloadMainOutputs || isDownloadingPowerPoint || isDownloadingSummaryPowerPoint || isDownloadingEstimatePdf || isCreatingBeautifulAi}
              >
                {isDownloadingEstimatePdf ? (
                  <Loader2 className="spin" size={18} aria-hidden="true" />
                ) : (
                  <FileDown size={18} aria-hidden="true" />
                )}
                <span>
                  <strong>{isDownloadingEstimatePdf ? "PDF作成中" : "見積PDFをダウンロード"}</strong>
                  <small>見積確認用</small>
                </span>
              </button>
              <button className="ppt-download-button markdown" type="button" onClick={() => downloadMarkdown()}>
                <Download size={18} aria-hidden="true" />
                <span>
                  <strong>Markdown</strong>
                  <small>原稿確認用</small>
                </span>
              </button>
            </div>
            <details className="analysis-foldout output-analysis-foldout">
              <summary>詳細分析を開く</summary>
            <p className="eyebrow">営業評価</p>
            <div className="rating-stack">
              <div className={`rank-card rank-${displayedWin.rank.toLowerCase()}`}>
                <span>受注確率</span>
                <strong>{displayedProbability}%</strong>
                <small>{displayedWin.rank}ランク / {displayedWin.label}</small>
              </div>
              <div className={`metric-card rank-${displayedWin.rank.toLowerCase()}`}>
                <span>受注リスク</span>
                <strong className="risk-stars">{displayedWin.riskLabel}</strong>
                <small>{displayedWin.riskScore} / 5</small>
              </div>
              <div className={`metric-card rank-${displayedWin.rank.toLowerCase()}`}>
                <span>受注確率向上予測</span>
                <strong>{displayedWin.probability}% → {displayedWin.projectedProbability}%</strong>
                <small>改善アクション実施後</small>
              </div>
              {salesIndicators.map((indicator) => (
                <div className={`metric-card rank-${indicator.rank.toLowerCase()}`} key={indicator.title}>
                  <span>{indicator.title}</span>
                  <strong>{indicator.rank}</strong>
                  <small>{indicator.label}</small>
                </div>
              ))}
            </div>
            <p className="rank-reason">{displayedWin.reason}</p>

            <div className="factor-grid">
              <div>
                <strong>リスク要因</strong>
                <ul>
                  {displayedWin.riskFactors.slice(0, 3).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
              <div>
                <strong>改善アクション</strong>
                <ul>
                  {displayedWin.improvementActions.slice(0, 3).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="decision-box">{dealEvaluation.decision}</div>

            <div className="next-action-panel">
              <strong>次にやること</strong>
              <ol>
                <li>内容を確認</li>
                <li>不足情報を追記</li>
                <li>PowerPointをダウンロード</li>
                <li>人が最終確認して提出</li>
              </ol>
            </div>

            <section className="ai-quality-panel" aria-label="AI品質チェック">
              <div className="quality-total">
                <span>AI品質チェック</span>
                <strong>{qualityScore.total}点</strong>
                <small>100点満点</small>
              </div>
              <div className="quality-grid">
                <div><span>提案力</span><strong>{qualityScore.proposal}</strong></div>
                <div><span>説得力</span><strong>{qualityScore.persuasion}</strong></div>
                <div><span>ROI</span><strong>{qualityScore.roi}</strong></div>
                <div><span>差別化</span><strong>{qualityScore.differentiation}</strong></div>
                <div><span>読みやすさ</span><strong>{qualityScore.readability}</strong></div>
              </div>
              <ul>
                {qualityScore.improvements.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </section>

            <section className="ai-assist-output-panel" aria-label="AI追加支援">
              <button className="secondary-button" type="button" onClick={() => setShowEmailDraft((current) => !current)}>
                <Mail size={16} aria-hidden="true" />
                提案書送付メールを作る
              </button>
              {showEmailDraft && (
                <div className="draft-box">
                  <strong>件名</strong>
                  <p>{draftEmail.subject}</p>
                  <strong>本文</strong>
                  <p>{draftEmail.body}</p>
                  <strong>署名</strong>
                  <p>{draftEmail.signature}</p>
                </div>
              )}
              <button className="secondary-button" type="button" onClick={() => setShowMinutes((current) => !current)}>
                <FileCheck2 size={16} aria-hidden="true" />
                AI議事録を作る
              </button>
              {showMinutes && (
                <div className="draft-box">
                  <strong>議事録</strong>
                  <ul>{aiMinutes.minutes.map((item) => <li key={item}>{item}</li>)}</ul>
                  <strong>ToDo</strong>
                  <ul>{aiMinutes.todos.map((item) => <li key={item}>{item}</li>)}</ul>
                  <strong>次回アクション</strong>
                  <ul>{aiMinutes.nextActions.map((item) => <li key={item}>{item}</li>)}</ul>
                </div>
              )}
            </section>

            <section className="win-improvement-panel" aria-label="AI改善提案">
              <strong>もっとこうすると受注率が上がります</strong>
              <ul>
                {winRateImprovements.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </section>

            <section className="similar-case-panel" aria-label="似ている過去案件">
              <strong>似ている過去案件</strong>
              {similarCases.length ? (
                similarCases.map(({ entry, score }) => (
                  <button className="similar-case-button" type="button" key={entry.id} onClick={() => restoreHistory(entry)}>
                    <span>{entry.clientName}</span>
                    <small>類似度 {score} / 再利用</small>
                  </button>
                ))
              ) : (
                <p>作成履歴が増えると、似ている案件をここに表示します。</p>
              )}
            </section>
            </details>
            <div className="slide-list">
              {result.powerpoint_generation_data.slides.map((slide) => (
                <div className="slide-row" key={slide.slide_no}>
                  <span>{slide.slide_no}</span>
                  <p>{slide.title}</p>
                </div>
              ))}
            </div>
          </aside>
        </div>
      )}

      <section className="history-panel" aria-label="作成履歴">
        <div className="history-heading">
          <div>
            <p className="eyebrow">作成履歴</p>
            <h3>作成履歴</h3>
          </div>
          <button className="text-button" type="button" onClick={clearHistory} disabled={history.length === 0}>
            履歴を削除
          </button>
        </div>
        {history.length === 0 ? (
          <p className="history-empty">作成した案件はここにローカル保存されます。</p>
        ) : (
          <div className="history-list">
            {history.map((entry) => (
              <article className="history-item" key={entry.id}>
                <div>
                  <span>{formatDateTime(entry.createdAt)}</span>
                  <strong>{entry.clientName}</strong>
                  <p>{entry.title}</p>
                </div>
                <div className="history-actions">
                  <button className="icon-button subtle" type="button" onClick={() => restoreHistory(entry)} title="この履歴を開く">
                    <RotateCcw size={16} aria-hidden="true" />
                  </button>
                  <button className="icon-button subtle" type="button" onClick={() => downloadMarkdown(entry.result, entry.form)} title="Markdownを再ダウンロード">
                    <History size={16} aria-hidden="true" />
                  </button>
                  <button
                    className="icon-button subtle"
                    type="button"
                    onClick={() => downloadPowerPointFor(entry.result, entry.form, false)}
                    title="詳細PowerPointを再ダウンロード"
                  >
                    <FileDown size={16} aria-hidden="true" />
                  </button>
                  <button
                    className="icon-button subtle"
                    type="button"
                    onClick={() => downloadPowerPointFor(entry.result, entry.form, true)}
                    title="要約PowerPointを再ダウンロード"
                  >
                    <Download size={16} aria-hidden="true" />
                  </button>
                  <button
                    className="icon-button subtle"
                    type="button"
                    onClick={() => downloadEstimatePdfFor(entry.result, entry.form)}
                    title="見積書PDFを再ダウンロード"
                  >
                    <FileDown size={16} aria-hidden="true" />
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </section>
  );
}
