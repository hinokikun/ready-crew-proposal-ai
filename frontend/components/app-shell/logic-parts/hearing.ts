import type {
  HearingResultSummary,
  HearingSheetCategory,
  InfoCheck
} from "@/components/app-shell/types";
import type { ProposalRequest } from "@/types/proposal";
import { allInputText } from "@/components/app-shell/logic-parts/intake";
import { getProposalProfile } from "@/components/app-shell/logic-parts/profiles";

export function hasAny(text: string, patterns: (RegExp | string)[]) {
  return patterns.some((pattern) => (typeof pattern === "string" ? text.includes(pattern) : pattern.test(text)));
}

export function buildInfoChecks(form: ProposalRequest): InfoCheck[] {
  const text = allInputText(form);
  const profile = getProposalProfile(text);
  const webProject = profile.category === "web";
  const budgetIsClear = hasAny(text, [/予算\s*[:：]?\s*[0-9０-９]+/, /[0-9０-９]+\s*(万|万円)/]) && !/予算.*未定|未定.*予算/.test(text);

  return [
    {
      key: "budget",
      label: "予算",
      found: budgetIsClear,
      targetField: "見積条件 > 予算感",
      nextQuestion: "想定予算、上限、分割提案の可否"
    },
    {
      key: "deadline",
      label: "納期",
      found: hasAny(text, ["納期", "公開希望", "公開時期", "リリース", "9月", "10月", "急ぎ", "早め"]) && !/納期.*未定|公開.*未定/.test(text),
      targetField: "見積条件 > 公開希望時期",
      nextQuestion: "希望公開日、必達期限、社内確認に必要な期間"
    },
    {
      key: "decision-maker",
      label: "決裁者",
      found: hasAny(text, ["決裁", "決裁者", "代表", "社長", "役員", "部長", "責任者", "稟議", "承認"]),
      targetField: "案件概要 または 提案先企業情報",
      nextQuestion: "最終決裁者、選定関与者、稟議の流れ"
    },
    {
      key: "current-site",
      label: webProject ? "既存サイトURL" : "既存情報",
      found: hasAny(text, [/https?:\/\/\S+/, "既存サイトURL", "既存資料", "対象業務", "URL", "PDF", "CSV", "Excel"]),
      targetField: "提案先企業情報",
      nextQuestion: webProject ? "既存サイトURL、アクセス状況、改善したいページ" : "対象業務、既存データ、連携先、利用中ツール"
    },
    {
      key: "cms",
      label: profile.requirementLabel,
      found: webProject
        ? hasAny(text, ["CMS", "WordPress", "ワードプレス", "更新", "運用"])
        : profile.qualityHints.some((keyword) => text.includes(keyword)) || Boolean(form.special_function_required.trim()),
      targetField: webProject ? "見積条件 > CMS有無" : "見積条件 > 導入要件",
      nextQuestion: webProject ? "CMS要否、更新担当者、更新頻度、承認フロー" : profile.qualityHints.join("、")
    },
    {
      key: "seo",
      label: webProject ? "SEO希望" : "成果指標",
      found: webProject
        ? hasAny(text, ["SEO", "検索", "自然検索", "流入", "記事", "コンテンツマーケティング"])
        : hasAny(text, ["KPI", "削減", "精度", "時間", "件数", "成功率", "エラー率", "入力ミス"]),
      targetField: webProject ? "見積条件 > SEO対策有無" : "提案条件 > KPI",
      nextQuestion: webProject ? "狙いたい検索キーワード、現状流入、SEO対象ページ" : "削減時間、精度目標、処理件数、成功条件"
    },
    {
      key: "competitor",
      label: "競合有無",
      found: Boolean(form.competitor_site_url.trim() || form.competitor_company_name.trim()) || hasAny(text, ["競合", "他社", "比較", "ベンチマーク", "差別化"]),
      targetField: "競合企業名・競合サイトURL",
      nextQuestion: "比較対象の競合サイト、勝ちたい訴求軸"
    }
  ];
}

export function buildHearingSheet(form: ProposalRequest): HearingSheetCategory[] {
  const text = allInputText(form);
  const profile = getProposalProfile(text);
  const webProject = profile.category === "web";
  const hasBusiness = hasAny(text, ["事業", "業種", "サービス", "商品", "商材", "不動産", "採用", "BtoB", "BtoC"]) || form.client_company_info.trim().length >= 20;
  const hasTarget = hasAny(text, ["ターゲット", "顧客", "ユーザー", "求職者", "法人", "個人", "購入者", "検討者", "ペルソナ"]);
  const hasCompetitor = Boolean(form.competitor_site_url.trim() || form.competitor_company_name.trim()) || hasAny(text, ["競合", "他社", "比較", "ベンチマーク", "差別化"]);
  const hasBudget = hasAny(text, [/予算\s*[:：]?\s*[0-9０-９]+/, /[0-9０-９]+\s*(万|万円)/]) && !/予算.*未定|未定.*予算/.test(text);
  const hasDeadline = hasAny(text, ["納期", "公開希望", "公開時期", "リリース", "9月", "10月", "急ぎ", "早め"]) && !/納期.*未定|公開.*未定/.test(text);
  const hasKpi = hasAny(text, ["KPI", "問い合わせ目標", "問合せ目標", "CV率", "コンバージョン", "アクセス数", "資料DL", "自然検索流入", "目標件数", "削減時間", "精度", "処理件数", "入力ミス"]);
  const hasCms = webProject
    ? hasAny(text, ["CMS", "WordPress", "ワードプレス", "更新機能"]) || Boolean(form.cms_required.trim())
    : profile.qualityHints.some((keyword) => text.includes(keyword)) || Boolean(form.special_function_required.trim());
  const hasOperation = hasAny(text, ["運用体制", "更新担当", "担当者", "保守", "月次", "レポート", "改善運用", "更新頻度"]);

  return [
    {
      key: "business",
      category: "事業内容",
      found: hasBusiness,
      summary: hasBusiness ? "事業・サービスの前提情報あり" : "事業内容、主力サービス、収益モデルが不足",
      questions: hasBusiness
        ? []
        : ["主力事業・主要サービスは何ですか？", "今回の提案で最も改善したい業務や成果は何ですか？"]
    },
    {
      key: "target",
      category: "ターゲット",
      found: hasTarget,
      summary: hasTarget ? "想定ユーザーの記載あり" : "誰に向けた提案かが不足",
      questions: hasTarget
        ? []
        : ["主な利用者や関係部門は誰ですか？", "優先したい対象顧客や業務範囲はありますか？"]
    },
    {
      key: "competitor",
      category: "競合",
      found: hasCompetitor,
      summary: hasCompetitor ? "競合・比較対象の情報あり" : "競合・比較対象が不足",
      questions: hasCompetitor
        ? []
        : ["比較対象の企業・サービスはありますか？", "提案時に比較されやすい選定軸はありますか？"]
    },
    {
      key: "budget",
      category: "予算",
      found: hasBudget,
      summary: hasBudget ? "予算感の記載あり" : "予算感・上限・調整余地が不足",
      questions: hasBudget
        ? []
        : ["想定予算または上限予算はいくらですか？", "必須範囲とオプションに分けた提案は可能ですか？"]
    },
    {
      key: "deadline",
      category: "納期",
      found: hasDeadline,
      summary: hasDeadline ? "公開希望時期の記載あり" : "公開希望時期・必達期限が不足",
      questions: hasDeadline
        ? []
        : ["公開希望時期はいつですか？", "社内確認や素材準備に必要な期間はどの程度ですか？"]
    },
    {
      key: "kpi",
      category: "KPI",
      found: hasKpi,
      summary: hasKpi ? "成果指標の記載あり" : "成果指標や目標値が不足",
      questions: hasKpi
        ? []
        : webProject
          ? ["年間の問い合わせ目標は？", "CV率、アクセス数、自然検索流入など重視するKPIは何ですか？"]
          : ["削減したい作業時間や件数は？", "精度、成功率、エラー率など重視するKPIは何ですか？"]
    },
    {
      key: "cms",
      category: profile.requirementLabel,
      found: hasCms,
      summary: hasCms ? `${profile.requirementLabel}の記載あり` : `${profile.requirementLabel}が不足`,
      questions: hasCms
        ? []
        : webProject
          ? ["CMSは必要ですか？", "自社で更新したいページやコンテンツは何ですか？"]
          : profile.qualityHints.map((hint) => `${hint}を確認してください`)
    },
    {
      key: "operation",
      category: "運用体制",
      found: hasOperation,
      summary: hasOperation ? "運用・更新体制の記載あり" : "公開後の担当者・更新頻度が不足",
      questions: hasOperation
        ? []
        : ["公開後の更新担当者は誰ですか？", "公開後の保守、改善提案、レポート支援は必要ですか？"]
    }
  ];
}

export function buildHearingSheetMarkdown(sheet: HearingSheetCategory[]) {
  const lines = sheet.map((item) => {
    const questions = item.questions.length
      ? item.questions.map((question) => `- Q. ${question}`).join("\n")
      : "- 入力情報あり。初回ヒアリングでは詳細条件を確認します。";
    return `### ${item.category}\n- 状態: ${item.found ? "入力情報あり" : "要ヒアリング"}\n- メモ: ${item.summary}\n${questions}`;
  });
  return `\n\n## ヒアリングシート\n\n${lines.join("\n\n")}`;
}

export function buildExportMarkdown(markdown: string, form: ProposalRequest) {
  return `${markdown.trim()}${buildHearingSheetMarkdown(buildHearingSheet(form))}${buildHearingResultMarkdown(buildHearingResultSummary(form))}\n`;
}

export function buildHearingResultSummary(form: ProposalRequest): HearingResultSummary {
  const rawLines = splitHearingResult(form.hearing_result);
  const hasInput = rawLines.length > 0;
  const unresolvedKeywords = [
    "未定",
    "未確認",
    "未決",
    "検討",
    "保留",
    "調整",
    "要相談",
    "確認中",
    "これから",
    "不明"
  ];
  if (!hasInput) {
    return {
      hasInput: false,
      minutes: ["ヒアリング結果を入力すると、議事録を自動生成します。"],
      decisions: ["ヒアリング結果入力後に抽出します。"],
      unresolved: ["ヒアリング結果入力後に抽出します。"],
      nextConfirmations: ["ヒアリング結果入力後に抽出します。"]
    };
  }

  const minutes = buildMeetingMinutes(rawLines);
  const decisions = pickHearingLines(rawLines, [
    "決定",
    "確定",
    "合意",
    "採用",
    "進める",
    "実施する",
    "依頼する",
    "WordPress",
    "CMSは",
    "公開は"
  ]).filter((line) => !hasAny(line, unresolvedKeywords));
  const unresolved = pickHearingLines(rawLines, unresolvedKeywords);
  const nextConfirmations = uniqueTextItems([
    ...pickHearingLines(rawLines, [
      "次回",
      "確認",
      "要確認",
      "宿題",
      "TODO",
      "誰",
      "いつ",
      "どの",
      "何",
      "ありますか",
      "ですか",
      "？",
      "?"
    ]),
    ...buildHearingSheet(form)
      .flatMap((item) => item.questions.map((question) => `${item.category}: ${question}`))
      .slice(0, 4)
  ]).slice(0, 5);

  return {
    hasInput,
    minutes: ensureSummaryItems(minutes, ["ヒアリング内容の要点を整理しました。"]),
    decisions: ensureSummaryItems(decisions, ["明確な決定事項は未抽出です。"]),
    unresolved: ensureSummaryItems(unresolved, ["大きな未決事項は未抽出です。"]),
    nextConfirmations: ensureSummaryItems(nextConfirmations, ["次回確認事項は未抽出です。"])
  };
}

export function buildHearingResultMarkdown(summary: HearingResultSummary) {
  if (!summary.hasInput) {
    return "";
  }
  return `\n\n## ヒアリング結果整理\n\n### 議事録\n${markdownBullets(summary.minutes)}\n\n### 決定事項\n${markdownBullets(summary.decisions)}\n\n### 未決事項\n${markdownBullets(summary.unresolved)}\n\n### 次回確認事項\n${markdownBullets(summary.nextConfirmations)}`;
}

export function splitHearingResult(value: string) {
  return value
    .split(/\r?\n|。|；|;/)
    .map((line) => line.replace(/^[・•\-\d０-９\s.．、]+/, "").trim())
    .filter(Boolean)
    .map((line) => trimText(line, 90));
}

export function buildMeetingMinutes(lines: string[]) {
  const topics = [
    { label: "目的", patterns: ["目的", "ゴール", "問い合わせ", "採用", "リニューアル", "成果"] },
    { label: "対象", patterns: ["ターゲット", "顧客", "ユーザー", "求職者", "法人", "個人"] },
    { label: "要件", patterns: ["CMS", "フォーム", "SEO", "物件検索", "ページ", "機能"] },
    { label: "条件", patterns: ["予算", "納期", "公開", "スケジュール"] },
    { label: "体制", patterns: ["担当", "決裁", "運用", "更新", "承認"] }
  ];
  const picked = topics
    .map((topic) => {
      const line = lines.find((item) => hasAny(item, topic.patterns));
      return line ? `${topic.label}: ${line}` : "";
    })
    .filter(Boolean);
  return uniqueTextItems([...picked, ...lines]).slice(0, 6);
}

export function pickHearingLines(lines: string[], keywords: string[]) {
  return uniqueTextItems(lines.filter((line) => hasAny(line, keywords))).slice(0, 5);
}

export function uniqueTextItems(items: string[]) {
  return Array.from(new Set(items.map((item) => item.trim()).filter(Boolean)));
}

export function ensureSummaryItems(items: string[], fallback: string[]) {
  return items.length ? items : fallback;
}

export function trimText(value: string, maxLength: number) {
  return value.length <= maxLength ? value : `${value.slice(0, maxLength - 1)}…`;
}

export function markdownBullets(items: string[]) {
  return items.map((item) => `- ${item}`).join("\n");
}
