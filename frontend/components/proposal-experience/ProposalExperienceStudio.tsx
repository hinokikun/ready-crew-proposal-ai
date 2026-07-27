"use client";

import { useEffect, useMemo, useState } from "react";
import { ArrowDown, ArrowUp, CheckCircle2, ClipboardCheck, FileDown, LayoutTemplate, RotateCcw, Sparkles, Wand2, XCircle } from "lucide-react";
import type { PowerPointSlide } from "@/types/proposal";
import { evaluatePresentationQuality } from "@/components/proposal-experience/presentationQualityEngine";
import { analyzePresentationDesign, type LayoutDecision } from "@/components/proposal-experience/presentationDesignerAi";
import { analyzeSalesStrategy } from "@/components/proposal-experience/salesStrategyAi";
import {
  approveWorkspace,
  buildStoryCandidates,
  confirmWorkspaceInformation,
  createProposalStrategyWorkspace,
  evaluateStrategyWorkspace,
  fieldToText,
  resetWorkspace,
  selectWorkspaceStory,
  selectWorkspaceTone,
  toneCandidates,
  updateWorkspaceField
} from "@/components/proposal-experience/strategyWorkspace";
import type { PresentationLayoutDecisionRequest } from "@/lib/pptx";
import {
  type AutoFixSuggestion,
  presentationTemplateOptions,
  type PresentationQualityReport,
  type PresentationTemplateId,
  type PromptBuilderDraft,
  type ProposalStrategyWorkspace,
  type ProposalExperienceStudioProps,
  type SalesStrategyBrief,
  type StrategyWorkspaceEditableField,
  type StrategyWorkspaceScore,
  type StoryPlan,
  type StoryCandidate,
  type StorySlide
} from "@/components/proposal-experience/types";

const draftKey = "ready-crew-v80-prompt-builder";
const storyKey = "ready-crew-v80-story-plan";
const stepLabels = ["案件基本情報", "顧客とターゲット", "現状と課題", "提案条件", "提案方針", "確認"];
const layoutTypes = [
  "Title Cover",
  "Executive Summary",
  "Problem Statement",
  "Before / After",
  "Process Flow",
  "KPI Dashboard",
  "Timeline",
  "Pricing",
  "Next Action"
];
const pptxSupportedLayoutIds = new Set([
  "LAYOUT-001",
  "LAYOUT-002",
  "LAYOUT-003",
  "LAYOUT-004",
  "LAYOUT-005",
  "LAYOUT-006",
  "LAYOUT-007",
  "LAYOUT-008",
  "LAYOUT-009",
  "LAYOUT-010",
  "LAYOUT-011",
  "LAYOUT-012",
  "LAYOUT-013",
  "LAYOUT-014",
  "LAYOUT-015",
  "LAYOUT-016",
  "LAYOUT-017"
]);

const initialDraft: PromptBuilderDraft = {
  projectName: "",
  clientName: "",
  industry: "",
  projectType: "",
  deadline: "",
  business: "",
  targetUsers: "",
  decisionMaker: "",
  stakeholders: "",
  priorities: "",
  currentState: "",
  visibleIssues: "",
  hiddenIssues: "",
  background: "",
  riskIfUnsolved: "",
  budget: "",
  scope: "",
  requiredFeatures: "",
  constraints: "",
  competitors: "",
  appeal: "課題解決型",
  tone: "信頼感",
  deckLength: "標準",
  designStyle: "corporate_clean",
  outputFormat: "PowerPoint / PDF"
};

type StudioMode = "builder" | "salesStrategy" | "story" | "editor" | "designer" | "layoutDesigner";

export function ProposalExperienceStudio({
  sourceText,
  result,
  isGenerating,
  canGenerate,
  canDownloadOutputs,
  canCreateBeautifulAi,
  selectedTemplate,
  onTemplateChange,
  onSourceTextChange,
  onGenerate,
  onDownloadPowerPoint,
  onDownloadPdf,
  onCreateBeautifulAi,
  lastPptxQualityReport
}: ProposalExperienceStudioProps) {
  const [step, setStep] = useState(0);
  const [draft, setDraft] = useState<PromptBuilderDraft>(initialDraft);
  const [story, setStory] = useState<StoryPlan>(() => buildStoryPlan(initialDraft, sourceText, result?.powerpoint_generation_data.slides ?? []));
  const [slides, setSlides] = useState<StorySlide[]>(story.slides);
  const [strategyWorkspace, setStrategyWorkspace] = useState<ProposalStrategyWorkspace>(() =>
    createProposalStrategyWorkspace(analyzeSalesStrategy({ draft: initialDraft, sourceText }))
  );
  const [selectedSlideId, setSelectedSlideId] = useState(story.slides[0]?.id ?? "");
  const [history, setHistory] = useState<StorySlide[][]>([]);
  const [future, setFuture] = useState<StorySlide[][]>([]);
  const [editSuggestion, setEditSuggestion] = useState<StorySlide | null>(null);
  const [dismissedAutoFixIds, setDismissedAutoFixIds] = useState<string[]>([]);
  const [autoFixStatuses, setAutoFixStatuses] = useState<Record<string, "applied" | "rejected">>({});
  const [layoutRevertState, setLayoutRevertState] = useState<Record<string, Pick<StorySlide, "layout" | "diagram" | "caution">>>({});
  const [layoutDecisionStatuses, setLayoutDecisionStatuses] = useState<Partial<Record<string, "applied" | "rejected">>>({});
  const [layoutStatusMessage, setLayoutStatusMessage] = useState("");
  const [mode, setMode] = useState<StudioMode>("builder");

  useEffect(() => {
    const savedDraft = window.localStorage.getItem(draftKey);
    const savedStory = window.localStorage.getItem(storyKey);
    if (savedDraft) {
      try {
        const parsed = JSON.parse(savedDraft) as PromptBuilderDraft;
        setDraft({ ...initialDraft, ...parsed });
        onTemplateChange(parsed.designStyle || selectedTemplate);
      } catch {
        setDraft(initialDraft);
      }
    }
    if (savedStory) {
      try {
        const parsed = JSON.parse(savedStory) as StoryPlan;
        setStory(parsed);
        setSlides(parsed.slides);
        setSelectedSlideId(parsed.slides[0]?.id ?? "");
      } catch {
        setStory(buildStoryPlan(initialDraft, sourceText, []));
      }
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      window.localStorage.setItem(draftKey, JSON.stringify(draft));
    }, 500);
    return () => window.clearTimeout(timer);
  }, [draft]);

  const promptSummary = useMemo(() => composePromptSummary(draft, sourceText), [draft, sourceText]);
  const salesStrategyBrief = useMemo(() => analyzeSalesStrategy({ draft, sourceText }), [draft, sourceText]);
  const confirmedSalesStrategyBrief = strategyWorkspace.status === "approved" ? strategyWorkspace.editedBrief : story.salesStrategyBrief;
  const workspaceScore = useMemo(() => evaluateStrategyWorkspace(strategyWorkspace), [strategyWorkspace]);
  const storyCandidates = useMemo(() => buildStoryCandidates(strategyWorkspace.editedBrief), [strategyWorkspace.editedBrief]);

  useEffect(() => {
    setStrategyWorkspace((current) => (current.status === "draft" ? createProposalStrategyWorkspace(salesStrategyBrief) : current));
  }, [salesStrategyBrief]);

  useEffect(() => {
    if (!result?.powerpoint_generation_data.slides?.length) return;
    const nextStory = buildStoryPlan(draft, sourceText, result.powerpoint_generation_data.slides, confirmedSalesStrategyBrief);
    setStory(nextStory);
    setSlides(nextStory.slides);
    setSelectedSlideId(nextStory.slides[0]?.id ?? "");
    window.localStorage.setItem(storyKey, JSON.stringify(nextStory));
  }, [result, confirmedSalesStrategyBrief]);

  const suggestions = useMemo(() => buildSmartSuggestions(draft, sourceText).slice(0, 3), [draft, sourceText]);
  const selectedSlide = slides.find((slide) => slide.id === selectedSlideId) ?? slides[0];
  const qualityReport = useMemo(() => evaluatePresentationQuality({ draft, story, slides }), [draft, story, slides]);
  const designAnalysis = useMemo(() => analyzePresentationDesign({ draft, story, slides, template: selectedTemplate, qualityReport, salesStrategyBrief: confirmedSalesStrategyBrief }), [draft, story, slides, selectedTemplate, qualityReport, confirmedSalesStrategyBrief]);
  const selectedLayoutDecision = designAnalysis.decisions.find((decision) => decision.slideId === selectedSlideId) ?? designAnalysis.decisions[0];
  const visibleAutoFixes = useMemo(
    () => qualityReport.autoFixSuggestions.filter((suggestion) => !dismissedAutoFixIds.includes(suggestion.id)),
    [dismissedAutoFixIds, qualityReport.autoFixSuggestions]
  );

  function updateDraft<K extends keyof PromptBuilderDraft>(key: K, value: PromptBuilderDraft[K]) {
    if (key === "designStyle") onTemplateChange(value as PresentationTemplateId);
    setDraft((current) => ({ ...current, [key]: value }));
  }

  function approveStrategyAndRebuildStory() {
    const approved = approveWorkspace(strategyWorkspace);
    setStrategyWorkspace(approved);
    const next = buildStoryPlan(draft, sourceText, result?.powerpoint_generation_data.slides ?? [], approved.editedBrief);
    setStory(next);
    setSlides(next.slides);
    setSelectedSlideId(next.slides[0]?.id ?? "");
    setMode("story");
    window.localStorage.setItem(storyKey, JSON.stringify(next));
  }

  function updateStrategyField(field: StrategyWorkspaceEditableField, value: string) {
    setStrategyWorkspace((current) => updateWorkspaceField(current, field, value));
  }

  function selectStoryCandidate(candidate: StoryCandidate) {
    setStrategyWorkspace((current) => selectWorkspaceStory(current, candidate));
  }

  function selectPresentationTone(tone: string) {
    setStrategyWorkspace((current) => selectWorkspaceTone(current, tone));
  }

  function confirmInformation(item: string) {
    setStrategyWorkspace((current) => confirmWorkspaceInformation(current, item));
  }

  function restoreAiStrategy() {
    setStrategyWorkspace((current) => resetWorkspace(current));
  }

  function openSalesStrategyReview() {
    setMode("salesStrategy");
  }

  function syncPromptToLegacyInput() {
    const next = promptSummary.trim();
    if (next) onSourceTextChange(next);
  }

  function updateSlide(id: string, patch: Partial<StorySlide>) {
    pushHistory();
    setSlides((current) => current.map((slide) => (slide.id === id ? { ...slide, ...patch } : slide)));
    setFuture([]);
  }

  function pushHistory() {
    setHistory((current) => [...current.slice(-19), slides]);
  }

  function moveSlide(id: string, direction: -1 | 1) {
    const index = slides.findIndex((slide) => slide.id === id);
    const target = index + direction;
    if (index < 0 || target < 0 || target >= slides.length) return;
    pushHistory();
    setSlides((current) => {
      const next = [...current];
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
    setFuture([]);
  }

  function addSlide() {
    pushHistory();
    const next: StorySlide = {
      id: `slide-${Date.now()}`,
      title: "追加スライド",
      purpose: "補足情報を整理する",
      message: "このスライドで伝える結論を入力してください。",
      layout: "Three Points",
      diagram: "アイコンカード",
      evidence: "追加根拠を確認",
      caution: "情報量を増やしすぎない"
    };
    setSlides((current) => [...current, next]);
    setSelectedSlideId(next.id);
  }

  function duplicateSlide(id: string) {
    const target = slides.find((slide) => slide.id === id);
    if (!target) return;
    pushHistory();
    const clone = { ...target, id: `slide-${Date.now()}`, title: `${target.title} コピー` };
    setSlides((current) => [...current, clone]);
    setSelectedSlideId(clone.id);
  }

  function deleteSlide(id: string) {
    if (slides.length <= 1) return;
    pushHistory();
    const next = slides.filter((slide) => slide.id !== id);
    setSlides(next);
    setSelectedSlideId(next[0]?.id ?? "");
  }

  function undo() {
    const previous = history.at(-1);
    if (!previous) return;
    setFuture((current) => [slides, ...current]);
    setSlides(previous);
    setHistory((current) => current.slice(0, -1));
  }

  function redo() {
    const next = future[0];
    if (!next) return;
    setHistory((current) => [...current, slides]);
    setSlides(next);
    setFuture((current) => current.slice(1));
  }

  function proposeEdit(action: string) {
    if (!selectedSlide) return;
    setEditSuggestion({
      ...selectedSlide,
      title: action.includes("短く") ? trimText(selectedSlide.title, 20) : selectedSlide.title,
      message: improveMessage(selectedSlide.message, action),
      diagram: action.includes("図解") ? "課題と解決策の図解" : selectedSlide.diagram,
      caution: "適用前に事実関係を確認してください。"
    });
  }

  function applySuggestion() {
    if (!editSuggestion) return;
    updateSlide(editSuggestion.id, editSuggestion);
    setEditSuggestion(null);
  }

  function applyAutoFix(suggestion: AutoFixSuggestion) {
    updateSlide(suggestion.slideId, suggestion.after);
    setDismissedAutoFixIds((current) => [...current, suggestion.id]);
    setAutoFixStatuses((current) => ({ ...current, [suggestion.id]: "applied" }));
  }

  function rejectAutoFix(suggestionId: string) {
    setDismissedAutoFixIds((current) => [...current, suggestionId]);
    setAutoFixStatuses((current) => ({ ...current, [suggestionId]: "rejected" }));
  }

  function applyLayoutDecision(decision: LayoutDecision) {
    const target = slides.find((slide) => slide.id === decision.slideId);
    if (!target) return;
    setLayoutRevertState((current) =>
      current[decision.slideId]
        ? current
        : {
            ...current,
            [decision.slideId]: { layout: target.layout, diagram: target.diagram, caution: target.caution }
          }
    );
    updateSlide(decision.slideId, {
      layout: decision.recommendedLayout.name,
      diagram: decision.recommendedLayout.diagramHint,
      caution: appendCaution(target.caution, `Presentation Designer AI: ${decision.recommendedLayout.id}を適用`)
    });
    setLayoutDecisionStatuses((current) => ({ ...current, [decision.slideId]: "applied" }));
    setLayoutStatusMessage(`${decision.slideTitle}へ${decision.recommendedLayout.name}を適用しました。`);
  }

  function revertLayoutDecision(decision: LayoutDecision) {
    const previous = layoutRevertState[decision.slideId];
    if (!previous) return;
    updateSlide(decision.slideId, previous);
    setLayoutRevertState((current) => {
      const { [decision.slideId]: _removed, ...rest } = current;
      return rest;
    });
    setLayoutDecisionStatuses((current) => ({ ...current, [decision.slideId]: "rejected" }));
    setLayoutStatusMessage(`${decision.slideTitle}のLayoutを元へ戻しました。`);
  }

  function buildPowerPointDataFromStudio() {
    const base = result?.powerpoint_generation_data;
    if (!base) return undefined;
    return {
      ...base,
      slides: slides.map((slide, index) => ({
        slide_no: index + 1,
        layout: slide.layout,
        title: slide.title,
        bullets: [slide.message, slide.evidence, slide.caution].filter(Boolean),
        speaker_notes: slide.purpose,
        visual_suggestion: slide.diagram
      }))
    };
  }

  function buildQualityState() {
    const entries = Object.entries(autoFixStatuses);
    return {
      applied_fixes: entries.filter(([, status]) => status === "applied").map(([id]) => id),
      rejected_fixes: entries.filter(([, status]) => status === "rejected").map(([id]) => id),
      pending_fix_count: visibleAutoFixes.length,
      source: "proposal_studio" as const
    };
  }

  function buildLayoutDecisionRequest(): PresentationLayoutDecisionRequest[] {
    return designAnalysis.decisions.map((decision) => {
      const status = layoutDecisionStatuses[decision.slideId] ?? "suggested";
      return {
        slide_id: decision.slideId,
        slide_index: decision.slideIndex,
        slide_type: decision.slideType,
        selected_layout_id: decision.recommendedLayout.id,
        recommended_layout_ids: decision.candidates.map((candidate) => candidate.id),
        selection_reason: decision.selectionReason,
        expected_effect: decision.expectedEffect,
        template_id: selectedTemplate,
        design_token_id: `${selectedTemplate}:${decision.designToken.spacing}`,
        applied_by: status === "suggested" ? "designer_ai" : "user",
        status,
        confidence: decision.variationApplied ? 0.78 : 0.88,
        human_review_required: decision.importance === "high" && decision.scoreDelta < 4
      };
    });
  }
  async function generateFromBuilder() {
    syncPromptToLegacyInput();
    await onGenerate();
  }

  return (
    <section className="v80-studio" data-testid="v80-proposal-studio" aria-label="Proposal Experience Studio">
      <div className="v80-studio-header">
        <div>
          <p className="eyebrow">Version 80 / Proposal Experience Edition</p>
          <h2>新規提案を、入力から品質確認まで1つの流れで整理します。</h2>
          <p>従来のクイック入力は残しつつ、ステップ編集、Story確認、3ペイン編集、Presentation Designerを追加しました。</p>
        </div>
        <div className="v80-score-card" data-testid="v80-quality-score">
          <span>Presentation Quality Score</span>
          <strong>{qualityReport.total}</strong>
          <small>Grade {qualityReport.grade}</small>
        </div>
      </div>

      <div className="v80-mode-tabs" role="tablist" aria-label="提案作成モード">
        {([
          ["builder", "Prompt Builder"],
          ["salesStrategy", "Sales Strategy"],
          ["story", "Story Engine"],
          ["editor", "3ペイン編集"],
          ["designer", "Designer"],
          ["layoutDesigner", "Presentation Designer"]
        ] as Array<[StudioMode, string]>).map(([key, label]) => (
          <button key={key} type="button" className={mode === key ? "is-active" : ""} onClick={() => setMode(key as typeof mode)}>
            {label}
          </button>
        ))}
      </div>

      {mode === "builder" && (
        <div className="v80-builder" data-testid="v80-prompt-builder">
          <StepRail step={step} setStep={setStep} />
          <div className="v80-builder-card">
            <BuilderFields step={step} draft={draft} updateDraft={updateDraft} sourceText={sourceText} onSourceTextChange={onSourceTextChange} />
            <div className="v80-smart-prompts" aria-live="polite">
              <strong>Smart Prompt Builder</strong>
              {suggestions.map((item) => (
                <p key={item}><Sparkles size={14} aria-hidden="true" /> {item}</p>
              ))}
              {!suggestions.length && <p><CheckCircle2 size={14} aria-hidden="true" /> 主要情報はそろっています。</p>}
            </div>
            <div className="v80-builder-actions">
              <button className="secondary-button" type="button" onClick={() => setStep(Math.max(0, step - 1))} disabled={step === 0}>戻る</button>
              <button className="secondary-button" type="button" onClick={() => setStep(Math.min(stepLabels.length - 1, step + 1))}>次へ</button>
              <button className="secondary-button" type="button" onClick={syncPromptToLegacyInput}>クイック入力へ反映</button>
              <button className="primary-button" type="button" onClick={openSalesStrategyReview}><Wand2 size={16} /> Sales Strategy確認</button>
              <button className="primary-button" type="button" onClick={() => void generateFromBuilder()} disabled={isGenerating || !canGenerate}>
                {isGenerating ? "生成中" : "生成開始"}
              </button>
            </div>
          </div>
          <aside className="v80-builder-summary">
            <strong>確認用Prompt</strong>
            <pre>{promptSummary || "入力するとAI用の要約が表示されます。"}</pre>
          </aside>
        </div>
      )}

      {mode === "salesStrategy" && (
        <SalesStrategyReviewPanel
          workspace={strategyWorkspace}
          score={workspaceScore}
          storyCandidates={storyCandidates}
          onUpdateField={updateStrategyField}
          onSelectStory={selectStoryCandidate}
          onSelectTone={selectPresentationTone}
          onConfirmInformation={confirmInformation}
          onReset={restoreAiStrategy}
          onApprove={approveStrategyAndRebuildStory}
        />
      )}

      {mode === "story" && (
        <div className="v80-story-grid" data-testid="v80-story-engine">
          <article className="v80-story-overview">
            <span>{story.storyType}</span>
            <h3>{story.mainClaim}</h3>
            <p>{story.reason}</p>
            <dl>
              <div><dt>意思決定者</dt><dd>{story.decisionMaker}</dd></div>
              <div><dt>Next Action</dt><dd>{story.nextAction}</dd></div>
            </dl>
            <DetailList title="ストーリーの流れ" items={story.flow} />
            <DetailList title="不足している根拠" items={story.missingEvidence} />
          </article>
          <SlideOutline slides={slides} selectedSlideId={selectedSlide?.id ?? ""} onSelect={setSelectedSlideId} onMove={moveSlide} onDelete={deleteSlide} onDuplicate={duplicateSlide} onAdd={addSlide} onUpdate={updateSlide} />
        </div>
      )}

      {mode === "editor" && selectedSlide && (
        <div className="v80-three-pane" data-testid="v80-slide-editor">
          <SlideList slides={slides} selectedSlideId={selectedSlide.id} onSelect={setSelectedSlideId} onMove={moveSlide} onAdd={addSlide} />
          <SlidePreview slide={selectedSlide} onUpdate={updateSlide} />
          <AiEditPanel
            slide={selectedSlide}
            suggestion={editSuggestion}
            autoFixes={visibleAutoFixes.filter((suggestion) => suggestion.slideId === selectedSlide.id)}
            onSuggest={proposeEdit}
            onApply={applySuggestion}
            onReject={() => setEditSuggestion(null)}
            onApplyAutoFix={applyAutoFix}
            onRejectAutoFix={rejectAutoFix}
            onUndo={undo}
            onRedo={redo}
            canUndo={history.length > 0}
            canRedo={future.length > 0}
          />
        </div>
      )}

      {mode === "layoutDesigner" && selectedLayoutDecision && (
        <PresentationDesignerPanel
          analysis={designAnalysis}
          decision={selectedLayoutDecision}
          selectedSlideId={selectedSlideId}
          onSelectSlide={setSelectedSlideId}
          onApply={applyLayoutDecision}
          onRevert={revertLayoutDecision}
          canRevert={Boolean(layoutRevertState[selectedLayoutDecision.slideId])}
          statusMessage={layoutStatusMessage}
        />
      )}

      {mode === "designer" && (
        <div className="v80-designer" data-testid="v80-presentation-designer">
          <TemplatePicker selected={selectedTemplate} onSelect={(template) => { onTemplateChange(template); updateDraft("designStyle", template); }} />
          <QualityReport report={qualityReport} autoFixes={visibleAutoFixes} onApplyAutoFix={applyAutoFix} onRejectAutoFix={rejectAutoFix} />
          <div className="v80-export-card">
            <h3>出力</h3>
            <p>選択したテンプレートはPowerPoint生成APIへ渡されます。既存PPTX生成ロジックを再利用します。</p>
            <button className="primary-button" type="button" onClick={() => void onDownloadPowerPoint(buildPowerPointDataFromStudio(), buildQualityState(), buildLayoutDecisionRequest())} disabled={!canDownloadOutputs}><FileDown size={16} /> PowerPoint生成</button>
            <button className="secondary-button" type="button" onClick={() => void onDownloadPdf()} disabled={!canDownloadOutputs}>PDF生成</button>
            <button className="secondary-button" type="button" onClick={() => void onCreateBeautifulAi()} disabled={!canCreateBeautifulAi}>Beautiful.ai生成</button>
            <PptxQualityDownloadSummary report={lastPptxQualityReport ?? null} />
          </div>
        </div>
      )}
    </section>
  );
}

function SalesStrategyReviewPanel({
  workspace,
  score,
  storyCandidates,
  onUpdateField,
  onSelectStory,
  onSelectTone,
  onConfirmInformation,
  onReset,
  onApprove
}: {
  workspace: ProposalStrategyWorkspace;
  score: StrategyWorkspaceScore;
  storyCandidates: StoryCandidate[];
  onUpdateField: (field: StrategyWorkspaceEditableField, value: string) => void;
  onSelectStory: (candidate: StoryCandidate) => void;
  onSelectTone: (tone: string) => void;
  onConfirmInformation: (item: string) => void;
  onReset: () => void;
  onApprove: () => void;
}) {
  const brief = workspace.editedBrief;
  const changedItems = workspace.changes.filter((change) => change.changed);
  const informationItems = brief.riskFactors.filter((risk) => risk.category !== "provided");
  return (
    <section className="v81-sales-strategy-review v81-strategy-workspace" data-testid="v81-sales-strategy-review" aria-label="Proposal Strategy Workspace">
      <div className="v81-sales-strategy-header">
        <div>
          <p className="eyebrow">Version81 Phase6 / Proposal Strategy Workspace</p>
          <h3>Proposal Strategy Workspace</h3>
          <p>Story Engineへ進む前に、営業戦略、意思決定者、競合状況、想定反論を確認します。</p>
        </div>
        <div className="v81-sales-confidence">
          <span>Strategy Score</span>
          <strong>{score.total}</strong>
          <small>{workspace.status} / {changedItems.length} edits</small>
        </div>
      </div>

      <div className="v81-workspace-grid" data-testid="v81-strategy-workspace">
        <aside className="v81-workspace-pane">
          <h4>AI Suggestions</h4>
          <StrategyAiValue label="Winning Strategy" value={workspace.aiBrief.winningStrategy} />
          <StrategyAiValue label="Decision Maker" value={workspace.aiBrief.decisionMaker} />
          <StrategyAiValue label="Competitive Position" value={workspace.aiBrief.competitiveSituation} />
          <StrategyAiValue label="Proposal Position" value={workspace.aiBrief.proposalPosition} />
          <StrategyAiValue label="Presentation Tone" value={workspace.aiBrief.recommendedPresentationTone} />
          <StrategyAiValue label="Recommended Story" value={workspace.aiBrief.recommendedStoryType} />
        </aside>
        <main className="v81-workspace-pane is-editor">
          <h4>Sales Edits</h4>
          <WorkspaceTextArea label="Winning Strategy" field="winningStrategy" brief={brief} onUpdate={onUpdateField} primary />
          <div className="v81-workspace-two">
            <WorkspaceInput label="Proposal Position" field="proposalPosition" brief={brief} onUpdate={onUpdateField} />
            <WorkspaceInput label="Decision Maker" field="decisionMaker" brief={brief} onUpdate={onUpdateField} />
            <WorkspaceInput label="Competitive Position" field="competitiveSituation" brief={brief} onUpdate={onUpdateField} />
            <WorkspaceSelect label="Presentation Tone" field="recommendedPresentationTone" value={brief.recommendedPresentationTone} options={toneCandidates.map((tone) => tone.tone)} onUpdate={onUpdateField} />
          </div>
          <WorkspaceTextArea label="Business Goal" field="businessGoal" brief={brief} onUpdate={onUpdateField} />
          <WorkspaceTextArea label="Pain Points" field="painPoints" brief={brief} onUpdate={onUpdateField} />
          <WorkspaceTextArea label="Differentiation" field="differentiation" brief={brief} onUpdate={onUpdateField} />
          <WorkspaceInput label="Recommended Story" field="recommendedStoryType" brief={brief} onUpdate={onUpdateField} />
          <WorkspaceTextArea label="Recommended Slide Types" field="recommendedSlideTypes" brief={brief} onUpdate={onUpdateField} />
          <WorkspaceTextArea label="Expected Objections" field="expectedObjections" brief={brief} onUpdate={onUpdateField} />
          <WorkspaceTextArea label="Executive Summary" field="executiveSummary" brief={brief} onUpdate={onUpdateField} />
        </main>
        <aside className="v81-workspace-pane">
          <h4>Strategy Score</h4>
          <div className="v81-workspace-score" data-testid="v81-strategy-score"><strong>{score.total}</strong><span>/ 100</span></div>
          {score.items.map((item) => (
            <article className="v81-score-row" key={item.key}>
              <div><span>{item.label}</span><strong>{item.score}</strong></div>
              <meter min={0} max={100} value={item.score} aria-label={`${item.label} ${item.score}`} />
              <small>{item.reason}</small>
            </article>
          ))}
        </aside>
      </div>

      <div className="v81-sales-strategy-grid">
        <article className="v81-sales-strategy-card is-primary">
          <span>Winning Strategy</span>
          <strong>{brief.winningStrategy}</strong>
          <p>{brief.executiveSummary}</p>
        </article>
        <article className="v81-sales-strategy-card">
          <span>Decision Maker</span>
          <strong>{brief.decisionMaker}</strong>
          <p>{brief.decisionProcess}</p>
          <ul>{brief.decisionMakerProfile.focusPoints.map((item) => <li key={item}>{item}</li>)}</ul>
        </article>
        <article className="v81-sales-strategy-card">
          <span>Competitive Position</span>
          <strong>{brief.competitiveSituation}</strong>
          <p>{brief.differentiation.join(" / ")}</p>
        </article>
        <article className="v81-sales-strategy-card">
          <span>Proposal Position</span>
          <strong>{brief.proposalPosition}</strong>
          <p>{brief.projectCategory} / {brief.customerIndustry}</p>
        </article>
        <article className="v81-sales-strategy-card">
          <span>Recommended Story</span>
          <strong>{brief.recommendedStoryType}</strong>
          <p>{brief.recommendedSlideTypes.join(" → ")}</p>
        </article>
        <article className="v81-sales-strategy-card">
          <span>Presentation Tone</span>
          <strong>{brief.recommendedPresentationTone}</strong>
          <p>{brief.decisionMakerProfile.proposalOrder.join(" → ")}</p>
        </article>
      </div>

      <div className="v81-sales-strategy-sections">
        <section>
          <h4>Expected Objections</h4>
          {brief.expectedObjections.map((item) => (
            <article key={item.objection}>
              <strong>{item.objection}</strong>
              <p>{item.reason}</p>
              <small>{item.recommendedSlide} / {item.recommendedEvidence}</small>
            </article>
          ))}
        </section>
        <section>
          <h4>Proposal Risks</h4>
          {brief.riskFactors.map((item) => (
            <article key={`${item.category}-${item.item}`}>
              <strong>{item.category}: {item.item}</strong>
              <p>{item.reason}</p>
            </article>
          ))}
        </section>
        <section>
          <h4>Human Review</h4>
          {brief.humanReviewReasons.length ? brief.humanReviewReasons.map((item) => <p key={item}>{item}</p>) : <p>追加確認なしでStory Engineへ進めます。</p>}
          <h4>Evidence Classification</h4>
          <p>不足: {brief.evidenceClassification.missing.join(" / ") || "なし"}</p>
          <p>仮説: {brief.evidenceClassification.hypothesis.join(" / ") || "なし"}</p>
          <p>確認必要: {brief.evidenceClassification.needsConfirmation.join(" / ") || "なし"}</p>
          <p>AI推定: {brief.evidenceClassification.aiInferred.join(" / ") || "なし"}</p>
        </section>
      </div>

      <div className="v81-workspace-comparison">
        <section>
          <h4>Diff</h4>
          {changedItems.length ? changedItems.map((item) => (
            <article key={item.field} data-testid="v81-strategy-diff">
              <strong>{item.field}</strong>
              <p>AI: {item.aiValue || "-"}</p>
              <p>Sales: {item.editedValue || "-"}</p>
            </article>
          )) : <p>No sales edits yet.</p>}
        </section>
        <section>
          <h4>Missing / Assumed Information</h4>
          {informationItems.length ? informationItems.map((item) => (
            <article key={`${item.category}-${item.item}`}>
              <strong>{item.category}: {item.item}</strong>
              <p>{item.reason}</p>
              <button type="button" onClick={() => onConfirmInformation(item.item)}>Mark confirmed</button>
            </article>
          )) : <p>All listed information is confirmed.</p>}
        </section>
      </div>

      <div className="v81-workspace-comparison">
        <section>
          <h4>Story Comparison</h4>
          {storyCandidates.map((candidate) => (
            <button key={candidate.id} type="button" className={workspace.selectedStoryId === candidate.id ? "is-active" : ""} onClick={() => onSelectStory(candidate)} data-testid="v81-story-candidate">
              <strong>{candidate.label}</strong>
              <span>{candidate.reason}</span>
              <small>{candidate.slideTypes.join(" -> ")}</small>
            </button>
          ))}
        </section>
        <section>
          <h4>Presentation Tone Comparison</h4>
          {toneCandidates.map((tone) => (
            <button key={tone.id} type="button" className={brief.recommendedPresentationTone === tone.tone ? "is-active" : ""} onClick={() => onSelectTone(tone.tone)} data-testid="v81-tone-candidate">
              <strong>{tone.label}</strong>
              <span>{tone.summary}</span>
            </button>
          ))}
        </section>
      </div>

      <div className="v81-sales-strategy-actions">
        <button className="secondary-button" type="button" onClick={onReset}>
          <RotateCcw size={16} /> Restore AI draft
        </button>
        <button className="primary-button" type="button" onClick={onApprove} aria-label="この戦略でStoryを作成">
          <CheckCircle2 size={16} /> この戦略でStoryを作成
        </button>
      </div>
    </section>
  );
}

function StrategyAiValue({ label, value }: { label: string; value: string }) {
  return (
    <article className="v81-ai-value">
      <span>{label}</span>
      <strong>{value || "-"}</strong>
    </article>
  );
}

function WorkspaceInput({
  label,
  field,
  brief,
  onUpdate
}: {
  label: string;
  field: StrategyWorkspaceEditableField;
  brief: SalesStrategyBrief;
  onUpdate: (field: StrategyWorkspaceEditableField, value: string) => void;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <input value={fieldToText(brief, field)} onChange={(event) => onUpdate(field, event.target.value)} />
    </label>
  );
}

function WorkspaceSelect({
  label,
  field,
  value,
  options,
  onUpdate
}: {
  label: string;
  field: StrategyWorkspaceEditableField;
  value: string;
  options: string[];
  onUpdate: (field: StrategyWorkspaceEditableField, value: string) => void;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <select value={value} onChange={(event) => onUpdate(field, event.target.value)}>
        {options.map((option) => <option value={option} key={option}>{option}</option>)}
      </select>
    </label>
  );
}

function WorkspaceTextArea({
  label,
  field,
  brief,
  onUpdate,
  primary = false
}: {
  label: string;
  field: StrategyWorkspaceEditableField;
  brief: SalesStrategyBrief;
  onUpdate: (field: StrategyWorkspaceEditableField, value: string) => void;
  primary?: boolean;
}) {
  return (
    <label className={primary ? "field v81-workspace-primary" : "field"}>
      <span>{label}</span>
      <textarea value={fieldToText(brief, field)} onChange={(event) => onUpdate(field, event.target.value)} rows={primary ? 4 : 3} />
    </label>
  );
}

function PresentationDesignerPanel({
  analysis,
  decision,
  selectedSlideId,
  onSelectSlide,
  onApply,
  onRevert,
  canRevert,
  statusMessage
}: {
  analysis: ReturnType<typeof analyzePresentationDesign>;
  decision: LayoutDecision;
  selectedSlideId: string;
  onSelectSlide: (id: string) => void;
  onApply: (decision: LayoutDecision) => void;
  onRevert: (decision: LayoutDecision) => void;
  canRevert: boolean;
  statusMessage: string;
}) {
  const pptxSupported = pptxSupportedLayoutIds.has(decision.recommendedLayout.id);
  return (
    <section className="v81-designer-ai" data-testid="v81-presentation-designer-ai" aria-label="Presentation Designer AI">
      <header className="v81-designer-ai-header">
        <div>
          <p className="eyebrow">Version81 Phase3</p>
          <h3>Presentation Designer AI</h3>
          <p>Story、Slide Type、文章量、Audience、Presentation Score、Quality Findingsから最適なLayoutを提案します。</p>
        </div>
        <div className="v81-designer-score">
          <span>Presentation Score</span>
          <strong>{analysis.averageScoreBefore} → {analysis.averageScoreAfter}</strong>
          <small>Score +{Math.max(0, analysis.averageScoreAfter - analysis.averageScoreBefore)}</small>
        </div>
      </header>

      <div className="v81-designer-grid">
        <aside className="v81-layout-list" aria-label="Layout decision list">
          {analysis.decisions.map((item) => (
            <button key={item.slideId} type="button" className={selectedSlideId === item.slideId ? "is-active" : ""} onClick={() => onSelectSlide(item.slideId)}>
              <span>{item.slideIndex}</span>
              <strong>{item.slideTitle}</strong>
              <small>{item.slideType} / {item.recommendedLayout.id}</small>
              <em>+{item.scoreDelta}</em>
            </button>
          ))}
        </aside>

        <article className="v81-layout-detail">
          <div className="v81-layout-title-row">
            <div>
              <span className="v81-badge">{decision.slideType}</span>
              <span className="v81-badge">{decision.importance}</span>
              <span className="v81-badge">{decision.audience}</span>
            </div>
            <strong>{decision.recommendedLayout.id} / {decision.recommendedLayout.name}</strong>
          </div>
          <div className="v81-layout-pptx-contract" data-testid="v81-layout-pptx-contract">
            <span>PPTX Renderer: {pptxSupported ? "supported" : "backend fallback"}</span>
            <span>Preview/PPTX: {pptxSupported ? "same structural layout" : "safe fallback report"}</span>
            <span>Token: {decision.designToken.template}:{decision.designToken.spacing}</span>
          </div>

          <div className="v81-layout-candidates">
            <h4>Layout候補</h4>
            {decision.candidates.map((candidate) => (
              <span key={candidate.id}>{candidate.id} {candidate.name}</span>
            ))}
          </div>

          <div className="v81-layout-reason">
            <h4>変更理由</h4>
            <p>{decision.selectionReason}</p>
            <h4>期待効果</h4>
            <p>{decision.expectedEffect}</p>
          </div>

          <div className="v81-layout-before-after">
            <section>
              <h4>Before</h4>
              <strong>{decision.currentLayout || "未設定"}</strong>
              <p>{decision.currentDiagram || "図解指定なし"}</p>
              <small>Score {decision.scoreBefore}</small>
            </section>
            <section>
              <h4>After</h4>
              <strong>{decision.recommendedLayout.name}</strong>
              <p>{decision.recommendedLayout.diagramHint}</p>
              <small>Score {decision.scoreAfter} / +{decision.scoreDelta}</small>
            </section>
          </div>

          <div className="v81-design-token">
            <h4>Design Token</h4>
            <span>{decision.designToken.colorRole}</span>
            <span>Spacing: {decision.designToken.spacing}</span>
            <span>Title {decision.designToken.titleSize}px</span>
            <span>Body {decision.designToken.bodySize}px</span>
            <span>Card {decision.designToken.cardPadding}px</span>
            <span>Icon {decision.designToken.iconSize}px</span>
          </div>

          <div className="v81-layout-actions">
            <button data-testid="v81-layout-apply" className="primary-button" type="button" onClick={() => onApply(decision)}>
              適用
            </button>
            <button data-testid="v81-layout-revert" className="secondary-button" type="button" onClick={() => onRevert(decision)} disabled={!canRevert}>
              元へ戻す
            </button>
          </div>
          {statusMessage && <p className="v81-layout-status" role="status">{statusMessage}</p>}
        </article>
      </div>

      <footer className="v81-layout-library">
        <h4>Layout Library</h4>
        {analysis.library.map((layout) => (
          <span key={layout.id}>{layout.id} {layout.name}</span>
        ))}
      </footer>
    </section>
  );
}

function BuilderFields({ step, draft, updateDraft, sourceText, onSourceTextChange }: { step: number; draft: PromptBuilderDraft; updateDraft: (key: keyof PromptBuilderDraft, value: string) => void; sourceText: string; onSourceTextChange: (value: string) => void }) {
  const fields: Array<[keyof PromptBuilderDraft, string, string]> =
    step === 0 ? [["projectName", "案件名", "例：AI-OCR導入支援"], ["clientName", "クライアント名", "例：株式会社サンプル"], ["industry", "業種", "例：製造業"], ["projectType", "案件種別", "例：AI導入"], ["deadline", "提案期限", "例：来週金曜"]] :
    step === 1 ? [["business", "顧客の事業内容", ""], ["targetUsers", "対象ユーザー", ""], ["decisionMaker", "意思決定者", ""], ["stakeholders", "関係者", ""], ["priorities", "顧客が重視すること", ""]] :
    step === 2 ? [["currentState", "現状", ""], ["visibleIssues", "顕在課題", ""], ["hiddenIssues", "潜在課題", ""], ["background", "背景", ""], ["riskIfUnsolved", "解決できない場合のリスク", ""]] :
    step === 3 ? [["budget", "予算", ""], ["scope", "対象範囲", ""], ["requiredFeatures", "必要機能", ""], ["constraints", "制約", ""], ["competitors", "競合情報", ""]] :
    step === 4 ? [["appeal", "重視する訴求", ""], ["tone", "提案のトーン", ""], ["deckLength", "資料の長さ", ""], ["outputFormat", "出力形式", ""]] : [];
  if (step === 5) {
    return <pre className="v80-confirmation">{composePromptSummary(draft, sourceText)}</pre>;
  }
  return (
    <div className="v80-field-grid">
      {fields.map(([key, label, placeholder]) => (
        <label className="field" key={key}>
          <span>{label}</span>
          <input value={String(draft[key] ?? "")} onChange={(event) => updateDraft(key, event.target.value)} placeholder={placeholder || `${label}を入力`} />
        </label>
      ))}
      {step === 0 && (
        <label className="field v80-wide">
          <span>クイック入力</span>
          <textarea value={sourceText} onChange={(event) => onSourceTextChange(event.target.value)} rows={5} placeholder="従来どおり、案件メールや議事録をそのまま貼り付けられます。" />
        </label>
      )}
    </div>
  );
}

function StepRail({ step, setStep }: { step: number; setStep: (step: number) => void }) {
  return (
    <ol className="v80-step-rail" aria-label="Prompt Builderステップ">
      {stepLabels.map((label, index) => (
        <li key={label} className={index === step ? "is-active" : index < step ? "is-done" : ""}>
          <button type="button" onClick={() => setStep(index)} aria-current={index === step ? "step" : undefined}>
            <span>{index < step ? "OK" : index + 1}</span>{label}
          </button>
        </li>
      ))}
    </ol>
  );
}

function SlideOutline({ slides, selectedSlideId, onSelect, onMove, onDelete, onDuplicate, onAdd, onUpdate }: { slides: StorySlide[]; selectedSlideId: string; onSelect: (id: string) => void; onMove: (id: string, direction: -1 | 1) => void; onDelete: (id: string) => void; onDuplicate: (id: string) => void; onAdd: () => void; onUpdate: (id: string, patch: Partial<StorySlide>) => void }) {
  return (
    <section className="v80-slide-outline">
      <div className="v80-section-title"><h3>スライド構成確認</h3><button type="button" onClick={onAdd}>追加</button></div>
      {slides.map((slide, index) => (
        <article key={slide.id} className={selectedSlideId === slide.id ? "is-selected" : ""}>
          <button type="button" onClick={() => onSelect(slide.id)}><span>{index + 1}</span>{slide.title}</button>
          <input aria-label={`${slide.title}のタイトル`} value={slide.title} onChange={(event) => onUpdate(slide.id, { title: event.target.value })} />
          <textarea aria-label={`${slide.title}の要点`} value={slide.message} onChange={(event) => onUpdate(slide.id, { message: event.target.value })} rows={2} />
          <div><button type="button" onClick={() => onMove(slide.id, -1)}><ArrowUp size={14} /></button><button type="button" onClick={() => onMove(slide.id, 1)}><ArrowDown size={14} /></button><button type="button" onClick={() => onDuplicate(slide.id)}>複製</button><button type="button" onClick={() => onDelete(slide.id)}>削除</button></div>
        </article>
      ))}
    </section>
  );
}

function SlideList({ slides, selectedSlideId, onSelect, onMove, onAdd }: { slides: StorySlide[]; selectedSlideId: string; onSelect: (id: string) => void; onMove: (id: string, direction: -1 | 1) => void; onAdd: () => void }) {
  return <aside className="v80-slide-list"><button type="button" onClick={onAdd}>スライド追加</button>{slides.map((slide, index) => <button key={slide.id} type="button" className={selectedSlideId === slide.id ? "is-active" : ""} onClick={() => onSelect(slide.id)}><span>{index + 1}</span><strong>{slide.title}</strong><small>{slide.layout}</small><i>{slide.caution ? "警告あり" : ""}</i><b onClick={(event) => { event.stopPropagation(); onMove(slide.id, -1); }}>上</b><b onClick={(event) => { event.stopPropagation(); onMove(slide.id, 1); }}>下</b></button>)}</aside>;
}

function SlidePreview({ slide, onUpdate }: { slide: StorySlide; onUpdate: (id: string, patch: Partial<StorySlide>) => void }) {
  return <section className="v80-slide-preview"><div className="v80-slide-canvas"><span>{slide.layout}</span><input aria-label="スライドタイトル" value={slide.title} onChange={(event) => onUpdate(slide.id, { title: event.target.value })} /><textarea aria-label="スライド本文" value={slide.message} onChange={(event) => onUpdate(slide.id, { message: event.target.value })} rows={4} /><div className="v80-diagram-preview"><strong>{slide.diagram}</strong><p>{slide.purpose}</p></div><small>{slide.evidence}</small></div></section>;
}

function AiEditPanel({
  slide,
  suggestion,
  autoFixes,
  onSuggest,
  onApply,
  onReject,
  onApplyAutoFix,
  onRejectAutoFix,
  onUndo,
  onRedo,
  canUndo,
  canRedo
}: {
  slide: StorySlide;
  suggestion: StorySlide | null;
  autoFixes: AutoFixSuggestion[];
  onSuggest: (action: string) => void;
  onApply: () => void;
  onReject: () => void;
  onApplyAutoFix: (suggestion: AutoFixSuggestion) => void;
  onRejectAutoFix: (suggestionId: string) => void;
  onUndo: () => void;
  onRedo: () => void;
  canUndo: boolean;
  canRedo: boolean;
}) {
  const actions = ["タイトルを短くする", "結論を先にする", "文章量を半分にする", "経営者向け表現にする", "数字を強調する", "図解へ変更する"];
  return <aside className="v80-ai-edit-panel"><h3>AI編集アシスタント</h3>{actions.map((action) => <button key={action} type="button" onClick={() => onSuggest(action)}>{action}</button>)}<div className="v80-undo-row"><button type="button" onClick={onUndo} disabled={!canUndo}><RotateCcw size={14} /> Undo</button><button type="button" onClick={onRedo} disabled={!canRedo}>Redo</button></div>{suggestion && <div className="v80-edit-comparison"><strong>変更前</strong><p>{slide.message}</p><strong>変更後</strong><p>{suggestion.message}</p><button type="button" onClick={onApply}><CheckCircle2 size={14} /> 適用</button><button type="button" onClick={onReject}><XCircle size={14} /> 却下</button></div>}<AutoFixList suggestions={autoFixes} onApply={onApplyAutoFix} onReject={onRejectAutoFix} compact /></aside>;
}

function TemplatePicker({ selected, onSelect }: { selected: PresentationTemplateId; onSelect: (template: PresentationTemplateId) => void }) {
  return <section className="v80-template-picker"><h3><LayoutTemplate size={18} /> PPTテンプレート</h3>{presentationTemplateOptions.map((template) => <button type="button" key={template.id} className={selected === template.id ? "is-active" : ""} onClick={() => onSelect(template.id)}><strong>{template.label}</strong><span>{template.summary}</span></button>)}</section>;
}

function QualityReport({ report, autoFixes, onApplyAutoFix, onRejectAutoFix }: { report: PresentationQualityReport; autoFixes: AutoFixSuggestion[]; onApplyAutoFix: (suggestion: AutoFixSuggestion) => void; onRejectAutoFix: (suggestionId: string) => void }) {
  return (
    <section className="v80-quality-report" data-testid="v81-quality-engine">
      <h3><ClipboardCheck size={18} /> Presentation Quality Engine</h3>
      <p>Version81 Planning Packに基づき、18カテゴリ、品質ルール、図解提案、文章Fit、Auto Fixを判定します。</p>
      <div className="v81-quality-summary">
        <strong>{report.total}</strong>
        <span>Grade {report.grade}</span>
        <small>18カテゴリ評価</small>
      </div>
      <div className="v81-quality-grid" aria-label="18カテゴリ評価">
        {report.items.map((item) => (
          <article className={`v81-quality-item is-${item.severity}`} key={item.key}>
            <div><span>{item.label}</span><strong>{item.score}</strong></div>
            <meter min={0} max={100} value={item.score} aria-label={`${item.label} ${item.score}点`} />
            <small>{item.reason}</small>
            <p>{item.improvement}</p>
          </article>
        ))}
      </div>
      <QualityRuleList report={report} />
      <AutoFixList suggestions={autoFixes} onApply={onApplyAutoFix} onReject={onRejectAutoFix} />
    </section>
  );
}

function PptxQualityDownloadSummary({ report }: { report: NonNullable<ProposalExperienceStudioProps["lastPptxQualityReport"]> | null }) {
  if (!report) return null;
  const appliedLayoutCount = report.layout_decisions?.filter((decision) => decision.status === "applied" || decision.status === "backend_fallback").length ?? 0;
  const fallbackCount = report.layout_fallbacks?.length ?? 0;
  const unsupportedCount = report.unsupported_layouts?.length ?? 0;
  const numericPreserved = report.numeric_integrity?.preserved ?? true;
  return (
    <div className="v81-pptx-quality-summary" data-testid="v81-pptx-quality-summary">
      <strong>PPTX Quality Report</strong>
      <span>Score {report.overall_score}</span>
      {typeof report.predicted_score === "number" && <span>Predicted {report.predicted_score}</span>}
      {typeof report.rendered_score === "number" && <span>Rendered {report.rendered_score}</span>}
      {typeof report.score_delta === "number" && <span>Score Delta {report.score_delta >= 0 ? "+" : ""}{report.score_delta}</span>}
      <span>{report.slide_count_before} -&gt; {report.slide_count_after} slides</span>
      <span>Layouts {appliedLayoutCount}</span>
      <span>Fallback {fallbackCount}</span>
      <span>Unsupported {unsupportedCount}</span>
      <span>{numericPreserved ? "Numbers preserved" : "Numbers require review"}</span>
      <span>{report.human_review_required ? "Human review required" : "Rendered check OK"}</span>
      {(report.human_review_items ?? []).slice(0, 2).map((item) => <small key={item}>{item}</small>)}
      {report.warnings.slice(0, 3).map((warning) => <small key={warning}>{warning}</small>)}
    </div>
  );
}
function QualityRuleList({ report }: { report: PresentationQualityReport }) {
  return (
    <div className="v81-engine-sections">
      <section>
        <h4>Quality Rule Engine</h4>
        {report.ruleFindings.length ? report.ruleFindings.map((finding) => (
          <article className={`v81-finding is-${finding.severity}`} key={`${finding.rule}-${finding.slideId ?? "deck"}-${finding.message}`}>
            <strong>{finding.rule}</strong>
            <span>{finding.slideTitle ?? "全体"}</span>
            <p>{finding.message}</p>
            <small>{finding.recommendation}</small>
          </article>
        )) : <p>重大な品質ルール違反はありません。</p>}
      </section>
      <section>
        <h4>Diagram Recommendation Engine</h4>
        {report.diagramRecommendations.length ? report.diagramRecommendations.map((item) => (
          <article className="v81-finding" key={`${item.slideId}-${item.diagramType}`}>
            <strong>{item.diagramType}</strong>
            <span>{item.slideTitle}</span>
            <p>{item.reason}</p>
            <small>優先度: {item.priority}</small>
          </article>
        )) : <p>追加の図解提案はありません。</p>}
      </section>
      <section>
        <h4>Content Fit Engine</h4>
        {report.fitRecommendations.length ? report.fitRecommendations.map((item) => (
          <article className="v81-finding" key={`${item.slideId}-${item.action}-${item.beforeLength}`}>
            <strong>{item.action}</strong>
            <span>{item.slideTitle}</span>
            <p>{item.reason}</p>
            <small>{item.beforeLength}文字 / {item.expectedEffect}</small>
          </article>
        )) : <p>文章量のFit提案はありません。</p>}
      </section>
    </div>
  );
}

function AutoFixList({ suggestions, onApply, onReject, compact = false }: { suggestions: AutoFixSuggestion[]; onApply: (suggestion: AutoFixSuggestion) => void; onReject: (suggestionId: string) => void; compact?: boolean }) {
  if (!suggestions.length) {
    return compact ? null : <section className="v81-auto-fix" data-testid="v81-auto-fix"><h4>AI Auto Fix</h4><p>現在適用できる自動修正案はありません。</p></section>;
  }
  return (
    <section className={compact ? "v81-auto-fix compact" : "v81-auto-fix"} data-testid="v81-auto-fix">
      <h4>AI Auto Fix</h4>
      {suggestions.map((suggestion) => (
        <article className="v81-auto-fix-card" key={suggestion.id}>
          <div>
            <strong>{suggestion.slideTitle}</strong>
            <span>{suggestion.reason}</span>
          </div>
          <div className="v81-before-after">
            <section>
              <h5>修正前</h5>
              <p>{suggestion.before.title}</p>
              <small>{suggestion.before.message}</small>
              <small>{suggestion.before.layout} / {suggestion.before.diagram}</small>
            </section>
            <section>
              <h5>修正後</h5>
              <p>{suggestion.after.title ?? suggestion.before.title}</p>
              <small>{suggestion.after.message ?? suggestion.before.message}</small>
              <small>{suggestion.after.layout ?? suggestion.before.layout} / {suggestion.after.diagram ?? suggestion.before.diagram}</small>
            </section>
          </div>
          <div className="v81-auto-fix-actions">
            <button type="button" onClick={() => onApply(suggestion)}><CheckCircle2 size={14} /> 適用</button>
            <button type="button" onClick={() => onReject(suggestion.id)}><XCircle size={14} /> 却下</button>
          </div>
        </article>
      ))}
    </section>
  );
}

function DetailList({ title, items }: { title: string; items: string[] }) {
  return <div className="v80-detail-list"><strong>{title}</strong><ul>{items.map((item) => <li key={item}>{item}</li>)}</ul></div>;
}

function composePromptSummary(draft: PromptBuilderDraft, sourceText: string) {
  return [
    `案件名: ${draft.projectName || "未入力"}`,
    `顧客名: ${draft.clientName || "未入力"}`,
    `業種/案件種別: ${draft.industry || "未入力"} / ${draft.projectType || "未入力"}`,
    `意思決定者: ${draft.decisionMaker || "AI推定: 部門責任者"}`,
    `現状: ${draft.currentState || sourceText.slice(0, 120) || "未入力"}`,
    `課題: ${draft.visibleIssues || "未入力"}`,
    `提案条件: 予算 ${draft.budget || "未定"} / 納期 ${draft.deadline || "要確認"} / 範囲 ${draft.scope || "要確認"}`,
    `競合: ${draft.competitors || "未確認"}`,
    `提案方針: ${draft.appeal} / ${draft.tone} / ${draft.deckLength} / ${presentationTemplateOptions.find((item) => item.id === draft.designStyle)?.label}`
  ].join("\n");
}

function buildStoryPlan(draft: PromptBuilderDraft, sourceText: string, generatedSlides: PowerPointSlide[] = [], salesStrategyBrief?: SalesStrategyBrief): StoryPlan {
  const text = `${composePromptSummary(draft, sourceText)}\n${sourceText}`;
  const fallbackStoryType = /AI|OCR|画像|生成AI/.test(text) ? "AI導入型" : /採用|人材|教育/.test(text) ? "採用強化型" : /EC|売上|購入/.test(text) ? "EC売上改善型" : /競合|差別化/.test(text) ? "競合差別化型" : /コスト|削減|効率/.test(text) ? "コスト削減型" : "課題解決型";
  const storyType = salesStrategyBrief?.recommendedStoryType || fallbackStoryType;
  const mainClaim = salesStrategyBrief?.winningStrategy || `${draft.clientName || "顧客"}の${draft.visibleIssues || draft.projectType || "課題"}を、段階的な提案で解決します。`;
  const baseSlides = generatedSlides.length ? generatedSlides : defaultSlides(storyType, salesStrategyBrief?.recommendedSlideTypes);
  const strategyFlow = salesStrategyBrief?.recommendedSlideTypes?.length ? salesStrategyBrief.recommendedSlideTypes : null;
  return {
    storyType,
    reason: salesStrategyBrief ? `Sales Strategy AIが${salesStrategyBrief.proposalPosition} / ${salesStrategyBrief.recommendedPresentationTone}として選択しました。` : "入力された業種、課題、予算、意思決定者から、営業担当が説明しやすい順序を選択しました。",
    decisionMaker: salesStrategyBrief?.decisionMaker || draft.decisionMaker || "AI推定: 部門責任者",
    mainClaim,
    flow: strategyFlow || ["現状の痛み", "解決方針", "導入ステップ", "効果測定", "意思決定"],
    slides: baseSlides.slice(0, 10).map((slide, index) => ({
      id: `story-${index + 1}`,
      title: slide.title || defaultSlides(storyType)[index % 6].title,
      purpose: index === 0 ? "第一印象で提案価値を伝える" : "意思決定に必要な論点を整理する",
      message: slide.bullets?.[0] || `${storyType}として、顧客が次に判断できる情報を示します。`,
      layout: layoutTypes[index % layoutTypes.length],
      diagram: index % 3 === 0 ? "Before / After" : index % 3 === 1 ? "プロセス図" : "KPIカード",
      evidence: draft.background || draft.business || "案件入力とヒアリング情報",
      caution: slide.bullets?.length > 6 ? "箇条書きが多いため分割候補" : ""
    })),
    missingEvidence: salesStrategyBrief ? [...salesStrategyBrief.evidenceClassification.missing, ...salesStrategyBrief.evidenceClassification.needsConfirmation, ...buildSmartSuggestions(draft, sourceText)] : buildSmartSuggestions(draft, sourceText),
    objections: salesStrategyBrief?.expectedObjections.length ? salesStrategyBrief.expectedObjections.map((item) => ({ objection: item.objection, response: `${item.recommendedSlide}で${item.recommendedEvidence}を示します。` })) : [
      { objection: "費用対効果が分かりにくい", response: "PoCまたは初期導入でKPIを測定し、次判断へつなげます。" },
      { objection: "現場運用が不安", response: "人の確認と例外処理を残した運用設計にします。" }
    ],
    nextAction: salesStrategyBrief?.humanReviewRequired ? "Sales Strategy Reviewの確認事項を埋めてからPPTX生成へ進みます。" : "スライド構成を承認してPPTX生成へ進みます。",
    salesStrategyBrief
  };
}

function defaultSlides(storyType: string, slideTypes?: string[]): PowerPointSlide[] {
  const titles = slideTypes?.length ? slideTypes.map(labelForSlideType) : ["表紙", "提案サマリー", "現状課題", "Before / After", "導入構成", "KPI設計", "スケジュール", "概算見積", "次のアクション"];
  return titles.map((title, index) => ({ slide_no: index + 1, layout: index === 0 ? "title" : "content", title, bullets: [`${storyType}の観点で${title}を整理します。`], speaker_notes: "", visual_suggestion: "" }));
}

function labelForSlideType(value: string): string {
  const labels: Record<string, string> = {
    Cover: "表紙",
    Problem: "現状課題",
    "Before / After": "Before / After",
    Architecture: "導入構成",
    PoC: "PoC計画",
    KPI: "KPI設計",
    Estimate: "概算見積",
    "Next Action": "次のアクション",
    Comparison: "競合比較",
    Timeline: "スケジュール",
    Roadmap: "ロードマップ",
    Flow: "業務フロー",
    Proposal: "提案方針",
    Risk: "リスク"
  };
  return labels[value] ?? value;
}

function buildSmartSuggestions(draft: PromptBuilderDraft, sourceText: string) {
  const suggestions = [];
  if (!draft.budget && !/予算|万円|円/.test(sourceText)) suggestions.push("予算が未入力です。概算でも入力すると見積の説得力が上がります。");
  if (!draft.decisionMaker) suggestions.push("意思決定者が不明です。経営層、部長、現場責任者のどなた向けか確認してください。");
  if (!draft.competitors && !/競合|比較/.test(sourceText)) suggestions.push("競合との差別化情報が不足しています。比較対象を入力すると提案が強くなります。");
  if (!draft.deadline && !/納期|期限|月|日/.test(sourceText)) suggestions.push("納期の背景を追加してください。スケジュール提案が現実的になります。");
  if (!draft.visibleIssues && !draft.currentState) suggestions.push("現状と課題を1つずつ入力してください。AIのストーリー構成が安定します。");
  return suggestions;
}

function trimText(value: string, max: number) {
  return value.length > max ? `${value.slice(0, max - 1)}…` : value;
}

function appendCaution(current: string, next: string): string {
  return [current, next].filter(Boolean).join(" / ");
}

function improveMessage(value: string, action: string) {
  if (action.includes("半分")) return trimText(value, Math.max(36, Math.floor(value.length / 2)));
  if (action.includes("結論")) return `結論: ${value.replace(/^結論[:：]\s*/, "")}`;
  if (action.includes("経営者")) return `${value} 投資判断に必要な効果、リスク、次の意思決定を明確にします。`;
  if (action.includes("数字")) return `${value} 評価指標と目標値はPoCまたは初回確認で確定します。`;
  return value;
}
