import type { PromptBuilderDraft, SalesStrategyBrief, SalesStrategyObjection, SalesStrategyRisk } from "@/components/proposal-experience/types";

type SalesStrategyInput = {
  draft: PromptBuilderDraft;
  sourceText: string;
};

type DecisionMakerKey =
  | "executive"
  | "department_head"
  | "manager"
  | "field_leader"
  | "information_systems"
  | "marketing"
  | "sales"
  | "hr"
  | "recruiting"
  | "unknown";

const decisionMakerProfiles: Record<DecisionMakerKey, SalesStrategyBrief["decisionMakerProfile"]> = {
  executive: {
    decisionMaker: "executive",
    focusPoints: ["投資判断", "全社効果", "リスク管理"],
    avoidExpressions: ["細かい機能説明から入る", "根拠のない効果断定"],
    proposalOrder: ["経営課題", "投資効果", "リスク", "意思決定事項"]
  },
  department_head: {
    decisionMaker: "department_head",
    focusPoints: ["部門成果", "体制", "実行可能性"],
    avoidExpressions: ["現場負荷を隠す", "抽象論だけで終える"],
    proposalOrder: ["部門課題", "解決方針", "導入範囲", "承認条件"]
  },
  manager: {
    decisionMaker: "manager",
    focusPoints: ["チーム負荷", "スケジュール", "運用手順"],
    avoidExpressions: ["理想像だけを語る"],
    proposalOrder: ["現状業務", "変更点", "支援内容", "次の確認"]
  },
  field_leader: {
    decisionMaker: "field_leader",
    focusPoints: ["日々の作業", "例外対応", "確認負荷"],
    avoidExpressions: ["完全自動化と断定する", "現場確認を軽く扱う"],
    proposalOrder: ["現在の業務", "AI支援範囲", "人の確認", "PoC"]
  },
  information_systems: {
    decisionMaker: "information_systems",
    focusPoints: ["連携", "セキュリティ", "運用責任"],
    avoidExpressions: ["ブラックボックス化", "権限やログを曖昧にする"],
    proposalOrder: ["構成", "連携", "安全性", "運用"]
  },
  marketing: {
    decisionMaker: "marketing",
    focusPoints: ["顧客体験", "CV", "ブランド"],
    avoidExpressions: ["内部都合だけで説明する"],
    proposalOrder: ["顧客課題", "体験改善", "差別化", "測定"]
  },
  sales: {
    decisionMaker: "sales",
    focusPoints: ["顧客価値", "差別化", "次アクション"],
    avoidExpressions: ["技術説明に寄りすぎる"],
    proposalOrder: ["顧客課題", "提案ポジション", "根拠", "次アクション"]
  },
  hr: {
    decisionMaker: "hr",
    focusPoints: ["応募者体験", "運用負荷", "採用品質"],
    avoidExpressions: ["候補者視点を抜く"],
    proposalOrder: ["採用課題", "体験設計", "運用", "効果測定"]
  },
  recruiting: {
    decisionMaker: "recruiting",
    focusPoints: ["応募数", "面接化率", "フォロー品質"],
    avoidExpressions: ["採用担当の負担を増やす"],
    proposalOrder: ["応募者接点", "改善施策", "運用", "採用KPI"]
  },
  unknown: {
    decisionMaker: "unknown",
    focusPoints: ["意思決定者確認", "成功条件", "不足情報"],
    avoidExpressions: ["承認者を決め打ちする"],
    proposalOrder: ["分かっている事実", "仮説", "確認事項", "レビュー依頼"]
  }
};

export function analyzeSalesStrategy({ draft, sourceText }: SalesStrategyInput): SalesStrategyBrief {
  const text = normalize(`${Object.values(draft).join(" ")} ${sourceText}`);
  const projectCategory = classifyProjectCategory(text);
  const decisionMaker = classifyDecisionMaker(text, draft.decisionMaker);
  const competitiveSituation = classifyCompetitiveSituation(text, draft.competitors);
  const proposalPosition = classifyProposalPosition(text, projectCategory);
  const recommendedStoryType = chooseStoryType(projectCategory, decisionMaker, proposalPosition, text);
  const recommendedPresentationTone = choosePresentationTone(decisionMaker, proposalPosition, competitiveSituation, text);
  const evidenceClassification = classifyEvidence(draft);
  const expectedObjections = buildExpectedObjections(draft, competitiveSituation, proposalPosition);
  const riskFactors = buildRiskFactors(draft, evidenceClassification, projectCategory);
  const humanReviewReasons = buildHumanReviewReasons(decisionMaker, evidenceClassification, expectedObjections, projectCategory);
  const confidence = calculateConfidence(draft, projectCategory, decisionMaker, evidenceClassification, humanReviewReasons);
  const winningStrategy = buildWinningStrategy(projectCategory, proposalPosition, competitiveSituation, decisionMaker);
  const recommendedSlideTypes = buildRecommendedSlideTypes(projectCategory, expectedObjections, competitiveSituation);

  return {
    schemaVersion: "sales_strategy_brief_v1",
    projectCategory,
    customerIndustry: draft.industry || "確認必要",
    customerSize: classifyCustomerSize(text),
    customerMaturity: classifyCustomerMaturity(text),
    businessModel: classifyBusinessModel(text),
    decisionMaker,
    decisionProcess: chooseDecisionProcess(decisionMaker, draft.stakeholders),
    stakeholders: splitItems(draft.stakeholders),
    businessGoal: draft.priorities || draft.business || "確認必要",
    currentSituation: draft.currentState || sourceText.slice(0, 180) || "確認必要",
    painPoints: splitItems(`${draft.visibleIssues}\n${draft.hiddenIssues}`).slice(0, 5),
    urgency: draft.deadline ? "期限あり" : "確認必要",
    budgetStatus: draft.budget ? "入力あり" : "確認必要",
    timeline: draft.deadline || "確認必要",
    competitiveSituation,
    proposalPosition,
    winningStrategy,
    expectedObjections,
    riskFactors,
    differentiation: buildDifferentiation(projectCategory, proposalPosition, competitiveSituation),
    recommendedStoryType,
    recommendedSlideTypes,
    recommendedPresentationTone,
    executiveSummary: buildExecutiveSummary(draft, projectCategory, proposalPosition, winningStrategy),
    confidence,
    humanReviewRequired: humanReviewReasons.length > 0,
    humanReviewReasons,
    decisionMakerProfile: decisionMakerProfiles[decisionMaker],
    evidenceClassification,
    selectionReasons: [
      `category=${projectCategory}`,
      `decision_maker=${decisionMaker}`,
      `competition=${competitiveSituation}`,
      `proposal_position=${proposalPosition}`,
      `tone=${recommendedPresentationTone}`
    ]
  };
}

function classifyProjectCategory(text: string): string {
  if (/ai-ocr|ocr|画像|認識|請求書|帳票/.test(text)) return "vision_ocr";
  if (/rpa|自動化|bot|ワークフロー|定型/.test(text)) return "automation";
  if (/crm|sfa|営業|パイプライン/.test(text)) return "crm_sales_intelligence";
  if (/チャット|chatbot|faq|問い合わせ/.test(text)) return "conversational_ai";
  if (/ナレッジ|検索|rag|社内文書/.test(text)) return "knowledge_ai";
  if (/生成ai|llm|プロンプト|文章生成/.test(text)) return "generative_ai_transformation";
  if (/web|サイト|cms|seo|ec|ux|cv/.test(text)) return "digital_experience";
  return "generic_consulting";
}

function classifyDecisionMaker(text: string, explicit: string): DecisionMakerKey {
  const source = normalize(`${explicit} ${text}`);
  if (/経営|役員|ceo|社長|決裁/.test(source)) return "executive";
  if (/部長|部門|責任者/.test(source)) return "department_head";
  if (/課長|manager|マネージャー/.test(source)) return "manager";
  if (/現場|運用|担当者|作業/.test(source)) return "field_leader";
  if (/情報システム|情シス|it|api|db|セキュリティ/.test(source)) return "information_systems";
  if (/マーケ|広報|ブランド|web|ec/.test(source)) return "marketing";
  if (/人事|採用|候補者/.test(source)) return source.includes("採用") ? "recruiting" : "hr";
  if (/営業|顧客|商談/.test(source)) return "sales";
  return "unknown";
}

function classifyCompetitiveSituation(text: string, competitors: string): string {
  const source = normalize(`${text} ${competitors}`);
  if (!source || !/競合|他社|比較|代替|competitor|vendor/.test(source)) return "競合情報未確認";
  if (/価格|費用|予算|安い|cost|price/.test(source)) return "価格競争";
  if (/品質|精度|正確|quality/.test(source)) return "品質競争";
  if (/スピード|短納期|急ぎ|speed/.test(source)) return "スピード競争";
  if (/dx|全社|デジタル/.test(source)) return "DX競争";
  if (/ai|ocr|llm/.test(source)) return "AI導入競争";
  if (/採用|ブランド|認知/.test(source)) return "ブランド競争";
  return "品質競争";
}

function classifyProposalPosition(text: string, category: string): string {
  if (/採用|人材|候補者/.test(text)) return "採用";
  if (/ブランド|認知|広報/.test(text)) return "ブランディング";
  if (/ec|通販|購入/.test(text)) return "EC改善";
  if (category === "digital_experience") return "Web改善";
  if (/売上|商談|受注/.test(text) || category === "crm_sales_intelligence") return "売上向上";
  if (/コスト|削減|効率|時間短縮/.test(text)) return "コスト削減";
  if (/dx|全社/.test(text)) return "DX";
  if (/ai|ocr|llm|生成ai|画像/.test(text)) return "AI";
  if (/マーケ|cv|seo/.test(text)) return "マーケティング";
  return "業務改善";
}

function chooseStoryType(category: string, decisionMaker: DecisionMakerKey, proposalPosition: string, text: string): string {
  if (decisionMaker === "executive") return "ROI";
  if (proposalPosition === "AI" || category.includes("ai") || category === "vision_ocr") return "AI";
  if (proposalPosition === "DX" || /dx/.test(text)) return "DX";
  if (category === "automation" || proposalPosition === "業務改善" || proposalPosition === "コスト削減") return "Automation";
  if (["Web改善", "EC改善", "マーケティング", "ブランディング", "採用"].includes(proposalPosition)) return "Customer Experience";
  return "Generic";
}

function choosePresentationTone(decisionMaker: DecisionMakerKey, proposalPosition: string, competitiveSituation: string, text: string): string {
  if (decisionMaker === "executive") return "Executive";
  if (/kpi|数値|%|データ/.test(text) || ["価格競争", "品質競争"].includes(competitiveSituation)) return "Data Driven";
  if (["Web改善", "EC改善", "マーケティング", "ブランディング", "採用"].includes(proposalPosition)) return "Agency";
  if (["information_systems", "department_head"].includes(decisionMaker)) return "Consulting";
  if (proposalPosition === "AI" || proposalPosition === "DX") return "Formal";
  return "Friendly";
}

function classifyEvidence(draft: PromptBuilderDraft): SalesStrategyBrief["evidenceClassification"] {
  return {
    missing: [
      !draft.industry ? "customer_industry" : "",
      !draft.visibleIssues && !draft.hiddenIssues ? "pain_points" : ""
    ].filter(Boolean),
    hypothesis: [!draft.stakeholders ? "stakeholders" : "", !draft.requiredFeatures ? "solution_scope" : ""].filter(Boolean),
    needsConfirmation: [
      !draft.decisionMaker ? "decision_maker" : "",
      !draft.budget ? "budget" : "",
      !draft.deadline ? "timeline" : "",
      !draft.priorities ? "business_goal" : ""
    ].filter(Boolean),
    aiInferred: [!draft.constraints ? "risk_factors" : ""].filter(Boolean)
  };
}

function buildExpectedObjections(draft: PromptBuilderDraft, competitiveSituation: string, proposalPosition: string): SalesStrategyObjection[] {
  const objections: SalesStrategyObjection[] = [];
  if (!draft.budget || competitiveSituation === "価格競争") {
    objections.push({ objection: "価格", reason: "費用対効果や他社比較で止まる可能性があります。", recommendedSlide: "Estimate", recommendedEvidence: "範囲、前提、段階導入案" });
  }
  if (!draft.deadline) {
    objections.push({ objection: "スケジュール", reason: "導入時期の判断材料が不足しています。", recommendedSlide: "Timeline", recommendedEvidence: "マイルストーンと意思決定ポイント" });
  }
  if (!draft.priorities) {
    objections.push({ objection: "ROI", reason: "成果指標が未確定です。", recommendedSlide: "KPI", recommendedEvidence: "現状値、目標値、測定方法" });
  }
  if (proposalPosition === "AI" || draft.requiredFeatures || draft.constraints) {
    objections.push({ objection: "導入負荷", reason: "運用変更や連携負荷を懸念される可能性があります。", recommendedSlide: "Architecture", recommendedEvidence: "人の確認、連携範囲、運用責任" });
  }
  if (competitiveSituation !== "競合情報未確認") {
    objections.push({ objection: "競合比較", reason: "他社との差が問われます。", recommendedSlide: "Comparison", recommendedEvidence: "比較軸と差別化理由" });
  }
  return uniqueBy(objections, (item) => item.objection).slice(0, 6);
}

function buildRiskFactors(draft: PromptBuilderDraft, evidence: SalesStrategyBrief["evidenceClassification"], category: string): SalesStrategyRisk[] {
  const risks: SalesStrategyRisk[] = [];
  splitItems(draft.constraints).forEach((item) => risks.push({ category: "provided", item, reason: "入力された制約です。" }));
  evidence.missing.forEach((item) => risks.push({ category: "missing", item, reason: "提案判断に必要な情報が不足しています。" }));
  evidence.hypothesis.forEach((item) => risks.push({ category: "hypothesis", item, reason: "現時点では仮説として扱います。" }));
  evidence.needsConfirmation.forEach((item) => risks.push({ category: "needs_confirmation", item, reason: "営業担当が確認してください。" }));
  if (category === "vision_ocr" || category.includes("ai")) {
    risks.push({ category: "ai_inferred", item: "ai_accuracy_and_human_review", reason: "AIの判断は人の確認を残す前提で扱います。" });
  }
  return risks.slice(0, 10);
}

function buildHumanReviewReasons(
  decisionMaker: DecisionMakerKey,
  evidence: SalesStrategyBrief["evidenceClassification"],
  objections: SalesStrategyObjection[],
  projectCategory: string
): string[] {
  const reasons: string[] = [];
  if (decisionMaker === "unknown") reasons.push("意思決定者が未確定です。");
  if (projectCategory === "generic_consulting") reasons.push("案件カテゴリが汎用判定です。");
  if (evidence.missing.length > 0) reasons.push("必須情報に不足があります。");
  if (evidence.needsConfirmation.length > 0) reasons.push("確認が必要な情報があります。");
  if (objections.length >= 4) reasons.push("想定反論が多いため営業確認が必要です。");
  return reasons;
}

function calculateConfidence(
  draft: PromptBuilderDraft,
  projectCategory: string,
  decisionMaker: DecisionMakerKey,
  evidence: SalesStrategyBrief["evidenceClassification"],
  reviewReasons: string[]
): number {
  let score = 0.38;
  if (projectCategory !== "generic_consulting") score += 0.16;
  if (decisionMaker !== "unknown") score += 0.14;
  if (draft.visibleIssues || draft.hiddenIssues) score += 0.08;
  if (draft.priorities || draft.business) score += 0.08;
  if (draft.budget) score += 0.05;
  if (draft.deadline) score += 0.05;
  score -= evidence.missing.length * 0.04;
  score -= evidence.needsConfirmation.length * 0.025;
  score -= Math.min(reviewReasons.length * 0.015, 0.08);
  return Math.max(0.15, Math.min(0.95, Math.round(score * 100) / 100));
}

function buildWinningStrategy(projectCategory: string, proposalPosition: string, competitiveSituation: string, decisionMaker: DecisionMakerKey): string {
  if (competitiveSituation === "価格競争") return "値引き前提ではなく、範囲分割と成果測定で投資判断しやすくする。";
  if (competitiveSituation === "品質競争") return "評価基準、レビュー工程、品質保証の見える化で勝つ。";
  if (competitiveSituation === "スピード競争") return "初期範囲を絞り、依存関係と意思決定日を明確にして勝つ。";
  if (proposalPosition === "AI" || projectCategory === "vision_ocr") return "AIを人の判断支援として位置付け、安全なPoCから導入判断につなげる。";
  if (decisionMaker === "executive") return "投資効果、リスク、次の承認事項を短く結び、経営判断を前に進める。";
  return "現状課題を具体的な範囲、測定方法、次アクションに落として勝つ。";
}

function buildRecommendedSlideTypes(projectCategory: string, objections: SalesStrategyObjection[], competitiveSituation: string): string[] {
  const base: Record<string, string[]> = {
    vision_ocr: ["Cover", "Problem", "Before / After", "Architecture", "PoC", "KPI", "Estimate", "Next Action"],
    automation: ["Cover", "Current State", "Flow", "Before / After", "KPI", "Risk", "Next Action"],
    digital_experience: ["Cover", "Problem", "Customer Journey", "Proposal", "Comparison", "Timeline", "KPI", "Next Action"],
    crm_sales_intelligence: ["Cover", "Problem", "Pipeline Analysis", "Proposal", "KPI", "Roadmap", "Estimate", "Next Action"],
    generic_consulting: ["Cover", "Problem", "Analysis", "Proposal", "Roadmap", "KPI", "Estimate", "Next Action"]
  };
  const slides = [...(base[projectCategory] ?? base.generic_consulting)];
  if (competitiveSituation !== "競合情報未確認" && !slides.includes("Comparison")) slides.splice(3, 0, "Comparison");
  objections.forEach((item) => {
    if (!slides.includes(item.recommendedSlide)) slides.splice(Math.max(1, slides.length - 2), 0, item.recommendedSlide);
  });
  return unique(slides).slice(0, 10);
}

function buildDifferentiation(projectCategory: string, proposalPosition: string, competitiveSituation: string): string[] {
  const points = ["判断基準を明確化", "段階導入", "未確定情報を人が確認"];
  if (projectCategory === "vision_ocr") points.push("AI候補提示と人の最終確認");
  if (proposalPosition === "Web改善" || proposalPosition === "EC改善") points.push("顧客体験と成果指標を接続");
  if (competitiveSituation !== "競合情報未確認") points.push("競合比較軸を明示");
  return unique(points);
}

function buildExecutiveSummary(draft: PromptBuilderDraft, projectCategory: string, proposalPosition: string, winningStrategy: string): string {
  const title = draft.projectName || "この案件";
  const problem = draft.visibleIssues || draft.currentState || "確認済み課題";
  return `${title}は${projectCategory}領域の${proposalPosition}提案です。${problem}を起点に、${winningStrategy}`;
}

function classifyCustomerSize(text: string): string {
  if (/全社|大規模|複数部門|enterprise/.test(text)) return "大規模";
  if (/中小|少人数|startup/.test(text)) return "中小規模";
  return "確認必要";
}

function classifyCustomerMaturity(text: string): string {
  if (/poc|検証|初期/.test(text)) return "検証段階";
  if (/標準化|改善|運用/.test(text)) return "改善段階";
  if (/全社|統制|ガバナンス/.test(text)) return "展開段階";
  return "確認必要";
}

function classifyBusinessModel(text: string): string {
  if (/ec|通販|購入/.test(text)) return "コマース";
  if (/saas|月額|subscription/.test(text)) return "サブスクリプション";
  if (/製造|物流|工場|在庫/.test(text)) return "オペレーション";
  if (/採用|人材|教育/.test(text)) return "人材・教育";
  return "確認必要";
}

function chooseDecisionProcess(decisionMaker: DecisionMakerKey, stakeholders: string): string {
  if (decisionMaker === "executive") return "経営承認";
  if (decisionMaker === "information_systems") return "技術・セキュリティ確認";
  if (decisionMaker === "field_leader") return "現場検証後に部門承認";
  if (splitItems(stakeholders).length >= 3) return "複数関係者レビュー";
  if (decisionMaker === "unknown") return "確認必要";
  return "部門承認";
}

function splitItems(value: string): string[] {
  return value
    .split(/\n|,|、|\/|・/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function normalize(value: string): string {
  return value.toLowerCase();
}

function unique(values: string[]): string[] {
  return values.filter((value, index) => values.indexOf(value) === index);
}

function uniqueBy<T>(values: T[], key: (value: T) => string): T[] {
  const seen = new Set<string>();
  return values.filter((value) => {
    const nextKey = key(value);
    if (seen.has(nextKey)) return false;
    seen.add(nextKey);
    return true;
  });
}
