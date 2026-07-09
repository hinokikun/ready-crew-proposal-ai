"use client";

import { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  Bot,
  CheckCircle2,
  Clipboard,
  Download,
  FileDown,
  FileText,
  History,
  Loader2,
  MessageCircle,
  RotateCcw,
  Send,
  Sparkles,
  X
} from "lucide-react";
import { analyzeProposal } from "@/lib/api";
import { downloadEstimatePdf } from "@/lib/pdf";
import { downloadProposalPowerPoint, downloadSummaryProposalPowerPoint } from "@/lib/pptx";
import type { AnalysisResponse, ProposalRequest, WinProbability } from "@/types/proposal";

const HISTORY_KEY = "ready-crew-proposal-history-v1";
const MAX_HISTORY_COUNT = 10;

const initialForm: ProposalRequest = {
  project_brief: "",
  client_company_info: "",
  competitor_site_url: "",
  competitor_company_name: "",
  estimated_page_count: "",
  cms_required: "",
  contact_form_required: "",
  special_function_required: "",
  seo_required: "",
  content_creation_required: "",
  desired_launch_timing: "",
  budget_range: "",
  hearing_result: "",
  own_service_info: "",
  past_proposal_template: "",
  case_studies: ""
};

const sampleBrief = `Ready Crew案件概要：
首都圏で賃貸・売買仲介を行う不動産会社が、Webサイトリニューアルを検討中。
目的は、物件問い合わせ数の増加、来店予約の獲得、地域名検索からの自然流入強化。
現行サイトは情報が古く、スマホで物件情報を探しにくい。採用ページも最低限の内容のみ。
予算感は350万〜500万円、公開希望は2026年10月末。CMSでお知らせ・実績・FAQを更新したい。
既存サイトURL：https://sample-realty.example.jp
競合は地域大手の不動産会社2社。物件検索、CTA、実績訴求、SEOコンテンツで差別化したい。
決裁者は代表取締役、窓口は営業企画部。初回提案では概算費用とスケジュールも知りたい。`;

type Rank = "A" | "B" | "C" | "D";
type InputMode = "easy" | "detail";
type SampleKind = "renewal" | "recruit" | "lp";
type ChatRole = "assistant" | "user";
type ChatAnswerKey = "project" | "company" | "trouble" | "budget" | "deadline" | "competitor";

type EasyInput = {
  projectType: string;
  trouble: string;
  budget: string;
  deadline: string;
  competitorSiteUrl: string;
  currentSiteUrl: string;
  cms: string;
  decisionMakers: string;
  purposes: string[];
};

type ChatMessage = {
  id: string;
  role: ChatRole;
  text: string;
};

type ChatQuestion = {
  key: ChatAnswerKey;
  label: string;
  question: string;
  placeholder: string;
};

type ChatAnswers = Partial<Record<ChatAnswerKey, string>>;

type ExtractedInfo = {
  companyName: string;
  contactPerson: string;
  projectContent: string;
  purposes: string[];
  trouble: string;
  budget: string;
  deadline: string;
  competitor: string;
  currentSiteUrl: string;
  cms: string;
  inquiryDetails: string;
};

type UrlInsight = {
  url: string;
  companyOverview: string;
  business: string;
  strengths: string;
  services: string;
  recruitment: string;
  seoStatus: string;
  improvementPoints: string[];
};

type SalesOpportunityScore = {
  score: number;
  stars: string;
  label: string;
  reasons: string[];
};

const initialEasyInput: EasyInput = {
  projectType: "",
  trouble: "",
  budget: "未定",
  deadline: "未定",
  competitorSiteUrl: "",
  currentSiteUrl: "",
  cms: "未定",
  decisionMakers: "",
  purposes: []
};

const purposeOptions = [
  "問い合わせを増やしたい",
  "採用を強化したい",
  "会社の信頼感を上げたい",
  "更新しやすくしたい",
  "SEOを強化したい"
];

const budgetOptions = ["未定", "100万円未満", "100〜300万円", "300〜500万円", "500万円以上"];
const deadlineOptions = ["未定", "1か月以内", "2〜3か月", "3か月以上"];
const cmsOptions = ["未定", "WordPress", "Movable Type", "独自CMS", "不要"];

const easySamples: Record<SampleKind, EasyInput> = {
  renewal: {
    projectType: "コーポレートサイトのリニューアル",
    trouble: "現行サイトの情報が古く、スマホで物件情報を探しにくい。問い合わせ導線も弱く、地域名検索からの流入を増やしたい。",
    budget: "300〜500万円",
    deadline: "2〜3か月",
    competitorSiteUrl: "https://area-rival-realty.example.jp",
    currentSiteUrl: "https://sample-realty.example.jp",
    cms: "WordPress",
    decisionMakers: "代表取締役、営業企画部",
    purposes: ["問い合わせを増やしたい", "会社の信頼感を上げたい", "更新しやすくしたい", "SEOを強化したい"]
  },
  recruit: {
    projectType: "採用サイト制作",
    trouble: "求人媒体に依存しており、自社の雰囲気や働く魅力が伝わっていない。応募数と応募者の質を改善したい。",
    budget: "100〜300万円",
    deadline: "3か月以上",
    competitorSiteUrl: "https://recruit-rival.example.jp",
    currentSiteUrl: "https://sample-company.example.jp",
    cms: "WordPress",
    decisionMakers: "人事責任者、代表取締役",
    purposes: ["採用を強化したい", "会社の信頼感を上げたい", "更新しやすくしたい"]
  },
  lp: {
    projectType: "新サービスのLP制作",
    trouble: "新サービスの特徴がまだ整理されておらず、広告流入後の問い合わせ率を高めるLPが必要。",
    budget: "100〜300万円",
    deadline: "1か月以内",
    competitorSiteUrl: "https://lp-rival.example.jp",
    currentSiteUrl: "https://sample-service.example.jp",
    cms: "不要",
    decisionMakers: "マーケティング責任者、事業責任者",
    purposes: ["問い合わせを増やしたい", "会社の信頼感を上げたい"]
  }
};

const chatQuestionFlow: ChatQuestion[] = [
  {
    key: "project",
    label: "案件内容",
    question: "どんな案件ですか？例：コーポレートサイトのリニューアル、採用サイト制作、LP制作など",
    placeholder: "例：不動産会社のWebサイトリニューアルです"
  },
  {
    key: "company",
    label: "お客様",
    question: "お客様はどんな会社ですか？会社名、業種、事業内容が分かる範囲で大丈夫です。",
    placeholder: "例：株式会社サンプル不動産。賃貸・売買仲介を行う会社です"
  },
  {
    key: "trouble",
    label: "困りごと",
    question: "お客様は何に困っていますか？問い合わせ、採用、SEO、更新性など、営業で聞いた内容をそのまま書いてください。",
    placeholder: "例：サイトが古く、問い合わせにつながっていません"
  },
  {
    key: "budget",
    label: "予算",
    question: "予算感は分かりますか？未定でも大丈夫です。",
    placeholder: "例：300万〜500万円、または未定"
  },
  {
    key: "deadline",
    label: "納期",
    question: "公開希望時期や納期はありますか？",
    placeholder: "例：10月末公開希望、または未定"
  },
  {
    key: "competitor",
    label: "競合",
    question: "競合サイトや比較されそうな会社はありますか？URLがあれば貼ってください。",
    placeholder: "例：https://example.co.jp、または競合未確認"
  }
];

const initialChatMessages: ChatMessage[] = [
  {
    id: "assistant-initial",
    role: "assistant",
    text: "こんにちは。AI営業アシスタントです。会話だけで提案書の材料を整理します。まず、どんな案件ですか？"
  }
];

type SalesIndicator = {
  title: string;
  rank: Rank;
  label: string;
};

type InfoCheck = {
  key: string;
  label: string;
  found: boolean;
  targetField: string;
  nextQuestion: string;
};

type HearingSheetCategory = {
  key: string;
  category: string;
  found: boolean;
  summary: string;
  questions: string[];
};

type HearingResultSummary = {
  hasInput: boolean;
  minutes: string[];
  decisions: string[];
  unresolved: string[];
  nextConfirmations: string[];
};

type DealEvaluation = {
  rank: Rank;
  probability: number;
  riskScore: number;
  riskLabel: string;
  projectedProbability: number;
  decision: string;
  reason: string;
  positives: string[];
  negatives: string[];
  improvementActions: string[];
};

type CompetitorPoint = {
  label: string;
  point: string;
};

type EstimatePriority = "必須対応" | "推奨対応" | "オプション対応";

type EstimateLine = {
  name: string;
  min: number;
  max: number;
  priority: EstimatePriority;
  enabled: boolean;
};

type EstimateSummary = {
  pageCount: number;
  totalMin: number;
  totalMax: number;
  totalLabel: string;
  budgetAmount: number | null;
  budgetLabel: string;
  budgetFit: "予算内" | "やや調整必要" | "予算超過の可能性あり" | "予算未入力";
  lines: EstimateLine[];
  required: string[];
  recommended: string[];
  optional: string[];
};

type HistoryEntry = {
  id: string;
  createdAt: string;
  title: string;
  clientName: string;
  form: ProposalRequest;
  result: AnalysisResponse;
};

type ProposalPlan = {
  inputInfo: string[];
  outputs: string[];
  aiScope: string[];
  humanScope: string[];
};

type BrowserUsePlan = {
  status: string;
  target: string;
  checks: string[];
  safety: string[];
};

type ConceptBlock = {
  title: string;
  label: string;
  items: string[];
};

type OutputDigestSection = {
  title: string;
  items: string[];
};

type ErrorAdvice = {
  title: string;
  cause: string;
  action: string;
  detail: string;
};

function allInputText(form: ProposalRequest) {
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

function buildEasyMissingItems(easyInput: EasyInput) {
  const missing: string[] = [];
  if (!easyInput.projectType.trim()) {
    missing.push("何を作りたいか");
  }
  if (!easyInput.trouble.trim() && easyInput.purposes.length === 0) {
    missing.push("お客様の困りごと、または目的を1つ以上");
  }
  return missing;
}

function optionalLabel(value: string) {
  return value.trim() || "任意・未入力";
}

function buildProjectBriefFromEasyInput(easyInput: EasyInput) {
  const purposes = easyInput.purposes.length ? easyInput.purposes.join("、") : "未選択";
  return `Ready Crew案件概要：
制作したいものは「${optionalLabel(easyInput.projectType)}」。
目的は、${purposes}。
お客様の困りごとは、${optionalLabel(easyInput.trouble)}。
予算感は「${easyInput.budget}」、納期は「${easyInput.deadline}」。
既存サイトURL：${optionalLabel(easyInput.currentSiteUrl)}
競合サイトURL：${optionalLabel(easyInput.competitorSiteUrl)}
CMS希望：${easyInput.cms}
決裁者・確認者：${optionalLabel(easyInput.decisionMakers)}
初回提案では、課題整理、提案方針、概算見積、スケジュール、PowerPoint提案書の初稿を作成したい。`;
}

function patchFormFromEasyInput(current: ProposalRequest, easyInput: EasyInput): ProposalRequest {
  const nextBrief = buildProjectBriefFromEasyInput(easyInput);
  const currentSiteLine = easyInput.currentSiteUrl.trim() ? `既存サイトURL：${easyInput.currentSiteUrl.trim()}` : "";
  const decisionLine = easyInput.decisionMakers.trim() ? `決裁者・確認者：${easyInput.decisionMakers.trim()}` : "";
  const existingClientInfo = current.client_company_info
    .split("\n")
    .filter((line) => !line.startsWith("既存サイトURL：") && !line.startsWith("決裁者・確認者："))
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
    cms_required: easyInput.cms,
    seo_required: easyInput.purposes.includes("SEOを強化したい") ? "あり" : current.seo_required,
    contact_form_required: easyInput.purposes.includes("問い合わせを増やしたい") ? "あり" : current.contact_form_required
  };
}

function extractFirstUrl(value: string | undefined) {
  if (!value) return "";
  return value.match(/https?:\/\/[^\s、。)）]+/)?.[0] ?? "";
}

function extractUrls(value: string | undefined) {
  if (!value) return [];
  return Array.from(new Set(value.match(/https?:\/\/[^\s、。)）]+/g) ?? []));
}

function withoutUrl(value: string | undefined) {
  if (!value) return "";
  return value.replace(/https?:\/\/[^\s、。)）]+/g, "").replace(/[、。,\s]+$/g, "").trim();
}

function isUnknownAnswer(value: string | undefined) {
  return !value?.trim() || /未定|不明|未確認|なし|まだ/.test(value);
}

function buildProjectBriefFromChatAnswers(answers: ChatAnswers) {
  const project = answers.project?.trim() || "未確認";
  const company = answers.company?.trim() || "未確認";
  const trouble = answers.trouble?.trim() || "未確認";
  const budget = answers.budget?.trim() || "未確認";
  const deadline = answers.deadline?.trim() || "未確認";
  const competitor = answers.competitor?.trim() || "未確認";

  return `AI営業アシスタント整理内容：
案件内容：${project}
お客様情報：${company}
お客様の困りごと：${trouble}
予算感：${budget}
公開希望時期・納期：${deadline}
競合情報：${competitor}
提案書では、現状理解、課題整理、Web戦略、競合比較、概算見積、スケジュール、体制、今後の進め方を整理する。`;
}

function compactText(value: string) {
  return value.replace(/\r/g, "").replace(/[ \t]+/g, " ").replace(/\n{3,}/g, "\n\n").trim();
}

function findLabeledValue(text: string, labels: string[]) {
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

function findSentence(text: string, patterns: (RegExp | string)[]) {
  const sentences = compactText(text)
    .split(/[\n。！？!?]/)
    .map((line) => line.trim())
    .filter(Boolean);
  return sentences.find((sentence) => hasAny(sentence, patterns)) ?? "";
}

function extractCompanyName(text: string, fallbackUrl = "") {
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

function extractPurposeList(text: string) {
  const candidates = [
    { keyword: /問い合わせ|問合せ|資料請求|来店予約|CV|コンバージョン/i, label: "問い合わせを増やしたい" },
    { keyword: /採用|応募|求人|人材/i, label: "採用を強化したい" },
    { keyword: /信頼|ブランド|ブランディング|認知|実績/i, label: "会社の信頼感を上げたい" },
    { keyword: /更新|CMS|お知らせ|ブログ|運用/i, label: "更新しやすくしたい" },
    { keyword: /SEO|検索|自然流入|流入|順位/i, label: "SEOを強化したい" }
  ];
  return candidates.filter((item) => item.keyword.test(text)).map((item) => item.label);
}

function extractProposalInfo(rawText: string, homepageUrl: string): ExtractedInfo {
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
    findSentence(text, ["リニューアル", "制作", "LP", "採用サイト", "Webサイト", "ホームページ", "コーポレートサイト"]);
  const trouble =
    findLabeledValue(text, ["課題", "困りごと", "悩み", "現状", "背景"]) ||
    findSentence(text, [/困|課題|古い|弱い|不足|できていない|伸びない|少ない|改善/]);
  const cms =
    findLabeledValue(text, ["CMS", "CMS希望", "更新"]) ||
    text.match(/WordPress|Movable Type|独自CMS|CMS不要|CMSあり/i)?.[0] ||
    "";
  const inquiryDetails =
    findLabeledValue(text, ["問い合わせ内容", "相談内容", "要望", "希望"]) ||
    findSentence(text, ["知りたい", "相談", "依頼", "提案", "見積", "スケジュール"]);
  const competitorUrl = extractFirstUrl(competitorLine);
  const currentSiteUrl = homepageUrl.trim() || extractFirstUrl(currentSiteLine) || urls.find((url) => url !== competitorUrl) || "";

  return {
    companyName: extractCompanyName(text, currentSiteUrl),
    contactPerson: findLabeledValue(text, ["担当者", "窓口", "ご担当", "決裁者", "確認者"]),
    projectContent,
    purposes: extractPurposeList(text),
    trouble,
    budget,
    deadline,
    competitor: competitorLine || competitorUrl || findLabeledValue(text, ["競合", "競合サイト", "競合企業"]),
    currentSiteUrl,
    cms,
    inquiryDetails
  };
}

function buildUrlInsight(url: string, rawText: string, extracted: ExtractedInfo): UrlInsight | null {
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

function buildChatAnswersFromExtracted(info: ExtractedInfo): ChatAnswers {
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

function buildFormFromExtracted(current: ProposalRequest, info: ExtractedInfo, insight: UrlInsight | null): ProposalRequest {
  const answers = buildChatAnswersFromExtracted(info);
  const next = applyChatAnswersToForm(current, answers);
  const urlInsightText = insight
    ? `URL解析メモ：
会社概要：${insight.companyOverview}
事業内容：${insight.business}
強み：${insight.strengths}
サービス：${insight.services}
採用情報：${insight.recruitment}
SEO状況：${insight.seoStatus}
改善ポイント：${insight.improvementPoints.join("、")}`
    : "";

  return {
    ...next,
    project_brief: `${next.project_brief}
抽出元情報：
目的：${info.purposes.join("、") || "未抽出"}
問い合わせ内容：${info.inquiryDetails || "未抽出"}
CMS：${info.cms || "未抽出"}
${urlInsightText}`.trim(),
    client_company_info: [
      info.companyName,
      info.contactPerson ? `担当者・確認者：${info.contactPerson}` : "",
      info.currentSiteUrl ? `会社ホームページURL：${info.currentSiteUrl}` : "",
      insight?.companyOverview,
      insight?.business,
      insight?.strengths
    ].filter(Boolean).join("\n"),
    cms_required: info.cms || next.cms_required,
    competitor_site_url: extractFirstUrl(info.competitor) || next.competitor_site_url,
    budget_range: info.budget || next.budget_range,
    desired_launch_timing: info.deadline || next.desired_launch_timing,
    hearing_result: [current.hearing_result, info.inquiryDetails, urlInsightText].filter(Boolean).join("\n\n")
  };
}

function findNextMissingQuestionIndex(answers: ChatAnswers) {
  return chatQuestionFlow.findIndex((question) => !answers[question.key]?.trim());
}

function applyChatAnswersToForm(current: ProposalRequest, answers: ChatAnswers): ProposalRequest {
  const allText = Object.values(answers).filter(Boolean).join("\n");
  const competitorUrl = extractFirstUrl(answers.competitor);
  const competitorName = withoutUrl(answers.competitor);

  return {
    ...current,
    project_brief: buildProjectBriefFromChatAnswers(answers),
    client_company_info: answers.company?.trim() || current.client_company_info,
    competitor_site_url: competitorUrl || current.competitor_site_url,
    competitor_company_name: competitorName || current.competitor_company_name,
    budget_range: isUnknownAnswer(answers.budget) ? current.budget_range : answers.budget?.trim() || current.budget_range,
    desired_launch_timing: isUnknownAnswer(answers.deadline) ? current.desired_launch_timing : answers.deadline?.trim() || current.desired_launch_timing,
    cms_required: /cms|wordpress|movable type|更新|お知らせ|ブログ/i.test(allText) ? "あり" : current.cms_required,
    contact_form_required: /問い合わせ|問合せ|フォーム|cta|資料請求|来店予約/i.test(allText) ? "あり" : current.contact_form_required,
    seo_required: /seo|検索|自然流入|流入|順位/i.test(allText) ? "あり" : current.seo_required,
    special_function_required: /物件検索|予約|会員|検索機能|絞り込み|シミュレーション/i.test(allText)
      ? "特殊機能あり"
      : current.special_function_required
  };
}

function buildChatReadiness(answers: ChatAnswers) {
  const required: Array<{ key: ChatAnswerKey; label: string }> = [
    { key: "project", label: "案件内容" },
    { key: "company", label: "お客様情報" },
    { key: "trouble", label: "困りごと" }
  ];
  const missing = required.filter((item) => !answers[item.key]?.trim()).map((item) => item.label);
  const answeredCount = chatQuestionFlow.filter((item) => answers[item.key]?.trim()).length;

  return {
    ready: missing.length === 0,
    missing,
    answeredCount,
    totalCount: chatQuestionFlow.length
  };
}

function buildLiveProjectSummary(form: ProposalRequest, missingItems: InfoCheck[]): OutputDigestSection[] {
  const brief = form.project_brief.trim().replace(/\s+/g, " ");
  return [
    {
      title: "現在の案件概要",
      items: [
        brief ? `${brief.slice(0, 150)}${brief.length > 150 ? "..." : ""}` : "チャットで回答すると、ここに案件概要が自動整理されます。"
      ]
    },
    {
      title: "整理済み情報",
      items: [
        `提案先: ${extractClientName(form)}`,
        `予算: ${form.budget_range.trim() || "未確認"}`,
        `納期: ${form.desired_launch_timing.trim() || "未確認"}`,
        `競合: ${form.competitor_site_url.trim() || form.competitor_company_name.trim() || "未確認"}`
      ]
    },
    {
      title: "次回確認事項",
      items: missingItems.length
        ? missingItems.slice(0, 4).map((item) => `${item.label}: ${item.nextQuestion}`)
        : ["提案書を生成できます。内容確認後、PPTX・PDF出力へ進めます。"]
    }
  ];
}

function buildSalesOpportunityScore(form: ProposalRequest, checks: InfoCheck[]): SalesOpportunityScore {
  const text = allInputText(form);
  let score = 2;
  const reasons: string[] = [];

  if (form.project_brief.trim().length >= 40) {
    score += 1;
    reasons.push("案件内容が整理されています");
  }
  if (checks.find((item) => item.key === "budget")?.found) {
    score += 1;
    reasons.push("予算感が確認できています");
  }
  if (checks.find((item) => item.key === "deadline")?.found) {
    score += 1;
    reasons.push("納期・公開希望が確認できています");
  }
  if (checks.find((item) => item.key === "decision-maker")?.found) {
    score += 1;
    reasons.push("決裁者・確認者の情報があります");
  }
  if (/問い合わせ|採用|SEO|リニューアル|CMS|資料請求|CV/.test(text)) {
    score += 1;
    reasons.push("提案テーマが具体的です");
  }
  if (/未定|未確認|不明/.test(text)) {
    score -= 1;
    reasons.push("未確認情報が残っています");
  }

  const normalizedScore = Math.max(1, Math.min(5, score));
  return {
    score: normalizedScore,
    stars: "★★★★★".slice(0, normalizedScore) + "☆☆☆☆☆".slice(0, 5 - normalizedScore),
    label: normalizedScore >= 4 ? "案件化しやすい" : normalizedScore >= 3 ? "追加確認で案件化しやすい" : "要ヒアリング",
    reasons: reasons.length ? reasons.slice(0, 4) : ["案件内容、予算、納期、決裁者を確認すると判断しやすくなります"]
  };
}

function buildAiRecommendations(form: ProposalRequest, insight: UrlInsight | null) {
  const text = allInputText(form);
  const recommendations: string[] = [];

  if (/問い合わせ|資料請求|CV|コンバージョン|来店予約/.test(text)) {
    recommendations.push("問い合わせ最大化提案：ファーストビュー、CTA、フォーム導線、FAQを改善してCVまでの迷いを減らします。");
  }
  if (/採用|求人|応募|人材/.test(text)) {
    recommendations.push("採用強化提案：職種理解、社員紹介、働く環境、応募導線を整えて応募前の不安を減らします。");
  }
  if (/SEO|検索|自然流入|流入|地域名/.test(text)) {
    recommendations.push("SEO強化提案：サービス別・課題別・FAQ・実績コンテンツを増やし、検索流入から問い合わせへつなげます。");
  }
  if (/CMS|更新|お知らせ|ブログ|運用/.test(text)) {
    recommendations.push("CMS運用提案：更新しやすい管理画面と投稿ルールを設計し、公開後の改善運用を回せる状態にします。");
  }
  if (/競合|比較|他社/.test(text) || form.competitor_site_url.trim()) {
    recommendations.push("競合差別化提案：競合より分かりやすい導線、実績訴求、CTA配置で選ばれる理由を明確にします。");
  }
  if (insight) {
    recommendations.push(`URL改善提案：${insight.improvementPoints[0]}し、既存サイトの強みを提案ストーリーへ反映します。`);
  }

  return uniqueTextItems(recommendations).slice(0, 3).length
    ? uniqueTextItems(recommendations).slice(0, 3)
    : [
        "現状理解提案：事業内容と顧客課題を整理し、提案サマリーで意思決定しやすくします。",
        "導線改善提案：主要CTAと問い合わせフォームまでの流れを短くし、成果につながる構成にします。",
        "運用改善提案：CMSと改善レポートを前提に、公開後も成果を伸ばす提案にします。"
      ];
}

function hasAny(text: string, patterns: (RegExp | string)[]) {
  return patterns.some((pattern) => (typeof pattern === "string" ? text.includes(pattern) : pattern.test(text)));
}

function buildInfoChecks(form: ProposalRequest): InfoCheck[] {
  const text = allInputText(form);
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
      label: "既存サイトURL",
      found: hasAny(text, [/https?:\/\/\S+/, "既存サイトURL", "URL"]),
      targetField: "提案先企業情報",
      nextQuestion: "既存サイトURL、アクセス状況、改善したいページ"
    },
    {
      key: "cms",
      label: "CMS希望",
      found: hasAny(text, ["CMS", "WordPress", "ワードプレス", "更新", "運用"]),
      targetField: "見積条件 > CMS有無",
      nextQuestion: "CMS要否、更新担当者、更新頻度、承認フロー"
    },
    {
      key: "seo",
      label: "SEO希望",
      found: hasAny(text, ["SEO", "検索", "自然検索", "流入", "記事", "コンテンツマーケティング"]),
      targetField: "見積条件 > SEO対策有無",
      nextQuestion: "狙いたい検索キーワード、現状流入、SEO対象ページ"
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

function buildHearingSheet(form: ProposalRequest): HearingSheetCategory[] {
  const text = allInputText(form);
  const hasBusiness = hasAny(text, ["事業", "業種", "サービス", "商品", "商材", "不動産", "採用", "BtoB", "BtoC"]) || form.client_company_info.trim().length >= 20;
  const hasTarget = hasAny(text, ["ターゲット", "顧客", "ユーザー", "求職者", "法人", "個人", "購入者", "検討者", "ペルソナ"]);
  const hasCompetitor = Boolean(form.competitor_site_url.trim() || form.competitor_company_name.trim()) || hasAny(text, ["競合", "他社", "比較", "ベンチマーク", "差別化"]);
  const hasBudget = hasAny(text, [/予算\s*[:：]?\s*[0-9０-９]+/, /[0-9０-９]+\s*(万|万円)/]) && !/予算.*未定|未定.*予算/.test(text);
  const hasDeadline = hasAny(text, ["納期", "公開希望", "公開時期", "リリース", "9月", "10月", "急ぎ", "早め"]) && !/納期.*未定|公開.*未定/.test(text);
  const hasKpi = hasAny(text, ["KPI", "問い合わせ目標", "問合せ目標", "CV率", "コンバージョン", "アクセス数", "資料DL", "自然検索流入", "目標件数"]);
  const hasCms = hasAny(text, ["CMS", "WordPress", "ワードプレス", "更新機能"]) || Boolean(form.cms_required.trim());
  const hasOperation = hasAny(text, ["運用体制", "更新担当", "担当者", "保守", "月次", "レポート", "改善運用", "更新頻度"]);

  return [
    {
      key: "business",
      category: "事業内容",
      found: hasBusiness,
      summary: hasBusiness ? "事業・サービスの前提情報あり" : "事業内容、主力サービス、収益モデルが不足",
      questions: hasBusiness
        ? []
        : ["主力事業・主要サービスは何ですか？", "今回のWebサイトで最も訴求したい強みは何ですか？"]
    },
    {
      key: "target",
      category: "ターゲット",
      found: hasTarget,
      summary: hasTarget ? "想定ユーザーの記載あり" : "誰に向けたサイトかが不足",
      questions: hasTarget
        ? []
        : ["主なターゲットユーザーは誰ですか？", "問い合わせしてほしい顧客層や優先したい属性はありますか？"]
    },
    {
      key: "competitor",
      category: "競合",
      found: hasCompetitor,
      summary: hasCompetitor ? "競合・比較対象の情報あり" : "競合サイト・比較対象が不足",
      questions: hasCompetitor
        ? []
        : ["競合サイトはありますか？", "提案時に比較されやすい企業・サービスはありますか？"]
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
      summary: hasKpi ? "成果指標の記載あり" : "問い合わせ数・CV率などの目標値が不足",
      questions: hasKpi
        ? []
        : ["年間の問い合わせ目標は？", "CV率、アクセス数、自然検索流入など重視するKPIは何ですか？"]
    },
    {
      key: "cms",
      category: "CMS",
      found: hasCms,
      summary: hasCms ? "CMS要否の記載あり" : "CMS要否・更新範囲が不足",
      questions: hasCms
        ? []
        : ["CMSは必要ですか？", "自社で更新したいページやコンテンツは何ですか？"]
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

function buildHearingSheetMarkdown(sheet: HearingSheetCategory[]) {
  const lines = sheet.map((item) => {
    const questions = item.questions.length
      ? item.questions.map((question) => `- Q. ${question}`).join("\n")
      : "- 入力情報あり。初回ヒアリングでは詳細条件を確認します。";
    return `### ${item.category}\n- 状態: ${item.found ? "入力情報あり" : "要ヒアリング"}\n- メモ: ${item.summary}\n${questions}`;
  });
  return `\n\n## ヒアリングシート\n\n${lines.join("\n\n")}`;
}

function buildExportMarkdown(markdown: string, form: ProposalRequest) {
  return `${markdown.trim()}${buildHearingSheetMarkdown(buildHearingSheet(form))}${buildHearingResultMarkdown(buildHearingResultSummary(form))}\n`;
}

function buildHearingResultSummary(form: ProposalRequest): HearingResultSummary {
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

function buildHearingResultMarkdown(summary: HearingResultSummary) {
  if (!summary.hasInput) {
    return "";
  }
  return `\n\n## ヒアリング結果整理\n\n### 議事録\n${markdownBullets(summary.minutes)}\n\n### 決定事項\n${markdownBullets(summary.decisions)}\n\n### 未決事項\n${markdownBullets(summary.unresolved)}\n\n### 次回確認事項\n${markdownBullets(summary.nextConfirmations)}`;
}

function splitHearingResult(value: string) {
  return value
    .split(/\r?\n|。|；|;/)
    .map((line) => line.replace(/^[・•\-\d０-９\s.．、]+/, "").trim())
    .filter(Boolean)
    .map((line) => trimText(line, 90));
}

function buildMeetingMinutes(lines: string[]) {
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

function pickHearingLines(lines: string[], keywords: string[]) {
  return uniqueTextItems(lines.filter((line) => hasAny(line, keywords))).slice(0, 5);
}

function uniqueTextItems(items: string[]) {
  return Array.from(new Set(items.map((item) => item.trim()).filter(Boolean)));
}

function ensureSummaryItems(items: string[], fallback: string[]) {
  return items.length ? items : fallback;
}

function trimText(value: string, maxLength: number) {
  return value.length <= maxLength ? value : `${value.slice(0, maxLength - 1)}…`;
}

function markdownBullets(items: string[]) {
  return items.map((item) => `- ${item}`).join("\n");
}

function deriveSalesIndicators(form: ProposalRequest): SalesIndicator[] {
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

function deriveBudgetRank(text: string): Omit<SalesIndicator, "title"> {
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

function deriveMaturityRank(text: string): Omit<SalesIndicator, "title"> {
  const checks = [
    /問い合わせ|問合せ|CV|採用|SEO|CMS|リニューアル/.test(text),
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

function deriveCompetitorPoints(form: ProposalRequest): CompetitorPoint[] {
  const text = allInputText(form);
  const competitorName = form.competitor_company_name.trim() || "競合サイト";

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

function deriveWinningStrategy(form: ProposalRequest) {
  const text = allInputText(form);
  if (hasAny(text, ["物件", "不動産", "賃貸", "売買"])) return "物件検索で勝つ";
  if (hasAny(text, ["SEO", "検索", "自然検索", "流入"])) return "SEOで勝つ";
  if (hasAny(text, ["実績", "事例", "導入"])) return "実績訴求で勝つ";
  if (hasAny(text, ["問い合わせ", "問合せ", "CV", "CTA"])) return "検索導線で勝つ";
  return "実績訴求とCTA改善で勝つ";
}

function normalizeNumberText(value: string) {
  return value
    .replace(/[０-９]/g, (char) => String.fromCharCode(char.charCodeAt(0) - 0xfee0))
    .replace(/[,，]/g, "");
}

function extractNumber(value: string) {
  const match = normalizeNumberText(value).match(/\d+(?:\.\d+)?/);
  return match ? Number(match[0]) : null;
}

function extractBudgetAmount(value: string) {
  const normalized = normalizeNumberText(value);
  const matches = [...normalized.matchAll(/(\d+(?:\.\d+)?)\s*(万円|万|円)/g)];
  if (!matches.length) return null;

  const amounts = matches.map((match) => {
    const amount = Number(match[1]);
    return match[2] === "円" ? Math.round(amount / 10000) : amount;
  });
  return Math.max(...amounts);
}

function flagEnabled(value: string, text: string, fallbackPatterns: string[]) {
  const target = `${value}\n${text}`;
  if (hasAny(value, ["なし", "不要", "無", "無し", "なし想定"])) return false;
  if (hasAny(value, ["あり", "有", "必要", "希望", "対象", "実施", "要"])) return true;
  return hasAny(target, fallbackPatterns);
}

function formatEstimateRange(line: EstimateLine) {
  return line.enabled ? `${line.min}万〜${line.max}万円` : "対象外";
}

function deriveEstimateSummary(form: ProposalRequest): EstimateSummary {
  const text = allInputText(form);
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

function deriveDealEvaluation(form: ProposalRequest, checks: InfoCheck[], estimate: EstimateSummary): DealEvaluation {
  const text = allInputText(form);
  const foundCount = checks.filter((item) => item.found).length;
  let probability = 35 + foundCount * 7;
  const hasCompetitorInfo = Boolean(form.competitor_site_url.trim() || form.competitor_company_name.trim());

  const positives = [
    hasAny(text, ["問い合わせ", "問合せ", "CV"]) ? "成果目的が明確" : "",
    hasAny(text, ["リニューアル", "刷新", "改修"]) ? "制作ニーズが顕在化" : "",
    hasAny(text, ["CMS", "SEO", "採用"]) ? "提案余地が複数ある" : "",
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

function riskFactorFromCheck(item: InfoCheck) {
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

function prioritizeRiskFactors(items: string[]) {
  const priority = ["予算", "納期", "競合", "決裁", "見積", "既存サイト", "CMS", "SEO"];
  const uniqueItems = Array.from(new Set(items.filter(Boolean)));
  return uniqueItems.sort((a, b) => {
    const aIndex = priority.findIndex((keyword) => a.includes(keyword));
    const bIndex = priority.findIndex((keyword) => b.includes(keyword));
    return (aIndex === -1 ? 99 : aIndex) - (bIndex === -1 ? 99 : bIndex);
  });
}

function deriveRiskScore(probability: number, riskCount: number) {
  let score = probability <= 25 ? 5 : probability <= 40 ? 4 : probability <= 60 ? 3 : probability <= 75 ? 2 : 1;
  if (riskCount >= 4) {
    score = Math.min(5, score + 1);
  }
  return score;
}

function buildRiskLabel(score: number) {
  const normalized = Math.max(1, Math.min(5, score));
  return `${"★".repeat(normalized)}${"☆".repeat(5 - normalized)}`;
}

function deriveProjectedProbability(probability: number, riskScore: number, actionCount: number) {
  let uplift = probability <= 25 ? 25 : probability <= 40 ? 20 : probability <= 60 ? 15 : 10;
  if (riskScore <= 2) {
    uplift = Math.min(uplift, 10);
  }
  if (actionCount < 3) {
    uplift = Math.max(8, uplift - 5);
  }
  return Math.min(90, probability + uplift);
}

function deriveImprovementActions(checks: InfoCheck[], estimate: EstimateSummary, hasCompetitorInfo: boolean) {
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

function extractClientName(form: ProposalRequest, result?: AnalysisResponse | null) {
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

function buildInputSummary(form: ProposalRequest) {
  const brief = form.project_brief.trim().replace(/\s+/g, " ");
  return [
    { label: "提案先", value: extractClientName(form) },
    { label: "競合企業", value: form.competitor_company_name.trim() || "未入力" },
    { label: "競合サイトURL", value: form.competitor_site_url.trim() || "未入力" },
    { label: "想定ページ数", value: form.estimated_page_count.trim() || "未入力" },
    { label: "予算感", value: form.budget_range.trim() || "未入力" },
    { label: "公開希望時期", value: form.desired_launch_timing.trim() || "未入力" },
    { label: "案件概要", value: brief ? `${brief.slice(0, 96)}${brief.length > 96 ? "..." : ""}` : "未入力" },
    { label: "ヒアリング結果", value: form.hearing_result.trim() ? `${form.hearing_result.trim().slice(0, 96)}${form.hearing_result.trim().length > 96 ? "..." : ""}` : "未入力" },
    { label: "自社サービス", value: form.own_service_info.trim() || "未入力" },
    { label: "成功事例", value: form.case_studies.trim() || "未入力" }
  ];
}

function buildProposalPlan(
  form: ProposalRequest,
  checks: InfoCheck[],
  estimate: EstimateSummary,
  hearingQuestionCount: number
): ProposalPlan {
  const foundLabels = checks.filter((item) => item.found).map((item) => item.label);
  const missingLabels = checks.filter((item) => !item.found).map((item) => item.label);
  const competitorReady = Boolean(form.competitor_site_url.trim() || form.competitor_company_name.trim());

  return {
    inputInfo: [
      `入力済み情報: ${foundLabels.length ? foundLabels.join("、") : "案件概要のみ"}`,
      `不足情報: ${missingLabels.length ? missingLabels.join("、") : "大きな不足なし"}`,
      `競合情報: ${competitorReady ? "比較観点を生成可能" : "URLまたは企業名の入力待ち"}`,
      `概算見積: ${estimate.totalLabel} / ${estimate.budgetFit}`
    ],
    outputs: [
      "Markdownの提案書初稿",
      "通常版PowerPoint・要約PowerPoint",
      "見積書PDF",
      `次回ヒアリング質問 ${hearingQuestionCount}件`
    ],
    aiScope: [
      "案件概要から顧客理解・課題・提案方針を整理",
      "競合比較、見積、受注確率、ヒアリング項目を生成",
      "過去テンプレート・成功事例の入力内容を提案構成へ反映",
      "人間が確認しやすい初稿として出力"
    ],
    humanScope: [
      "提案先の固有名詞、実績、金額、納期の最終確認",
      "競合サイトの実画面確認と営業判断",
      "機密情報・顧客情報の取り扱い判断",
      "客先提出前の表現、法務、契約条件の確認"
    ]
  };
}

function buildBrowserUsePlan(form: ProposalRequest, competitorPoints: CompetitorPoint[]): BrowserUsePlan {
  const target = form.competitor_site_url.trim() || form.competitor_company_name.trim() || "競合サイトURL未入力";
  const hasTarget = target !== "競合サイトURL未入力";

  return {
    status: hasTarget ? "確認観点を生成済み" : "URL入力待ち",
    target,
    checks: competitorPoints.map((item) => `${item.label}: ${item.point}`),
    safety: [
      "公開ページの閲覧・比較観点生成に限定",
      "ログイン、フォーム送信、問い合わせ送信は行わない",
      "個人情報・認証情報・非公開情報は入力しない"
    ]
  };
}

function buildAutomationConcept(form: ProposalRequest, deal: DealEvaluation): ConceptBlock {
  const client = extractClientName(form);
  return {
    title: "Automations想定",
    label: "将来の自動確認機能",
    items: [
      "毎朝Ready Crew案件を確認し、新着案件を一覧化",
      "予算・納期・決裁者・競合情報が揃う案件を優先表示",
      `${client}のような高優先度案件は受注確率 ${deal.probability}% を目安に営業へ通知`,
      "今回は自動実行せず、画面上の企画表示に留める"
    ]
  };
}

function buildMcpConcept(form: ProposalRequest): ConceptBlock {
  const hasTemplate = Boolean(form.past_proposal_template.trim());
  const hasCases = Boolean(form.case_studies.trim());
  return {
    title: "MCP連携構想",
    label: "企画レベル",
    items: [
      `Google Drive: ${hasTemplate ? "入力済みテンプレートを提案構成に反映" : "過去提案書テンプレートの参照を想定"}`,
      `GitHub: ${hasCases ? "成功事例データを実績紹介に反映" : "実績情報・制作ナレッジの参照を想定"}`,
      "機密情報を扱う連携は、権限・保存範囲・共有先を確認してから実装",
      "今回は外部連携せず、入力済みテキストだけで生成"
    ]
  };
}

function buildOutputDigest(
  result: AnalysisResponse | null,
  estimate: EstimateSummary,
  form: ProposalRequest,
  missingItems: InfoCheck[],
  hearingSummary: HearingResultSummary
): OutputDigestSection[] {
  if (!result) {
    return [];
  }

  const analysis = result.analysis;
  const topIssues = analysis.issue_priorities.length
    ? analysis.issue_priorities.slice(0, 3).map((item) => `${item.issue}: ${item.proposed_response}`)
    : analysis.assumed_customer_issues.slice(0, 3).map((item) => item.issue);
  const nextItems = uniqueTextItems([
    ...missingItems.map((item) => `${item.targetField}: ${item.nextQuestion}`),
    ...hearingSummary.nextConfirmations
  ]).slice(0, 4);
  const schedule = form.desired_launch_timing.trim() || "公開希望時期は次回確認";

  return [
    {
      title: "提案要約",
      items: [analysis.project_summary, `受注確率: ${analysis.win_probability.probability ?? 0}% / ${analysis.win_probability.rank}ランク`]
    },
    {
      title: "顧客課題",
      items: topIssues.length ? topIssues : ["顧客課題はMarkdown本文で確認できます。"]
    },
    {
      title: "提案方針",
      items: [analysis.proposal_policy, analysis.proposal_story].filter(Boolean).slice(0, 2)
    },
    {
      title: "見積・スケジュール",
      items: [`概算見積: ${estimate.totalLabel}（${estimate.budgetFit}）`, `スケジュール: ${schedule}`]
    },
    {
      title: "次回確認事項",
      items: nextItems.length ? nextItems : ["客先提出前に固有名詞、金額、納期、実績表記を最終確認します。"]
    }
  ];
}

function buildErrorAdvice(message: string): ErrorAdvice {
  const normalized = message.toLowerCase();

  if (/429|rate|レート|制限|quota|insufficient_quota/.test(normalized) || /API.*制限|上限/.test(message)) {
    return {
      title: "OpenAI API制限の可能性があります",
      cause: "短時間の利用回数、API利用上限、または請求設定により生成が止まった可能性があります。",
      action: "少し時間を置いて再実行するか、OpenAIの利用上限・請求設定・APIキーを確認してください。",
      detail: message
    };
  }

  if (/400|422|入力|不足|min_length|validation|短く/.test(normalized) || /入力|不足/.test(message)) {
    return {
      title: "入力内容を確認してください",
      cause: "案件概要が短い、必須項目が不足している、または送信形式が想定と異なる可能性があります。",
      action: "案件概要に目的、予算、納期、既存サイトURL、競合情報を追記してから再生成してください。",
      detail: message
    };
  }

  if (/failed to fetch|network|通信|接続|cors|502|503|504|timeout|タイムアウト/.test(normalized) || /通信|接続|タイムアウト|CORS/.test(message)) {
    return {
      title: "通信エラーの可能性があります",
      cause: "FrontendからBackendへ接続できていない、Backendが停止している、またはCORS設定が合っていない可能性があります。",
      action: "RenderのBackendが起動しているか、VercelのNEXT_PUBLIC_API_URLとBackendのCORS設定を確認してください。",
      detail: message
    };
  }

  return {
    title: "生成中にエラーが発生しました",
    cause: "一時的なAPIエラー、入力内容、またはBackendログで確認できる問題の可能性があります。",
    action: "入力内容を保存したうえで再実行し、解消しない場合はBackendログを確認してください。",
    detail: message
  };
}

function extractProbability(winProbability?: WinProbability, fallback = 0) {
  if (typeof winProbability?.probability === "number" && winProbability.probability > 0) {
    return winProbability.probability;
  }
  const label = winProbability?.label ?? "";
  const match = label.match(/(\d{1,3})\s*%/);
  if (match) {
    return Number(match[1]);
  }
  return fallback;
}

function buildDisplayedWinProbability(winProbability: WinProbability | undefined, fallback: DealEvaluation) {
  const probability = extractProbability(winProbability, fallback.probability);
  const riskScore = Math.max(
    1,
    Math.min(5, winProbability?.risk_score ?? deriveRiskScore(probability, winProbability?.risk_factors?.length ?? fallback.negatives.length))
  );
  const projectedProbability =
    winProbability?.projected_probability_after_actions && winProbability.projected_probability_after_actions > probability
      ? winProbability.projected_probability_after_actions
      : deriveProjectedProbability(probability, riskScore, fallback.improvementActions.length);

  return {
    rank: winProbability?.rank ?? fallback.rank,
    label: winProbability?.label ?? `${fallback.rank}ランク`,
    reason: winProbability?.reason ?? fallback.reason,
    probability,
    riskScore,
    riskLabel: winProbability?.risk_label || buildRiskLabel(riskScore),
    projectedProbability,
    positives: winProbability?.positive_factors?.length ? winProbability.positive_factors : fallback.positives,
    riskFactors: winProbability?.risk_factors?.length ? winProbability.risk_factors : fallback.negatives,
    improvementActions: winProbability?.improvement_actions?.length
      ? winProbability.improvement_actions
      : fallback.improvementActions
  };
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("ja-JP", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

function safeHistoryParse(value: string | null): HistoryEntry[] {
  if (!value) return [];
  try {
    const parsed = JSON.parse(value) as HistoryEntry[];
    if (!Array.isArray(parsed)) return [];
    return parsed.map((entry) => ({
      ...entry,
      form: normalizeForm(entry.form)
    }));
  } catch {
    return [];
  }
}

function normalizeForm(value: Partial<ProposalRequest> | undefined): ProposalRequest {
  return {
    ...initialForm,
    ...(value ?? {})
  };
}

function downloadTextFile(content: string, filename: string, type = "text/markdown;charset=utf-8") {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function sanitizeFileName(value: string) {
  return value.replace(/[\\/:*?"<>|]/g, "-").replace(/\s+/g, " ").trim().slice(0, 80);
}

export default function Home() {
  const [form, setForm] = useState<ProposalRequest>(initialForm);
  const [inputMode, setInputMode] = useState<InputMode>("easy");
  const [easyInput, setEasyInput] = useState<EasyInput>(initialEasyInput);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>(initialChatMessages);
  const [chatAnswers, setChatAnswers] = useState<ChatAnswers>({});
  const [chatQuestionIndex, setChatQuestionIndex] = useState(0);
  const [chatDraft, setChatDraft] = useState("");
  const [rawSourceText, setRawSourceText] = useState("");
  const [companyHomeUrl, setCompanyHomeUrl] = useState("");
  const [extractedInfo, setExtractedInfo] = useState<ExtractedInfo | null>(null);
  const [urlInsight, setUrlInsight] = useState<UrlInsight | null>(null);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isDownloadingPowerPoint, setIsDownloadingPowerPoint] = useState(false);
  const [isDownloadingSummaryPowerPoint, setIsDownloadingSummaryPowerPoint] = useState(false);
  const [isDownloadingEstimatePdf, setIsDownloadingEstimatePdf] = useState(false);
  const [error, setError] = useState("");
  const [copyState, setCopyState] = useState<"idle" | "copied">("idle");

  useEffect(() => {
    setHistory(safeHistoryParse(window.localStorage.getItem(HISTORY_KEY)));
  }, []);

  const canSubmit = useMemo(() => {
    return form.project_brief.trim().length >= 20 && !isLoading;
  }, [form.project_brief, isLoading]);

  const easyMissingItems = useMemo(() => buildEasyMissingItems(easyInput), [easyInput]);
  const canOrganizeEasyInput = easyMissingItems.length === 0;
  const chatReadiness = useMemo(() => buildChatReadiness(chatAnswers), [chatAnswers]);
  const infoChecks = useMemo(() => buildInfoChecks(form), [form]);
  const missingItems = useMemo(() => infoChecks.filter((item) => !item.found), [infoChecks]);
  const liveProjectSummary = useMemo(() => buildLiveProjectSummary(form, missingItems), [form, missingItems]);
  const salesOpportunityScore = useMemo(() => buildSalesOpportunityScore(form, infoChecks), [form, infoChecks]);
  const hearingSheet = useMemo(() => buildHearingSheet(form), [form]);
  const hearingQuestionCount = useMemo(
    () => hearingSheet.reduce((count, item) => count + item.questions.length, 0),
    [hearingSheet]
  );
  const hearingResultSummary = useMemo(() => buildHearingResultSummary(form), [form]);
  const salesIndicators = useMemo(() => deriveSalesIndicators(form), [form]);
  const estimateSummary = useMemo(() => deriveEstimateSummary(form), [form]);
  const dealEvaluation = useMemo(() => deriveDealEvaluation(form, infoChecks, estimateSummary), [form, infoChecks, estimateSummary]);
  const competitorPoints = useMemo(() => deriveCompetitorPoints(form), [form]);
  const winningStrategy = useMemo(() => deriveWinningStrategy(form), [form]);
  const proposalPlan = useMemo(
    () => buildProposalPlan(form, infoChecks, estimateSummary, hearingQuestionCount),
    [form, infoChecks, estimateSummary, hearingQuestionCount]
  );
  const browserUsePlan = useMemo(() => buildBrowserUsePlan(form, competitorPoints), [form, competitorPoints]);
  const automationConcept = useMemo(() => buildAutomationConcept(form, dealEvaluation), [form, dealEvaluation]);
  const mcpConcept = useMemo(() => buildMcpConcept(form), [form]);
  const aiRecommendations = useMemo(() => buildAiRecommendations(form, urlInsight), [form, urlInsight]);
  const inputSummary = useMemo(() => buildInputSummary(form), [form]);
  const displayedWin = useMemo(
    () => buildDisplayedWinProbability(result?.analysis.win_probability, dealEvaluation),
    [result?.analysis.win_probability, dealEvaluation]
  );
  const outputDigest = useMemo(
    () => buildOutputDigest(result, estimateSummary, form, missingItems, hearingResultSummary),
    [result, estimateSummary, form, missingItems, hearingResultSummary]
  );
  const displayedProbability = displayedWin.probability;
  const displayedMarkdown = useMemo(
    () => (result?.markdown ? buildExportMarkdown(result.markdown, form) : ""),
    [result?.markdown, form]
  );
  const errorAdvice = useMemo(() => (error ? buildErrorAdvice(error) : null), [error]);
  const currentChatQuestion = chatQuestionFlow[Math.min(chatQuestionIndex, chatQuestionFlow.length - 1)];

  function updateField(field: keyof ProposalRequest, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function updateEasyField(field: keyof EasyInput, value: string) {
    setEasyInput((current) => ({ ...current, [field]: value }));
  }

  function toggleEasyPurpose(purpose: string) {
    setEasyInput((current) => ({
      ...current,
      purposes: current.purposes.includes(purpose)
        ? current.purposes.filter((item) => item !== purpose)
        : [...current.purposes, purpose]
    }));
  }

  function organizeEasyInput() {
    if (!canOrganizeEasyInput) {
      return;
    }
    setForm((current) => patchFormFromEasyInput(current, easyInput));
    setError("");
  }

  function organizeSourceText() {
    if (!rawSourceText.trim() && !companyHomeUrl.trim()) {
      setError("案件メール、議事録、チャット、Ready Crew案件情報、または会社ホームページURLを入力してください。");
      return;
    }

    const nextExtracted = extractProposalInfo(rawSourceText, companyHomeUrl);
    const nextInsight = buildUrlInsight(companyHomeUrl, rawSourceText, nextExtracted);
    const nextAnswers = buildChatAnswersFromExtracted(nextExtracted);
    const nextMissingIndex = findNextMissingQuestionIndex(nextAnswers);
    const missingQuestion =
      nextMissingIndex >= 0
        ? `${chatQuestionFlow[nextMissingIndex].label}だけ教えてください。\n${chatQuestionFlow[nextMissingIndex].question}`
        : "必要な情報が揃いました。提案書を生成できます。";

    setExtractedInfo(nextExtracted);
    setUrlInsight(nextInsight);
    setChatAnswers(nextAnswers);
    setChatQuestionIndex(nextMissingIndex >= 0 ? nextMissingIndex : chatQuestionFlow.length);
    setChatDraft("");
    setForm((current) => buildFormFromExtracted(current, nextExtracted, nextInsight));
    setChatMessages([
      ...initialChatMessages,
      {
        id: `assistant-extract-${Date.now()}`,
        role: "assistant",
        text: `貼り付け情報を整理しました。
会社名：${nextExtracted.companyName || "未抽出"}
案件内容：${nextExtracted.projectContent || "未抽出"}
困りごと：${nextExtracted.trouble || "未抽出"}
予算：${nextExtracted.budget || "未抽出"}
納期：${nextExtracted.deadline || "未抽出"}
競合：${nextExtracted.competitor || "未抽出"}`
      },
      {
        id: `assistant-missing-${Date.now()}`,
        role: "assistant",
        text: nextMissingIndex >= 0 ? missingQuestion : "このまま「今の内容で生成する」から提案書を作成できます。"
      }
    ]);
    setError("");
  }

  function submitChatAnswer(event?: React.FormEvent<HTMLFormElement>) {
    event?.preventDefault();
    const answer = chatDraft.trim();
    if (!answer) {
      return;
    }

    if (chatQuestionIndex >= chatQuestionFlow.length) {
      setChatMessages((current) => [
        ...current,
        { id: `user-${Date.now()}`, role: "user", text: answer },
        {
          id: `assistant-${Date.now()}-extra`,
          role: "assistant",
          text: "追加情報として反映しました。必要であれば、この内容で提案書を生成できます。"
        }
      ]);
      setForm((current) => ({
        ...current,
        hearing_result: [current.hearing_result, answer].filter(Boolean).join("\n")
      }));
      setChatDraft("");
      setError("");
      return;
    }

    const question = chatQuestionFlow[chatQuestionIndex];
    const nextAnswers = { ...chatAnswers, [question.key]: answer };
    const nextIndex = findNextMissingQuestionIndex(nextAnswers);
    const nextReadiness = buildChatReadiness(nextAnswers);
    const nextAssistantText =
      nextIndex >= 0
        ? `${nextReadiness.ready ? "提案書を生成できます。精度を上げるため、未確認の項目だけ確認します。\n" : ""}${chatQuestionFlow[nextIndex].label}だけ教えてください。\n${chatQuestionFlow[nextIndex].question}`
        : "必要な情報が揃いました。提案書を生成できます。まだ未確認の項目があっても「今の内容で生成する」から進められます。";

    setChatMessages((current) => [
      ...current,
      { id: `user-${Date.now()}`, role: "user", text: answer },
      { id: `assistant-${Date.now()}-next`, role: "assistant", text: nextAssistantText }
    ]);
    setChatAnswers(nextAnswers);
    setChatQuestionIndex(nextIndex >= 0 ? nextIndex : chatQuestionFlow.length);
    setChatDraft("");
    setForm((current) => applyChatAnswersToForm(current, nextAnswers));
    setError("");
  }

  function generateFromChatNow() {
    const nextForm = Object.keys(chatAnswers).length > 0 ? applyChatAnswersToForm(form, chatAnswers) : form;
    if (nextForm.project_brief.trim().length < 20) {
      setError("まずはチャットで案件内容を1つ入力してください。途中でも生成できます。");
      return;
    }
    setForm(nextForm);
    setError("");
    setIsConfirmOpen(true);
  }

  function resetChat() {
    setChatMessages(initialChatMessages);
    setChatAnswers({});
    setChatQuestionIndex(0);
    setChatDraft("");
    setRawSourceText("");
    setCompanyHomeUrl("");
    setExtractedInfo(null);
    setUrlInsight(null);
    setForm(initialForm);
    setResult(null);
    setError("");
  }

  function persistHistory(nextHistory: HistoryEntry[]) {
    setHistory(nextHistory);
    try {
      window.localStorage.setItem(HISTORY_KEY, JSON.stringify(nextHistory));
    } catch {
      setError("生成は完了しましたが、履歴のローカル保存に失敗しました。ブラウザの保存容量を確認してください。");
    }
  }

  function saveHistory(response: AnalysisResponse) {
    const entry: HistoryEntry = {
      id: `${Date.now()}`,
      createdAt: new Date().toISOString(),
      title: response.powerpoint_generation_data.deck_title || "提案書初稿",
      clientName: extractClientName(form, response),
      form,
      result: response
    };
    const nextHistory = [entry, ...history.filter((item) => item.id !== entry.id)].slice(0, MAX_HISTORY_COUNT);
    persistHistory(nextHistory);
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) {
      return;
    }
    setError("");
    setIsConfirmOpen(true);
  }

  async function generateProposal() {
    setIsConfirmOpen(false);
    setIsLoading(true);
    setError("");
    setCopyState("idle");

    try {
      const response = await analyzeProposal(form);
      setResult(response);
      saveHistory(response);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "予期しないエラーが発生しました。");
    } finally {
      setIsLoading(false);
    }
  }

  async function copyMarkdown() {
    if (!result?.markdown) {
      return;
    }

    await navigator.clipboard.writeText(buildExportMarkdown(result.markdown, form));
    setCopyState("copied");
    window.setTimeout(() => setCopyState("idle"), 1800);
  }

  function downloadMarkdown(targetResult = result, targetForm = form) {
    if (!targetResult?.markdown) {
      return;
    }

    const clientName = extractClientName(targetForm, targetResult);
    downloadTextFile(buildExportMarkdown(targetResult.markdown, targetForm), `${sanitizeFileName(clientName)}_提案書初稿.md`);
  }

  async function downloadPowerPointFor(targetResult: AnalysisResponse, targetForm: ProposalRequest, summary: boolean) {
    if (summary) {
      setIsDownloadingSummaryPowerPoint(true);
    } else {
      setIsDownloadingPowerPoint(true);
    }
    setError("");

    try {
      const downloader = summary ? downloadSummaryProposalPowerPoint : downloadProposalPowerPoint;
      await downloader(
        targetResult.powerpoint_generation_data,
        targetResult.analysis.win_probability,
        targetForm.project_brief,
        targetForm.client_company_info,
        targetForm.competitor_site_url,
        targetForm.competitor_company_name,
        targetForm.estimated_page_count,
        targetForm.cms_required,
        targetForm.contact_form_required,
        targetForm.special_function_required,
        targetForm.seo_required,
        targetForm.content_creation_required,
        targetForm.desired_launch_timing,
        targetForm.budget_range,
        targetForm.own_service_info,
        targetForm.past_proposal_template,
        targetForm.case_studies
      );
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : summary
            ? "要約PowerPointの生成に失敗しました。Backendログを確認してください。"
            : "PowerPointの生成に失敗しました。"
      );
    } finally {
      if (summary) {
        setIsDownloadingSummaryPowerPoint(false);
      } else {
        setIsDownloadingPowerPoint(false);
      }
    }
  }

  async function downloadPowerPoint() {
    if (!result) return;
    await downloadPowerPointFor(result, form, false);
  }

  async function downloadSummaryPowerPoint() {
    if (!result) return;
    await downloadPowerPointFor(result, form, true);
  }

  async function downloadEstimatePdfFor(targetResult: AnalysisResponse, targetForm: ProposalRequest) {
    setIsDownloadingEstimatePdf(true);
    setError("");

    try {
      await downloadEstimatePdf(
        targetResult.powerpoint_generation_data,
        targetForm,
        targetResult.analysis.win_probability
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "見積書PDFの生成に失敗しました。Backendログを確認してください。");
    } finally {
      setIsDownloadingEstimatePdf(false);
    }
  }

  async function downloadEstimatePdfCurrent() {
    if (!result) return;
    await downloadEstimatePdfFor(result, form);
  }

  function restoreHistory(entry: HistoryEntry) {
    setForm(normalizeForm(entry.form));
    setInputMode("detail");
    setChatMessages([
      ...initialChatMessages,
      {
        id: `assistant-history-${Date.now()}`,
        role: "assistant",
        text: "生成履歴を読み込みました。右側の整理済み概要を確認し、必要に応じて提案書を再ダウンロードできます。"
      }
    ]);
    setChatAnswers({});
    setChatQuestionIndex(0);
    setChatDraft("");
    setResult(entry.result);
    setError("");
    setCopyState("idle");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function clearHistory() {
    persistHistory([]);
  }

  function loadChatSample(kind: SampleKind) {
    const sample = easySamples[kind];
    const company =
      kind === "renewal"
        ? "株式会社東都リビング。首都圏で賃貸・売買仲介、物件管理を展開する不動産会社です。"
        : kind === "recruit"
          ? "株式会社サンプル製作所。BtoB向け製造・保守サービスを展開する会社です。"
          : "株式会社サンプルマーケティング。新規Webサービスの広告配信とリード獲得を強化している会社です。";
    const nextAnswers: ChatAnswers = {
      project: sample.projectType,
      company,
      trouble: sample.trouble,
      budget: sample.budget,
      deadline: sample.deadline,
      competitor: sample.competitorSiteUrl
    };

    fillSample(kind);
    setChatAnswers(nextAnswers);
    setChatQuestionIndex(chatQuestionFlow.length);
    setChatDraft("");
    setChatMessages([
      ...initialChatMessages,
      {
        id: `assistant-sample-${Date.now()}`,
        role: "assistant",
        text: "サンプル案件を読み込みました。右側の整理済み概要を確認し、そのまま提案書を生成できます。"
      }
    ]);
  }

  function fillSample(kind: SampleKind = "renewal") {
    const sample = easySamples[kind];
    const sampleClientInfo =
      kind === "renewal"
        ? "株式会社東都リビング\n首都圏で賃貸・売買仲介、物件管理を展開\n既存サイトURL：https://sample-realty.example.jp\n決裁者：代表取締役、窓口：営業企画部"
        : kind === "recruit"
          ? "株式会社サンプル製作所\n首都圏でBtoB向け製造・保守サービスを展開\n既存サイトURL：https://sample-company.example.jp\n決裁者：代表取締役、窓口：人事責任者"
          : "株式会社サンプルマーケティング\n新規Webサービスの広告配信とリード獲得を強化中\n既存サイトURL：https://sample-service.example.jp\n決裁者：事業責任者、窓口：マーケティング責任者";
    setEasyInput(sample);
    setForm((current) => ({
      ...patchFormFromEasyInput(current, sample),
      project_brief: kind === "renewal" ? sampleBrief : buildProjectBriefFromEasyInput(sample),
      client_company_info: sampleClientInfo,
      competitor_company_name:
        kind === "renewal"
          ? "エリア大手不動産グループ"
          : kind === "recruit"
            ? "採用競合企業"
            : "競合LPサービス",
      estimated_page_count: kind === "renewal" ? "18ページ" : kind === "recruit" ? "10ページ" : "1ページ",
      special_function_required: kind === "renewal" ? "物件検索あり" : "",
      content_creation_required: kind === "lp" ? "原稿作成あり" : "原稿作成一部あり",
      hearing_result:
        kind === "renewal"
          ? "問い合わせ数の増加を最優先にしたい。CMSはWordPressで進める方針。予算は350万〜500万円。公開希望は2026年10月末。物件登録データの連携方法は未確認。年間問い合わせ目標は現状比150%。"
          : kind === "recruit"
            ? "応募数と応募者の質を改善したい。社員インタビューと職種紹介を入れたい。公開時期は3か月以上で検討。採用責任者と代表が確認する。"
            : "広告配信用LPとして早めに公開したい。問い合わせフォームとCTAを重視。予算は100〜300万円。訴求整理と原稿作成も相談したい。",
      own_service_info: "Webサイト制作、情報設計、CMS構築、SEO初期設計、公開後の改善運用、月次レポートを支援",
      past_proposal_template: "表紙、提案サマリー、現状理解、競合比較、ターゲット分析、Web戦略、サイトマップ、KPI、制作方針、スケジュール、体制、費用概算、今後の進め方",
      case_studies:
        kind === "recruit"
          ? "採用サイトA：応募数160%増加\n製造業B：説明会予約数1.7倍"
          : kind === "lp"
            ? "SaaS企業A：資料請求CV率1.9倍\n新サービスLP：広告CPA25%改善"
            : "不動産会社A：問い合わせ件数150%増加\n不動産会社B：CV率1.8倍\n住宅販売会社C：自然検索流入2.1倍"
    }));
    setError("");
  }

  return (
    <main className="app-shell">
      <section className="workspace-header" aria-label="アプリ概要">
        <div>
          <p className="eyebrow">Ready Crew Proposal AI</p>
          <h1>案件概要から提案書初稿を生成</h1>
        </div>
        <div className="status-pill">
          <CheckCircle2 size={16} aria-hidden="true" />
          MVP
        </div>
      </section>

      <section className="capability-panel" aria-label="このAIでできること">
        <div className="section-heading">
          <p className="eyebrow">Value</p>
          <h2>このAIでできること</h2>
        </div>
        <div className="capability-grid">
          <article>
            <strong>提案書作成時間を短縮</strong>
            <p>案件概要から提案サマリー、課題、方針、構成案まで一気に初稿化します。</p>
          </article>
          <article>
            <strong>不足情報をAIがチェック</strong>
            <p>予算、納期、決裁者、競合、CMS、SEOなど、次回確認すべき情報を整理します。</p>
          </article>
          <article>
            <strong>PowerPoint・PDFを自動生成</strong>
            <p>詳細PPTX、要約PPTX、見積書PDFをダウンロードして、営業資料作成に使えます。</p>
          </article>
        </div>
      </section>

      <section className="before-after-panel" aria-label="Before After比較">
        <div>
          <span>Before</span>
          <strong>手作業で2〜3時間</strong>
          <p>案件整理、構成検討、資料たたき台、見積整理を個別に作成。</p>
        </div>
        <div>
          <span>After</span>
          <strong>AIで20〜30分に短縮</strong>
          <p>初稿生成後、人が30分程度で確認・調整して提出準備へ。</p>
        </div>
      </section>

      <section className="usage-steps" aria-label="使い方4ステップ">
        <article>
          <span>1</span>
          <div>
            <strong>情報を貼り付ける</strong>
            <p>案件メール、議事録、チャット、Ready Crew案件情報をそのまま貼り付けます。</p>
          </div>
        </article>
        <article>
          <span>2</span>
          <div>
            <strong>AIが整理する</strong>
            <p>会社名、案件内容、目的、予算、納期、競合、CMSを自動抽出します。</p>
          </div>
        </article>
        <article>
          <span>3</span>
          <div>
            <strong>不足情報だけ回答</strong>
            <p>抽出できなかった項目だけ、AI営業アシスタントが追加で質問します。</p>
          </div>
        </article>
        <article>
          <span>4</span>
          <div>
            <strong>提案書生成</strong>
            <p>Markdown、PPTX、要約PPTX、見積書PDFを保存できます。</p>
          </div>
        </article>
      </section>

      <section className="extractor-panel" aria-label="AI情報抽出モード">
        <div className="extractor-heading">
          <div>
            <p className="eyebrow">AI Extract Mode</p>
            <h2>案件メール・議事録・チャット・Ready Crew案件情報を<br />そのまま貼り付けてください</h2>
          </div>
          <div className="extractor-score">
            <span>案件化しやすさ</span>
            <strong>{salesOpportunityScore.stars}</strong>
            <small>{salesOpportunityScore.label}</small>
          </div>
        </div>

        <div className="extractor-flow" aria-label="4ステップ">
          <div><span>1</span><strong>情報を貼り付ける</strong></div>
          <div><span>2</span><strong>AIが整理する</strong></div>
          <div><span>3</span><strong>不足情報だけ回答</strong></div>
          <div><span>4</span><strong>提案書生成</strong></div>
        </div>

        <div className="extractor-grid">
          <label className="field extractor-main-input">
            <div className="field-title-row">
              <span>貼り付け情報</span>
              <small>Ready Crew案件メール、Zoom議事録、Slack、Teams、Chatwork、メールをそのまま貼り付け</small>
            </div>
            <textarea
              value={rawSourceText}
              onChange={(event) => setRawSourceText(event.target.value)}
              placeholder="例：
Ready Crew案件情報
株式会社サンプル不動産様。Webサイトリニューアル希望。
現行サイトが古く、問い合わせ数を増やしたい。
予算は300万〜500万円。10月末公開希望。
CMSはWordPress希望。競合：https://example.co.jp"
              rows={9}
            />
          </label>

          <div className="url-analysis-box">
            <label className="field">
              <div className="field-title-row">
                <span>会社ホームページURL</span>
                <small>URLだけでも解析メモを作成</small>
              </div>
              <input
                value={companyHomeUrl}
                onChange={(event) => setCompanyHomeUrl(event.target.value)}
                placeholder="https://example.co.jp"
              />
            </label>
            <button className="primary-button" type="button" onClick={organizeSourceText}>
              <Sparkles size={18} aria-hidden="true" />
              AIが整理する
            </button>
            <div className="score-reason-box">
              <strong>スコア理由</strong>
              <ul>
                {salesOpportunityScore.reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {(extractedInfo || urlInsight) && (
          <div className="extractor-result-grid">
            {extractedInfo && (
              <article className="extractor-result-card">
                <strong>AI抽出結果</strong>
                <dl>
                  <div><dt>会社名</dt><dd>{extractedInfo.companyName || "未抽出"}</dd></div>
                  <div><dt>担当者</dt><dd>{extractedInfo.contactPerson || "未抽出"}</dd></div>
                  <div><dt>案件内容</dt><dd>{extractedInfo.projectContent || "未抽出"}</dd></div>
                  <div><dt>目的</dt><dd>{extractedInfo.purposes.join("、") || "未抽出"}</dd></div>
                  <div><dt>困りごと</dt><dd>{extractedInfo.trouble || "未抽出"}</dd></div>
                  <div><dt>予算</dt><dd>{extractedInfo.budget || "未抽出"}</dd></div>
                  <div><dt>納期</dt><dd>{extractedInfo.deadline || "未抽出"}</dd></div>
                  <div><dt>競合</dt><dd>{extractedInfo.competitor || "未抽出"}</dd></div>
                  <div><dt>CMS</dt><dd>{extractedInfo.cms || "未抽出"}</dd></div>
                  <div><dt>問い合わせ内容</dt><dd>{extractedInfo.inquiryDetails || "未抽出"}</dd></div>
                </dl>
              </article>
            )}

            {urlInsight && (
              <article className="extractor-result-card">
                <strong>URL解析メモ</strong>
                <dl>
                  <div><dt>会社概要</dt><dd>{urlInsight.companyOverview}</dd></div>
                  <div><dt>事業内容</dt><dd>{urlInsight.business}</dd></div>
                  <div><dt>強み</dt><dd>{urlInsight.strengths}</dd></div>
                  <div><dt>サービス</dt><dd>{urlInsight.services}</dd></div>
                  <div><dt>採用情報</dt><dd>{urlInsight.recruitment}</dd></div>
                  <div><dt>SEO状況</dt><dd>{urlInsight.seoStatus}</dd></div>
                </dl>
              </article>
            )}
          </div>
        )}
      </section>

      <section className="workspace-grid">
        <form className="input-panel chat-input-panel" onSubmit={handleSubmit}>
          <div className="panel-heading">
            <div>
              <p className="eyebrow">AI Sales Assistant</p>
              <h2>会話で案件を整理</h2>
            </div>
          </div>

          <section className="sales-chat-panel" aria-label="AI営業アシスタント">
            <div className="sales-chat-hero">
              <div className="assistant-avatar">
                <Bot size={22} aria-hidden="true" />
              </div>
              <div>
                <strong>AI営業アシスタント</strong>
                <p>質問に答えるだけで、案件概要・競合情報・見積条件を整理します。</p>
              </div>
            </div>

            <div className="chat-sample-row" aria-label="サンプル案件">
              <button className="sample-button" type="button" onClick={() => loadChatSample("renewal")}>
                Webリニューアル
              </button>
              <button className="sample-button" type="button" onClick={() => loadChatSample("recruit")}>
                採用サイト
              </button>
              <button className="sample-button" type="button" onClick={() => loadChatSample("lp")}>
                LP制作
              </button>
            </div>

            <div className={`chat-ready-card ${chatReadiness.ready ? "is-ready" : ""}`}>
              <MessageCircle size={18} aria-hidden="true" />
              <div>
                <strong>{chatReadiness.ready ? "提案書を生成できます" : "会話で必要情報を整理中"}</strong>
                <p>
                  {chatReadiness.ready
                    ? "不足項目は次回確認事項として扱い、このまま生成へ進めます。"
                    : `最低限必要: ${chatReadiness.missing.join("、") || "入力中"} / 回答 ${chatReadiness.answeredCount}件`}
                </p>
              </div>
            </div>

            <div className="chat-thread" aria-live="polite">
              {chatMessages.map((message) => (
                <div className={`chat-message ${message.role}`} key={message.id}>
                  <span>{message.role === "assistant" ? "AI" : "あなた"}</span>
                  <p>{message.text}</p>
                </div>
              ))}
            </div>

            <div className="chat-compose" aria-label="チャット入力">
              <input
                value={chatDraft}
                onChange={(event) => setChatDraft(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    event.preventDefault();
                    submitChatAnswer();
                  }
                }}
                placeholder={chatQuestionIndex < chatQuestionFlow.length ? currentChatQuestion.placeholder : "追加情報やヒアリングメモを入力"}
              />
              <button className="icon-button send-button" type="button" onClick={() => submitChatAnswer()} title="送信">
                <Send size={17} aria-hidden="true" />
              </button>
            </div>

            <div className="chat-action-row">
              <button className="secondary-button" type="button" onClick={resetChat}>
                最初から
              </button>
              <button className="primary-button" type="button" onClick={generateFromChatNow} disabled={isLoading}>
                {isLoading ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <Sparkles size={18} aria-hidden="true" />}
                {isLoading ? "生成中" : "今の内容で生成する"}
              </button>
            </div>
          </section>

          <div className="input-mode-tabs" aria-label="入力方式">
            <button
              className={inputMode === "easy" ? "is-active" : ""}
              type="button"
              onClick={() => setInputMode("easy")}
            >
              かんたん入力
            </button>
            <button
              className={inputMode === "detail" ? "is-active" : ""}
              type="button"
              onClick={() => setInputMode("detail")}
            >
              詳細入力
            </button>
          </div>

          {inputMode === "easy" && (
            <section className="easy-input-panel" aria-label="かんたん入力">
              <div className="easy-panel-heading">
                <div>
                  <p className="eyebrow">Easy Input</p>
                  <h3>長文を書かずに、まずは最低限だけ入力</h3>
                </div>
                <span>初期表示</span>
              </div>

              <div className="sample-scenario-panel">
                <strong>まずはサンプルで試す</strong>
                <div className="sample-scenario-buttons">
                  <button className="sample-button" type="button" onClick={() => fillSample("renewal")}>
                    Webサイトリニューアル案件
                  </button>
                  <button className="sample-button" type="button" onClick={() => fillSample("recruit")}>
                    採用サイト制作案件
                  </button>
                  <button className="sample-button" type="button" onClick={() => fillSample("lp")}>
                    LP制作案件
                  </button>
                </div>
              </div>

              <div className="minimum-input-box">
                <strong>最低限これだけ入れれば生成できます</strong>
                <p>「何を作りたいか」と「お客様の困りごと」または「目的」を1つ選べば、AI用の案件概要を作れます。</p>
                {easyMissingItems.length > 0 ? (
                  <ul>
                    {easyMissingItems.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                ) : (
                  <span>最低限の入力は完了しています。</span>
                )}
              </div>

              <div className="easy-field-grid">
                <label className={`field ${!easyInput.projectType.trim() ? "needs-input" : ""}`}>
                  <div className="field-title-row">
                    <span>何を作りたいか</span>
                    <small>必須</small>
                  </div>
                  <input
                    value={easyInput.projectType}
                    onChange={(event) => updateEasyField("projectType", event.target.value)}
                    placeholder="例：コーポレートサイトのリニューアル"
                  />
                </label>

                <label className={`field ${!easyInput.trouble.trim() && easyInput.purposes.length === 0 ? "needs-input" : ""}`}>
                  <div className="field-title-row">
                    <span>お客様の困りごと</span>
                    <small>目的を選べば任意</small>
                  </div>
                  <textarea
                    value={easyInput.trouble}
                    onChange={(event) => updateEasyField("trouble", event.target.value)}
                    placeholder="例：現行サイトが古く、問い合わせにつながっていない"
                    rows={4}
                  />
                </label>
              </div>

              <div className="purpose-check-panel">
                <div className="field-title-row">
                  <span>目的</span>
                  <small>チェックボックスで選択</small>
                </div>
                <div className="purpose-check-grid">
                  {purposeOptions.map((purpose) => (
                    <label className="purpose-check" key={purpose}>
                      <input
                        type="checkbox"
                        checked={easyInput.purposes.includes(purpose)}
                        onChange={() => toggleEasyPurpose(purpose)}
                      />
                      <span>{purpose}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="easy-select-grid">
                <label className="field">
                  <div className="field-title-row">
                    <span>予算</span>
                    <small>任意</small>
                  </div>
                  <select value={easyInput.budget} onChange={(event) => updateEasyField("budget", event.target.value)}>
                    {budgetOptions.map((option) => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </label>
                <label className="field">
                  <div className="field-title-row">
                    <span>納期</span>
                    <small>任意</small>
                  </div>
                  <select value={easyInput.deadline} onChange={(event) => updateEasyField("deadline", event.target.value)}>
                    {deadlineOptions.map((option) => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </label>
                <label className="field">
                  <div className="field-title-row">
                    <span>CMS希望</span>
                    <small>任意</small>
                  </div>
                  <select value={easyInput.cms} onChange={(event) => updateEasyField("cms", event.target.value)}>
                    {cmsOptions.map((option) => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </label>
              </div>

              <div className="easy-field-grid">
                <label className="field">
                  <div className="field-title-row">
                    <span>競合サイトURL</span>
                    <small>任意</small>
                  </div>
                  <input
                    value={easyInput.competitorSiteUrl}
                    onChange={(event) => updateEasyField("competitorSiteUrl", event.target.value)}
                    placeholder="https://example.com"
                  />
                </label>
                <label className="field">
                  <div className="field-title-row">
                    <span>既存サイトURL</span>
                    <small>任意</small>
                  </div>
                  <input
                    value={easyInput.currentSiteUrl}
                    onChange={(event) => updateEasyField("currentSiteUrl", event.target.value)}
                    placeholder="https://example.co.jp"
                  />
                </label>
                <label className="field easy-field-wide">
                  <div className="field-title-row">
                    <span>決裁者・確認者</span>
                    <small>任意</small>
                  </div>
                  <input
                    value={easyInput.decisionMakers}
                    onChange={(event) => updateEasyField("decisionMakers", event.target.value)}
                    placeholder="例：代表取締役、営業部長、人事責任者"
                  />
                </label>
              </div>

              <div className="organized-preview">
                <strong>AI用に整理された案件概要</strong>
                <p>{form.project_brief.trim() ? "整理済みです。必要なら詳細入力で編集できます。" : "まだ整理されていません。「入力内容を整理」を押すと案件概要欄へ文章化します。"}</p>
              </div>
            </section>
          )}

          <section className="check-panel" aria-label="入力内容チェック">
            <div className="check-panel-header">
              <div>
                <p className="eyebrow">Pre Check</p>
                <h3>入力内容の不足チェック</h3>
              </div>
              <span className={`decision-pill rank-${dealEvaluation.rank.toLowerCase()}`}>
                {dealEvaluation.rank} / {dealEvaluation.probability}%
              </span>
            </div>
            <div className="check-grid">
              {infoChecks.map((item) => (
                <div className={`check-item ${item.found ? "is-found" : "is-missing"}`} key={item.key}>
                  <span className="check-dot">{item.found ? "OK" : "要確認"}</span>
                  <strong>{item.label}</strong>
                </div>
              ))}
            </div>
            {missingItems.length > 0 && (
              <div className="warning-box">
                <AlertCircle size={18} aria-hidden="true" />
                <div>
                  <strong>次回確認事項</strong>
                  <p className="warning-lead">不足があっても生成できます。精度を上げる場合は、以下の欄へ追記してください。</p>
                  <ul>
                    {missingItems.map((item) => (
                      <li className="missing-guidance-item" key={item.key}>
                        <strong>{item.label}</strong>
                        <span>追記先: {item.targetField}</span>
                        <small>{item.nextQuestion}</small>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </section>

          <section className="plan-panel" aria-label="提案前プラン">
            <div className="check-panel-header">
              <div>
                <p className="eyebrow">/plan</p>
                <h3>提案前プラン</h3>
              </div>
              <span className="decision-pill rank-b">生成前整理</span>
            </div>
            <div className="plan-grid">
              <article className="plan-card">
                <strong>入力情報</strong>
                <ul>
                  {proposalPlan.inputInfo.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
              <article className="plan-card">
                <strong>出力内容</strong>
                <ul>
                  {proposalPlan.outputs.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
              <article className="plan-card">
                <strong>AIが担当する範囲</strong>
                <ul>
                  {proposalPlan.aiScope.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
              <article className="plan-card">
                <strong>人間が確認する範囲</strong>
                <ul>
                  {proposalPlan.humanScope.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
            </div>
          </section>

          {inputMode === "detail" && (
            <>
          <section className="hearing-panel" aria-label="ヒアリングシート">
            <div className="check-panel-header">
              <div>
                <p className="eyebrow">Hearing Sheet</p>
                <h3>ヒアリングシート</h3>
              </div>
              <span className={`decision-pill ${hearingQuestionCount > 0 ? "rank-c" : "rank-a"}`}>
                質問 {hearingQuestionCount}件
              </span>
            </div>
            <div className="hearing-list">
              {hearingSheet.map((item) => (
                <article className={`hearing-item ${item.found ? "is-found" : "is-missing"}`} key={item.key}>
                  <div className="hearing-item-header">
                    <strong>{item.category}</strong>
                    <span>{item.found ? "確認済み" : "要確認"}</span>
                  </div>
                  <p>{item.summary}</p>
                  {item.questions.length > 0 && (
                    <ul>
                      {item.questions.map((question) => (
                        <li key={question}>Q. {question}</li>
                      ))}
                    </ul>
                  )}
                </article>
              ))}
            </div>
          </section>

          <label className="field">
            <div className="field-title-row">
              <span>案件概要</span>
              <small>何を書けばいい？ 目的・予算・納期・既存URL・競合があると精度が上がります。</small>
            </div>
            <textarea
              required
              minLength={20}
              value={form.project_brief}
              onChange={(event) => updateField("project_brief", event.target.value)}
              placeholder="Ready Crewから届いた案件概要を貼り付けてください。"
              rows={10}
            />
          </label>

          <label className="field">
            <div className="field-title-row">
              <span>提案先企業情報</span>
              <small>企業名、業種、担当者、決裁者、既存サイトURLを書きます。</small>
            </div>
            <textarea
              value={form.client_company_info}
              onChange={(event) => updateField("client_company_info", event.target.value)}
              placeholder="企業名、業種、事業内容、既存サイトURLなど"
              rows={4}
            />
          </label>

          <label className="field">
            <div className="field-title-row">
              <span>ヒアリング結果</span>
              <small>決定事項、未決事項、次回確認事項をメモのまま貼り付けます。</small>
            </div>
            <textarea
              value={form.hearing_result}
              onChange={(event) => updateField("hearing_result", event.target.value)}
              placeholder="商談メモ、ヒアリング結果、決まったこと、未確認事項などを貼り付けてください。"
              rows={7}
            />
          </label>

          <section className="meeting-panel" aria-label="ヒアリング結果整理">
            <div className="check-panel-header">
              <div>
                <p className="eyebrow">Meeting Notes</p>
                <h3>ヒアリング結果整理</h3>
              </div>
              <span className={`decision-pill ${hearingResultSummary.hasInput ? "rank-a" : "rank-d"}`}>
                {hearingResultSummary.hasInput ? "生成済み" : "未入力"}
              </span>
            </div>
            <div className="meeting-summary-grid">
              <article className="meeting-summary-card">
                <strong>議事録</strong>
                <ul>
                  {hearingResultSummary.minutes.slice(0, 4).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
              <article className="meeting-summary-card">
                <strong>決定事項</strong>
                <ul>
                  {hearingResultSummary.decisions.slice(0, 4).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
              <article className="meeting-summary-card">
                <strong>未決事項</strong>
                <ul>
                  {hearingResultSummary.unresolved.slice(0, 4).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
              <article className="meeting-summary-card">
                <strong>次回確認事項</strong>
                <ul>
                  {hearingResultSummary.nextConfirmations.slice(0, 4).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
            </div>
          </section>

          <div className="field-grid">
            <label className="field">
              <div className="field-title-row">
                <span>競合企業名</span>
                <small>比較されやすい会社名</small>
              </div>
              <textarea
                value={form.competitor_company_name}
                onChange={(event) => updateField("competitor_company_name", event.target.value)}
                placeholder="比較対象の企業名、サービス名など"
                rows={2}
              />
            </label>

            <label className="field">
              <div className="field-title-row">
                <span>競合サイトURL</span>
                <small>公開ページのみ。ログイン操作は想定しません。</small>
              </div>
              <textarea
                value={form.competitor_site_url}
                onChange={(event) => updateField("competitor_site_url", event.target.value)}
                placeholder="https://example.com"
                rows={2}
              />
            </label>
          </div>

          <section className="competitor-panel" aria-label="競合分析支援">
            <div className="check-panel-header">
              <div>
                <p className="eyebrow">Competitor</p>
                <h3>競合分析支援</h3>
              </div>
              <span className={`decision-pill ${infoChecks.find((item) => item.key === "competitor")?.found ? "rank-a" : "rank-c"}`}>
                {infoChecks.find((item) => item.key === "competitor")?.found ? "競合あり" : "未確認"}
              </span>
            </div>
            <div className="winning-strategy">
              <span>勝ち筋</span>
              <strong>{winningStrategy}</strong>
            </div>
            <div className="competitor-point-grid">
              {competitorPoints.map((item) => (
                <div className="competitor-point" key={item.label}>
                  <strong>{item.label}</strong>
                  <p>{item.point}</p>
                </div>
              ))}
            </div>
            <div className="browser-use-box">
              <div className="browser-use-header">
                <div>
                  <span>Browser Use活用想定</span>
                  <strong>{browserUsePlan.status}</strong>
                </div>
                <small>{browserUsePlan.target}</small>
              </div>
              <div className="browser-use-grid">
                <div>
                  <strong>確認観点</strong>
                  <ul>
                    {browserUsePlan.checks.slice(0, 6).map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <strong>安全ルール</strong>
                  <ul>
                    {browserUsePlan.safety.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </section>

          <section className="estimate-input-panel" aria-label="見積条件入力">
            <div className="check-panel-header">
              <div>
                <p className="eyebrow">Estimate</p>
                <h3>見積条件</h3>
              </div>
              <span className="decision-pill rank-b">{estimateSummary.pageCount}ページ想定</span>
            </div>
            <div className="estimate-field-grid">
              <label className="field">
                <span>想定ページ数</span>
                <input
                  value={form.estimated_page_count}
                  onChange={(event) => updateField("estimated_page_count", event.target.value)}
                  placeholder="例：12ページ"
                />
              </label>
              <label className="field">
                <span>CMS有無</span>
                <input
                  value={form.cms_required}
                  onChange={(event) => updateField("cms_required", event.target.value)}
                  placeholder="あり / なし / 未定"
                />
              </label>
              <label className="field">
                <span>問い合わせフォーム有無</span>
                <input
                  value={form.contact_form_required}
                  onChange={(event) => updateField("contact_form_required", event.target.value)}
                  placeholder="あり / なし / 未定"
                />
              </label>
              <label className="field">
                <span>特殊機能有無</span>
                <input
                  value={form.special_function_required}
                  onChange={(event) => updateField("special_function_required", event.target.value)}
                  placeholder="物件検索、予約、会員機能など"
                />
              </label>
              <label className="field">
                <span>SEO対策有無</span>
                <input
                  value={form.seo_required}
                  onChange={(event) => updateField("seo_required", event.target.value)}
                  placeholder="あり / なし / 初期設計のみ"
                />
              </label>
              <label className="field">
                <span>撮影・原稿作成有無</span>
                <input
                  value={form.content_creation_required}
                  onChange={(event) => updateField("content_creation_required", event.target.value)}
                  placeholder="撮影あり、原稿作成一部あり など"
                />
              </label>
              <label className="field">
                <span>公開希望時期</span>
                <input
                  value={form.desired_launch_timing}
                  onChange={(event) => updateField("desired_launch_timing", event.target.value)}
                  placeholder="例：9月公開希望"
                />
              </label>
              <label className="field">
                <span>予算感</span>
                <input
                  value={form.budget_range}
                  onChange={(event) => updateField("budget_range", event.target.value)}
                  placeholder="例：300万〜500万円"
                />
              </label>
            </div>
          </section>

          <section className="estimate-panel" aria-label="概算見積AI">
            <div className="check-panel-header">
              <div>
                <p className="eyebrow">Estimate AI</p>
                <h3>概算見積レンジ</h3>
              </div>
              <span
                className={`decision-pill ${
                  estimateSummary.budgetFit === "予算内"
                    ? "rank-a"
                    : estimateSummary.budgetFit === "予算超過の可能性あり"
                      ? "rank-c"
                      : "rank-b"
                }`}
              >
                {estimateSummary.budgetFit}
              </span>
            </div>
            <div className="estimate-total">
              <span>合計概算</span>
              <strong>{estimateSummary.totalLabel}</strong>
              <small>予算感: {estimateSummary.budgetLabel}</small>
            </div>
            <div className="estimate-line-list">
              {estimateSummary.lines.map((line) => (
                <div className={line.enabled ? "estimate-line" : "estimate-line muted"} key={line.name}>
                  <span>{line.name}</span>
                  <strong>{formatEstimateRange(line)}</strong>
                </div>
              ))}
            </div>
            <div className="priority-columns">
              <div>
                <strong>必須対応</strong>
                <p>{estimateSummary.required.join("、") || "次回確認"}</p>
              </div>
              <div>
                <strong>推奨対応</strong>
                <p>{estimateSummary.recommended.join("、") || "次回確認"}</p>
              </div>
              <div>
                <strong>オプション対応</strong>
                <p>{estimateSummary.optional.join("、") || "次回確認"}</p>
              </div>
            </div>
          </section>

          <label className="field">
            <span>自社サービス情報</span>
            <textarea
              value={form.own_service_info}
              onChange={(event) => updateField("own_service_info", event.target.value)}
              placeholder="制作範囲、得意領域、運用支援、CMS構築など"
              rows={4}
            />
          </label>

          <label className="field">
            <span>過去提案書テンプレート</span>
            <textarea
              value={form.past_proposal_template}
              onChange={(event) => updateField("past_proposal_template", event.target.value)}
              placeholder="よく使う構成、言い回し、会社紹介の型など"
              rows={4}
            />
          </label>

          <label className="field">
            <span>成功事例データ</span>
            <textarea
              value={form.case_studies}
              onChange={(event) => updateField("case_studies", event.target.value)}
              placeholder="類似業界、類似課題、成果、制作内容など"
              rows={4}
            />
          </label>

          <section className="deal-panel" aria-label="案件ランク判定">
            <p className="eyebrow">Deal Rank</p>
            <div className="deal-score-row">
              <strong>受注確率</strong>
              <span>{dealEvaluation.probability}%</span>
            </div>
            <div className="risk-summary-row">
              <span>受注リスク</span>
              <strong aria-label={`受注リスク ${dealEvaluation.riskScore} / 5`}>{dealEvaluation.riskLabel}</strong>
            </div>
            <div className="probability-uplift">
              受注確率向上予測 <strong>{dealEvaluation.probability}% → {dealEvaluation.projectedProbability}%</strong>
            </div>
            <p>{dealEvaluation.reason}</p>
            <div className="mini-factor-grid">
              <div>
                <strong>リスク要因</strong>
                <ul>
                  {dealEvaluation.negatives.slice(0, 3).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
              <div>
                <strong>改善アクション</strong>
                <ul>
                  {dealEvaluation.improvementActions.slice(0, 3).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="decision-box">{dealEvaluation.decision}</div>
          </section>

          <section className="workflow-panel" aria-label="業務改善連携構想">
            <div className="check-panel-header">
              <div>
                <p className="eyebrow">Workflow Concept</p>
                <h3>将来の自動化・連携構想</h3>
              </div>
              <span className="decision-pill rank-b">企画表示</span>
            </div>
            <div className="concept-grid">
              {[automationConcept, mcpConcept].map((block) => (
                <article className="concept-card" key={block.title}>
                  <div className="concept-card-header">
                    <strong>{block.title}</strong>
                    <span>{block.label}</span>
                  </div>
                  <ul>
                    {block.items.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>
            <p className="safe-note">
              この表示は業務改善コースの活用想定です。外部サービス連携、自動巡回、機密情報参照はまだ実行しません。
            </p>
          </section>
            </>
          )}

          <section className="generate-flow-panel" aria-label="生成までの流れ">
            <div>
              <span>1</span>
              <strong>まずはサンプルで試す</strong>
              <p>3種類のサンプルから近い案件を選べます。</p>
            </div>
            <div>
              <span>2</span>
              <strong>入力内容を整理</strong>
              <p>かんたん入力をAI用の案件概要に変換します。</p>
              <button className="secondary-button" type="button" onClick={organizeEasyInput} disabled={!canOrganizeEasyInput}>
                入力内容をAI用に整理
              </button>
            </div>
            <div>
              <span>3</span>
              <strong>提案書を生成</strong>
              <p>整理済みの内容からMarkdown・PPTX・PDFを作成します。</p>
              <button className="primary-button" type="submit" disabled={!canSubmit}>
                {isLoading ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <Sparkles size={18} aria-hidden="true" />}
                {isLoading ? "生成中" : "提案書を生成"}
              </button>
            </div>
          </section>

          {!canSubmit && !isLoading && (
            <p className="submit-help">かんたん入力では「入力内容をAI用に整理」を押すと生成できます。詳細入力では案件概要を20文字以上入力してください。</p>
          )}

          {errorAdvice && (
            <div className="error-box detailed-error-box" role="alert">
              <AlertCircle size={18} aria-hidden="true" />
              <div>
                <strong>{errorAdvice.title}</strong>
                <p><b>原因:</b> {errorAdvice.cause}</p>
                <p><b>対処:</b> {errorAdvice.action}</p>
                <small>{errorAdvice.detail}</small>
              </div>
            </div>
          )}
        </form>

        <section className="result-panel" aria-label="生成結果">
          <section className="live-brief-panel" aria-label="現在整理された案件概要">
            <div className="live-brief-header">
              <div>
                <p className="eyebrow">Live Brief</p>
                <h2>現在整理された案件概要</h2>
              </div>
              <span className={`decision-pill ${chatReadiness.ready ? "rank-a" : "rank-c"}`}>
                {chatReadiness.ready ? "生成可能" : "整理中"}
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
          </section>

          <div className="panel-heading">
            <div>
              <p className="eyebrow">Output</p>
              <h2>生成結果</h2>
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
              <strong>提案書初稿を生成しています</strong>
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
                  <strong>資料生成準備中</strong>
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
              </section>

              <article className="markdown-preview">
                <pre>{displayedMarkdown}</pre>
              </article>

              <aside className="ppt-panel">
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

                <p className="eyebrow">Export</p>
                <h3>{result.powerpoint_generation_data.deck_title}</h3>
                <p className="ppt-help">Markdown、詳細版PowerPoint、要約版PowerPoint、見積書PDFを保存できます。</p>
                <div className="ppt-button-stack">
                  <button className="ppt-download-button markdown" type="button" onClick={() => downloadMarkdown()}>
                    <Download size={18} aria-hidden="true" />
                    Markdown
                  </button>
                  <button
                    className="ppt-download-button"
                    type="button"
                    onClick={downloadPowerPoint}
                    disabled={!result || isDownloadingPowerPoint || isDownloadingSummaryPowerPoint || isDownloadingEstimatePdf}
                  >
                    {isDownloadingPowerPoint ? (
                      <Loader2 className="spin" size={18} aria-hidden="true" />
                    ) : (
                      <FileDown size={18} aria-hidden="true" />
                    )}
                    {isDownloadingPowerPoint ? "生成中" : "PowerPoint"}
                  </button>
                  <button
                    className="ppt-download-button summary"
                    type="button"
                    onClick={downloadSummaryPowerPoint}
                    disabled={!result || isDownloadingPowerPoint || isDownloadingSummaryPowerPoint || isDownloadingEstimatePdf}
                  >
                    {isDownloadingSummaryPowerPoint ? (
                      <Loader2 className="spin" size={18} aria-hidden="true" />
                    ) : (
                      <FileDown size={18} aria-hidden="true" />
                    )}
                    {isDownloadingSummaryPowerPoint ? "要約版生成中" : "要約PowerPoint"}
                  </button>
                  <button
                    className="ppt-download-button pdf"
                    type="button"
                    onClick={downloadEstimatePdfCurrent}
                    disabled={!result || isDownloadingPowerPoint || isDownloadingSummaryPowerPoint || isDownloadingEstimatePdf}
                  >
                    {isDownloadingEstimatePdf ? (
                      <Loader2 className="spin" size={18} aria-hidden="true" />
                    ) : (
                      <FileDown size={18} aria-hidden="true" />
                    )}
                    {isDownloadingEstimatePdf ? "PDF生成中" : "見積書PDF"}
                  </button>
                </div>
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

          <section className="history-panel" aria-label="生成履歴">
            <div className="history-heading">
              <div>
                <p className="eyebrow">History</p>
                <h3>生成履歴</h3>
              </div>
              <button className="text-button" type="button" onClick={clearHistory} disabled={history.length === 0}>
                履歴を削除
              </button>
            </div>
            {history.length === 0 ? (
              <p className="history-empty">生成した案件はここにローカル保存されます。</p>
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
      </section>

      {isConfirmOpen && (
        <div className="confirm-overlay" role="dialog" aria-modal="true" aria-label="生成前確認">
          <div className="confirm-modal">
            <div className="confirm-header">
              <div>
                <p className="eyebrow">Confirm</p>
                <h2>この内容で生成しますか？</h2>
              </div>
              <button className="icon-button" type="button" onClick={() => setIsConfirmOpen(false)} title="閉じる">
                <X size={18} aria-hidden="true" />
              </button>
            </div>

            <div className="summary-list">
              {inputSummary.map((item) => (
                <div key={item.label}>
                  <span>{item.label}</span>
                  <p>{item.value}</p>
                </div>
              ))}
            </div>

            <div className={`confirm-rank rank-${dealEvaluation.rank.toLowerCase()}`}>
              <strong>{dealEvaluation.rank}ランク / 受注確率 {dealEvaluation.probability}%</strong>
              <span>{dealEvaluation.decision}</span>
            </div>

            <div className="confirm-plan-grid">
              <div>
                <strong>AI担当範囲</strong>
                <ul>
                  {proposalPlan.aiScope.slice(0, 3).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
              <div>
                <strong>人間の確認範囲</strong>
                <ul>
                  {proposalPlan.humanScope.slice(0, 3).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>

            {missingItems.length > 0 && (
              <div className="warning-box">
                <AlertCircle size={18} aria-hidden="true" />
                <div>
                  <strong>不足情報があります。生成は可能ですが、次回確認事項として反映します。</strong>
                  <p className="warning-lead">提案精度を上げる場合は、以下の欄へ追記してください。</p>
                  <ul>
                    {missingItems.map((item) => (
                      <li className="missing-guidance-item" key={item.key}>
                        <strong>{item.label}</strong>
                        <span>追記先: {item.targetField}</span>
                        <small>{item.nextQuestion}</small>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            <div className="modal-actions">
              <button className="secondary-button" type="button" onClick={() => setIsConfirmOpen(false)}>
                戻って修正
              </button>
              <button className="primary-button" type="button" onClick={generateProposal}>
                {missingItems.length > 0 ? "この内容でも生成する" : "この内容で生成"}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
