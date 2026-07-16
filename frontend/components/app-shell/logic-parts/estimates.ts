import type {
  CompetitorPoint,
  DealEvaluation,
  EstimateLine,
  EstimateSummary,
  InfoCheck,
  Rank,
  SalesIndicator
} from "@/components/app-shell/types";
import type { AnalysisResponse, ProposalRequest } from "@/types/proposal";
import { allInputText } from "@/components/app-shell/logic-parts/intake";
import { hasAny } from "@/components/app-shell/logic-parts/hearing";
import { getProposalProfile } from "@/components/app-shell/logic-parts/profiles";

export function deriveSalesIndicators(form: ProposalRequest): SalesIndicator[] {
  const text = allInputText(form);

  return [
    {
      title: "予算確度",
      ...deriveBudgetRank(text)
    },
    {
      title: "案件成熟度",
      ...deriveMaturityRank(text)
    }
  ];
}

export function deriveBudgetRank(text: string): Omit<SalesIndicator, "title"> {
  if (/予算\s*[:：]?\s*[0-9０-９]+|[0-9０-９]+\s*(万|万円)/.test(text)) {
    return { rank: "A", label: "予算条件あり" };
  }
  if (text.includes("予算") && !/未定|未確認|これから/.test(text)) {
    return { rank: "B", label: "予算感あり" };
  }
  if (/予算.*未定|未定.*予算|予算未定/.test(text)) {
    return { rank: "C", label: "予算未定" };
  }
  return { rank: "D", label: "予算情報なし" };
}

export function deriveMaturityRank(text: string): Omit<SalesIndicator, "title"> {
  const profile = getProposalProfile(text);
  const checks = [
    profile.positiveKeywords.some((keyword) => text.includes(keyword)) || /問い合わせ|問合せ|採用|導入|改善|効率化|自動化/.test(text),
    /予算|[0-9０-９]+\s*(万|万円)/.test(text),
    /納期|公開時期|公開希望|急ぎ|早め|リリース/.test(text),
    /決裁|代表|社長|責任者|稟議/.test(text),
    text.length >= 180
  ];
  const score = checks.filter(Boolean).length;
  if (score >= 4) return { rank: "A", label: "提案条件が具体的" };
  if (score === 3) return { rank: "B", label: "主要条件あり" };
  if (score === 2) return { rank: "C", label: "追加確認で具体化" };
  return { rank: "D", label: "初回確認を優先" };
}

export function deriveCompetitorPoints(form: ProposalRequest): CompetitorPoint[] {
  const text = allInputText(form);
  const profile = getProposalProfile(text);
  const competitorName = form.competitor_company_name.trim() || profile.competitorNameFallback;

  if (profile.category !== "web") {
    return profile.competitorPoints.map((item) => ({
      label: item.label,
      point: `${competitorName}と比較し、${item.point}`
    }));
  }

  return [
    {
      label: "デザイン",
      point: `${competitorName}よりも第一印象、信頼感、問い合わせ導線の見つけやすさを強化`
    },
    {
      label: "SEO",
      point: hasAny(text, ["SEO", "検索", "自然検索"])
        ? "検索流入を獲得するページ構造とキーワード設計で差別化"
        : "主要サービス名・地域名・課題名での検索導線を設計"
    },
    {
      label: "導線設計",
      point: "比較検討から問い合わせまでのクリック数を減らし、CTAを明確化"
    },
    {
      label: "コンテンツ量",
      point: "サービス、実績、FAQ、導入事例を厚くして検討材料を増やす"
    },
    {
      label: "更新性",
      point: hasAny(text, ["CMS", "更新", "運用"])
        ? "CMSで実績・お知らせ・FAQを継続更新できる状態を作る"
        : "公開後に情報鮮度を維持できる更新領域を設計"
    },
    {
      label: "CTA",
      point: "ページ下部・実績・FAQから問い合わせへ自然につなげる"
    }
  ];
}

export function deriveWinningStrategy(form: ProposalRequest) {
  const text = allInputText(form);
  const profile = getProposalProfile(text);
  if (profile.category !== "web") {
    return profile.winningStrategy;
  }
  if (hasAny(text, ["物件", "不動産", "賃貸", "売買"])) return "物件検索で勝つ";
  if (hasAny(text, ["SEO", "検索", "自然検索", "流入"])) return "SEOで勝つ";
  if (hasAny(text, ["実績", "事例", "導入"])) return "実績訴求で勝つ";
  if (hasAny(text, ["問い合わせ", "問合せ", "CV", "CTA"])) return "検索導線で勝つ";
  return "実績訴求とCTA改善で勝つ";
}

export function normalizeNumberText(value: string) {
  return value
    .replace(/[０-９]/g, (char) => String.fromCharCode(char.charCodeAt(0) - 0xfee0))
    .replace(/[,，]/g, "");
}

export function extractNumber(value: string) {
  const match = normalizeNumberText(value).match(/\d+(?:\.\d+)?/);
  return match ? Number(match[0]) : null;
}

export function extractBudgetAmount(value: string) {
  const normalized = normalizeNumberText(value);
  const matches = [...normalized.matchAll(/(\d+(?:\.\d+)?)\s*(万円|万|円)/g)];
  if (!matches.length) return null;

  const amounts = matches.map((match) => {
    const amount = Number(match[1]);
    return match[2] === "円" ? Math.round(amount / 10000) : amount;
  });
  return Math.max(...amounts);
}

export function flagEnabled(value: string, text: string, fallbackPatterns: string[]) {
  const target = `${value}\n${text}`;
  if (hasAny(value, ["なし", "不要", "無", "無し", "なし想定"])) return false;
  if (hasAny(value, ["あり", "有", "必要", "希望", "対象", "実施", "要"])) return true;
  return hasAny(target, fallbackPatterns);
}

export function formatEstimateRange(line: EstimateLine) {
  return line.enabled ? `${line.min}万〜${line.max}万円` : "対象外";
}

export function deriveEstimateSummary(form: ProposalRequest): EstimateSummary {
  const text = allInputText(form);
  const profile = getProposalProfile(text);
  if (profile.category !== "web") {
    const lines = profile.estimateLines;
    const enabledLines = lines.filter((line) => line.enabled);
    const totalMin = enabledLines.reduce((sum, line) => sum + line.min, 0);
    const totalMax = enabledLines.reduce((sum, line) => sum + line.max, 0);
    const budgetAmount = extractBudgetAmount(`${form.budget_range}\n${text}`);
    const budgetFit =
      budgetAmount === null
        ? "予算未入力"
        : budgetAmount >= totalMax
          ? "予算内"
          : budgetAmount >= totalMin * 0.85
            ? "やや調整必要"
            : "予算超過の可能性あり";

    return {
      pageCount: profile.estimatePageCount,
      totalMin,
      totalMax,
      totalLabel: `${totalMin}万〜${totalMax}万円`,
      budgetAmount,
      budgetLabel: budgetAmount === null ? "未入力" : `${budgetAmount}万円`,
      budgetFit,
      lines,
      required: enabledLines.filter((line) => line.priority === "必須対応").map((line) => line.name),
      recommended: enabledLines.filter((line) => line.priority === "推奨対応").map((line) => line.name),
      optional: enabledLines.filter((line) => line.priority === "オプション対応").map((line) => line.name)
    };
  }
  const pageCount =
    extractNumber(form.estimated_page_count) ??
    extractNumber(text.match(/\d+[ 　]*(ページ|頁|p)/i)?.[0] ?? "") ??
    10;
  const normalizedPageCount = Math.max(1, Math.min(60, Math.round(pageCount)));
  const pageBase = Math.max(8, normalizedPageCount);

  const hasCms = flagEnabled(form.cms_required, text, ["CMS", "WordPress", "更新"]);
  const hasForm = flagEnabled(form.contact_form_required, text, ["問い合わせフォーム", "問合せフォーム", "フォーム", "資料請求"]);
  const hasSpecial = flagEnabled(form.special_function_required, text, ["物件検索", "検索機能", "会員", "予約", "決済", "特殊機能"]);
  const hasSeo = flagEnabled(form.seo_required, text, ["SEO", "自然検索", "検索流入"]);
  const hasContent = flagEnabled(form.content_creation_required, text, ["撮影", "原稿", "ライティング", "取材"]);

  const lines: EstimateLine[] = [
    { name: "要件整理・ディレクション", min: normalizedPageCount > 15 ? 45 : 30, max: normalizedPageCount > 15 ? 75 : 50, priority: "必須対応", enabled: true },
    { name: "情報設計・ワイヤーフレーム", min: 25 + pageBase, max: 45 + pageBase * 2, priority: "必須対応", enabled: true },
    { name: "デザイン制作", min: 45 + pageBase * 4, max: 75 + pageBase * 7, priority: "必須対応", enabled: true },
    { name: "フロントエンド実装", min: 50 + pageBase * 5, max: 85 + pageBase * 8, priority: "必須対応", enabled: true },
    { name: "CMS構築", min: 50, max: 90, priority: "推奨対応", enabled: hasCms },
    { name: "フォーム実装", min: 15, max: 30, priority: "必須対応", enabled: hasForm },
    { name: "特殊機能開発", min: 80, max: 180, priority: "オプション対応", enabled: hasSpecial },
    { name: "SEO初期設計", min: 20, max: 40, priority: "推奨対応", enabled: hasSeo },
    { name: "撮影・原稿作成", min: 30, max: 80, priority: "オプション対応", enabled: hasContent },
    { name: "テスト・公開作業", min: 20, max: 35, priority: "必須対応", enabled: true },
    { name: "運用保守", min: 10, max: 20, priority: "オプション対応", enabled: true }
  ];

  const enabledLines = lines.filter((line) => line.enabled);
  const totalMin = enabledLines.reduce((sum, line) => sum + line.min, 0);
  const totalMax = enabledLines.reduce((sum, line) => sum + line.max, 0);
  const budgetAmount = extractBudgetAmount(`${form.budget_range}\n${text}`);
  const budgetFit =
    budgetAmount === null
      ? "予算未入力"
      : budgetAmount >= totalMax
        ? "予算内"
        : budgetAmount >= totalMin * 0.85
          ? "やや調整必要"
          : "予算超過の可能性あり";

  return {
    pageCount: normalizedPageCount,
    totalMin,
    totalMax,
    totalLabel: `${totalMin}万〜${totalMax}万円`,
    budgetAmount,
    budgetLabel: budgetAmount === null ? "未入力" : `${budgetAmount}万円`,
    budgetFit,
    lines,
    required: enabledLines.filter((line) => line.priority === "必須対応").map((line) => line.name),
    recommended: enabledLines.filter((line) => line.priority === "推奨対応").map((line) => line.name),
    optional: enabledLines.filter((line) => line.priority === "オプション対応").map((line) => line.name)
  };
}

export function deriveDealEvaluation(form: ProposalRequest, checks: InfoCheck[], estimate: EstimateSummary): DealEvaluation {
  const text = allInputText(form);
  const profile = getProposalProfile(text);
  const foundCount = checks.filter((item) => item.found).length;
  let probability = 35 + foundCount * 7;
  const hasCompetitorInfo = Boolean(form.competitor_site_url.trim() || form.competitor_company_name.trim());

  const positives = [
    hasAny(text, ["問い合わせ", "問合せ", "CV", "削減", "効率化", "精度", "定着"]) ? "成果目的が明確" : "",
    hasAny(text, ["リニューアル", "刷新", "改修", "導入", "自動化", "連携"]) ? "実行ニーズが顕在化" : "",
    profile.positiveKeywords.some((keyword) => text.includes(keyword)) ? `${profile.label}として提案テーマが具体的` : "",
    hasCompetitorInfo ? "競合比較を前提に勝ち筋を提示できる" : "",
    estimate.budgetFit === "予算内" ? "概算見積と予算感が合っている" : "",
    form.client_company_info.trim() ? "提案先情報あり" : "",
    form.case_studies.trim() ? "実績訴求に使える情報あり" : ""
  ].filter((item): item is string => Boolean(item));

  const negativeCandidates = checks
    .filter((item) => !item.found)
    .map(riskFactorFromCheck);
  if (hasCompetitorInfo) {
    negativeCandidates.push("競合有り");
  }
  if (estimate.budgetFit === "やや調整必要") {
    negativeCandidates.push("見積と予算に調整余地あり");
  }
  if (estimate.budgetFit === "予算超過の可能性あり") {
    negativeCandidates.push("見積が予算を超える可能性あり");
  }
  const negatives = prioritizeRiskFactors(negativeCandidates);

  probability += positives.length * 3;
  if (hasCompetitorInfo) probability += 4;
  if (estimate.budgetFit === "予算内") probability += 6;
  if (estimate.budgetFit === "やや調整必要") probability -= 6;
  if (estimate.budgetFit === "予算超過の可能性あり") probability -= 14;
  probability -= negatives.length * 4;
  probability = Math.max(20, Math.min(90, probability));

  const rank: Rank = probability >= 80 ? "A" : probability >= 60 ? "B" : probability >= 40 ? "C" : "D";
  const riskScore = deriveRiskScore(probability, negatives.length);
  const improvementActions = deriveImprovementActions(checks, estimate, hasCompetitorInfo);
  const projectedProbability = deriveProjectedProbability(probability, riskScore, improvementActions.length);
  const decision =
    probability >= 60 ? "提案推奨" : probability >= 40 ? "条件確認後に提案" : "見送り検討";
  const reason =
    probability >= 60
      ? "提案の目的が見えており、追加確認を行えば営業提案に進めます。"
      : probability >= 40
        ? "提案前に主要条件を補うことで、提案精度を高められます。"
        : "案件条件が薄いため、提案工数をかける前に一次確認を優先します。";

  return {
    rank,
    probability,
    riskScore,
    riskLabel: buildRiskLabel(riskScore),
    projectedProbability,
    decision,
    reason,
    positives: positives.length ? positives : ["案件概要の入力あり"],
    negatives: negatives.length ? negatives : ["大きな不足情報は少ない状態"],
    improvementActions
  };
}

export function riskFactorFromCheck(item: InfoCheck) {
  const labels: Record<string, string> = {
    budget: "予算未確定",
    deadline: "納期未確認",
    "decision-maker": "決裁者未確認",
    "current-site": "既存サイトURL未確認",
    cms: "CMS希望未確認",
    seo: "SEO希望未確認",
    competitor: "競合未確認"
  };
  return labels[item.key] ?? `${item.label}未確認`;
}

export function prioritizeRiskFactors(items: string[]) {
  const priority = ["予算", "納期", "競合", "決裁", "見積", "既存サイト", "CMS", "SEO"];
  const uniqueItems = Array.from(new Set(items.filter(Boolean)));
  return uniqueItems.sort((a, b) => {
    const aIndex = priority.findIndex((keyword) => a.includes(keyword));
    const bIndex = priority.findIndex((keyword) => b.includes(keyword));
    return (aIndex === -1 ? 99 : aIndex) - (bIndex === -1 ? 99 : bIndex);
  });
}

export function deriveRiskScore(probability: number, riskCount: number) {
  let score = probability <= 25 ? 5 : probability <= 40 ? 4 : probability <= 60 ? 3 : probability <= 75 ? 2 : 1;
  if (riskCount >= 4) {
    score = Math.min(5, score + 1);
  }
  return score;
}

export function buildRiskLabel(score: number) {
  const normalized = Math.max(1, Math.min(5, score));
  return `${"★".repeat(normalized)}${"☆".repeat(5 - normalized)}`;
}

export function deriveProjectedProbability(probability: number, riskScore: number, actionCount: number) {
  let uplift = probability <= 25 ? 25 : probability <= 40 ? 20 : probability <= 60 ? 15 : 10;
  if (riskScore <= 2) {
    uplift = Math.min(uplift, 10);
  }
  if (actionCount < 3) {
    uplift = Math.max(8, uplift - 5);
  }
  return Math.min(90, probability + uplift);
}

export function deriveImprovementActions(checks: InfoCheck[], estimate: EstimateSummary, hasCompetitorInfo: boolean) {
  const missingKeys = new Set(checks.filter((item) => !item.found).map((item) => item.key));
  const actions = [
    missingKeys.has("decision-maker") ? "決裁者確認" : "決裁プロセス確認",
    missingKeys.has("budget") || estimate.budgetFit === "やや調整必要" || estimate.budgetFit === "予算超過の可能性あり" ? "予算確認" : "",
    !hasCompetitorInfo || missingKeys.has("competitor") ? "競合ヒアリング" : "競合比較条件確認",
    missingKeys.has("deadline") ? "納期確認" : "",
    missingKeys.has("cms") ? "CMS要件確認" : "",
    missingKeys.has("seo") ? "SEO要件確認" : ""
  ].filter(Boolean);
  return Array.from(new Set(actions)).slice(0, 3);
}

export function extractClientName(form: ProposalRequest, result?: AnalysisResponse | null) {
  const fromResult = result?.powerpoint_generation_data.client_name?.trim();
  if (fromResult && fromResult !== "提案先企業") {
    return fromResult;
  }
  const firstLine = form.client_company_info
    .split(/\r?\n/)
    .map((line) => line.trim())
    .find(Boolean);
  return firstLine || "提案先企業";
}
