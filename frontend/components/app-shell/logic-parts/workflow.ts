import type {
  AiEmployeeRole,
  AutoFlowStatus,
  ChatMessage,
  ChatQuestion,
  DigitalAgentStep,
  EasyInput,
  GeneratedCounts,
  GuideStep,
  MinimalInput,
  RoleplayScenario,
  SampleKind,
  SourceTemplateKind,
  WorkMode
} from "@/components/app-shell/types";
import type { AnalysisResponse } from "@/types/proposal";

export function hashWorkspaceSeed(value: string) {
  let hash = 0;
  for (let index = 0; index < value.length; index += 1) {
    hash = (hash << 5) - hash + value.charCodeAt(index);
    hash |= 0;
  }
  return Math.abs(hash).toString(36);
}

export const MAX_ASSISTANT_QUESTIONS = 3;

export const wizardSteps: Array<{ step: GuideStep; title: string }> = [
  { step: 1, title: "案件メールを貼る" },
  { step: 2, title: "AIに全部おまかせ" },
  { step: 3, title: "内容確認" },
  { step: 4, title: "提案書作成" },
  { step: 5, title: "PPTダウンロード" }
];

export function buildWizardMessage(step: GuideStep) {
  switch (step) {
    case 1:
      return "案件メールを貼るだけで提案書を作成します。";
    case 2:
      return "次はこちら。AIに整理をまかせます。";
    case 3:
      return "確認してください。このまま作成できます。";
    case 4:
      return "提案書を作成しましょう。";
    case 5:
      return "完成しました。まず要約PPTを確認してください。";
    default:
      return "次に進めます。";
  }
}

export function buildAutoFlowMessage(status: AutoFlowStatus, result: AnalysisResponse | null, question?: ChatQuestion) {
  if (result) {
    return "完成しました。要約PPTをダウンロードできます。";
  }
  switch (status) {
    case "typing":
      return "案件内容を読み取っています。";
    case "analyzing":
      return "不足情報を確認しています。";
    case "question":
      return question ? `${question.label}だけ教えてください。` : "不足情報だけ確認します。";
    case "reviewing":
      return "提案書の骨子を作成しています。";
    case "generating":
      return "提案書と出力データを作成しています。";
    case "complete":
      return "ダウンロード準備ができました。";
    default:
      return "案件メールを貼ってください。";
  }
}

export const operationGuideSteps: Array<{ step: GuideStep; title: string }> = [
  { step: 1, title: "案件メール・議事録・URLを貼る" },
  { step: 2, title: "「AIに全部おまかせ」を押す" },
  { step: 3, title: "整理結果を確認する" },
  { step: 4, title: "「提案書を作成」を押す" },
  { step: 5, title: "PPTX / PDFをダウンロードする" }
];

export const workModeTabs: Array<{ key: WorkMode; label: string; note: string }> = [
  { key: "sales", label: "営業提案AI", note: "提案書・見積・資料出力" },
  { key: "coach", label: "商談コーチAI", note: "商談前後の支援" },
  { key: "minutes", label: "議事録AI", note: "決定事項とToDo整理" },
  { key: "mail", label: "メール作成AI", note: "件名・本文・返信案" },
  { key: "tasks", label: "タスク整理AI", note: "優先度と期限整理" },
  { key: "faq", label: "社内FAQ AI", note: "回答案と確認先" },
  { key: "summary", label: "資料要約AI", note: "要点とリスク抽出" },
  { key: "reports", label: "日報/週報AI", note: "報告文を作成" }
];

export const workModeGroups: Array<{ category: string; modes: WorkMode[] }> = [
  { category: "提案作成", modes: ["sales"] },
  { category: "商談支援", modes: ["coach", "reports"] },
  { category: "社内業務", modes: ["minutes", "mail", "tasks", "faq", "summary"] }
];

export const workModeMap = new Map(workModeTabs.map((mode) => [mode.key, mode]));

export const aiEmployeeRoles: Array<{ key: AiEmployeeRole; label: string; mission: string }> = [
  { key: "secretary", label: "AI秘書", mission: "予定、確認事項、送付メールを整える" },
  { key: "sales", label: "AI営業", mission: "受注確率と提案ストーリーを強化する" },
  { key: "director", label: "AIディレクター", mission: "要件、体制、進行リスクを整理する" },
  { key: "writer", label: "AIライター", mission: "訴求、原稿、メール文を磨く" },
  { key: "designer", label: "AIデザイナー", mission: "見せ方、導線、資料品質を改善する" },
  { key: "pm", label: "AI PM", mission: "見積、スケジュール、タスクを管理する" }
];

export const mcpConnectorCards = [
  "Google Drive",
  "GitHub",
  "Notion",
  "Slack",
  "Teams",
  "Google Calendar",
  "Gmail",
  "Outlook",
  "OneDrive",
  "Salesforce",
  "HubSpot",
  "kintone"
];

export const initialAgentSteps: DigitalAgentStep[] = [
  { label: "会社調査", detail: "会社URLと案件情報から概要・採用・ニュース・SNS確認観点を整理", status: "waiting" },
  { label: "競合調査", detail: "比較対象、導入効果、運用性、成果指標を整理", status: "waiting" },
  { label: "提案書作成", detail: "提案コンセプト、構成、初稿生成に進む準備", status: "waiting" },
  { label: "見積", detail: "導入範囲、連携、検証、運用支援から概算レンジを確認", status: "waiting" },
  { label: "メール", detail: "提案書送付や次回確認依頼のメール文を準備", status: "waiting" }
];

export const initialModeCounts: GeneratedCounts = {
  sales: 0,
  coach: 0,
  minutes: 0,
  mail: 0,
  tasks: 0,
  faq: 0,
  summary: 0,
  reports: 0
};

export const initialEasyInput: EasyInput = {
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

export const initialMinimalInput: MinimalInput = {
  companyName: "",
  goal: "",
  trouble: ""
};

export const purposeOptions = [
  "問い合わせを増やしたい",
  "採用を強化したい",
  "会社の信頼感を上げたい",
  "業務を効率化したい",
  "精度や品質を上げたい",
  "運用しやすくしたい",
  "検索・集客を強化したい"
];

export const budgetOptions = ["未定", "100万円未満", "100〜300万円", "300〜500万円", "500万円以上"];
export const deadlineOptions = ["未定", "1か月以内", "2〜3か月", "3か月以上"];
export const cmsOptions = ["未定", "AI-OCR", "API/CSV連携", "RPA", "CRM/SFA", "Web/CMS", "不要"];

export const easySamples: Record<SampleKind, EasyInput> = {
  renewal: {
    projectType: "AI-OCRによる請求書読み取り自動化",
    trouble: "請求書の確認と会計システムへの転記に時間がかかり、入力ミスも発生している。会社名、日付、金額、請求書番号を抽出したい。",
    budget: "300〜500万円",
    deadline: "2〜3か月",
    competitorSiteUrl: "比較対象：AI-OCRクラウドサービス",
    currentSiteUrl: "請求書PDF、CSV出力、会計システム",
    cms: "AI-OCR",
    decisionMakers: "経理責任者、情報システム部",
    purposes: ["業務を効率化したい", "精度や品質を上げたい", "運用しやすくしたい"]
  },
  recruit: {
    projectType: "RPAによる定型入力作業の自動化",
    trouble: "毎日同じ内容を複数システムへ転記しており、作業時間と確認漏れが増えている。",
    budget: "100〜300万円",
    deadline: "3か月以上",
    competitorSiteUrl: "比較対象：既存RPAツール",
    currentSiteUrl: "受注管理システム、Excel台帳",
    cms: "RPA",
    decisionMakers: "業務部長、情報システム部",
    purposes: ["業務を効率化したい", "運用しやすくしたい"]
  },
  lp: {
    projectType: "CRM/SFA導入による案件管理の標準化",
    trouble: "営業ごとに案件管理方法が異なり、進捗、失注理由、次アクションが見えにくい。",
    budget: "100〜300万円",
    deadline: "1か月以内",
    competitorSiteUrl: "比較対象：既存CRM/SFA",
    currentSiteUrl: "Excel案件台帳、顧客リスト",
    cms: "CRM/SFA",
    decisionMakers: "営業責任者、管理部",
    purposes: ["業務を効率化したい", "運用しやすくしたい"]
  },
  seo: {
    projectType: "コーポレートサイト改善",
    trouble: "サービス内容が伝わりにくく、問い合わせにつながる導線と更新体制を見直したい。",
    budget: "100〜300万円",
    deadline: "2〜3か月",
    competitorSiteUrl: "https://web-rival.example.jp",
    currentSiteUrl: "https://sample-web.example.jp",
    cms: "Web/CMS",
    decisionMakers: "マーケティング責任者、営業責任者",
    purposes: ["検索・集客を強化したい", "問い合わせを増やしたい", "運用しやすくしたい"]
  }
};

export const chatQuestionFlow: ChatQuestion[] = [
  {
    key: "project",
    label: "案件内容",
    question: "どんな案件ですか？例：AI-OCR、RPA、CRM導入、Web改善など",
    placeholder: "例：請求書をAI-OCRで読み取り、会計システムへ連携したい案件です"
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
    question: "お客様は何に困っていますか？作業時間、入力ミス、管理方法、問い合わせなど、営業で聞いた内容をそのまま書いてください。",
    placeholder: "例：帳票確認と転記に時間がかかり、入力ミスもあります"
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
    question: "比較されそうな会社・サービス・URLはありますか？分からなければ未確認で大丈夫です。",
    placeholder: "例：既存OCRサービス、または競合未確認"
  }
];

export const initialChatMessages: ChatMessage[] = [
  {
    id: "assistant-initial",
    role: "assistant",
    text: "こんにちは。AI営業アシスタントです。会話だけで提案書の材料を整理します。まず、どんな案件ですか？"
  }
];

export const sourceTemplates: Record<SourceTemplateKind, string> = {
  readyCrew: `Ready Crew案件メールを貼る例：
株式会社サンプル経理様よりAI-OCR導入の相談。
請求書PDFを読み取り、会社名、日付、金額、請求書番号を抽出したい。
予算感は300万〜500万円。PoCは2〜3か月で検討。
CSVまたは会計システムAPIへ連携したい。
比較対象：AI-OCRクラウドサービス
決裁者は管理部長、窓口は経理責任者。初回提案では概算費用とスケジュールを知りたい。`,
  hearing: `ヒアリングメモを貼る例：
商談メモ
お客様：株式会社サンプル物流、業務部長様
相談内容：RPAで定型入力作業を自動化したい。
課題：受注情報をExcelと基幹システムへ二重入力しており、作業時間と確認漏れが増えている。
目的：業務効率化、入力ミス削減、例外処理の標準化。
予算：100万〜300万円
納期：3か月以上で検討
導入要件：RPA、監視、運用マニュアル
競合：既存RPAツールと比較したい。`,
  slack: `Slack相談文を貼る例：
営業相談です。CRM/SFA導入の引き合いがありました。
案件ステータスや次アクションが営業担当ごとにばらばらで、管理者が進捗を見にくいそうです。
予算はまだざっくり100〜300万円くらい。1か月以内に初期設計を始めたい。
既存のExcel案件台帳から移行したいとのこと。`
};

export const roleplayScenarios: Record<RoleplayScenario, { label: string; customer: string; firstMessage: string }> = {
  renewal: {
    label: "Webリニューアル案件",
    customer: "不動産会社の営業企画部長",
    firstMessage: "現行サイトが古いのは分かっていますが、どこから直すべきか判断できていません。費用対効果も気になります。"
  },
  recruit: {
    label: "採用サイト案件",
    customer: "採用責任者",
    firstMessage: "応募数も応募者の質も課題です。ただ、採用サイトにどこまで投資すべきか社内で迷っています。"
  },
  lp: {
    label: "LP制作案件",
    customer: "マーケティング責任者",
    firstMessage: "広告流入はありますが、問い合わせにつながりません。短期間で改善したいです。"
  },
  branding: {
    label: "ブランディング案件",
    customer: "代表取締役",
    firstMessage: "会社の強みが伝わっていない気がします。競合と比べて選ばれる理由を明確にしたいです。"
  }
};
