"use client";

import { memo, useEffect, useMemo, useState } from "react";
import { CheckCircle2, FileDown, HelpCircle, Pencil, Sparkles, X } from "lucide-react";
import { BeautifulAiSimpleCard } from "@/components/guided-flow/BeautifulAiSimpleCard";
import { SimpleErrorMessage } from "@/components/guided-flow/SimpleErrorMessage";
import { StepFooter } from "@/components/guided-flow/StepFooter";
import { StepNavigation } from "@/components/guided-flow/StepNavigation";
import { ProposalValidationPanel } from "@/components/ProposalValidationPanel";
import type { PowerPointData, SemanticCandidate, SemanticCandidateSet, SemanticRelationshipInput } from "@/types/proposal";
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
  beautifulAiManualUrl?: string;
  beautifulAiNotice?: string;
  beautifulAiRequirements: BeautifulAiSimpleRequirement[];
  beautifulAiResult?: { editor_url?: string; player_url?: string } | null;
  canCompleteQualityGate: boolean;
  canGenerate: boolean;
  canSeeDetailMode: boolean;
  canDownloadMainOutputs: boolean;
  detailMode: boolean;
  draftNotice?: string;
  draftSaveStatus?: string;
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
  onDiscardDraft?: () => void;
  onDownloadDetail: () => Promise<void> | void;
  onDownloadPdf: () => Promise<void> | void;
  onDownloadSummary: () => Promise<void> | void;
  onGenerate: () => Promise<boolean | string | void> | boolean | string | void;
  onNewCase: () => void;
  onOpenBeautifulAiUrl: (url: string) => void;
  onOpenCrm: () => void;
  onRetry?: () => void;
  onShowGuide: () => void;
  onSemanticCandidatesChange?: (candidates: SemanticCandidate[]) => void;
  onSemanticRelationshipsChange?: (relationships: SemanticRelationshipInput[]) => void;
  onSourceTextChange: (value: string) => void;
  onToggleDetailMode: () => void;
  onUseSample: () => void;
  organizationName: string;
  panels: GuidedFlowPanels;
  powerpointData?: PowerPointData | null;
  proposalContext?: Record<string, unknown>;
  qualityGate: GuidedQualityGate | null;
  qualityGateComplete: boolean;
  qualityGateIsLoading: boolean;
  semanticCandidates?: SemanticCandidateSet | null;
  semanticRelationships?: SemanticRelationshipInput[];
  roleLabel: string;
  showSalesCopilotMarker: boolean;
  sourceText: string;
  summaryItems: GuidedSummaryItem[];
  workspaceName: string;
};

const steps: GuidedStep[] = [
  { id: 1, shortLabel: "案件入力", title: "案件情報を貼り付ける" },
  { id: 2, shortLabel: "AI分析", title: "AIが提案の流れを作る" },
  { id: 3, shortLabel: "内容確認", title: "提案内容を確認する" },
  { id: 4, shortLabel: "提出前チェック", title: "提出前に確認する" },
  { id: 5, shortLabel: "出力", title: "ダウンロード・出力する" }
];

const baseQualityItems = [
  "会社名・担当者名に誤りがない",
  "金額・見積条件を確認した",
  "納期・スケジュールを確認した",
  "AI推測の項目を人の目で確認した",
  "実績・事例表記を確認した",
  "法務・契約条件に問題がない",
  "上長レビューが必要か確認した",
  "社外提出前に人が最終確認した"
];

const categoryQualityItems: Record<string, string[]> = {
  ai_ocr: [
    "対象帳票・抽出項目に誤りがない",
    "読取精度の目標を確認した",
    "連携先と出力形式を確認した",
    "例外処理と人手確認フローを確認した",
    "個人情報・機密情報の扱いを確認した",
    "PoC範囲と本導入条件を確認した",
    "社外提出前に人が最終確認した"
  ],
  rpa: [
    "対象業務と手順を確認した",
    "例外処理を確認した",
    "利用システムの権限を確認した",
    "停止時の対応を確認した",
    "効果測定方法を確認した",
    "社外提出前に人が最終確認した"
  ],
  crm: [
    "顧客・商談項目を確認した",
    "権限設計を確認した",
    "データ移行範囲を確認した",
    "レポート指標を確認した",
    "運用定着方法を確認した",
    "社外提出前に人が最終確認した"
  ]
};

function detectGuidedCategory(sourceText: string) {
  if (/(ai-ocr|aiocr|ocr|帳票|請求書|納品書|スキャン|読み取り|読取|抽出)/i.test(sourceText)) return "ai_ocr";
  if (/(rpa|定型業務|ロボット|入力作業|自動化)/i.test(sourceText)) return "rpa";
  if (/(crm|sfa|顧客管理|商談管理|営業管理|salesforce|hubspot)/i.test(sourceText)) return "crm";
  if (/(webサイト|サイトリニューアル|コーポレートサイト|ホームページ|cms|seo|wordpress|問い合わせフォーム)/i.test(sourceText)) return "web";
  return sourceText.trim() ? "business" : "business";
}

function qualityItemsForSource(sourceText: string) {
  const category = detectGuidedCategory(sourceText);
  return categoryQualityItems[category] || baseQualityItems;
}

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

function outputTitle(choice: OutputChoice) {
  if (choice === "detail") return "詳細版PowerPoint";
  if (choice === "pdf") return "見積PDF";
  if (choice === "beautiful") return "Beautiful.ai";
  return "要約版PowerPoint";
}

const criticalSemanticTypes = new Set(["decision_condition", "accountable_owner", "approver", "execution_action", "evidence", "decision_context"]);
const semanticTypeLabels: Record<string, string> = {
  decision_condition: "判断条件",
  accountable_owner: "責任者",
  approver: "承認者",
  execution_action: "実行内容",
  evidence: "根拠・出典",
  decision_context: "判断の対象"
};
function semanticStatusLabel(candidate: SemanticCandidate) {
  if (candidate.review_state === "CONFIRMED") return "確認済み";
  if (candidate.review_state === "CORRECTED") return "修正済み";
  if (candidate.review_state === "REJECTED") return "使用しない";
  return "未確認";
}

function GuidedFlowBase(props: GuidedFlowProps) {
  const [activeStep, setActiveStep] = useState<GuidedStepId>(1);
  const [checkedItems, setCheckedItems] = useState<Record<string, boolean>>({});
  const [selectedOutput, setSelectedOutput] = useState<OutputChoice>("summary");
  const [isCompletingGate, setIsCompletingGate] = useState(false);
  const [localNotice, setLocalNotice] = useState("");
  const [editingCandidateId, setEditingCandidateId] = useState<string | null>(null);
  const [editingValue, setEditingValue] = useState("");
  const hasInput = props.sourceText.trim().length > 0;
  const isOutputBusy = props.isDownloadingSummary || props.isDownloadingDetail || props.isDownloadingPdf || props.beautifulAiIsCreating;
  const qualityItems = useMemo(() => qualityItemsForSource(props.sourceText), [props.sourceText]);
  const uncheckedCount = qualityItems.filter((item) => !checkedItems[item]).length;
  const allQualityChecked = uncheckedCount === 0;
  const missingQuestions = props.summaryItems.filter((item) => item.inferred || /未定|要確認|未入力/.test(item.value)).slice(0, 3);
  const semanticCandidates = props.semanticCandidates?.candidates || [];
  const visibleSemanticCandidates = semanticCandidates.filter((candidate) => criticalSemanticTypes.has(candidate.semantic_type));
  const acceptedSemanticCount = visibleSemanticCandidates.filter((candidate) => candidate.review_state === "CONFIRMED" || candidate.review_state === "CORRECTED").length;
  const rejectedSemanticCount = visibleSemanticCandidates.filter((candidate) => candidate.review_state === "REJECTED").length;
  const resolvedSemanticCount = acceptedSemanticCount + rejectedSemanticCount;
  const semanticConfirmationReady = semanticCandidates.length === 0 || semanticCandidates.every((candidate) => candidate.review_state === "CONFIRMED" || candidate.review_state === "CORRECTED" || candidate.review_state === "REJECTED");
  const semanticConfirmationBlockingCount = semanticCandidates.filter((candidate) => candidate.review_state !== "CONFIRMED" && candidate.review_state !== "CORRECTED" && candidate.review_state !== "REJECTED").length;
  const [relationshipFrom, setRelationshipFrom] = useState("");
  const [relationshipTo, setRelationshipTo] = useState("");
  const [relationshipType, setRelationshipType] = useState<"causality" | "dependency">("causality");
  const reviewedCandidates = semanticCandidates.filter((candidate) => candidate.review_state === "CONFIRMED" || candidate.review_state === "CORRECTED");
  const relationships = props.semanticRelationships || [];

  useEffect(() => {
    if (props.isGenerating) setActiveStep(2);
  }, [props.isGenerating]);

  useEffect(() => {
    if (props.hasProposal && activeStep === 2) setActiveStep(3);
  }, [activeStep, props.hasProposal]);

  useEffect(() => {
    if (props.qualityGateComplete) {
      setCheckedItems(Object.fromEntries(qualityItems.map((item) => [item, true])));
    }
  }, [props.qualityGateComplete, qualityItems]);

  const completedSteps = useMemo(() => {
    const done = new Set<GuidedStepId>();
    if (hasInput) done.add(1);
    if (props.hasProposal) {
      done.add(2);
      if (activeStep > 3 || props.qualityGateComplete) done.add(3);
    }
    if (props.qualityGateComplete) done.add(4);
    if (props.hasDownloadedSummary || props.beautifulAiResult) done.add(5);
    return done;
  }, [activeStep, hasInput, props.beautifulAiResult, props.hasDownloadedSummary, props.hasProposal, props.qualityGateComplete]);

  function isStepAvailable(step: GuidedStepId) {
    if (step === 1) return true;
    if (step === 2) return hasInput || props.hasProposal;
    if (step === 3) return props.hasProposal;
    if (step === 4) return props.hasProposal && (activeStep !== 3 || semanticConfirmationReady);
    if (step === 5) return props.hasProposal;
    return false;
  }

  async function startGeneration() {
    if (!hasInput) {
      setLocalNotice("案件メール、議事録、ヒアリングメモなどを貼り付けてください。");
      return;
    }
    setLocalNotice("");
    setActiveStep(2);
    const generated = await props.onGenerate();
    if (typeof generated === "string") {
      setLocalNotice(generated);
      setActiveStep(1);
    } else if (generated === false) {
      setActiveStep(1);
    }
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

  function confirmSemanticCandidate(candidate: SemanticCandidate) {
    props.onSemanticCandidatesChange?.(semanticCandidates.map((item) => item.id === candidate.id ? { ...item, review_state: "CONFIRMED", confirmation_authority: "USER_EXPLICIT" } : item));
  }

  function startSemanticEdit(candidate: SemanticCandidate) {
    setEditingCandidateId(candidate.id);
    setEditingValue(candidate.value);
  }

  function saveSemanticEdit(candidate: SemanticCandidate) {
    const value = editingValue.trim();
    if (!value) return;
    props.onSemanticCandidatesChange?.(semanticCandidates.map((item) => item.id === candidate.id ? { ...item, value, authority: "USER_EXPLICIT", review_state: "CORRECTED", inferred: false, original_candidate_id: item.original_candidate_id || item.id, confirmation_authority: "USER_EXPLICIT" } : item));
    setEditingCandidateId(null);
    setEditingValue("");
  }

  function rejectSemanticCandidate(candidate: SemanticCandidate) {
    props.onSemanticCandidatesChange?.(semanticCandidates.map((item) => item.id === candidate.id ? { ...item, review_state: "REJECTED" } : item));
  }

  function addRelationship() {
    if (!relationshipFrom || !relationshipTo || relationshipFrom === relationshipTo) return;
    if (!reviewedCandidates.some((candidate) => candidate.id === relationshipFrom) || !reviewedCandidates.some((candidate) => candidate.id === relationshipTo)) return;
    props.onSemanticRelationshipsChange?.([...relationships, { from_item: relationshipFrom, to_item: relationshipTo, relationship_type: relationshipType, review_state: "CONFIRMED", authority: "USER_EXPLICIT", confirmation_authority: "USER_EXPLICIT", provenance_state: "supplied" }]);
    setRelationshipFrom("");
    setRelationshipTo("");
  }

  function removeRelationship(index: number) {
    props.onSemanticRelationshipsChange?.(relationships.filter((_, relationshipIndex) => relationshipIndex !== index));
  }

  function continueToQualityGate() {
    if (!props.hasProposal || !semanticConfirmationReady) return;
    setActiveStep(4);
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
  const outputHelpText =
    selectedOutput === "beautiful" && !props.beautifulAiCanCreate
      ? props.beautifulAiDisabledReason
      : !props.qualityGateComplete
        ? "提出前チェックを完了するとダウンロードできます。"
        : undefined;
  const currentStepTitle = steps.find((step) => step.id === activeStep)?.title || "案件情報を貼り付ける";

  return (
    <section className="guided-flow-shell" aria-label="AI営業秘書の提案書作成フロー" data-testid="guided-flow">
      <div className="guided-top-bar">
        <div>
          <p className="eyebrow">提案書作成</p>
          <h2>案件情報を貼り付けるだけで、提案書の初稿を作れます。</h2>
          <p>案件入力、AI分析、内容確認、提出前チェック、出力の順番で進みます。専門的な設定は必要な時だけ開けます。</p>
        </div>
        <div className="guided-context">
          <span>組織: {props.organizationName || "未設定"}</span>
          <span>チーム: {props.workspaceName || "未設定"}</span>
          <span>権限: {props.roleLabel}</span>
          {props.canSeeDetailMode && (
            <button className="secondary-button" onClick={props.onToggleDetailMode} type="button" aria-label={props.detailMode ? "通常表示に戻す" : "詳細モード"}>
              {props.detailMode ? "通常表示に戻す" : "詳細機能を表示"}
            </button>
          )}
        </div>
      </div>

      <div className="guided-user-dashboard" aria-label="現在の状態">
        <article data-testid={props.showSalesCopilotMarker ? "sales-copilot" : undefined} aria-label="次にやること">
          <span>次にやること</span>
          <strong>{props.hasProposal ? "内容確認と提出前チェックを進めましょう" : "新しい提案書を作成しましょう"}</strong>
        </article>
        <article>
          <span>現在の状態</span>
          <strong>{props.isGenerating ? "AIが作成中" : props.hasProposal ? "提案書が完成" : "入力待ち"}</strong>
        </article>
        <article>
          <span>未確認事項</span>
          <strong>{props.hasProposal && !props.qualityGateComplete ? `${uncheckedCount}件` : "なし"}</strong>
        </article>
        <article>
          <span>現在のステップ</span>
          <strong>{currentStepTitle}</strong>
        </article>
      </div>

      <StepNavigation activeStep={activeStep} completedSteps={completedSteps} isStepAvailable={isStepAvailable} onSelectStep={setActiveStep} steps={steps} />
      <SimpleErrorMessage message={props.errorMessage} onRetry={props.onRetry} />

      {activeStep === 1 && (
        <article className="guided-step-card guided-intake-step">
          <div className="section-heading">
            <div>
              <p className="eyebrow">STEP 1 案件入力</p>
              <h2>案件情報を貼り付けてください</h2>
              <p>案件情報を貼り付けるだけで開始できます。会社名、予算、納期が分からない場合もそのまま作成できます。</p>
            </div>
          </div>
          <div className="guided-input-intro">
            <strong>まずは案件情報を貼り付けてください</strong>
            <span>案件メール / 議事録 / ヒアリングメモ / 案件概要</span>
          </div>
          <label className="field guided-source-field" htmlFor="guided-source-text">
            <span>案件メール・議事録・ヒアリングメモ</span>
            <textarea
              data-testid="project-source-input"
              id="guided-source-text"
              aria-describedby="guided-source-help guided-source-warning"
              onChange={(event) => {
                props.onSourceTextChange(event.target.value);
                setLocalNotice("");
              }}
              placeholder="例: お客様からAI-OCR導入の相談がありました。現在は帳票確認を手作業で行っており、確認時間を短縮したい。予算と納期は未定です。"
              rows={10}
              value={props.sourceText}
            />
          </label>
          <p id="guided-source-help" className="guided-field-help">案件概要だけでも大丈夫です。不明な情報はAIが「要確認」として整理します。</p>
          {props.draftNotice && (
            <div className="guided-draft-notice" role="status">
              <span>{props.draftNotice}</span>
              {props.onDiscardDraft && <button className="text-button" onClick={props.onDiscardDraft} type="button">この入力を破棄</button>}
            </div>
          )}
          {props.draftSaveStatus && <p className="guided-draft-save-status" role="status">{props.draftSaveStatus}</p>}
          {localNotice && <p id="guided-source-warning" className="guided-inline-warning" role="alert">{localNotice}</p>}
          <div className="guided-aux-actions">
            <button className="secondary-button" onClick={props.onUseSample} type="button">
              <Sparkles size={16} aria-hidden="true" />
              サンプル入力
            </button>
            <button className="text-button" onClick={props.onShowGuide} type="button">
              <HelpCircle size={16} aria-hidden="true" />
              入力例を見る
            </button>
          </div>
          <details className="guided-detail-foldout">
            <summary>詳細条件を設定する（任意）</summary>
            <p>業種、予算、納期、競合などはAIが本文から抽出します。必要な項目は、生成後の内容確認画面で修正してください。</p>
          </details>
          <StepFooter
            disabled={!hasInput || !props.canGenerate}
            helpText={!hasInput ? "案件情報を貼り付けると作成を開始できます。" : undefined}
            isLoading={props.isGenerating}
            onNext={startGeneration}
            primaryLabel="AIで提案書を作成"
          />
        </article>
      )}

      {activeStep === 2 && (
        <article className="guided-step-card" aria-busy={props.isGenerating}>
          <div className="section-heading">
            <div>
              <p className="eyebrow">STEP 2 AI分析</p>
              <h2>AIが提案書の流れを作成しています</h2>
              <p>通常1〜2分程度かかります。この画面を閉じずにお待ちください。</p>
            </div>
          </div>
          <div className="guided-processing-note" role="status" aria-live="polite">
            <strong>AIが案件情報を整理して提案書を作成しています</strong>
            <span>通常1〜2分程度かかります。この画面を閉じずにお待ちください。</span>
          </div>
          <div className="guided-progress-list" aria-live="polite">
            {props.generationStages.slice(0, 4).map((stage) => (
              <div className={`guided-progress-row is-${stage.status}`} key={stage.label}>
                <span>{statusLabel(stage.status)}</span>
                <strong>{stage.label}</strong>
                <small>{stage.helper}</small>
              </div>
            ))}
          </div>
          {props.detailMode && (
            <details className="guided-detail-foldout">
              <summary>詳細な処理状況を見る</summary>
              {props.panels.workspaceProgress}
            </details>
          )}
          <StepFooter
            backLabel="案件入力へ戻る"
            disabled={!props.hasProposal}
            helpText={props.hasProposal ? "提案書が完成しました。" : "作成完了後に次へ進めます。"}
            onBack={() => setActiveStep(1)}
            onNext={() => setActiveStep(3)}
            primaryLabel="内容を確認する"
          />
        </article>
      )}

      {activeStep === 3 && (
        <article className="guided-step-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">STEP 3 内容確認</p>
              <h2>AIが整理した内容を確認してください</h2>
              <p>案件概要、課題、提案方針などを確認します。AI推測と表示された項目は、提出前に人の目で確認してください。</p>
            </div>
            <span>{uncheckedCount > 0 ? `未確認 ${uncheckedCount}件` : "確認済み"}</span>
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
          {visibleSemanticCandidates.length > 0 && (
            <section className="guided-semantic-confirmation" aria-labelledby="guided-semantic-confirmation-heading">
              <div className="guided-semantic-confirmation__header">
                <div>
                  <p className="eyebrow">重要項目の確認</p>
                  <h3 id="guided-semantic-confirmation-heading">AIが整理した重要項目を確認してください</h3>
                  <p>AIが整理した内容のうち、提出前に確認が必要な項目だけ表示しています。</p>
                </div>
                <strong aria-live="polite">判断済み {resolvedSemanticCount} / {visibleSemanticCandidates.length}（採用 {acceptedSemanticCount}・不採用 {rejectedSemanticCount}）</strong>
              </div>
              <div className="guided-semantic-card-list">
                {visibleSemanticCandidates.map((candidate) => {
                  const isEditing = editingCandidateId === candidate.id;
                  const isAiProposal = candidate.authority === "AI_PROPOSED" && candidate.review_state === "UNCONFIRMED";
                  return (
                    <article className={`guided-semantic-card is-${candidate.review_state.toLowerCase()}`} key={candidate.id}>
                      <div className="guided-semantic-card__topline">
                        <span className="guided-semantic-card__type">{semanticTypeLabels[candidate.semantic_type] || "確認項目"}</span>
                        <span className="guided-semantic-card__status">{semanticStatusLabel(candidate)}</span>
                      </div>
                      {isAiProposal && <span className="guided-semantic-card__ai-label">AIによる候補</span>}
                      {candidate.semantic_type === "evidence" && (
                        <div className="guided-semantic-evidence-meta"><span>出典</span><strong>{candidate.source_reference || candidate.source_field || "出典を確認してください"}</strong></div>
                      )}
                      {candidate.relationship_type && candidate.from_item && candidate.to_item && (
                        <div className="guided-semantic-handoff" aria-label="引き継ぎ"><span>{candidate.from_item}</span><span aria-hidden="true">→</span><span>{candidate.to_item}</span></div>
                      )}
                      {isEditing ? (
                        <div className="guided-semantic-edit-row">
                          <label htmlFor={`semantic-edit-${candidate.id}`}>内容を編集</label>
                          <input id={`semantic-edit-${candidate.id}`} value={editingValue} onChange={(event) => setEditingValue(event.target.value)} />
                          <button className="primary-button" onClick={() => saveSemanticEdit(candidate)} type="button">内容を確定</button>
                          <button className="text-button" onClick={() => setEditingCandidateId(null)} type="button">キャンセル</button>
                        </div>
                      ) : <p className="guided-semantic-card__value">{candidate.value}</p>}
                      {candidate.semantic_type === "evidence" && <small className="guided-semantic-evidence-state">確認状態: {candidate.admissible_as_evidence ? "出典を確認してください" : "未確認"}</small>}
                      {candidate.review_state !== "REJECTED" && !isEditing && (
                        <div className="guided-semantic-card__actions">
                          {candidate.review_state !== "CONFIRMED" && candidate.review_state !== "CORRECTED" && <button className="primary-button" onClick={() => confirmSemanticCandidate(candidate)} type="button"><CheckCircle2 size={15} aria-hidden="true" />この内容で確定</button>}
                          <button className="secondary-button" onClick={() => startSemanticEdit(candidate)} type="button"><Pencil size={15} aria-hidden="true" />編集</button>
                          <button className="text-button" onClick={() => rejectSemanticCandidate(candidate)} type="button"><X size={15} aria-hidden="true" />この候補を使わない</button>
                        </div>
                      )}
                    </article>
                  );
                })}
              </div>
              {semanticConfirmationBlockingCount > 0 && <p className="guided-semantic-confirmation__hint" role="status">一部の項目は未確認です。必要に応じて確認してください。</p>}
            </section>
          )}
          {missingQuestions.length > 0 && (
            <div className="guided-question-card">
              <strong>提案書をより正確にするため、あと{missingQuestions.length}点だけ確認してください</strong>
              <ol>
                {missingQuestions.map((item) => (
                  <li key={item.label}>{item.label}: {truncate(item.value, 80)}。分からない場合は未定のままで進められます。</li>
                ))}
              </ol>
            </div>
          )}
          {reviewedCandidates.length >= 2 && (
            <section className="guided-semantic-confirmation" aria-labelledby="guided-relationship-heading">
              <div className="guided-semantic-confirmation__header">
                <div>
                  <p className="eyebrow">項目同士の関係</p>
                  <h3 id="guided-relationship-heading">明確な関係がある場合だけ設定してください</h3>
                  <p>関係がない場合は設定せず、そのまま進められます。</p>
                </div>
              </div>
              <div className="guided-semantic-edit-row">
                <div className="guided-semantic-field">
                <label htmlFor="relationship-from">起点</label>
                <select id="relationship-from" value={relationshipFrom} onChange={(event) => setRelationshipFrom(event.target.value)}>
                  <option value="">項目を選択</option>
                  {reviewedCandidates.map((candidate) => <option key={candidate.id} value={candidate.id}>{semanticTypeLabels[candidate.semantic_type] || "確認項目"}</option>)}
                </select>
                </div>
                <div className="guided-semantic-field">
                <label htmlFor="relationship-type">関係</label>
                <select id="relationship-type" value={relationshipType} onChange={(event) => setRelationshipType(event.target.value as "causality" | "dependency")}>
                  <option value="causality">AがBにつながる</option>
                  <option value="dependency">Bを行うにはAが必要</option>
                </select>
                </div>
                <div className="guided-semantic-field">
                <label htmlFor="relationship-to">終点</label>
                <select id="relationship-to" value={relationshipTo} onChange={(event) => setRelationshipTo(event.target.value)}>
                  <option value="">項目を選択</option>
                  {reviewedCandidates.map((candidate) => <option key={candidate.id} value={candidate.id}>{semanticTypeLabels[candidate.semantic_type] || "確認項目"}</option>)}
                </select>
                </div>
                <button className="primary-button" onClick={addRelationship} type="button" disabled={!relationshipFrom || !relationshipTo || relationshipFrom === relationshipTo}>この関係を確認</button>
              </div>
              {relationships.map((relationship, index) => {
                const from = reviewedCandidates.find((candidate) => candidate.id === relationship.from_item);
                const to = reviewedCandidates.find((candidate) => candidate.id === relationship.to_item);
                return <div className="guided-semantic-handoff" key={`${relationship.from_item}-${relationship.to_item}-${index}`}><div className="guided-semantic-handoff__item"><small>起点</small><strong>{semanticTypeLabels[from?.semantic_type || ""] || "確認項目"}</strong></div><span className="guided-semantic-handoff__direction" aria-hidden="true">{relationship.relationship_type === "dependency" ? "→ 必要" : "→ つながる"}</span><div className="guided-semantic-handoff__item"><small>終点</small><strong>{semanticTypeLabels[to?.semantic_type || ""] || "確認項目"}</strong></div><span className="guided-semantic-handoff__status">確認済み</span><button className="text-button" onClick={() => removeRelationship(index)} type="button">削除</button></div>;
              })}
            </section>
          )}
          <details className="guided-detail-foldout">
            <summary>詳細分析・AIレビューを開く</summary>
            <div className="guided-panel-stack">
              {props.panels.presentationReview}
              {props.panels.proposalOptimization}
            </div>
          </details>
          <StepFooter
            backLabel="AI分析へ戻る"
            disabled={!props.hasProposal || !semanticConfirmationReady}
            helpText={semanticConfirmationBlockingCount > 0 ? `未確認の候補が${semanticConfirmationBlockingCount}件あります。候補を確定または編集して内容を確定してください。` : undefined}
            onBack={() => setActiveStep(2)}
            onNext={continueToQualityGate}
            primaryLabel="内容を確認しました。提出前チェックへ進む"
          />
        </article>
      )}

      {activeStep === 4 && (
        <article className="guided-step-card" data-testid="guided-quality-check">
          <div className="section-heading">
            <div>
              <p className="eyebrow">STEP 4 提出前チェック</p>
              <h2>提出してよい状態か最終確認してください</h2>
              <p>Step 3が内容の確認、Step 4が社外提出前の最終確認です。すべて確認するとPowerPoint、PDF、Beautiful.ai出力が利用できます。</p>
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
            helpText={props.qualityGateComplete ? "ダウンロードできる状態です。" : allQualityChecked ? "すべて確認済みです。" : `あと${uncheckedCount}項目の確認が必要です`}
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
              <p className="eyebrow">STEP 5 ダウンロード・出力</p>
              <h2>提案書を出力できます</h2>
              <p>用途に合わせてPowerPoint、PDF、Beautiful.aiを選んでください。</p>
            </div>
          </div>
          {props.powerpointData && (
            <ProposalValidationPanel powerpointData={props.powerpointData} proposalContext={props.proposalContext} />
          )}
          <div className="guided-output-grid">
            {[
              { id: "summary" as const, title: "要約版PowerPoint", text: "短時間の説明・概要共有向け" },
              { id: "detail" as const, title: "詳細版PowerPoint", text: "正式な提案・詳細説明向け" },
              { id: "pdf" as const, title: "見積PDF", text: "見積内容の共有向け" }
            ].map((item) => (
              <button className={`guided-output-option ${selectedOutput === item.id ? "is-selected" : ""}`} key={item.id} onClick={() => setSelectedOutput(item.id)} type="button">
                <FileDown size={18} aria-hidden="true" />
                <strong>{item.title}</strong>
                <span>{item.text}</span>
              </button>
            ))}
            <button className={`guided-output-option ${selectedOutput === "beautiful" ? "is-selected" : ""}`} onClick={() => setSelectedOutput("beautiful")} type="button">
              <Sparkles size={18} aria-hidden="true" />
              <strong>Beautiful.aiで作成</strong>
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
          {outputHelpText && <p className="guided-disabled-reason" role="status">{outputHelpText}</p>}
          {props.beautifulAiNotice && <p className="guided-inline-note" role="status">{props.beautifulAiNotice}</p>}
          {props.beautifulAiManualUrl && (
            <p className="guided-inline-note" role="status">
              <a href={props.beautifulAiManualUrl} target="_blank" rel="noreferrer">Beautiful.aiを手動で開く</a>
            </p>
          )}
          {props.beautifulAiError && <p className="guided-inline-warning" role="alert">{props.beautifulAiError}</p>}
          <StepFooter
            backLabel="提出前チェックへ戻る"
            disabled={outputDisabled}
            helpText={outputDisabled ? outputHelpText : `${outputTitle(selectedOutput)}を出力します。`}
            isLoading={isOutputBusy}
            onBack={() => setActiveStep(4)}
            onNext={() => void runSelectedOutput()}
            primaryLabel={selectedOutput === "beautiful" ? "Beautiful.aiで提案書を作成" : "選択した形式でダウンロード"}
          />
          <details className="guided-detail-foldout">
            <summary>出力設定・詳細機能を開く</summary>
            <div className="guided-panel-stack">
              {props.panels.beautifulAiDiagnostics}
              {props.panels.presentationReview}
              {props.panels.proposalOptimization}
            </div>
          </details>
        </article>
      )}
    </section>
  );
}

export const GuidedFlow = memo(GuidedFlowBase);
