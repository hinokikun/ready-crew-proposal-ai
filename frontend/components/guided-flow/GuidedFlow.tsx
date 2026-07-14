"use client";

import { memo, useEffect, useMemo, useState } from "react";
import { CheckCircle2, ChevronDown, FileDown, FileText, HelpCircle, Sparkles } from "lucide-react";
import { BeautifulAiSimpleCard } from "@/components/guided-flow/BeautifulAiSimpleCard";
import { SimpleErrorMessage } from "@/components/guided-flow/SimpleErrorMessage";
import { StepFooter } from "@/components/guided-flow/StepFooter";
import { StepNavigation } from "@/components/guided-flow/StepNavigation";
import type {
  BeautifulAiSimpleRequirement,
  GuidedFlowPanels,
  GuidedProgressStage,
  GuidedQualityGate,
  GuidedStep,
  GuidedStepId,
  GuidedSummaryItem
} from "@/components/guided-flow/types";

type OutputChoice = "summary" | "detail" | "pdf" | "beautiful";

type GuidedFlowProps = {
  beautifulAiCanCreate: boolean;
  beautifulAiDisabledReason: string;
  beautifulAiError: string;
  beautifulAiIsCreating: boolean;
  beautifulAiRequirements: BeautifulAiSimpleRequirement[];
  beautifulAiResult?: { editor_url?: string; player_url?: string } | null;
  canCompleteQualityGate: boolean;
  canGenerate: boolean;
  canSeeDetailMode: boolean;
  canDownloadMainOutputs: boolean;
  detailMode: boolean;
  errorMessage: string;
  generationStages: GuidedProgressStage[];
  hasDownloadedSummary: boolean;
  hasProposal: boolean;
  isDownloadingDetail: boolean;
  isDownloadingPdf: boolean;
  isDownloadingSummary: boolean;
  isGenerating: boolean;
  onCompleteQualityGate: (items: string[]) => Promise<void> | void;
  onCreateBeautifulAi: () => Promise<void> | void;
  onDownloadDetail: () => Promise<void> | void;
  onDownloadPdf: () => Promise<void> | void;
  onDownloadSummary: () => Promise<void> | void;
  onGenerate: () => Promise<void> | void;
  onNewCase: () => void;
  onOpenBeautifulAiUrl: (url: string) => void;
  onOpenCrm: () => void;
  onRetry?: () => void;
  onShowGuide: () => void;
  onSourceTextChange: (value: string) => void;
  onToggleDetailMode: () => void;
  onUseSample: () => void;
  organizationName: string;
  panels: GuidedFlowPanels;
  qualityGate: GuidedQualityGate | null;
  qualityGateComplete: boolean;
  qualityGateIsLoading: boolean;
  roleLabel: string;
  showSalesCopilotMarker: boolean;
  sourceText: string;
  summaryItems: GuidedSummaryItem[];
  workspaceName: string;
};

const steps: GuidedStep[] = [
  { id: 1, shortLabel: "案件入力", title: "案件情報を入力" },
  { id: 2, shortLabel: "AI作成", title: "AIで提案書を作成" },
  { id: 3, shortLabel: "内容確認", title: "提案内容を確認" },
  { id: 4, shortLabel: "品質確認", title: "提出前チェック" },
  { id: 5, shortLabel: "出力", title: "出力方法を選択" },
  { id: 6, shortLabel: "改善", title: "AIレビューと改善" },
  { id: 7, shortLabel: "完了", title: "完了" }
];

const qualityItems = [
  "会社名に誤りがない",
  "金額が正しい",
  "納期が現実的",
  "提案内容に不足がない",
  "AI推測の項目を確認した",
  "社外提出前に上長確認した"
];

function truncate(value: string, max = 150) {
  const trimmed = value.trim();
  if (!trimmed) return "未入力";
  return trimmed.length > max ? `${trimmed.slice(0, max)}...` : trimmed;
}

function formatDateTime(value?: string | null) {
  if (!value) return "未取得";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("ja-JP", { dateStyle: "short", timeStyle: "short" });
}

function statusLabel(status: GuidedProgressStage["status"]) {
  if (status === "done") return "完了";
  if (status === "running") return "処理中";
  if (status === "error") return "エラー";
  return "待機中";
}

function GuidedFlowBase(props: GuidedFlowProps) {
  const [activeStep, setActiveStep] = useState<GuidedStepId>(1);
  const [checkedItems, setCheckedItems] = useState<Record<string, boolean>>({});
  const [selectedOutput, setSelectedOutput] = useState<OutputChoice>("summary");
  const [isCompletingGate, setIsCompletingGate] = useState(false);
  const [localNotice, setLocalNotice] = useState("");
  const hasInput = props.sourceText.trim().length > 0;
  const isOutputBusy = props.isDownloadingSummary || props.isDownloadingDetail || props.isDownloadingPdf || props.beautifulAiIsCreating;
  const uncheckedCount = qualityItems.filter((item) => !checkedItems[item]).length;
  const allQualityChecked = uncheckedCount === 0;

  useEffect(() => {
    if (props.isGenerating) setActiveStep(2);
  }, [props.isGenerating]);

  useEffect(() => {
    if (props.hasProposal && activeStep < 3) setActiveStep(3);
  }, [activeStep, props.hasProposal]);

  useEffect(() => {
    if (props.qualityGateComplete) {
      setCheckedItems(Object.fromEntries(qualityItems.map((item) => [item, true])));
    }
  }, [props.qualityGateComplete]);

  const completedSteps = useMemo(() => {
    const done = new Set<GuidedStepId>();
    if (hasInput) done.add(1);
    if (props.hasProposal) {
      done.add(2);
      if (activeStep > 3 || props.qualityGateComplete) done.add(3);
    }
    if (props.qualityGateComplete) done.add(4);
    if (props.hasDownloadedSummary || props.beautifulAiResult) done.add(5);
    if (activeStep > 6) done.add(6);
    if (activeStep === 7) done.add(7);
    return done;
  }, [activeStep, hasInput, props.beautifulAiResult, props.hasDownloadedSummary, props.hasProposal, props.qualityGateComplete]);

  function isStepAvailable(step: GuidedStepId) {
    if (step === 1) return true;
    if (step === 2) return hasInput || props.hasProposal;
    if (step === 3 || step === 4) return props.hasProposal;
    if (step === 5 || step === 6) return props.hasProposal && props.qualityGateComplete;
    return Boolean(props.hasProposal && (props.hasDownloadedSummary || props.beautifulAiResult));
  }

  async function startGeneration() {
    if (!hasInput) {
      setLocalNotice("案件情報を入力してください");
      return;
    }
    setLocalNotice("");
    setActiveStep(2);
    await props.onGenerate();
  }

  async function completeQualityGate() {
    if (!allQualityChecked || props.qualityGateComplete || !props.canCompleteQualityGate) return;
    setIsCompletingGate(true);
    setLocalNotice("");
    try {
      await props.onCompleteQualityGate(qualityItems);
    } finally {
      setIsCompletingGate(false);
    }
  }

  async function runSelectedOutput() {
    if (selectedOutput === "detail") {
      await props.onDownloadDetail();
      return;
    }
    if (selectedOutput === "pdf") {
      await props.onDownloadPdf();
      return;
    }
    if (selectedOutput === "beautiful") {
      await props.onCreateBeautifulAi();
      return;
    }
    await props.onDownloadSummary();
  }

  const outputDisabled =
    selectedOutput === "beautiful" ? !props.beautifulAiCanCreate || isOutputBusy : !props.canDownloadMainOutputs || isOutputBusy;

  return (
    <section className="guided-flow-shell" aria-label="AIウィザード" data-testid="guided-flow">
      <div className="guided-top-bar">
        <div>
          <p className="eyebrow">Simple Guided UI</p>
          <h2>営業AIオペレーションセンター</h2>
          <p>次へ進むだけで、提案書作成から提出前チェック、出力まで進められます。</p>
        </div>
        <div className="guided-context">
          <span>Organization: {props.organizationName || "未設定"}</span>
          <span>Workspace: {props.workspaceName || "未設定"}</span>
          <span>Role: {props.roleLabel}</span>
          {props.canSeeDetailMode && (
            <button className="secondary-button" onClick={props.onToggleDetailMode} type="button">
              {props.detailMode ? "通常モードに戻る" : "詳細モード"}
            </button>
          )}
        </div>
      </div>

      <div className="guided-user-dashboard" aria-label="今日やること">
        <article data-testid={props.showSalesCopilotMarker ? "sales-copilot" : undefined} aria-label="Sales Copilot">
          <span>Sales Copilot</span>
          <strong>{props.hasProposal ? "提出前チェックと出力を進めます" : "新しい案件を始めます"}</strong>
        </article>
        <article>
          <span>作業中の案件</span>
          <strong>{props.hasProposal ? "1件" : "まだ案件がありません"}</strong>
        </article>
        <article>
          <span>最近作成した提案書</span>
          <strong>{props.hasProposal ? "作成済み" : "作成するとここに表示されます"}</strong>
        </article>
        <article>
          <span>進行中のステップ</span>
          <strong>{steps.find((step) => step.id === activeStep)?.title}</strong>
        </article>
      </div>

      <StepNavigation activeStep={activeStep} completedSteps={completedSteps} isStepAvailable={isStepAvailable} onSelectStep={setActiveStep} steps={steps} />
      <SimpleErrorMessage message={props.errorMessage} onRetry={props.onRetry} />

      {activeStep === 1 && (
        <article className="guided-step-card guided-intake-step">
          <div className="section-heading">
            <div>
              <p className="eyebrow">STEP 1</p>
              <h2>案件情報を貼り付けてください</h2>
              <p>案件メール、議事録、ヒアリングメモをそのまま貼り付けられます。</p>
            </div>
          </div>
          <label className="field guided-source-field" htmlFor="guided-source-text">
            <span>案件メール・議事録・URL・メモ</span>
            <textarea
              data-testid="project-source-input"
              id="guided-source-text"
              onChange={(event) => {
                props.onSourceTextChange(event.target.value);
                setLocalNotice("");
              }}
              placeholder="Ready Crewの案件メール、議事録、ヒアリングメモをそのまま貼り付けてください"
              rows={8}
              value={props.sourceText}
            />
          </label>
          {localNotice && <p className="guided-inline-warning" role="alert">{localNotice}</p>}
          <div className="guided-aux-actions">
            <button className="secondary-button" onClick={props.onUseSample} type="button">
              <Sparkles size={16} aria-hidden="true" />
              サンプルを使う
            </button>
            <button className="text-button" onClick={props.onShowGuide} type="button">
              <HelpCircle size={16} aria-hidden="true" />
              使い方を見る
            </button>
          </div>
          <StepFooter disabled={!hasInput || !props.canGenerate} helpText={!hasInput ? "案件情報を入力してください" : undefined} isLoading={props.isGenerating} onNext={startGeneration} primaryLabel="この内容で提案書を作る" />
        </article>
      )}

      {activeStep === 2 && (
        <article className="guided-step-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">STEP 2</p>
              <h2>AIが提案書を作成しています</h2>
              <p>内部ではAI社員が順番に確認します。通常モードでは作業工程だけを表示します。</p>
            </div>
          </div>
          <div className="guided-progress-list" aria-live="polite">
            {props.generationStages.map((stage) => (
              <div className={`guided-progress-row is-${stage.status}`} key={stage.label}>
                <span>{statusLabel(stage.status)}</span>
                <strong>{stage.label}</strong>
                <small>{stage.helper}</small>
              </div>
            ))}
          </div>
          <details className="guided-detail-foldout">
            <summary>AI Workspaceの詳細を見る</summary>
            {props.panels.workspaceProgress}
          </details>
          <StepFooter backLabel="案件入力へ戻る" disabled={!props.hasProposal} helpText={props.hasProposal ? "作成が完了しました" : "作成完了後に自動で次へ進めます"} onBack={() => setActiveStep(1)} onNext={() => setActiveStep(3)} primaryLabel="内容を確認する" />
        </article>
      )}

      {activeStep === 3 && (
        <article className="guided-step-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">STEP 3</p>
              <h2>提案内容を確認してください</h2>
              <p>必要な情報だけを先に確認します。詳しい本文は詳細から見られます。</p>
            </div>
          </div>
          <div className="guided-summary-grid">
            {props.summaryItems.map((item) => (
              <article key={item.label}>
                <span>{item.label}</span>
                <p>{truncate(item.value)}</p>
                {item.inferred && <small>AI推測</small>}
              </article>
            ))}
          </div>
          <p className="guided-next-hint">次に、提出前チェックへ進んで内容を人が確認してください。</p>
          <details className="guided-detail-foldout">
            <summary>詳細を見る</summary>
            <p>提案書本文や過去の詳細パネルは詳細モードで確認できます。通常モードでは次の操作だけを表示します。</p>
          </details>
          <StepFooter backLabel="作成状況へ戻る" disabled={!props.hasProposal} onBack={() => setActiveStep(2)} onNext={() => setActiveStep(4)} primaryLabel="内容を確認しました。品質確認へ進む" />
        </article>
      )}

      {activeStep === 4 && (
        <article className="guided-step-card" data-testid="guided-quality-check">
          <div className="section-heading">
            <div>
              <p className="eyebrow">STEP 4</p>
              <h2>提出前に内容を確認してください</h2>
              <p>以下を確認し、問題がなければチェックしてください。</p>
            </div>
            <span>{props.qualityGateComplete ? "完了" : uncheckedCount < qualityItems.length ? "確認中" : "未確認"}</span>
          </div>
          {props.qualityGateComplete ? (
            <div className="guided-quality-complete">
              <CheckCircle2 size={22} aria-hidden="true" />
              <div>
                <strong>提出前チェックが完了しました</strong>
                <p>完了日時: {formatDateTime(props.qualityGate?.completed_at || props.qualityGate?.updated_at)}</p>
                <p>確認者: {props.roleLabel}</p>
                <p>ステータス: {props.qualityGate?.bypassed ? "管理者バイパス" : "完了"}</p>
              </div>
            </div>
          ) : (
            <div className="guided-quality-list" aria-label="提出前チェック項目">
              {qualityItems.map((item) => (
                <label className={checkedItems[item] ? "is-checked" : ""} key={item}>
                  <input
                    checked={Boolean(checkedItems[item])}
                    disabled={!props.canCompleteQualityGate || props.qualityGateIsLoading || isCompletingGate}
                    onChange={() => setCheckedItems((current) => ({ ...current, [item]: !current[item] }))}
                    type="checkbox"
                  />
                  <span>{item}</span>
                </label>
              ))}
            </div>
          )}
          <StepFooter
            backLabel="内容確認へ戻る"
            disabled={!props.qualityGateComplete && (!allQualityChecked || !props.canCompleteQualityGate)}
            helpText={props.qualityGateComplete ? "ダウンロード可能になりました" : allQualityChecked ? "すべて確認済みです" : `あと${uncheckedCount}項目の確認が必要です`}
            isLoading={isCompletingGate}
            onBack={() => setActiveStep(3)}
            onNext={props.qualityGateComplete ? () => setActiveStep(5) : completeQualityGate}
            primaryLabel={props.qualityGateComplete ? "出力方法を選ぶ" : "提出前チェックを完了する"}
          />
        </article>
      )}

      {activeStep === 5 && (
        <article className="guided-step-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">STEP 5</p>
              <h2>提案書を出力する</h2>
              <p>最初は要約PowerPointをおすすめします。その他の形式も選べます。</p>
            </div>
          </div>
          <div className="guided-output-grid">
            {[
              { id: "summary" as const, title: "要約PowerPoint", text: "短時間の説明向け" },
              { id: "detail" as const, title: "詳細PowerPoint", text: "社内確認・本提案向け" },
              { id: "pdf" as const, title: "見積PDF", text: "見積書として保存" }
            ].map((item) => (
              <button className={`guided-output-option ${selectedOutput === item.id ? "is-selected" : ""}`} key={item.id} onClick={() => setSelectedOutput(item.id)} type="button">
                <FileDown size={18} aria-hidden="true" />
                <strong>{item.title}</strong>
                <span>{item.text}</span>
              </button>
            ))}
            <button className={`guided-output-option ${selectedOutput === "beautiful" ? "is-selected" : ""}`} onClick={() => setSelectedOutput("beautiful")} type="button">
              <Sparkles size={18} aria-hidden="true" />
              <strong>Beautiful.ai</strong>
              <span>デザインされたプレゼンを作成</span>
            </button>
          </div>
          {selectedOutput === "beautiful" && (
            <BeautifulAiSimpleCard
              canCreate={props.beautifulAiCanCreate}
              disabledReason={props.beautifulAiDisabledReason}
              isCreating={props.beautifulAiIsCreating}
              onCreate={() => void props.onCreateBeautifulAi()}
              requirements={props.beautifulAiRequirements}
              resultLinks={props.beautifulAiResult ? { editorUrl: props.beautifulAiResult.editor_url, playerUrl: props.beautifulAiResult.player_url, onOpen: props.onOpenBeautifulAiUrl } : undefined}
            />
          )}
          {props.beautifulAiError && <p className="guided-inline-warning" role="alert">{props.beautifulAiError}</p>}
          <StepFooter
            backLabel="提出前チェックへ戻る"
            disabled={outputDisabled}
            helpText={selectedOutput === "beautiful" && !props.beautifulAiCanCreate ? props.beautifulAiDisabledReason : undefined}
            isLoading={isOutputBusy}
            onBack={() => setActiveStep(4)}
            onNext={() => void runSelectedOutput()}
            primaryLabel={selectedOutput === "beautiful" ? "Beautiful.aiで提案書を作成" : "選択した形式で出力する"}
          />
          <button className="text-button guided-next-link" onClick={() => setActiveStep(6)} type="button">
            AIレビューと改善へ進む
          </button>
        </article>
      )}

      {activeStep === 6 && (
        <article className="guided-step-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">STEP 6</p>
              <h2>AIレビューと改善</h2>
              <p>AIが提案書を確認します。スコアや内部根拠は折りたたみ内で確認できます。</p>
            </div>
          </div>
          <div className="guided-improvement-intro">
            <article><strong>良い点</strong><p>提案方針と構成を確認します。</p></article>
            <article><strong>修正した方がよい点</strong><p>ROI、競合比較、導入計画などを確認します。</p></article>
            <article><strong>おすすめ改善TOP5</strong><p>AIによる推定です。最終判断は人が確認してください。</p></article>
          </div>
          <details className="guided-detail-foldout" open>
            <summary>AIレビューと改善を開く</summary>
            <div className="guided-panel-stack">
              {props.panels.presentationReview}
              {props.panels.proposalOptimization}
            </div>
          </details>
          <StepFooter backLabel="出力へ戻る" onBack={() => setActiveStep(5)} onNext={() => setActiveStep(7)} primaryLabel="改善内容を確認しました" />
        </article>
      )}

      {activeStep === 7 && (
        <article className="guided-step-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">STEP 7</p>
              <h2>完了</h2>
              <p>作成した提案書と確認状態をまとめます。</p>
            </div>
          </div>
          <div className="guided-completion-grid">
            <article><FileText size={18} aria-hidden="true" /><strong>作成した提案書</strong><span>{props.hasProposal ? "作成済み" : "未作成"}</span></article>
            <article><CheckCircle2 size={18} aria-hidden="true" /><strong>提出前チェック</strong><span>{props.qualityGateComplete ? "完了" : "未完了"}</span></article>
            <article><FileDown size={18} aria-hidden="true" /><strong>ダウンロード済み出力</strong><span>{props.hasDownloadedSummary ? "要約PowerPoint" : "未確認"}</span></article>
            <article><Sparkles size={18} aria-hidden="true" /><strong>Beautiful.ai</strong><span>{props.beautifulAiResult ? "作成済み" : "未作成"}</span></article>
          </div>
          <StepFooter backLabel="改善へ戻る" onBack={() => setActiveStep(6)} onNext={props.onNewCase} primaryLabel="この案件を完了する" />
          <div className="guided-aux-actions">
            <button className="secondary-button" onClick={props.onNewCase} type="button">最初から新しい案件を作る</button>
            <button className="secondary-button" onClick={props.onOpenCrm} type="button">CRMで案件を見る</button>
            <button className="text-button" onClick={() => setActiveStep(6)} type="button">改訂版を作る</button>
          </div>
        </article>
      )}

      {props.detailMode && props.canSeeDetailMode && (
        <details className="guided-technical-detail" open>
          <summary><ChevronDown size={16} aria-hidden="true" /> 管理者向け診断を表示</summary>
          {props.panels.beautifulAiDiagnostics}
        </details>
      )}
    </section>
  );
}

export const GuidedFlow = memo(GuidedFlowBase);
