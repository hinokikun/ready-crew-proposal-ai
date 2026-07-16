import type {
  AiMinutes,
  ChatAnswerKey,
  ChatAnswers,
  CoachQuestion,
  DailyReport,
  DealEvaluation,
  DraftEmail,
  EstimateSummary,
  ExtractedInfo,
  HistoryEntry,
  InfoCheck,
  KnowledgeGroups,
  MeetingEvaluation,
  NextMeetingPrep,
  OutputDigestSection,
  PreviewSlide,
  QualityScore,
  SalesOpportunityScore,
  StrategyCard,
  UrlInsight
} from "@/components/app-shell/types";
import type { AnalysisResponse, ProposalRequest } from "@/types/proposal";
import { chatQuestionFlow } from "@/components/app-shell/logic-parts/workflow";
import { allInputText, buildProjectBriefFromChatAnswers, extractFirstUrl, isUnknownAnswer, withoutUrl } from "@/components/app-shell/logic-parts/intake";
import { buildInfoChecks, uniqueTextItems } from "@/components/app-shell/logic-parts/hearing";
import { deriveDealEvaluation, deriveEstimateSummary, extractClientName } from "@/components/app-shell/logic-parts/estimates";

export function findNextMissingQuestionIndex(answers: ChatAnswers) {
  return chatQuestionFlow.findIndex((question) => !answers[question.key]?.trim());
}

export function applyChatAnswersToForm(
  current: ProposalRequest,
  answers: ChatAnswers,
  options: { preserveCurrent?: boolean } = {}
): ProposalRequest {
  const allText = Object.values(answers).filter(Boolean).join("\n");
  const competitorUrl = extractFirstUrl(answers.competitor);
  const competitorName = withoutUrl(answers.competitor);
  const preserveCurrent = options.preserveCurrent ?? true;
  const hasCmsIntent = /cms|wordpress|movable type/i.test(allText);
  const hasContactIntent = /cta|contact|form/i.test(allText);
  const hasSeoIntent = /seo/i.test(allText);
  const hasSpecialFunctionIntent = /search|filter|simulation|ai-ocr|ocr|csv|rpa/i.test(allText);

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
      : current.special_function_required,
    ...(preserveCurrent
      ? {}
      : {
          client_company_info: answers.company?.trim() || "",
          competitor_site_url: competitorUrl || "",
          competitor_company_name: competitorName || "",
          estimated_page_count: "",
          cms_required: hasCmsIntent ? "あり" : "",
          contact_form_required: hasContactIntent ? "あり" : "",
          special_function_required: hasSpecialFunctionIntent ? "特殊機能あり" : "",
          seo_required: hasSeoIntent ? "あり" : "",
          content_creation_required: "",
          desired_launch_timing: isUnknownAnswer(answers.deadline) ? "" : answers.deadline?.trim() || "",
          budget_range: isUnknownAnswer(answers.budget) ? "" : answers.budget?.trim() || "",
          hearing_result: "",
          own_service_info: "",
          past_proposal_template: "",
          case_studies: ""
        })
  };
}

export function buildChatReadiness(answers: ChatAnswers) {
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

export function buildLiveProjectSummary(form: ProposalRequest, missingItems: InfoCheck[]): OutputDigestSection[] {
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
        : ["提案書を作成できます。内容確認後、PPTX・PDF出力へ進めます。"]
    }
  ];
}

export function buildSalesOpportunityScore(form: ProposalRequest, checks: InfoCheck[]): SalesOpportunityScore {
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

export function buildAiRecommendations(form: ProposalRequest, insight: UrlInsight | null) {
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

export function buildStrategyCards(form: ProposalRequest, recommendations: string[]): StrategyCard[] {
  const text = allInputText(form);
  const cards: StrategyCard[] = [];

  if (/デザイン|古い|信頼|ブランド|ブランディング|見た目/.test(text)) {
    cards.push({ title: "デザイン重視", reason: "信頼感や第一印象の改善が成果に直結するため、ファーストビューと実績訴求を強化します。" });
  }
  if (/SEO|検索|自然流入|流入|地域名/.test(text)) {
    cards.push({ title: "SEO重視", reason: "検索流入が課題に含まれるため、サービス別・FAQ・事例コンテンツで入口を増やします。" });
  }
  if (/採用|求人|応募|人材/.test(text)) {
    cards.push({ title: "採用強化", reason: "応募前の不安を減らすため、社員紹介・職種紹介・働く環境を分かりやすくします。" });
  }
  if (/問い合わせ|資料請求|CV|CTA|来店予約/.test(text)) {
    cards.push({ title: "問い合わせ最大化", reason: "問い合わせ導線が成果に直結するため、CTA配置とフォーム到達までの流れを短縮します。" });
  }
  if (/競合|比較|他社/.test(text)) {
    cards.push({ title: "差別化重視", reason: "競合比較が想定されるため、選ばれる理由と実績訴求を明確にします。" });
  }

  recommendations.forEach((item) => {
    if (cards.length < 3) {
      const [title, reason] = item.split("：");
      cards.push({ title: title || "提案強化", reason: reason || item });
    }
  });

  return cards.slice(0, 3);
}

export function buildPreviewSlides(form: ProposalRequest, strategies: StrategyCard[], estimate: EstimateSummary): PreviewSlide[] {
  const client = extractClientName(form);
  return [
    { title: `${client} Webサイト制作ご提案`, body: "現状理解から課題、戦略、制作方針、費用、進め方までを整理します。" },
    { title: "提案サマリー", body: form.project_brief.trim().slice(0, 180) || "案件メールの内容をもとに提案サマリーを整理します。" },
    { title: "現状理解・課題", body: form.hearing_result.trim().slice(0, 180) || "不足情報は次回確認事項として扱い、仮説ベースで課題を整理します。" },
    { title: "AI提案戦略", body: strategies.map((item) => `${item.title}: ${item.reason}`).join("\n") },
    { title: "競合・SEO方針", body: `競合: ${form.competitor_site_url || form.competitor_company_name || "競合未確認"}\nSEO: ${form.seo_required || "要確認"}` },
    { title: "概算見積・スケジュール", body: `概算見積: ${estimate.totalLabel}\n予算適合: ${estimate.budgetFit}\n納期: ${form.desired_launch_timing || "要確認"}` },
    { title: "今後の進め方", body: "不足情報確認、要件定義、構成案作成、デザイン制作、実装、検証、公開の順で進行します。" }
  ];
}

export function buildQualityScore(
  result: AnalysisResponse | null,
  form: ProposalRequest,
  deal: DealEvaluation,
  estimate: EstimateSummary,
  strategies: StrategyCard[]
): QualityScore {
  const hasResult = Boolean(result);
  const proposal = Math.min(100, 62 + strategies.length * 8 + (form.project_brief.length > 120 ? 12 : 0));
  const persuasion = Math.min(100, 58 + deal.positives.length * 7 + (form.case_studies.trim() ? 12 : 0));
  const roi = Math.min(100, 55 + (estimate.budgetFit === "予算内" ? 18 : estimate.budgetFit === "やや調整必要" ? 10 : 4));
  const differentiation = Math.min(100, 56 + (form.competitor_site_url || form.competitor_company_name ? 18 : 6) + strategies.length * 4);
  const readability = Math.min(100, hasResult ? 82 : 72);
  const total = Math.round((proposal + persuasion + roi + differentiation + readability) / 5);
  const improvements = [
    form.case_studies.trim() ? "成功事例の成果数値を表紙直後の提案サマリーにも反映します。" : "類似実績を1〜2件追加すると説得力が上がります。",
    form.budget_range.trim() && form.budget_range !== "未定" ? "予算内・オプションの切り分けを明確にします。" : "予算確認後、必須範囲とオプション範囲を再整理します。",
    form.competitor_site_url.trim() ? "競合サイトのCTA・SEO・実績訴求を実画面で確認します。" : "競合サイトURLを確認すると差別化提案が強くなります。"
  ];

  return { total, proposal, persuasion, roi, differentiation, readability, improvements };
}

export function buildDraftEmail(form: ProposalRequest): DraftEmail {
  const client = extractClientName(form);
  return {
    subject: `【ご提案資料送付】${client} Webサイト制作のご提案`,
    body: `${client}
ご担当者様

お世話になっております。
Webサイト制作のご相談について、初回提案資料をお送りします。

本資料では、現状理解、想定課題、提案方針、概算費用、スケジュールを整理しております。
未確認事項については、次回のお打ち合わせで確認させてください。

ご確認のほど、よろしくお願いいたします。`,
    signature: "AI営業秘書\n営業担当"
  };
}

export function buildAiMinutes(form: ProposalRequest, extracted: ExtractedInfo | null): AiMinutes {
  const source = form.hearing_result.trim() || form.project_brief.trim();
  const minutes = [
    `${extractClientName(form)}の相談内容を確認`,
    extracted?.projectContent || "Webサイト制作・改善提案について協議",
    extracted?.trouble || "現状課題と改善方針を整理"
  ];
  const todos = [
    form.budget_range && form.budget_range !== "未定" ? "予算範囲に合わせた提案範囲を調整" : "予算感を確認",
    form.desired_launch_timing && form.desired_launch_timing !== "要確認" ? "公開希望時期から逆算してスケジュール作成" : "公開希望時期を確認",
    form.competitor_site_url || form.competitor_company_name ? "競合比較観点を提案書に反映" : "競合サイトを確認"
  ];
  const nextActions = [
    "提案書初稿を確認",
    "不足情報を次回ヒアリングで確認",
    source ? "提案範囲・費用・スケジュールを合意形成" : "案件メールまたは商談メモを追加"
  ];

  return { minutes, todos, nextActions };
}

export function buildWinRateImprovements(deal: DealEvaluation, quality: QualityScore) {
  return [
    `決裁者・予算・納期の確認で受注確率を${deal.probability}%から${deal.projectedProbability}%へ引き上げます。`,
    quality.roi < 75 ? "費用対効果の説明を追加し、必須範囲とオプション範囲を分けます。" : "ROI説明は十分です。成果指標を提案サマリーに強調します。",
    quality.differentiation < 80 ? "競合比較を1枚追加し、勝ち筋を明確にします。" : "競合差別化の軸を維持し、実績訴求を強めます。"
  ];
}

export function buildSimilarCases(history: HistoryEntry[], form: ProposalRequest) {
  const text = allInputText(form);
  const keywords = ["不動産", "採用", "LP", "SEO", "CMS", "問い合わせ", "リニューアル", "物件", "資料請求"];
  return history
    .map((entry) => {
      const entryText = allInputText(entry.form);
      const score = keywords.reduce((sum, keyword) => sum + (text.includes(keyword) && entryText.includes(keyword) ? 1 : 0), 0);
      return { entry, score };
    })
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 3);
}

export function buildDashboardMetrics(history: HistoryEntry[], result: AnalysisResponse | null) {
  const today = new Date().toDateString();
  const todayCount = history.filter((entry) => new Date(entry.createdAt).toDateString() === today).length + (result ? 1 : 0);
  const proposalCount = history.length + (result ? 1 : 0);
  const savedHours = Math.max(0, Math.round(proposalCount * 2.2 * 10) / 10);

  return [
    { label: "今日の作成数", value: `${todayCount}件`, note: "今日整理した案件" },
    { label: "AI削減時間", value: `${savedHours}h`, note: "累計目安" },
    { label: "作成履歴", value: `${history.length}件`, note: "ローカル保存" },
    { label: "提案書作成数", value: `${proposalCount}件`, note: "原稿 / PPTX作成" },
    { label: "平均作成時間", value: "20分", note: "従来2〜3時間から短縮" },
  ];
}

export function buildMonthlyDashboardMetrics(history: HistoryEntry[], result: AnalysisResponse | null, quality: QualityScore, deal: DealEvaluation) {
  const now = new Date();
  const monthEntries = history.filter((entry) => {
    const date = new Date(entry.createdAt);
    return date.getFullYear() === now.getFullYear() && date.getMonth() === now.getMonth();
  });
  const proposalCount = monthEntries.length + (result ? 1 : 0);
  const winCount = monthEntries.filter((entry) => (entry.result.analysis.win_probability.probability ?? 0) >= 70).length + (deal.probability >= 70 ? 1 : 0);
  const avgProbability = proposalCount
    ? Math.round(
        (monthEntries.reduce((sum, entry) => sum + (entry.result.analysis.win_probability.probability ?? 0), 0) + deal.probability) /
          proposalCount
      )
    : deal.probability;
  return [
    { label: "今月提案数", value: `${proposalCount}件`, note: "今月の提案準備" },
    { label: "今月受注数", value: `${winCount}件`, note: "70%以上を受注見込みで計上" },
    { label: "AI削減時間", value: `${Math.round(proposalCount * 2.2 * 10) / 10}h`, note: "今月の削減目安" },
    { label: "平均品質スコア", value: `${quality.total}点`, note: "現在案件を基準表示" },
    { label: "平均受注確率", value: `${avgProbability}%`, note: "履歴と現在案件の平均" }
  ];
}

export function buildPreMeetingChecklist(checks: InfoCheck[]) {
  const found = new Map(checks.map((item) => [item.key, item.found]));
  return [
    { label: "この会社の事業内容を理解していますか", done: Boolean(found.get("current-site")) },
    { label: "競合を確認しましたか", done: Boolean(found.get("competitor")) },
    { label: "予算を確認しましたか", done: Boolean(found.get("budget")) },
    { label: "納期を確認しましたか", done: Boolean(found.get("deadline")) },
    { label: "決裁者を確認しましたか", done: Boolean(found.get("decision-maker")) },
    { label: "CMS希望を確認しましたか", done: Boolean(found.get("cms")) }
  ];
}

export function buildCoachQuestions(form: ProposalRequest, missingItems: InfoCheck[]): CoachQuestion[] {
  const text = allInputText(form);
  const base: CoachQuestion[] = [
    { priority: 5, question: "最終決裁者はどなたですか？", reason: "提案後の意思決定ルートを確認するため" },
    { priority: 5, question: "今回のWeb制作で最も達成したい成果は何ですか？", reason: "提案軸とKPIを合わせるため" },
    { priority: 4, question: "予算の上限と、段階提案の可否を教えてください。", reason: "必須範囲とオプションを分けるため" },
    { priority: 4, question: "公開希望日は必達ですか、それとも目安ですか？", reason: "スケジュールリスクを判断するため" },
    { priority: 4, question: "公開後の更新担当者はいますか？", reason: "CMSと運用体制を設計するため" },
    { priority: 4, question: "競合サイトで良いと思う点・避けたい点はありますか？", reason: "差別化と好みを把握するため" },
    { priority: 3, question: "現在のサイトで一番困っているページはどこですか？", reason: "改善優先度を決めるため" },
    { priority: 3, question: "問い合わせや応募の現在数と目標数はありますか？", reason: "成果指標とROIを提示するため" },
    { priority: 3, question: "写真撮影・原稿作成は社内対応できますか？", reason: "制作範囲と見積精度を上げるため" },
    { priority: 3, question: "社内確認に必要な人数と確認期間を教えてください。", reason: "手戻りと納期遅延を防ぐため" }
  ];

  const missingBoost = missingItems.map((item) => ({
    priority: 5,
    question: `${item.label}について確認してください。${item.nextQuestion}は分かりますか？`,
    reason: "不足情報を埋めると提案精度が上がるため"
  }));
  const industryQuestion = /採用|求人|応募/.test(text)
    ? [{ priority: 5, question: "採用したい職種と応募者像を教えてください。", reason: "採用サイトの訴求軸を決めるため" }]
    : /不動産|物件/.test(text)
      ? [{ priority: 5, question: "物件情報の登録・検索・更新はどのように運用していますか？", reason: "物件検索やCMS要件を決めるため" }]
      : [];

  return uniqueTextItems([...industryQuestion, ...missingBoost, ...base].map((item) => `${item.priority}|${item.question}|${item.reason}`))
    .map((item) => {
      const [priority, question, reason] = item.split("|");
      return { priority: Number(priority), question, reason };
    })
    .sort((a, b) => b.priority - a.priority)
    .slice(0, 10);
}

export function starsFromPriority(priority: number) {
  const normalized = Math.max(1, Math.min(5, priority));
  return `${"★".repeat(normalized)}${"☆".repeat(5 - normalized)}`;
}

export function buildRealtimeQuestion(liveMemo: string, questions: CoachQuestion[]) {
  const text = liveMemo || "";
  if (!text.trim()) return questions[0]?.question ?? "まず現状課題を確認しましょう。";
  if (!/予算|費用|金額/.test(text)) return "予算感と上限、段階提案の可否を確認しましょう。";
  if (!/納期|公開|いつ|時期/.test(text)) return "公開希望時期と必達期限を確認しましょう。";
  if (!/決裁|承認|社長|代表|役員/.test(text)) return "決裁者と承認フローを確認しましょう。";
  if (!/競合|比較|他社/.test(text)) return "比較している競合サイトや参考サイトを確認しましょう。";
  if (!/KPI|目標|問い合わせ|応募|CV/.test(text)) return "成果目標やKPIを数字で確認しましょう。";
  return "最後に、次回までの提出物と確認スケジュールを合意しましょう。";
}

export function buildMeetingEvaluation(memo: string, form: ProposalRequest): MeetingEvaluation {
  const text = `${memo}\n${allInputText(form)}`;
  const hearing = Math.min(100, 50 + ["予算", "納期", "決裁", "競合", "CMS", "KPI"].filter((word) => text.includes(word)).length * 8);
  const proposal = Math.min(100, 55 + ["提案", "改善", "SEO", "CTA", "CMS", "運用"].filter((word) => text.includes(word)).length * 7);
  const closing = Math.min(100, 48 + ["次回", "提出", "確認", "合意", "スケジュール"].filter((word) => text.includes(word)).length * 9);
  const questions = Math.min(100, 52 + (memo.match(/？|\?/g)?.length ?? 0) * 8 + ["誰", "いつ", "いくら", "どの"].filter((word) => text.includes(word)).length * 6);
  const information = Math.min(100, 50 + ["会社", "担当", "目的", "課題", "予算", "納期", "競合", "運用"].filter((word) => text.includes(word)).length * 6);
  const total = Math.round((hearing + proposal + closing + questions + information) / 5);

  return {
    total,
    hearing,
    proposal,
    closing,
    questions,
    information,
    comment: total >= 80 ? "商談情報が十分に整理されています。提案書の説得力を高められます。" : total >= 65 ? "基本情報は取れています。不足条件を追加確認すると受注確度が上がります。" : "商談情報がまだ薄い状態です。次回は予算・納期・決裁者を優先確認しましょう。",
    goodPoints: [
      text.includes("課題") || text.includes("困") ? "課題を確認できています" : "提案に必要な会話の土台を作れています",
      text.includes("予算") ? "予算に触れられています" : "提案範囲の相談に進めています",
      text.includes("次回") ? "次回アクションを意識できています" : "提案準備へ進める情報があります"
    ],
    improvements: [
      text.includes("決裁") ? "決裁者情報を提案書にも反映しましょう" : "決裁者と承認フローを確認しましょう",
      text.includes("KPI") || text.includes("目標") ? "KPIを提案サマリーで強調しましょう" : "問い合わせ数・応募数などの目標値を確認しましょう",
      text.includes("競合") ? "競合比較を具体化しましょう" : "競合サイトや比較対象を確認しましょう"
    ],
    nextFocus: ["最終決裁者", "予算上限", "公開希望時期", "競合比較", "公開後の運用体制"].filter((item) => !text.includes(item.slice(0, 2))).slice(0, 3)
  };
}

export function buildNextMeetingPrep(form: ProposalRequest, missingItems: InfoCheck[]): NextMeetingPrep {
  return {
    confirmations: missingItems.slice(0, 5).map((item) => `${item.label}: ${item.nextQuestion}`),
    homework: [
      "競合サイトの導線・CTA・SEO観点を確認",
      "必須範囲とオプション範囲の見積を整理",
      "提案サマリーとKPI案を1枚で説明できるよう準備"
    ],
    deliverables: [
      "要約PowerPoint",
      "詳細PowerPoint",
      "概算見積書PDF",
      "次回確認事項リスト"
    ]
  };
}

export function buildWinRateCoachAdvice(form: ProposalRequest, strategyCards: StrategyCard[]) {
  const text = allInputText(form);
  return {
    additions: [
      text.includes("KPI") ? "KPI達成までの改善サイクルを追加" : "問い合わせ数・応募数などのKPI目標を追加",
      "費用対効果と優先順位を1枚で説明",
      "次回確認事項を商談最後に合意"
    ],
    differentiation: [
      form.competitor_site_url || form.competitor_company_name ? "競合のCTA・コンテンツ量・SEOとの差を表で提示" : "競合サイトを確認して比較表を追加",
      strategyCards[0] ? `${strategyCards[0].title}を中心軸にする` : "実績訴求と運用支援を差別化軸にする",
      "公開後の改善運用まで含めて提案"
    ],
    delight: [
      "初回から要約版PPTと見積書PDFをセットで提示",
      "お客様側の社内説明に使いやすい1枚サマリーを追加",
      "CMS更新マニュアルや公開後30日改善プランを提案"
    ]
  };
}

export function buildSalesDailyReport(form: ProposalRequest, evaluation: MeetingEvaluation): DailyReport {
  return {
    activities: ["Ready Crew案件の整理", "AIによる提案書初稿作成", "商談準備チェックと質問設計"],
    meeting: [`${extractClientName(form)}のWeb制作相談`, form.project_brief.trim().slice(0, 90) || "案件概要は要確認"],
    results: [`商談評価 ${evaluation.total}点`, `受注確率 ${deriveDealEvaluation(form, buildInfoChecks(form), deriveEstimateSummary(form)).probability}%`],
    issues: evaluation.improvements,
    tomorrow: ["不足情報の確認", "提案資料の最終調整", "次回商談日程の確認"]
  };
}

export function buildBossReport(form: ProposalRequest, deal: DealEvaluation, missingItems: InfoCheck[]) {
  const report = `${extractClientName(form)}のWeb制作案件です。${form.project_brief.trim().slice(0, 90)}。受注確率は${deal.probability}%、判断は「${deal.decision}」。現在の課題は${missingItems.map((item) => item.label).slice(0, 3).join("、") || "大きな不足なし"}です。今後は不足情報確認、競合比較、概算見積の調整を行い、次回商談で提案内容を固めます。`;
  return report.slice(0, 300);
}

export function classifyKnowledge(history: HistoryEntry[], form: ProposalRequest): KnowledgeGroups {
  const similar = buildSimilarCases(history, form).map((item) => item.entry);
  const success = history.filter((entry) => (entry.result.analysis.win_probability.probability ?? 0) >= 70).slice(0, 3);
  const lost = history.filter((entry) => (entry.result.analysis.win_probability.probability ?? 0) < 40).slice(0, 3);
  return { similar, success, lost };
}
