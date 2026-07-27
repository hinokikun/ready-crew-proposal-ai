import type {
  AutoFixSuggestion,
  ContentFitRecommendation,
  DiagramRecommendation,
  DiagramType,
  PresentationQualityCategoryScore,
  PresentationQualityReport,
  PromptBuilderDraft,
  QualityRuleFinding,
  StoryPlan,
  StorySlide
} from "@/components/proposal-experience/types";

type EvaluationInput = {
  draft: PromptBuilderDraft;
  story: StoryPlan;
  slides: StorySlide[];
};

type CategoryDefinition = {
  key: string;
  label: string;
  weight: number;
  evaluate: (input: EvaluationInput) => CategoryEvaluation;
};

type CategoryEvaluation = {
  score: number;
  reason: string;
  improvement: string;
};

const maxTitleLength = 36;
const maxMessageLength = 180;
const denseMessageLength = 260;
const maxBulletCount = 6;

const categories: CategoryDefinition[] = [
  { key: "story", label: "Story", weight: 10, evaluate: ({ story }) => scoreBoolean(story.flow.length >= 5 && story.mainClaim.length > 12, "Storyの流れと主張が整理されています。", "Storyの起点、提案方針、意思決定までの流れを補ってください。") },
  { key: "customer_understanding", label: "Customer Understanding", weight: 8, evaluate: ({ draft }) => scoreBoolean(Boolean(draft.business || draft.targetUsers || draft.priorities), "顧客理解に必要な情報があります。", "顧客の事業、対象ユーザー、重視点を追加してください。") },
  { key: "problem_definition", label: "Problem Definition", weight: 8, evaluate: ({ draft }) => scoreBoolean(Boolean(draft.visibleIssues || draft.hiddenIssues || draft.riskIfUnsolved), "課題とリスクが確認できます。", "顕在課題、潜在課題、未解決時のリスクを具体化してください。") },
  { key: "proposal_specificity", label: "Proposal Specificity", weight: 8, evaluate: ({ draft }) => scoreBoolean(Boolean(draft.scope || draft.requiredFeatures || draft.constraints), "提案範囲と条件が具体化されています。", "対象範囲、必要機能、制約を追加してください。") },
  { key: "evidence", label: "Evidence", weight: 8, evaluate: ({ story }) => scoreByCount(story.missingEvidence.length, 0, 3, "根拠不足が少ない状態です。", "不足根拠を確認し、仮説と事実を分けてください。") },
  { key: "differentiation", label: "Differentiation", weight: 6, evaluate: ({ draft }) => scoreBoolean(Boolean(draft.competitors), "競合・比較情報があります。", "競合、代替案、自社の差別化ポイントを追加してください。") },
  { key: "executive_relevance", label: "Executive Relevance", weight: 6, evaluate: ({ draft, story }) => scoreBoolean(Boolean(draft.decisionMaker || /経営|役員|部長|責任者|投資|ROI/.test(story.mainClaim)), "意思決定者向けの観点があります。", "決裁者、投資判断、リスク、Next Actionを明確にしてください。") },
  { key: "sales_persuasiveness", label: "Sales Persuasiveness", weight: 6, evaluate: ({ story }) => scoreBoolean(Boolean(story.nextAction && story.objections.length >= 1), "反論対応とNext Actionがあります。", "想定反論と回答、次に合意したい行動を追加してください。") },
  { key: "slide_objective", label: "Slide Objective", weight: 6, evaluate: ({ slides }) => scoreBoolean(slides.every((slide) => slide.purpose.length > 8), "各スライドの目的が設定されています。", "各スライドで何を理解してほしいかを1文で明記してください。") },
  { key: "content_volume", label: "Content Volume", weight: 5, evaluate: ({ slides }) => scoreByCount(slides.filter((slide) => slide.message.length > maxMessageLength).length, 0, Math.max(1, slides.length / 3), "本文量は概ね適切です。", "長文スライドを圧縮、分割、図解化してください。") },
  { key: "readability", label: "Readability", weight: 5, evaluate: ({ slides }) => scoreByCount(slides.filter((slide) => slide.title.length > maxTitleLength).length, 0, 2, "タイトルは読みやすい長さです。", "長いタイトルを短くし、結論を先に置いてください。") },
  { key: "visual_hierarchy", label: "Visual Hierarchy", weight: 5, evaluate: ({ slides }) => scoreBoolean(slides.some((slide) => hasNumber(slide.message) || /重要|効果|削減|改善|目標/.test(slide.message)), "重要語や数字を強調できる余地があります。", "重要数字、成果、判断ポイントを主役にしてください。") },
  { key: "layout", label: "Layout", weight: 5, evaluate: ({ slides }) => scoreBoolean(hasEnoughLayoutDiversity(slides) && !hasTripleLayoutRepeat(slides), "レイアウトの多様性があります。", "同じレイアウトの連続を避け、比較、フロー、KPIなどを混ぜてください。") },
  { key: "diagram_use", label: "Diagram Use", weight: 4, evaluate: ({ slides }) => scoreBoolean(slides.filter((slide) => hasConcreteDiagram(slide)).length >= Math.ceil(slides.length * 0.5), "図解利用が一定量あります。", "文章だけのスライドに比較表、フロー、KPIカードを提案してください。") },
  { key: "design_consistency", label: "Design Consistency", weight: 4, evaluate: ({ draft, slides }) => scoreBoolean(Boolean(draft.designStyle) && slides.every((slide) => slide.layout), "テンプレートとレイアウトが設定されています。", "テンプレートとレイアウトタイプをすべてのスライドへ設定してください。") },
  { key: "brand_consistency", label: "Brand Consistency", weight: 3, evaluate: ({ draft }) => scoreBoolean(Boolean(draft.clientName), "顧客名を資料全体で参照できます。", "顧客名、会社名、フッターなどのBrand Kit情報を確認してください。") },
  { key: "estimate_consistency", label: "Estimate Consistency", weight: 2, evaluate: ({ draft }) => scoreBoolean(Boolean(draft.budget || draft.scope), "予算または範囲が見積と接続できます。", "見積条件、対象範囲、除外条件を入力してください。") },
  { key: "next_action", label: "Next Action", weight: 1, evaluate: ({ story }) => scoreBoolean(story.nextAction.length > 10, "Next Actionがあります。", "次回確認事項、合意事項、提出後アクションを追加してください。") }
];

export function evaluatePresentationQuality(input: EvaluationInput): PresentationQualityReport {
  const items = categories.map((category) => toCategoryScore(category, category.evaluate(input)));
  const weightTotal = items.reduce((sum, item) => sum + item.weight, 0);
  const total = Math.round(items.reduce((sum, item) => sum + item.score * item.weight, 0) / weightTotal);
  const ruleFindings = evaluateQualityRules(input);
  const diagramRecommendations = recommendDiagrams(input.slides);
  const fitRecommendations = recommendContentFit(input.slides);
  const autoFixSuggestions = buildAutoFixSuggestions(input.slides, ruleFindings, diagramRecommendations, fitRecommendations);
  return {
    total,
    grade: total >= 90 ? "A" : total >= 75 ? "B" : total >= 60 ? "C" : "D",
    items,
    warnings: ruleFindings.filter((finding) => finding.severity !== "info").map((finding) => `${finding.slideTitle ? `${finding.slideTitle}: ` : ""}${finding.message}`),
    ruleFindings,
    diagramRecommendations,
    fitRecommendations,
    autoFixSuggestions
  };
}

function evaluateQualityRules({ draft, slides }: EvaluationInput): QualityRuleFinding[] {
  const findings: QualityRuleFinding[] = [];
  slides.forEach((slide) => {
    const bulletCount = countBullets(slide.message);
    if (slide.title.length > maxTitleLength) {
      findings.push(rule("タイトル長", slide, "warning", `タイトルが${slide.title.length}文字です。`, "36文字以内を目安に短くしてください。"));
    }
    if (slide.message.length > maxMessageLength) {
      findings.push(rule("本文量", slide, slide.message.length > denseMessageLength ? "critical" : "warning", `本文が${slide.message.length}文字です。`, "圧縮、分割、図解化のいずれかを検討してください。"));
    }
    if (slide.message.length > denseMessageLength || bulletCount > maxBulletCount) {
      findings.push(rule("余白", slide, "warning", "情報量が多く、余白が不足しやすい状態です。", "本文を分けるか、図解カードへ変換してください。"));
    }
    if (bulletCount > maxBulletCount) {
      findings.push(rule("箇条書き数", slide, "warning", `箇条書き相当の要素が${bulletCount}件あります。`, "6件以内へ集約してください。"));
    }
    if (shouldUseDiagram(slide) && !hasConcreteDiagram(slide)) {
      findings.push(rule("図解不足", slide, "warning", "文章で説明している内容に対して図解が不足しています。", "比較表、フロー、KPIカードなどへ変換してください。"));
    }
    if (!isSingleMessage(slide.message)) {
      findings.push(rule("ページ毎1メッセージ", slide, "warning", "1スライド内に複数の主張が含まれています。", "主張を1つに絞り、残りは別スライドへ分けてください。"));
    }
  });

  if (/競合|比較|差別|Before|After/i.test(combinedSlideText(slides, draft)) && !slides.some((slide) => /Comparison|Matrix|Before|After|比較|マトリクス/.test(`${slide.layout} ${slide.diagram}`))) {
    findings.push({ rule: "比較表不足", severity: "warning", message: "比較や差別化の内容がありますが、比較表またはマトリクスがありません。", recommendation: "競合比較、Before/After、評価軸マトリクスのいずれかを追加してください。" });
  }

  if (hasTripleLayoutRepeat(slides)) {
    findings.push({ rule: "レイアウト重複", severity: "warning", message: "同じレイアウトが3枚以上連続しています。", recommendation: "連続するスライドの一部を図解、KPI、比較、Timelineへ変更してください。" });
  }

  if (!slides.some((slide) => hasNumber(slide.message) || /KPI|効果|削減|率|時間/.test(slide.title))) {
    findings.push({ rule: "強調不足", severity: "info", message: "成果や判断材料になる数字が目立っていません。", recommendation: "KPIカードまたはLarge Numberで重要指標を強調してください。" });
  }
  return findings;
}

function recommendDiagrams(slides: StorySlide[]): DiagramRecommendation[] {
  const recommendations: DiagramRecommendation[] = [];
  slides.forEach((slide) => {
    const text = `${slide.title} ${slide.message} ${slide.purpose} ${slide.evidence}`;
    const diagramType = chooseDiagramType(text);
    if (!diagramType || slide.diagram.includes(diagramType)) return;
    recommendations.push({
      slideId: slide.id,
      slideTitle: slide.title,
      diagramType,
      reason: `${diagramType}にすると、文章説明を視覚的に理解しやすくなります。`,
      priority: slide.message.length > maxMessageLength ? "high" : "medium"
    });
  });
  return recommendations.slice(0, 6);
}

function recommendContentFit(slides: StorySlide[]): ContentFitRecommendation[] {
  const recommendations: ContentFitRecommendation[] = [];
  slides.forEach((slide) => {
    if (slide.message.length > denseMessageLength) {
      recommendations.push({ slideId: slide.id, slideTitle: slide.title, action: "分割", reason: "本文量が多く、1スライドで読み切りにくい状態です。", beforeLength: slide.message.length, expectedEffect: "1ページ1メッセージを維持できます。" });
    } else if (slide.message.length > maxMessageLength) {
      recommendations.push({ slideId: slide.id, slideTitle: slide.title, action: "圧縮", reason: "本文が長く、余白を圧迫する可能性があります。", beforeLength: slide.message.length, expectedEffect: "視認性が上がります。" });
    }
    if (shouldUseDiagram(slide)) {
      recommendations.push({ slideId: slide.id, slideTitle: slide.title, action: "図解化", reason: "工程、比較、数値、分類の説明が含まれています。", beforeLength: slide.message.length, expectedEffect: "営業担当が説明しやすくなります。" });
    }
  });
  return recommendations.slice(0, 8);
}

function buildAutoFixSuggestions(slides: StorySlide[], findings: QualityRuleFinding[], diagrams: DiagramRecommendation[], fits: ContentFitRecommendation[]): AutoFixSuggestion[] {
  const suggestions: AutoFixSuggestion[] = [];
  slides.forEach((slide) => {
    if (slide.title.length > maxTitleLength) {
      suggestions.push(autoFix(slide, "title", "長いタイトルを短くします。", { title: shortenTitle(slide.title), caution: appendCaution(slide.caution, "タイトルを短縮しました。") }));
    }
    if (slide.message.length > maxMessageLength || !isSingleMessage(slide.message)) {
      suggestions.push(autoFix(slide, "content", "本文を結論先行で圧縮します。", { message: compressMessage(slide.message), caution: appendCaution(slide.caution, "本文を圧縮しました。") }));
    }
    const diagram = diagrams.find((item) => item.slideId === slide.id);
    if (diagram) {
      suggestions.push(autoFix(slide, "diagram", `${diagram.diagramType}へ図解方針を変更します。`, { diagram: diagram.diagramType, layout: layoutForDiagram(diagram.diagramType), caution: appendCaution(slide.caution, "図解方針を変更しました。") }));
    }
  });

  const duplicated = findings.find((finding) => finding.rule === "レイアウト重複");
  if (duplicated && slides[2]) {
    suggestions.push(autoFix(slides[2], "layout", "連続するレイアウトを別タイプへ変更します。", { layout: "Process Flow", diagram: "フロー", caution: appendCaution(slides[2].caution, "レイアウト重複を避けました。") }));
  }

  const splitTarget = fits.find((item) => item.action === "分割");
  if (splitTarget) {
    const slide = slides.find((item) => item.id === splitTarget.slideId);
    if (slide) suggestions.push(autoFix(slide, "message", "分割前提で主張を1つに絞ります。", { message: firstSentence(slide.message), caution: appendCaution(slide.caution, "残りの論点は別スライド化候補です。") }));
  }

  return uniqueById(suggestions).slice(0, 6);
}

function toCategoryScore(category: CategoryDefinition, evaluation: CategoryEvaluation): PresentationQualityCategoryScore {
  const score = clampScore(evaluation.score);
  return {
    key: category.key,
    label: category.label,
    score,
    weight: category.weight,
    reason: evaluation.reason,
    improvement: evaluation.improvement,
    severity: score >= 80 ? "ok" : score >= 60 ? "warning" : "critical"
  };
}

function scoreBoolean(ok: boolean, reason: string, improvement: string): CategoryEvaluation {
  return { score: ok ? 90 : 55, reason: ok ? reason : "改善余地があります。", improvement };
}

function scoreByCount(count: number, best: number, warning: number, reason: string, improvement: string): CategoryEvaluation {
  if (count <= best) return { score: 92, reason, improvement: "維持してください。" };
  if (count <= warning) return { score: 72, reason: "軽微な改善余地があります。", improvement };
  return { score: 48, reason: "重要な改善が必要です。", improvement };
}

function rule(ruleName: string, slide: StorySlide, severity: QualityRuleFinding["severity"], message: string, recommendation: string): QualityRuleFinding {
  const meta = qualityRuleMeta(`${ruleName} ${message} ${recommendation}`);
  return {
    rule: ruleName,
    slideId: slide.id,
    slideTitle: slide.title,
    severity,
    message,
    recommendation,
    ...meta,
    auto_fixable: severity !== "info",
    confidence: 0.82,
    human_review_required: severity === "critical"
  };
}

function qualityRuleMeta(text: string): Pick<QualityRuleFinding, "rule_id" | "category"> {
  if (/KPI|%|数字|数値|time|rate/i.test(text)) return { rule_id: "PPT-NUMERIC-001", category: "numeric" };
  if (/比較|競合|Before|After|comparison|matrix/i.test(text)) return { rule_id: "PPT-COMPARE-001", category: "diagram" };
  if (/図解|フロー|ロードマップ|タイムライン|diagram|flow|timeline|roadmap/i.test(text)) return { rule_id: "PPT-DIAGRAM-001", category: "diagram" };
  if (/タイトル|title/i.test(text)) return { rule_id: "PPT-TITLE-001", category: "title" };
  if (/箇条|bullet/i.test(text)) return { rule_id: "PPT-BULLET-001", category: "content_fit" };
  if (/余白|overflow|fit/i.test(text)) return { rule_id: "PPT-OVERFLOW-001", category: "overflow" };
  if (/レイアウト|layout/i.test(text)) return { rule_id: "PPT-LAYOUT-001", category: "layout" };
  return { rule_id: "PPT-BODY-001", category: "content_fit" };
}

function autoFix(slide: StorySlide, type: AutoFixSuggestion["type"], reason: string, after: AutoFixSuggestion["after"]): AutoFixSuggestion {
  return {
    id: `${type}-${slide.id}`,
    slideId: slide.id,
    slideTitle: slide.title,
    type,
    reason,
    before: { title: slide.title, message: slide.message, layout: slide.layout, diagram: slide.diagram, caution: slide.caution },
    after
  };
}

function countBullets(text: string): number {
  const lineBullets = text.split(/\n|・|•|-/).filter((item) => item.trim().length > 0).length;
  const commaItems = text.split(/、|,|，/).filter((item) => item.trim().length > 0).length;
  return Math.max(lineBullets, commaItems);
}

function chooseDiagramType(text: string): DiagramType | null {
  if (/比較|競合|差別|Before|After|対比|強み|弱み/i.test(text)) return "比較表";
  if (/納期|日程|スケジュール|月|週|フェーズ|段階/.test(text)) return "タイムライン";
  if (/ロードマップ|将来|中長期|拡張|展開/.test(text)) return "ロードマップ";
  if (/KPI|指標|精度|率|削減|時間|件|%|％|円|万円/.test(text)) return "KPIカード";
  if (/業務|処理|連携|確認|承認|登録|入力|出力|API|CSV/.test(text)) return "フロー";
  if (/評価|優先|カテゴリ|分類|リスク|影響|難易度/.test(text)) return "マトリクス";
  return null;
}

function layoutForDiagram(diagramType: DiagramType): string {
  const map: Record<DiagramType, string> = {
    比較表: "Comparison Table",
    タイムライン: "Timeline",
    ロードマップ: "Roadmap",
    KPIカード: "KPI Dashboard",
    フロー: "Process Flow",
    マトリクス: "Competitor Matrix"
  };
  return map[diagramType];
}

function shouldUseDiagram(slide: StorySlide): boolean {
  return Boolean(chooseDiagramType(`${slide.title} ${slide.message} ${slide.purpose}`));
}

function hasConcreteDiagram(slide: StorySlide): boolean {
  return /比較|表|タイムライン|ロードマップ|KPI|カード|フロー|プロセス|マトリクス|Before|After|構成|図/.test(slide.diagram);
}

function hasEnoughLayoutDiversity(slides: StorySlide[]): boolean {
  return new Set(slides.map((slide) => slide.layout)).size >= Math.min(5, slides.length);
}

function hasTripleLayoutRepeat(slides: StorySlide[]): boolean {
  return slides.some((slide, index) => index >= 2 && slides[index - 1]?.layout === slide.layout && slides[index - 2]?.layout === slide.layout);
}

function isSingleMessage(message: string): boolean {
  const sentenceCount = message.split(/。|\.|!|！|\?|？/).filter((item) => item.trim().length > 8).length;
  const connectors = (message.match(/また|さらに|加えて|一方|ただし/g) ?? []).length;
  return sentenceCount <= 2 && connectors <= 1;
}

function hasNumber(text: string): boolean {
  return /\d|[０-９]|%|％|円|万円|件|時間|分/.test(text);
}

function combinedSlideText(slides: StorySlide[], draft: PromptBuilderDraft): string {
  return `${Object.values(draft).join(" ")} ${slides.map((slide) => `${slide.title} ${slide.message} ${slide.diagram}`).join(" ")}`;
}

function shortenTitle(title: string): string {
  return title.length <= 24 ? title : `${title.slice(0, 23)}…`;
}

function compressMessage(message: string): string {
  const first = firstSentence(message);
  if (first.length <= 90) return first.startsWith("結論") ? first : `結論: ${first}`;
  return `結論: ${first.slice(0, 88)}…`;
}

function firstSentence(message: string): string {
  return message.split(/。|\.|\n/).find((part) => part.trim().length > 0)?.trim() || message.slice(0, 100);
}

function appendCaution(current: string, next: string): string {
  return current ? `${current} / ${next}` : next;
}

function uniqueById(suggestions: AutoFixSuggestion[]): AutoFixSuggestion[] {
  const seen = new Set<string>();
  return suggestions.filter((suggestion) => {
    if (seen.has(suggestion.id)) return false;
    seen.add(suggestion.id);
    return true;
  });
}

function clampScore(value: number): number {
  return Math.max(0, Math.min(100, Math.round(value)));
}
