import type { PresentationQualityReport, PresentationTemplateId, PromptBuilderDraft, SalesStrategyBrief, StoryPlan, StorySlide } from "@/components/proposal-experience/types";

export type SlideType =
  | "Cover"
  | "Agenda"
  | "Problem"
  | "Current State"
  | "Analysis"
  | "Comparison"
  | "Proposal"
  | "Feature"
  | "Benefit"
  | "Timeline"
  | "Roadmap"
  | "Estimate"
  | "KPI"
  | "Case Study"
  | "Risk"
  | "FAQ"
  | "Summary"
  | "Next Action"
  | "Closing";

export type LayoutDefinition = {
  id: string;
  name: string;
  bestFor: SlideType[];
  density: "low" | "medium" | "high";
  visualFocus: "message" | "comparison" | "timeline" | "metrics" | "flow" | "image" | "decision";
  diagramHint: string;
  expectedEffect: string;
};

export type DesignToken = {
  template: PresentationTemplateId;
  colorRole: string;
  spacing: "compact" | "balanced" | "generous";
  titleSize: number;
  bodySize: number;
  cardPadding: number;
  diagramGap: number;
  tablePadding: number;
  iconSize: number;
};

export type LayoutDecision = {
  slideId: string;
  slideIndex: number;
  slideTitle: string;
  slideType: SlideType;
  currentLayout: string;
  currentDiagram: string;
  recommendedLayout: LayoutDefinition;
  candidates: LayoutDefinition[];
  selectionReason: string;
  expectedEffect: string;
  importance: "high" | "medium" | "low";
  audience: string;
  designToken: DesignToken;
  scoreBefore: number;
  scoreAfter: number;
  scoreDelta: number;
  variationApplied: boolean;
};

export type PresentationDesignAnalysis = {
  decisions: LayoutDecision[];
  library: LayoutDefinition[];
  token: DesignToken;
  averageScoreBefore: number;
  averageScoreAfter: number;
};

type DesignerInput = {
  draft: PromptBuilderDraft;
  story: StoryPlan;
  slides: StorySlide[];
  template: PresentationTemplateId;
  qualityReport: PresentationQualityReport;
  salesStrategyBrief?: SalesStrategyBrief;
};

export const layoutLibrary: LayoutDefinition[] = [
  { id: "LAYOUT-001", name: "Title Only", bestFor: ["Agenda", "Summary"], density: "low", visualFocus: "message", diagramHint: "Large title and sparse support text", expectedEffect: "論点を絞り、読み始めの負荷を下げます。" },
  { id: "LAYOUT-002", name: "Title + Body", bestFor: ["Current State", "Analysis", "Feature", "FAQ"], density: "medium", visualFocus: "message", diagramHint: "Title, concise body, one supporting callout", expectedEffect: "説明文を整理し、標準的な読みやすさを保ちます。" },
  { id: "LAYOUT-003", name: "Two Column", bestFor: ["Problem", "Proposal", "Risk"], density: "medium", visualFocus: "comparison", diagramHint: "Issue and response split into two areas", expectedEffect: "課題と打ち手の対応関係を見つけやすくします。" },
  { id: "LAYOUT-004", name: "Three Column", bestFor: ["Benefit", "Feature", "Case Study"], density: "medium", visualFocus: "decision", diagramHint: "Three grouped messages with icons", expectedEffect: "3つの論点を同じ粒度で比較できます。" },
  { id: "LAYOUT-005", name: "Hero", bestFor: ["Cover", "Closing"], density: "low", visualFocus: "image", diagramHint: "Hero visual with strong message layer", expectedEffect: "第一印象と提案テーマを強く印象づけます。" },
  { id: "LAYOUT-006", name: "KPI Cards", bestFor: ["KPI", "Benefit"], density: "medium", visualFocus: "metrics", diagramHint: "Metric cards with status and basis", expectedEffect: "数値と判断基準を主役にできます。" },
  { id: "LAYOUT-007", name: "Comparison Table", bestFor: ["Comparison"], density: "high", visualFocus: "comparison", diagramHint: "Criteria rows and option columns", expectedEffect: "差分と選定理由を一目で説明できます。" },
  { id: "LAYOUT-008", name: "Timeline", bestFor: ["Timeline"], density: "medium", visualFocus: "timeline", diagramHint: "Horizontal milestones with decision gates", expectedEffect: "時系列と判断ポイントを同時に示せます。" },
  { id: "LAYOUT-009", name: "Roadmap", bestFor: ["Roadmap"], density: "medium", visualFocus: "timeline", diagramHint: "Phased roadmap with outcome labels", expectedEffect: "段階導入の全体像を伝えやすくします。" },
  { id: "LAYOUT-010", name: "Flow", bestFor: ["Current State", "Proposal", "Next Action"], density: "medium", visualFocus: "flow", diagramHint: "Process boxes and arrows", expectedEffect: "業務や意思決定の流れを追いやすくします。" },
  { id: "LAYOUT-011", name: "Matrix", bestFor: ["Analysis", "Risk", "Comparison"], density: "high", visualFocus: "decision", diagramHint: "Two-axis matrix", expectedEffect: "優先順位やリスクの位置づけを説明できます。" },
  { id: "LAYOUT-012", name: "Quote", bestFor: ["Summary", "Case Study"], density: "low", visualFocus: "message", diagramHint: "Key statement with evidence caption", expectedEffect: "伝えたい一文を記憶に残しやすくします。" },
  { id: "LAYOUT-013", name: "Image Left", bestFor: ["Problem", "Current State", "Case Study"], density: "medium", visualFocus: "image", diagramHint: "Visual placeholder on left, explanation on right", expectedEffect: "対象業務や現場イメージを補強します。" },
  { id: "LAYOUT-014", name: "Image Right", bestFor: ["Proposal", "Feature", "Benefit"], density: "medium", visualFocus: "image", diagramHint: "Explanation on left, visual placeholder on right", expectedEffect: "提案内容を視覚的に補足します。" },
  { id: "LAYOUT-015", name: "Large Number", bestFor: ["KPI", "Benefit", "Estimate"], density: "low", visualFocus: "metrics", diagramHint: "One dominant metric with context", expectedEffect: "重要な数値を見落としにくくします。" },
  { id: "LAYOUT-016", name: "Checklist", bestFor: ["Risk", "FAQ", "Next Action"], density: "medium", visualFocus: "decision", diagramHint: "Action checklist with status marks", expectedEffect: "確認事項と次の行動を実行しやすくします。" },
  { id: "LAYOUT-017", name: "Closing", bestFor: ["Closing", "Next Action"], density: "low", visualFocus: "decision", diagramHint: "Next action and final message", expectedEffect: "最後に取るべき行動を明確にします。" }
];

const slideTypeLayouts: Record<SlideType, string[]> = {
  Cover: ["LAYOUT-005", "LAYOUT-001"],
  Agenda: ["LAYOUT-001", "LAYOUT-010"],
  Problem: ["LAYOUT-003", "LAYOUT-013", "LAYOUT-011"],
  "Current State": ["LAYOUT-010", "LAYOUT-013", "LAYOUT-002"],
  Analysis: ["LAYOUT-011", "LAYOUT-006", "LAYOUT-002"],
  Comparison: ["LAYOUT-007", "LAYOUT-003", "LAYOUT-011"],
  Proposal: ["LAYOUT-014", "LAYOUT-010", "LAYOUT-003"],
  Feature: ["LAYOUT-004", "LAYOUT-014", "LAYOUT-002"],
  Benefit: ["LAYOUT-006", "LAYOUT-004", "LAYOUT-015"],
  Timeline: ["LAYOUT-008", "LAYOUT-009"],
  Roadmap: ["LAYOUT-009", "LAYOUT-008"],
  Estimate: ["LAYOUT-015", "LAYOUT-007", "LAYOUT-002"],
  KPI: ["LAYOUT-006", "LAYOUT-015", "LAYOUT-011"],
  "Case Study": ["LAYOUT-013", "LAYOUT-012", "LAYOUT-004"],
  Risk: ["LAYOUT-011", "LAYOUT-016", "LAYOUT-003"],
  FAQ: ["LAYOUT-016", "LAYOUT-002"],
  Summary: ["LAYOUT-012", "LAYOUT-004", "LAYOUT-001"],
  "Next Action": ["LAYOUT-016", "LAYOUT-017", "LAYOUT-010"],
  Closing: ["LAYOUT-017", "LAYOUT-005"]
};

const templateTokens: Record<PresentationTemplateId, DesignToken> = {
  corporate_clean: { template: "corporate_clean", colorRole: "Navy / Blue / White", spacing: "balanced", titleSize: 34, bodySize: 18, cardPadding: 18, diagramGap: 18, tablePadding: 12, iconSize: 28 },
  modern_dark: { template: "modern_dark", colorRole: "Navy gradient / Cyan accent", spacing: "generous", titleSize: 36, bodySize: 18, cardPadding: 20, diagramGap: 22, tablePadding: 12, iconSize: 30 },
  creative_agency: { template: "creative_agency", colorRole: "Blue / Cyan / Soft white", spacing: "generous", titleSize: 36, bodySize: 18, cardPadding: 22, diagramGap: 24, tablePadding: 14, iconSize: 30 },
  executive_minimal: { template: "executive_minimal", colorRole: "Navy / Gray / White", spacing: "generous", titleSize: 32, bodySize: 17, cardPadding: 16, diagramGap: 22, tablePadding: 12, iconSize: 24 },
  data_driven: { template: "data_driven", colorRole: "Blue / Cyan / Data green", spacing: "balanced", titleSize: 34, bodySize: 17, cardPadding: 18, diagramGap: 18, tablePadding: 12, iconSize: 26 },
  warm_professional: { template: "warm_professional", colorRole: "Navy / Warm gray / Blue", spacing: "balanced", titleSize: 33, bodySize: 18, cardPadding: 18, diagramGap: 18, tablePadding: 12, iconSize: 26 },
  japanese_business: { template: "japanese_business", colorRole: "Navy / White / Indigo", spacing: "compact", titleSize: 31, bodySize: 17, cardPadding: 14, diagramGap: 16, tablePadding: 10, iconSize: 24 },
  bold_vision: { template: "bold_vision", colorRole: "Deep navy / Bright blue / Cyan", spacing: "generous", titleSize: 38, bodySize: 18, cardPadding: 22, diagramGap: 24, tablePadding: 14, iconSize: 32 }
};

export function analyzePresentationDesign(input: DesignerInput): PresentationDesignAnalysis {
  const token = templateTokens[input.template] ?? templateTokens.corporate_clean;
  const decisions: LayoutDecision[] = [];

  input.slides.forEach((slide, index) => {
    const slideType = classifySlideType(slide, index, input.slides.length);
    const candidates = selectCandidates(slide, slideType, input).slice(0, 4);
    const previousTwo = decisions.slice(-2).map((decision) => decision.recommendedLayout.id);
    let recommended = candidates[0] ?? layoutById("LAYOUT-002");
    let variationApplied = false;
    if (previousTwo.length === 2 && previousTwo.every((id) => id === recommended.id)) {
      const varied = candidates.find((candidate) => candidate.id !== recommended.id) ?? layoutLibrary.find((layout) => !previousTwo.includes(layout.id));
      if (varied) {
        recommended = varied;
        variationApplied = true;
      }
    }

    const scoreBefore = scoreCurrentLayout(slide, slideType, input.qualityReport.total);
    const scoreDelta = estimateScoreDelta(slide, slideType, recommended, input.qualityReport);
    const scoreAfter = Math.min(100, scoreBefore + scoreDelta);
    decisions.push({
      slideId: slide.id,
      slideIndex: index + 1,
      slideTitle: slide.title,
      slideType,
      currentLayout: slide.layout,
      currentDiagram: slide.diagram,
      recommendedLayout: recommended,
      candidates,
      selectionReason: buildSelectionReason(slide, slideType, recommended, variationApplied, input),
      expectedEffect: recommended.expectedEffect,
      importance: estimateImportance(slide, slideType, index, input.slides.length),
      audience: input.salesStrategyBrief?.decisionMaker || input.draft.decisionMaker || input.story.decisionMaker || "営業担当 / 意思決定者",
      designToken: token,
      scoreBefore,
      scoreAfter,
      scoreDelta: scoreAfter - scoreBefore,
      variationApplied
    });
  });

  return {
    decisions,
    library: layoutLibrary,
    token,
    averageScoreBefore: Math.round(average(decisions.map((decision) => decision.scoreBefore))),
    averageScoreAfter: Math.round(average(decisions.map((decision) => decision.scoreAfter)))
  };
}

export function classifySlideType(slide: StorySlide, index: number, totalSlides: number): SlideType {
  const text = `${slide.title} ${slide.purpose} ${slide.message} ${slide.layout} ${slide.diagram}`.toLowerCase();
  if (index === 0 || /cover|表紙|title cover|hero/.test(text)) return "Cover";
  if (/agenda|目次|流れ/.test(text)) return "Agenda";
  if (/faq|質問|q&a/.test(text)) return "FAQ";
  if (/risk|リスク|懸念|注意/.test(text)) return "Risk";
  if (/estimate|見積|費用|価格|budget|予算/.test(text)) return "Estimate";
  if (/kpi|指標|効果|削減|率|%|score|quality/.test(text)) return "KPI";
  if (/timeline|schedule|スケジュール|日程|フェーズ/.test(text)) return "Timeline";
  if (/roadmap|ロードマップ|将来|展開/.test(text)) return "Roadmap";
  if (/before|after|比較|競合|差分|対比/.test(text)) return "Comparison";
  if (/case|事例|実績/.test(text)) return "Case Study";
  if (/problem|課題|痛み|困り|不足/.test(text)) return "Problem";
  if (/current|現状|as-is|業務/.test(text)) return "Current State";
  if (/analysis|分析|要因|洞察/.test(text)) return "Analysis";
  if (/feature|機能|仕様/.test(text)) return "Feature";
  if (/benefit|メリット|価値|成果/.test(text)) return "Benefit";
  if (/proposal|提案|解決|導入/.test(text)) return "Proposal";
  if (/next|action|次|承認|確認/.test(text) || index === totalSlides - 1) return "Next Action";
  if (/closing|まとめ|結論/.test(text)) return "Closing";
  return index >= totalSlides - 2 ? "Summary" : "Analysis";
}

function selectCandidates(slide: StorySlide, slideType: SlideType, input: DesignerInput): LayoutDefinition[] {
  const structuralSlide = slideType === "Cover" || slideType === "Agenda" || slideType === "Closing";
  const ids = [
    ...(structuralSlide ? slideTypeLayouts[slideType] : signalLayoutIds(slide, input)),
    ...(structuralSlide ? signalLayoutIds(slide, input) : slideTypeLayouts[slideType]),
    ...salesStrategyLayoutIds(input.salesStrategyBrief),
    ...storyLayoutIds(input.salesStrategyBrief?.recommendedStoryType || input.story.storyType),
    ...templateLayoutIds(input.template)
  ];
  return unique(ids).map(layoutById);
}

function signalLayoutIds(slide: StorySlide, input: DesignerInput): string[] {
  const text = `${slide.title} ${slide.purpose} ${slide.message} ${slide.diagram} ${slide.evidence}`.toLowerCase();
  const ids: string[] = [];
  if (/before|after|比較|競合|差分|対比/.test(text)) ids.push("LAYOUT-007", "LAYOUT-003");
  if (/kpi|%|削減|時間|円|score|quality|精度/.test(text)) ids.push("LAYOUT-006", "LAYOUT-015");
  if (/スケジュール|timeline|フェーズ|日程/.test(text)) ids.push("LAYOUT-008");
  if (/roadmap|ロードマップ|段階|展開/.test(text)) ids.push("LAYOUT-009");
  if (/flow|フロー|業務|連携|api|csv|承認|確認/.test(text)) ids.push("LAYOUT-010");
  if (/matrix|優先|評価|リスク|難易度|影響/.test(text)) ids.push("LAYOUT-011");
  if (/画像|現場|商品|画面|サンプル/.test(text)) ids.push("LAYOUT-013", "LAYOUT-014");
  if (slide.message.length > 220) ids.push("LAYOUT-003", "LAYOUT-010");
  if (input.qualityReport.ruleFindings.some((finding) => finding.slideId === slide.id && finding.category === "diagram")) ids.push("LAYOUT-010", "LAYOUT-011");
  return ids;
}

function storyLayoutIds(storyType: string): string[] {
  if (/ROI|KPI|効果|コスト/.test(storyType)) return ["LAYOUT-006", "LAYOUT-015"];
  if (/AI|DX|導入|Automation|自動/.test(storyType)) return ["LAYOUT-010", "LAYOUT-009", "LAYOUT-014"];
  if (/競合|差別/.test(storyType)) return ["LAYOUT-007", "LAYOUT-011"];
  return ["LAYOUT-003", "LAYOUT-004"];
}

function salesStrategyLayoutIds(brief?: SalesStrategyBrief): string[] {
  if (!brief) return [];
  const ids: string[] = [];
  if (brief.recommendedPresentationTone === "Executive") ids.push("LAYOUT-012", "LAYOUT-015", "LAYOUT-017");
  if (brief.recommendedPresentationTone === "Data Driven") ids.push("LAYOUT-006", "LAYOUT-011", "LAYOUT-015");
  if (brief.recommendedPresentationTone === "Agency") ids.push("LAYOUT-013", "LAYOUT-014", "LAYOUT-004");
  if (["AI", "業務改善", "DX"].includes(brief.proposalPosition)) ids.push("LAYOUT-010", "LAYOUT-009");
  if (brief.competitiveSituation !== "競合情報未確認") ids.push("LAYOUT-007", "LAYOUT-011");
  return ids;
}

function templateLayoutIds(template: PresentationTemplateId): string[] {
  if (template === "data_driven") return ["LAYOUT-006", "LAYOUT-011", "LAYOUT-015"];
  if (template === "executive_minimal") return ["LAYOUT-001", "LAYOUT-012", "LAYOUT-016"];
  if (template === "bold_vision" || template === "modern_dark") return ["LAYOUT-005", "LAYOUT-014", "LAYOUT-015"];
  if (template === "creative_agency") return ["LAYOUT-013", "LAYOUT-014", "LAYOUT-004"];
  return ["LAYOUT-003", "LAYOUT-010", "LAYOUT-016"];
}

function buildSelectionReason(slide: StorySlide, slideType: SlideType, layout: LayoutDefinition, variationApplied: boolean, input: DesignerInput): string {
  const reasons = [`Slide Typeは${slideType}です。`, `${layout.name}は${layout.visualFocus}を主役にできます。`];
  if (/比較|before|after|競合|差分/i.test(`${slide.title} ${slide.message}`)) reasons.push("比較要素を検出しました。");
  if (/kpi|%|時間|削減|円|精度/i.test(`${slide.title} ${slide.message}`)) reasons.push("数値・KPI要素を検出しました。");
  if (slide.message.length > 180) reasons.push("文章量が多いため、圧縮・分割・図解化しやすい構成を優先しました。");
  if (input.draft.decisionMaker) reasons.push(`Audienceは${input.draft.decisionMaker}を想定しています。`);
  if (input.salesStrategyBrief) {
    reasons.push(`Sales Strategy: ${input.salesStrategyBrief.winningStrategy}`);
    reasons.push(`Tone=${input.salesStrategyBrief.recommendedPresentationTone} / Position=${input.salesStrategyBrief.proposalPosition}`);
  }
  if (variationApplied) reasons.push("同一Layoutが3ページ続かないようVariationを適用しました。");
  return reasons.join(" ");
}

function estimateScoreDelta(slide: StorySlide, slideType: SlideType, layout: LayoutDefinition, report: PresentationQualityReport): number {
  let delta = slideTypeLayouts[slideType].includes(layout.id) ? 6 : 3;
  if (layout.visualFocus === "comparison" && /比較|before|after|競合|差分/i.test(`${slide.title} ${slide.message}`)) delta += 3;
  if (layout.visualFocus === "metrics" && /kpi|%|時間|削減|円|精度/i.test(`${slide.title} ${slide.message}`)) delta += 3;
  if (layout.visualFocus === "flow" && /業務|フロー|連携|確認|承認|api|csv/i.test(`${slide.title} ${slide.message}`)) delta += 3;
  if (slide.message.length > 220 && layout.density !== "high") delta += 2;
  if (report.ruleFindings.some((finding) => finding.slideId === slide.id && finding.category === "layout")) delta += 2;
  return Math.max(2, Math.min(14, delta));
}

function scoreCurrentLayout(slide: StorySlide, slideType: SlideType, baseScore: number): number {
  const current = slide.layout.toLowerCase();
  const expectedNames = slideTypeLayouts[slideType].map((id) => layoutById(id).name.toLowerCase());
  const match = expectedNames.some((name) => current.includes(name) || name.includes(current));
  const lengthPenalty = slide.message.length > 240 ? 8 : slide.message.length > 180 ? 4 : 0;
  return Math.max(45, Math.min(92, baseScore + (match ? 4 : -6) - lengthPenalty));
}

function estimateImportance(slide: StorySlide, slideType: SlideType, index: number, total: number): LayoutDecision["importance"] {
  if (index === 0 || index === total - 1) return "high";
  if (["Problem", "Comparison", "Proposal", "Estimate", "KPI", "Risk"].includes(slideType)) return "high";
  if (slide.message.length > 180 || /重要|必須|承認|判断/.test(`${slide.title} ${slide.message}`)) return "medium";
  return "low";
}

function layoutById(id: string): LayoutDefinition {
  return layoutLibrary.find((layout) => layout.id === id) ?? layoutLibrary[1];
}

function unique(values: string[]): string[] {
  return values.filter((value, index) => values.indexOf(value) === index);
}

function average(values: number[]): number {
  if (!values.length) return 0;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}
