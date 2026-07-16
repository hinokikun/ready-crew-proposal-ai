import type {
  AiEmployeeRole,
  BrowserUsePlan,
  CompanyResearch,
  CompetitorPoint,
  ConceptBlock,
  DealEvaluation,
  ErrorAdvice,
  EstimateSummary,
  ExtractedInfo,
  FaqAiResult,
  HearingResultSummary,
  HistoryEntry,
  InfoCheck,
  MailAiResult,
  MinutesAiResult,
  OutputDigestSection,
  ProposalPlan,
  ReportAiResult,
  SummaryAiResult,
  TaskAiResult
} from "@/components/app-shell/types";
import type { AnalysisResponse, ProposalRequest, WinProbability } from "@/types/proposal";
import { initialForm } from "@/components/app-shell/constants";
import { toFriendlyError } from "@/lib/errorMessage";
import { aiEmployeeRoles } from "@/components/app-shell/logic-parts/workflow";
import { allInputText } from "@/components/app-shell/logic-parts/intake";
import { uniqueTextItems } from "@/components/app-shell/logic-parts/hearing";
import { buildRiskLabel, deriveProjectedProbability, deriveRiskScore, extractClientName } from "@/components/app-shell/logic-parts/estimates";
import { getProposalProfile } from "@/components/app-shell/logic-parts/profiles";

export function buildInputSummary(form: ProposalRequest) {
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

export function buildProposalPlan(
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

export function buildBrowserUsePlan(form: ProposalRequest, competitorPoints: CompetitorPoint[]): BrowserUsePlan {
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

export function buildAutomationConcept(form: ProposalRequest, deal: DealEvaluation): ConceptBlock {
  const client = extractClientName(form);
  return {
    title: "自動確認の想定",
    label: "将来の自動確認機能",
    items: [
      "毎朝Ready Crew案件を確認し、新着案件を一覧化",
      "予算・納期・決裁者・競合情報が揃う案件を優先表示",
      `${client}のような高優先度案件は受注確率 ${deal.probability}% を目安に営業へ通知`,
      "今回は自動実行せず、画面上の企画表示に留める"
    ]
  };
}

export function buildMcpConcept(form: ProposalRequest): ConceptBlock {
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

export function buildOutputDigest(
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

export function buildErrorAdvice(message: string): ErrorAdvice {
  const friendly = toFriendlyError(new Error(message));
  return {
    title: friendly.title,
    cause: friendly.cause,
    action: friendly.action,
    detail: message
  };
}
export function extractProbability(winProbability?: WinProbability, fallback = 0) {
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

export function buildDisplayedWinProbability(winProbability: WinProbability | undefined, fallback: DealEvaluation) {
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

export function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("ja-JP", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

export function safeHistoryParse(value: string | null): HistoryEntry[] {
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

export function normalizeForm(value: Partial<ProposalRequest> | undefined): ProposalRequest {
  return {
    ...initialForm,
    ...(value ?? {})
  };
}

export function downloadTextFile(content: string, filename: string, type = "text/markdown;charset=utf-8") {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function sanitizeFileName(value: string) {
  return value.replace(/[\\/:*?"<>|]/g, "-").replace(/\s+/g, " ").trim().slice(0, 80);
}

export function splitBusinessLines(value: string, fallback: string[] = []) {
  const lines = value
    .split(/\r?\n|。|;|；/)
    .map((line) => line.replace(/^[-・\s]+/, "").trim())
    .filter((line) => line.length >= 3);
  return uniqueTextItems(lines.length ? lines : fallback);
}

export function pickBusinessItems(value: string, keywords: string[], fallback: string[], limit = 4) {
  const lines = splitBusinessLines(value);
  const matched = lines.filter((line) => keywords.some((keyword) => line.includes(keyword)));
  return uniqueTextItems([...(matched.length ? matched : lines), ...fallback]).slice(0, limit);
}

export function buildInternalMinutes(input: string): MinutesAiResult {
  const text = input.trim();
  const lines = splitBusinessLines(text, ["会議内容を確認し、目的・課題・決定事項・次回アクションを整理します。"]);
  const decisions = pickBusinessItems(text, ["決定", "合意", "進め", "対応", "採用"], ["提案方針と次回確認事項を整理して進行します。"], 3);
  const unresolved = pickBusinessItems(text, ["未定", "確認", "課題", "懸念", "不足"], ["予算、納期、決裁者、運用体制の未確定項目を確認します。"], 4);
  const todoSources = pickBusinessItems(text, ["対応", "作成", "確認", "送付", "共有", "準備"], lines, 5);
  return {
    minutes: lines.slice(0, 5),
    decisions,
    unresolved,
    todos: todoSources.slice(0, 5).map((task, index) => ({
      task,
      owner: index === 0 ? "営業担当" : "担当者確認",
      deadline: task.includes("至急") || task.includes("今週") ? "今週中" : "次回商談前"
    })),
    nextConfirmations: unresolved.slice(0, 4)
  };
}

export function buildInternalMail(purpose: string, recipient: string, content: string, tone: string): MailAiResult {
  const target = recipient.trim() || "ご担当者様";
  const mailPurpose = purpose.trim() || "提案内容のご案内";
  const bodyItems = splitBusinessLines(content, ["ご相談内容を踏まえ、提案資料の初稿を準備しました。"]);
  const selectedTone = tone.trim() || "丁寧";
  const body = `${target}\n\nいつもお世話になっております。\n${mailPurpose}についてご連絡いたします。\n\n${bodyItems
    .slice(0, 4)
    .map((item) => `・${item}`)
    .join("\n")}\n\nご確認いただき、ご不明点や追加で確認したい点がありましたらお知らせください。\n引き続きよろしくお願いいたします。\n\n署名`;
  return {
    subject: `【ご確認】${mailPurpose}`,
    body,
    reply: `${target}\n\nご返信ありがとうございます。いただいた内容を踏まえて、提案内容と見積条件を更新いたします。\n次回までに確認事項を整理してお送りします。`,
    polite: `${target}\n\n平素より大変お世話になっております。\n${mailPurpose}につきまして、下記の通りご案内申し上げます。\n\n${bodyItems.slice(0, 3).join("\n")}\n\nお忙しいところ恐れ入りますが、ご確認のほどよろしくお願いいたします。`,
    short: `${target}\n\n${mailPurpose}の件、要点を共有いたします。\n${bodyItems.slice(0, 3).map((item) => `・${item}`).join("\n")}\n\nご確認をお願いいたします。${selectedTone ? `\n\nトーン: ${selectedTone}` : ""}`
  };
}

export function buildInternalTasks(input: string): TaskAiResult {
  const items = splitBusinessLines(input, ["案件内容を確認し、次にやることを整理します。"]).slice(0, 6);
  const priorities = ["高", "高", "中", "中", "低", "低"];
  return {
    tasks: items.map((item, index) => ({
      task: item,
      priority: priorities[index] ?? "中",
      owner: item.includes("顧客") || item.includes("お客様") ? "営業担当" : "担当者確認",
      deadline: item.includes("納期") || item.includes("公開") ? "日程確認後" : "次回確認まで",
      risk: item.includes("未定") || item.includes("確認") ? "未確定のまま進むと手戻りが発生" : "対応漏れに注意"
    })),
    nextAction: "優先度が高い項目から、担当者と期限を確定します。"
  };
}

export function buildInternalFaq(question: string): FaqAiResult {
  const q = question.trim() || "社内ルールや過去資料の確認事項";
  const department = q.includes("見積") || q.includes("請求") ? "経理・営業管理" : q.includes("契約") ? "法務・管理部" : "担当部署";
  return {
    answer: `${q}については、現時点の入力情報をもとに一次回答を作成します。正式回答は担当部署の確認後に共有します。`,
    department,
    references: ["過去提案書テンプレート", "社内制作フロー", "見積ルール", "案件管理シート"],
    notes: [
      "現時点では外部DBへ接続せず、入力文から回答案を作成します。",
      "Google Driveや社内FAQ/RAGは今後MCPで連携予定です。",
      "顧客名、金額、契約条件は社外共有前に人が確認します。"
    ]
  };
}

export function buildInternalSummary(input: string): SummaryAiResult {
  const lines = splitBusinessLines(input, ["資料内容を確認し、要点・アクション・リスクを整理します。"]);
  return {
    threeLines: uniqueTextItems(lines).slice(0, 3),
    points: pickBusinessItems(input, ["目的", "課題", "提案", "重要", "方針"], lines, 5),
    actions: pickBusinessItems(input, ["対応", "作成", "確認", "送付", "実施"], ["次回までに不足情報を確認します。"], 4),
    risks: pickBusinessItems(input, ["懸念", "リスク", "未定", "不足", "遅延"], ["予算、納期、担当者が未確定の場合は進行リスクになります。"], 4),
    bossSummary: `${lines.slice(0, 3).join("。")}。次回までに重要事項を確認し、提案内容へ反映します。`
  };
}

export function buildInternalReport(input: string): ReportAiResult {
  const lines = splitBusinessLines(input, ["本日の活動内容を整理します。"]);
  const actions = pickBusinessItems(input, ["商談", "提案", "確認", "作成", "連絡"], lines, 4);
  const issues = pickBusinessItems(input, ["課題", "未定", "不足", "懸念"], ["未確定項目を次回確認します。"], 3);
  return {
    daily: actions,
    weekly: uniqueTextItems([...actions, "提案準備と顧客確認事項の整理を進めました。"]).slice(0, 5),
    results: pickBusinessItems(input, ["完了", "成果", "作成", "送付"], ["提案準備の初稿を作成しました。"], 3),
    issues,
    tomorrow: ["不足情報の確認", "提案資料の更新", "次回商談に向けた質問準備"],
    bossMessage: `本日は${actions[0] ?? "案件対応"}を進めました。課題は${issues[0] ?? "未確定項目の確認"}です。明日は不足情報の確認と提案資料の更新を進めます。`
  };
}

export function extractDomainLabel(url: string) {
  try {
    const parsed = new URL(url.startsWith("http") ? url : `https://${url}`);
    return parsed.hostname.replace(/^www\./, "");
  } catch {
    return url.trim() || "会社URL未入力";
  }
}

export function buildCompanyResearch(url: string, form: ProposalRequest, extractedInfo: ExtractedInfo | null): CompanyResearch {
  const domain = extractDomainLabel(url);
  const allText = allInputText(form);
  const profile = getProposalProfile(allText);
  const clientName = extractClientName(form);
  const competitor = form.competitor_company_name.trim() || extractedInfo?.competitor || "同業・地域競合";
  const hasRecruit = /採用|求人|人材|応募|社員/i.test(allText);
  const hasSeo = /SEO|検索|自然流入|流入|地域名/i.test(allText);
  const hasCms = /CMS|WordPress|更新|お知らせ/i.test(allText);

  return {
    overview: `${clientName === "提案先企業" ? domain : clientName}の公開情報、案件概要、既存情報をもとに、事業内容・顧客接点・改善余地を確認します。`,
    competitors: uniqueTextItems([competitor, form.competitor_site_url.trim(), "比較対象サービス", "導入効果・運用性で比較される企業"]).slice(0, 4),
    recruitment: hasRecruit ? "採用情報の訴求、社員紹介、応募導線を重点確認します。" : "採用情報は未入力です。会社理解と信頼形成の補助情報として確認します。",
    news: uniqueTextItems([
      "直近のお知らせ更新頻度",
      "新サービス・店舗・採用に関する発信",
      hasCms ? "継続更新できる運用設計" : "更新停止がないか確認"
    ]).slice(0, 4),
    services: uniqueTextItems([
      form.project_brief.includes("物件") ? "物件検索・問い合わせ導線" : profile.requirementLabel,
      form.project_brief.includes("採用") ? "採用コンテンツ" : "サービス紹介",
      hasSeo ? "SEO記事・FAQ・地域ページ" : "FAQ・実績・導入事例"
    ]),
    sns: ["X / Instagram / Facebook / LinkedInの有無", "更新頻度", "サイト導線との接続", "採用・実績訴求への活用"]
  };
}

export function buildRoleGuidance(role: AiEmployeeRole, form: ProposalRequest, estimate: EstimateSummary) {
  const roleLabel = aiEmployeeRoles.find((item) => item.key === role)?.label ?? "AI社員";
  const base = {
    secretary: ["次回確認事項、日程、送付メールを先に整えます。", "未入力項目を確認リスト化し、営業担当の抜け漏れを減らします。"],
    sales: ["受注確率、競合差別化、提案ストーリーを強化します。", "顧客が社内説明しやすい要約PowerPointを優先します。"],
    director: ["要件、導入構成、提案範囲、体制を具体化します。", "導入要件、成果指標、運用保守の前提条件を提案に反映します。"],
    writer: ["提案サマリー、メール、顧客課題の言葉を磨きます。", "AIっぽい曖昧表現を減らし、営業が話しやすい表現に整えます。"],
    designer: ["PowerPointの見せ方、導線図、KPI、比較表の視認性を確認します。", "顧客の信頼感が伝わる清潔な資料構成に寄せます。"],
    pm: ["見積、スケジュール、リスク、担当者を整理します。", `概算見積は${estimate.totalLabel}を前提に、必須・推奨・オプションを分けます。`]
  } satisfies Record<AiEmployeeRole, string[]>;

  return {
    title: `${roleLabel}として提案を支援`,
    items: uniqueTextItems([...base[role], form.budget_range ? `予算感「${form.budget_range}」との整合性を確認します。` : "予算未入力の場合は次回確認事項に入れます。"]).slice(0, 4)
  };
}

export function buildAiCoworkerReviews(role: AiEmployeeRole, form: ProposalRequest, estimate: EstimateSummary) {
  const roleGuidance = buildRoleGuidance(role, form, estimate);
  return [
    { reviewer: "営業AI", comment: "顧客課題、受注確率、競合差別化を先に伝える構成にします。", improvement: roleGuidance.items[0] },
    { reviewer: "PM AI", comment: "予算、納期、体制、リスクを見積条件と合わせて明確化します。", improvement: `概算見積 ${estimate.totalLabel} の前提条件を資料内に残します。` },
    { reviewer: "デザイナーAI", comment: "情報量の多いスライドはカード、表、ステップ図に分けて読みやすくします。", improvement: "顧客が30秒で理解できるサマリーとKPIを強調します。" },
    { reviewer: "社長AI", comment: "提案が売上・採用・問い合わせ改善にどう効くかを経営目線で補強します。", improvement: "投資対効果と次回アクションを最後に明確化します。" }
  ];
}
