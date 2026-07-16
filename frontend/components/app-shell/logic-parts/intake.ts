import type {
  ChatAnswers,
  EasyInput,
  ExtractedInfo,
  MinimalInput,
  UrlInsight
} from "@/components/app-shell/types";
import type { ProposalRequest } from "@/types/proposal";
import { hasAny } from "@/components/app-shell/logic-parts/hearing";
import { applyChatAnswersToForm } from "@/components/app-shell/logic-parts/strategy";
import { getProposalProfile, isWebProposalText } from "@/components/app-shell/logic-parts/profiles";

export function allInputText(form: ProposalRequest) {
  return [
    form.project_brief,
    form.client_company_info,
    form.competitor_site_url,
    form.competitor_company_name,
    form.estimated_page_count,
    form.cms_required,
    form.contact_form_required,
    form.special_function_required,
    form.seo_required,
    form.content_creation_required,
    form.desired_launch_timing,
    form.budget_range,
    form.hearing_result,
    form.own_service_info,
    form.past_proposal_template,
    form.case_studies
  ].join("\n");
}

export function buildEasyMissingItems(easyInput: EasyInput) {
  const missing: string[] = [];
  if (!easyInput.projectType.trim()) {
    missing.push("何を作りたいか");
  }
  if (!easyInput.trouble.trim() && easyInput.purposes.length === 0) {
    missing.push("お客様の困りごと、または目的を1つ以上");
  }
  return missing;
}

export function optionalLabel(value: string) {
  return value.trim() || "任意・未入力";
}

export function buildProjectBriefFromEasyInput(easyInput: EasyInput) {
  const purposes = easyInput.purposes.length ? easyInput.purposes.join("、") : "未選択";
  const profile = getProposalProfile([easyInput.projectType, easyInput.trouble, purposes, easyInput.cms].join("\n"));
  const existingLabel = profile.category === "web" ? "既存サイトURL" : "既存資料・対象業務URL";
  const competitorLabel = profile.category === "web" ? "競合サイトURL" : "比較対象";
  return `Ready Crew案件概要：
相談内容は「${optionalLabel(easyInput.projectType)}」。
目的は、${purposes}。
お客様の困りごとは、${optionalLabel(easyInput.trouble)}。
予算感は「${easyInput.budget}」、納期は「${easyInput.deadline}」。
${existingLabel}：${optionalLabel(easyInput.currentSiteUrl)}
${competitorLabel}：${optionalLabel(easyInput.competitorSiteUrl)}
${profile.requirementLabel}：${easyInput.cms}
決裁者・確認者：${optionalLabel(easyInput.decisionMakers)}
初回提案では、課題整理、提案方針、概算見積、スケジュール、PowerPoint提案書の初稿を作成したい。`;
}

export function patchFormFromEasyInput(current: ProposalRequest, easyInput: EasyInput): ProposalRequest {
  const nextBrief = buildProjectBriefFromEasyInput(easyInput);
  const isWeb = isWebProposalText(nextBrief);
  const currentSiteLine = easyInput.currentSiteUrl.trim()
    ? `${isWeb ? "既存サイトURL" : "既存資料・対象業務URL"}：${easyInput.currentSiteUrl.trim()}`
    : "";
  const decisionLine = easyInput.decisionMakers.trim() ? `決裁者・確認者：${easyInput.decisionMakers.trim()}` : "";
  const existingClientInfo = current.client_company_info
    .split("\n")
    .filter((line) => !line.startsWith("既存サイトURL：") && !line.startsWith("既存資料・対象業務URL：") && !line.startsWith("決裁者・確認者："))
    .join("\n")
    .trim();
  const clientInfo = [existingClientInfo, currentSiteLine, decisionLine]
    .filter(Boolean)
    .join("\n")
    .trim();

  return {
    ...current,
    project_brief: nextBrief,
    client_company_info: clientInfo,
    competitor_site_url: easyInput.competitorSiteUrl.trim(),
    budget_range: easyInput.budget === "未定" ? "" : easyInput.budget,
    desired_launch_timing: easyInput.deadline === "未定" ? "" : easyInput.deadline,
    cms_required: isWeb ? easyInput.cms : current.cms_required,
    special_function_required: isWeb ? current.special_function_required : easyInput.cms,
    seo_required: isWeb && easyInput.purposes.includes("検索・集客を強化したい") ? "あり" : current.seo_required,
    contact_form_required: easyInput.purposes.includes("問い合わせを増やしたい") ? "あり" : current.contact_form_required
  };
}

export function patchFormFromMinimalInput(current: ProposalRequest, minimalInput: MinimalInput): ProposalRequest {
  const companyName = minimalInput.companyName.trim() || "提案先企業";
  const goal = minimalInput.goal.trim() || NEUTRAL_PROJECT_FALLBACK;
  const trouble = minimalInput.trouble.trim() || "現状課題は要確認";
  return fillMissingProposalForm({
    ...current,
    project_brief: `Ready Crew案件概要：
会社名：${companyName}
やりたいこと：${goal}
困りごと：${trouble}
予算：未定
納期：要確認
導入要件：要確認
競合：未確認
決裁者：要確認
ターゲット：要確認
初回提案では、課題整理、提案方針、概算見積、スケジュール、提案書初稿を作成したい。`,
    client_company_info: `${companyName}
担当者・決裁者：要確認
ターゲット：要確認`,
    budget_range: "未定",
    desired_launch_timing: "要確認",
    special_function_required: "要確認",
    competitor_company_name: "競合未確認",
    hearing_result: `やりたいこと：${goal}
困りごと：${trouble}
次回確認事項：予算、納期、導入要件、競合、決裁者、ターゲット`
  });
}

export function extractFirstUrl(value: string | undefined) {
  if (!value) return "";
  return value.match(/https?:\/\/[^\s、。)）]+/)?.[0] ?? "";
}

export function extractUrls(value: string | undefined) {
  if (!value) return [];
  return Array.from(new Set(value.match(/https?:\/\/[^\s、。)）]+/g) ?? []));
}

export function withoutUrl(value: string | undefined) {
  if (!value) return "";
  return value.replace(/https?:\/\/[^\s、。)）]+/g, "").replace(/[、。,\s]+$/g, "").trim();
}

export function isUnknownAnswer(value: string | undefined) {
  return !value?.trim() || /未定|不明|未確認|なし|まだ/.test(value);
}

export function buildProjectBriefFromChatAnswers(answers: ChatAnswers) {
  const project = answers.project?.trim() || "未確認";
  const company = answers.company?.trim() || "未確認";
  const trouble = answers.trouble?.trim() || "未確認";
  const budget = answers.budget?.trim() || "未確認";
  const deadline = answers.deadline?.trim() || "未確認";
  const competitor = answers.competitor?.trim() || "未確認";

  const profile = getProposalProfile(`${project}\n${company}\n${trouble}`);

  return `AI営業アシスタント整理内容：
案件内容：${project}
お客様情報：${company}
お客様の困りごと：${trouble}
予算感：${budget}
公開希望時期・納期：${deadline}
競合情報：${competitor}
提案書では、現状理解、課題整理、${profile.winningStrategy}、競合比較、概算見積、スケジュール、体制、今後の進め方を整理する。`;
}

export function compactText(value: string) {
  return value.replace(/\r/g, "").replace(/[ \t]+/g, " ").replace(/\n{3,}/g, "\n\n").trim();
}

const NEUTRAL_PROJECT_FALLBACK = "入力された案件情報をもとにした提案";

export function hasMeaningfulSourceText(value: string) {
  return compactText(value).length >= 8;
}

function firstMeaningfulLine(text: string) {
  return compactText(text)
    .split("\n")
    .map((line) => line.trim())
    .find((line) => line.length >= 6) || "";
}

function isAiOcrProjectText(text: string) {
  return /AI[-\s]?OCR|OCR|文書認識|帳票|請求書|納品書|注文書|申込書|PDF|スキャン|読み取り|項目抽出|CSV|会計システム|RPA|データ入力自動化/i.test(text);
}

function isWebProjectText(text: string) {
  return /Webサイト|サイトリニューアル|コーポレートサイト|ホームページ|LP|CMS|SEO|WordPress|問い合わせ|採用サイト/i.test(text);
}

function inferProjectContentFromRaw(text: string) {
  const source = compactText(text);
  if (!source) return "";
  if (isAiOcrProjectText(source)) {
    return "AI-OCRによる請求書・帳票読み取りと項目抽出の自動化提案";
  }
  if (isWebProjectText(source)) {
    return "Webサイト制作・改善提案";
  }
  return firstMeaningfulLine(source).slice(0, 180) || NEUTRAL_PROJECT_FALLBACK;
}

export function findLabeledValue(text: string, labels: string[]) {
  const lines = compactText(text).split("\n").map((line) => line.trim()).filter(Boolean);
  for (const label of labels) {
    const escaped = label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const direct = lines.find((line) => new RegExp(`^${escaped}\\s*[:：]\\s*`, "i").test(line));
    if (direct) {
      return direct.replace(new RegExp(`^${escaped}\\s*[:：]\\s*`, "i"), "").trim();
    }
    const included = lines.find((line) => line.includes(label) && /[:：]/.test(line));
    if (included) {
      return included.split(/[:：]/).slice(1).join("：").trim();
    }
  }
  return "";
}

export function findSentence(text: string, patterns: (RegExp | string)[]) {
  const sentences = compactText(text)
    .split(/[\n。！？!?]/)
    .map((line) => line.trim())
    .filter(Boolean);
  return sentences.find((sentence) => hasAny(sentence, patterns)) ?? "";
}

export function extractCompanyName(text: string, fallbackUrl = "") {
  const labeled = findLabeledValue(text, ["会社名", "企業名", "顧客名", "社名", "提案先", "お客様"]);
  if (labeled) return labeled;
  const match = text.match(/(?:株式会社|有限会社|合同会社|医療法人|学校法人|社会福祉法人)[^\s　、。:：\n]{1,30}/);
  if (match) return match[0];
  if (fallbackUrl) {
    try {
      return new URL(fallbackUrl).hostname.replace(/^www\./, "");
    } catch {
      return "";
    }
  }
  return "";
}

export function extractPurposeList(text: string) {
  const candidates = [
    { keyword: /問い合わせ|問合せ|資料請求|来店予約|CV|コンバージョン/i, label: "問い合わせを増やしたい" },
    { keyword: /採用|応募|求人|人材/i, label: "採用を強化したい" },
    { keyword: /信頼|ブランド|ブランディング|認知|実績/i, label: "会社の信頼感を上げたい" },
    { keyword: /自動化|効率化|削減|省力化|RPA|AI-OCR|OCR/i, label: "業務を効率化したい" },
    { keyword: /精度|読取|項目抽出|照合|ミス|品質/i, label: "精度や品質を上げたい" },
    { keyword: /更新|CMS|お知らせ|ブログ|運用/i, label: "運用しやすくしたい" },
    { keyword: /SEO|検索|自然流入|流入|順位/i, label: "検索・集客を強化したい" }
  ];
  return candidates.filter((item) => item.keyword.test(text)).map((item) => item.label);
}

export function extractProposalInfo(rawText: string, homepageUrl: string): ExtractedInfo {
  const text = compactText(rawText);
  const urls = extractUrls(`${text}\n${homepageUrl}`);
  const competitorLine = findSentence(text, ["競合", "比較", "他社"]);
  const currentSiteLine = findSentence(text, ["既存サイト", "現行サイト", "会社HP", "ホームページURL", "URL"]);
  const budget =
    findLabeledValue(text, ["予算", "予算感", "費用", "金額"]) ||
    text.match(/\d{2,4}\s*万\s*(?:円)?\s*[〜~～-]\s*\d{2,4}\s*万\s*円?/)?.[0] ||
    text.match(/\d{2,4}\s*万円(?:以内|程度|前後)?/)?.[0] ||
    "";
  const deadline =
    findLabeledValue(text, ["納期", "公開希望", "公開時期", "希望時期", "リリース"]) ||
    text.match(/\d{4}年\d{1,2}月(?:末|中|上旬|下旬)?/)?.[0] ||
    text.match(/\d{1,2}月(?:末|中|上旬|下旬)?/)?.[0] ||
    "";
  const projectContent =
    findLabeledValue(text, ["案件内容", "依頼内容", "相談内容", "制作内容", "概要"]) ||
    findSentence(text, ["AI-OCR", "OCR", "帳票", "請求書", "RPA", "CRM", "SFA", "ERP", "リニューアル", "制作", "LP", "採用サイト", "Webサイト", "ホームページ", "コーポレートサイト"]);
  const trouble =
    findLabeledValue(text, ["課題", "困りごと", "悩み", "現状", "背景"]) ||
    findSentence(text, [/困|課題|古い|弱い|不足|できていない|伸びない|少ない|改善/]);
  const cms =
    findLabeledValue(text, ["CMS", "CMS希望", "更新"]) ||
    text.match(/WordPress|Movable Type|独自CMS|CMS不要|CMSあり/i)?.[0] ||
    "";
  const target =
    findLabeledValue(text, ["ターゲット", "対象", "ユーザー", "顧客", "求職者"]) ||
    findSentence(text, ["ターゲット", "ユーザー", "顧客", "求職者", "学生", "法人", "個人"]);
  const seoIssue =
    findLabeledValue(text, ["SEO課題", "SEO", "検索課題"]) ||
    findSentence(text, ["SEO", "検索", "自然流入", "順位", "流入"]);
  const inquiryDetails =
    findLabeledValue(text, ["問い合わせ内容", "相談内容", "要望", "希望"]) ||
    findSentence(text, ["知りたい", "相談", "依頼", "提案", "見積", "スケジュール"]);
  const competitorUrl = extractFirstUrl(competitorLine);
  const currentSiteUrl = homepageUrl.trim() || extractFirstUrl(currentSiteLine) || urls.find((url) => url !== competitorUrl) || "";
  const inferredProjectContent = inferProjectContentFromRaw(text);

  return {
    companyName: extractCompanyName(text, currentSiteUrl),
    contactPerson: findLabeledValue(text, ["担当者", "窓口", "ご担当", "決裁者", "確認者"]),
    projectContent: projectContent || inferredProjectContent,
    purposes: extractPurposeList(text),
    trouble,
    budget,
    deadline,
    competitor: competitorLine || competitorUrl || findLabeledValue(text, ["競合", "競合サイト", "競合企業"]),
    currentSiteUrl,
    cms,
    target,
    seoIssue,
    inquiryDetails
  };
}

export function buildUrlInsight(url: string, rawText: string, extracted: ExtractedInfo): UrlInsight | null {
  const targetUrl = url.trim() || extracted.currentSiteUrl.trim();
  if (!targetUrl) return null;
  let hostname = targetUrl;
  try {
    hostname = new URL(targetUrl).hostname.replace(/^www\./, "");
  } catch {
    hostname = targetUrl.replace(/^https?:\/\//, "").split("/")[0];
  }
  const text = `${rawText}\n${extracted.projectContent}\n${extracted.trouble}`;
  const isRecruit = /採用|求人|応募|人材/.test(text);
  const isRealEstate = /不動産|物件|賃貸|売買|住宅/.test(text);
  const isLp = /LP|ランディング|広告|CPA|資料請求/.test(text);

  return {
    url: targetUrl,
    companyOverview: `${extracted.companyName || hostname}の公開サイトとして、事業理解・信頼形成・問い合わせ導線の確認対象にします。`,
    business: isRealEstate
      ? "不動産・住宅領域のサービス訴求、物件情報、来店・問い合わせ獲得が中心と想定します。"
      : isRecruit
        ? "採用広報、職種理解、応募導線、社員紹介を中心に整理します。"
        : "サービス紹介、実績訴求、問い合わせ獲得を中心に整理します。",
    strengths: "既存の事業実績、専門性、地域性、顧客対応力を強みとして提案に転換します。",
    weaknesses: "サイト上で強み・実績・問い合わせ導線が分散している前提で、訴求整理と導線短縮を改善ポイントにします。",
    competitors: extracted.competitor || "競合未確認。次回ヒアリングで比較対象サイトを確認します。",
    services: isLp ? "新サービスの価値訴求、CTA、フォーム導線を重点確認します。" : "主要サービス、料金・事例・FAQ・問い合わせ導線を確認対象にします。",
    recruitment: isRecruit ? "採用情報、社員インタビュー、働く環境、応募導線を重点的に改善します。" : "採用情報がある場合は、信頼感と企業理解を補強する要素として扱います。",
    seoStatus: /SEO|検索|自然流入|流入/.test(text)
      ? "検索流入強化が論点に含まれるため、カテゴリ設計・見出し・FAQ・事例コンテンツを強化します。"
      : "現時点ではSEO要件が未確定のため、基本的なサイト構造・タイトル・導線改善を初期提案に含めます。",
    improvementPoints: [
      "ファーストビューで提供価値とCTAを明確化",
      "サービス・実績・FAQから問い合わせまでの導線を短縮",
      "CMS更新しやすい情報設計とSEOに強いコンテンツ構造を提案"
    ]
  };
}

export function hostnameFromUrl(value: string) {
  if (!value.trim()) return "";
  try {
    return new URL(value.trim()).hostname.replace(/^www\./, "");
  } catch {
    return value.replace(/^https?:\/\//, "").split("/")[0];
  }
}

export function fillMissingExtractedInfo(info: ExtractedInfo, homepageUrl: string): ExtractedInfo {
  const fallbackHost = hostnameFromUrl(homepageUrl || info.currentSiteUrl);
  return {
    ...info,
    companyName: info.companyName || fallbackHost || "提案先企業",
    contactPerson: info.contactPerson || "要確認",
    projectContent: info.projectContent || NEUTRAL_PROJECT_FALLBACK,
    purposes: info.purposes.length ? info.purposes : ["問い合わせを増やしたい"],
    trouble: info.trouble || "現状課題は要確認。入力案件の目的と改善余地を整理します。",
    budget: info.budget || "未定",
    deadline: info.deadline || "要確認",
    competitor: info.competitor || "競合未確認",
    currentSiteUrl: info.currentSiteUrl || homepageUrl.trim(),
    cms: info.cms || "要確認",
    target: info.target || "要確認",
    seoIssue: info.seoIssue || "要確認",
    inquiryDetails: info.inquiryDetails || "提案内容、概算費用、スケジュールを確認したい"
  };
}

export function fillMissingProposalForm(form: ProposalRequest): ProposalRequest {
  const hasCompetitor = Boolean(form.competitor_site_url.trim() || form.competitor_company_name.trim());
  const hasDecisionMaker = /決裁者|確認者|担当者/.test(form.client_company_info) || /決裁者|確認者|担当者/.test(form.project_brief);
  const hasTarget = /ターゲット|対象|顧客|求職者|ユーザー/.test(allInputText(form));
  const clientCompanyInfo = form.client_company_info.trim() || "提案先企業";
  return {
    ...form,
    project_brief:
      form.project_brief.trim() ||
      "入力された案件情報をもとにした提案。詳細条件は要確認として、提案書初稿を作成します。",
    client_company_info: [
      clientCompanyInfo,
      hasDecisionMaker ? "" : "担当者・決裁者：要確認",
      hasTarget ? "" : "ターゲット：要確認"
    ]
      .filter(Boolean)
      .join("\n"),
    budget_range: form.budget_range.trim() || "未定",
    desired_launch_timing: form.desired_launch_timing.trim() || "要確認",
    cms_required: form.cms_required.trim() || "要確認",
    competitor_company_name: hasCompetitor ? form.competitor_company_name : "競合未確認",
    hearing_result:
      form.hearing_result.trim() ||
      "未入力項目は次回確認事項として扱い、初回提案では仮説ベースで整理します。"
  };
}

export function buildChatAnswersFromExtracted(info: ExtractedInfo): ChatAnswers {
  return {
    ...(info.projectContent ? { project: info.projectContent } : {}),
    ...(info.companyName || info.contactPerson || info.currentSiteUrl
      ? { company: [info.companyName, info.contactPerson ? `担当者：${info.contactPerson}` : "", info.currentSiteUrl ? `URL：${info.currentSiteUrl}` : ""].filter(Boolean).join("。") }
      : {}),
    ...(info.trouble || info.purposes.length ? { trouble: [info.trouble, info.purposes.length ? `目的：${info.purposes.join("、")}` : ""].filter(Boolean).join("。") } : {}),
    ...(info.budget ? { budget: info.budget } : {}),
    ...(info.deadline ? { deadline: info.deadline } : {}),
    ...(info.competitor ? { competitor: info.competitor } : {})
  };
}

export function buildFormFromExtracted(
  current: ProposalRequest,
  info: ExtractedInfo,
  insight: UrlInsight | null,
  options: { rawSourceText?: string; preserveCurrent?: boolean } = {}
): ProposalRequest {
  const answers = buildChatAnswersFromExtracted(info);
  const sourceText = compactText(options.rawSourceText ?? "");
  const next = applyChatAnswersToForm(current, answers, { preserveCurrent: options.preserveCurrent ?? true });
  const urlInsightText = insight
    ? `URL解析メモ：
会社概要：${insight.companyOverview}
事業内容：${insight.business}
強み：${insight.strengths}
サービス：${insight.services}
採用情報：${insight.recruitment}
SEO状況：${insight.seoStatus}
弱み：${insight.weaknesses}
競合：${insight.competitors}
改善ポイント：${insight.improvementPoints.join("、")}`
    : "";
  const profile = getProposalProfile(`${sourceText}\n${info.projectContent}\n${info.trouble}`);
  const webProject = profile.category === "web";

  return {
    ...next,
    project_brief: `${sourceText || next.project_brief}
抽出元情報：
目的：${info.purposes.join("、") || "未抽出"}
ターゲット：${info.target || "未抽出"}
${webProject ? "SEO課題" : "効果測定"}：${webProject ? info.seoIssue || "未抽出" : "要確認"}
問い合わせ内容：${info.inquiryDetails || "未抽出"}
${profile.requirementLabel}：${webProject ? info.cms || "未抽出" : next.special_function_required || "未抽出"}
${urlInsightText}`.trim(),
    client_company_info: [
      info.companyName,
      info.contactPerson ? `担当者・確認者：${info.contactPerson}` : "",
      info.currentSiteUrl ? `会社ホームページURL：${info.currentSiteUrl}` : "",
      insight?.companyOverview,
      insight?.business,
      insight?.strengths
    ].filter(Boolean).join("\n"),
    cms_required: webProject ? info.cms || next.cms_required : next.cms_required,
    special_function_required: webProject ? next.special_function_required : next.special_function_required || info.inquiryDetails || profile.requirementLabel,
    competitor_site_url: extractFirstUrl(info.competitor) || next.competitor_site_url,
    budget_range: info.budget || next.budget_range,
    desired_launch_timing: info.deadline || next.desired_launch_timing,
    hearing_result: [options.preserveCurrent === false ? "" : current.hearing_result, info.inquiryDetails, urlInsightText].filter(Boolean).join("\n\n")
  };
}
