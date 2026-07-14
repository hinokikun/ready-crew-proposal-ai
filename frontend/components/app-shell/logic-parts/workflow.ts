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
  { label: "競合調査", detail: "競合、導線、SEO、CTA、コンテンツ量を比較する観点を作成", status: "waiting" },
  { label: "提案書作成", detail: "提案コンセプト、構成、初稿生成に進む準備", status: "waiting" },
  { label: "見積", detail: "ページ数、CMS、特殊機能、予算感から概算レンジを確認", status: "waiting" },
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
  "更新しやすくしたい",
  "SEOを強化したい"
];

export const budgetOptions = ["未定", "100万円未満", "100〜300万円", "300〜500万円", "500万円以上"];
export const deadlineOptions = ["未定", "1か月以内", "2〜3か月", "3か月以上"];
export const cmsOptions = ["未定", "WordPress", "Movable Type", "独自CMS", "不要"];

export const easySamples: Record<SampleKind, EasyInput> = {
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
  },
  seo: {
    projectType: "SEO改善・コンテンツ改善",
    trouble: "自然検索からの流入が伸びておらず、問い合わせにつながる検索キーワードやコンテンツ設計を見直したい。",
    budget: "100〜300万円",
    deadline: "2〜3か月",
    competitorSiteUrl: "https://seo-rival.example.jp",
    currentSiteUrl: "https://sample-seo.example.jp",
    cms: "WordPress",
    decisionMakers: "マーケティング責任者、営業責任者",
    purposes: ["SEOを強化したい", "問い合わせを増やしたい", "更新しやすくしたい"]
  }
};

export const chatQuestionFlow: ChatQuestion[] = [
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

export const initialChatMessages: ChatMessage[] = [
  {
    id: "assistant-initial",
    role: "assistant",
    text: "こんにちは。AI営業アシスタントです。会話だけで提案書の材料を整理します。まず、どんな案件ですか？"
  }
];

export const sourceTemplates: Record<SourceTemplateKind, string> = {
  readyCrew: `Ready Crew案件メールを貼る例：
株式会社サンプル不動産様よりWebサイトリニューアルの相談。
現行サイトが古く、スマホで物件情報を探しにくい。問い合わせ件数を増やしたい。
予算感は300万〜500万円。公開希望は10月末。
CMSはWordPress希望。お知らせ、実績、FAQを更新したい。
競合サイト：https://area-rival-realty.example.jp
既存サイト：https://sample-realty.example.jp
決裁者は代表取締役、窓口は営業企画部。初回提案では概算費用とスケジュールを知りたい。`,
  hearing: `ヒアリングメモを貼る例：
商談メモ
お客様：株式会社サンプル製作所、人事責任者様
相談内容：採用サイトを新しく作りたい。
課題：求人媒体に依存しており、自社の雰囲気や働く魅力が伝わっていない。応募数と応募者の質を改善したい。
目的：採用強化、会社の信頼感向上、更新しやすい採用情報の発信。
予算：100万〜300万円
納期：3か月以上で検討
CMS：WordPress希望
競合：採用競合企業のサイトを参考にしたい。`,
  slack: `Slack相談文を貼る例：
営業相談です。新サービスLP制作の引き合いがありました。
広告流入後の問い合わせ率を上げたいそうです。予算はまだざっくり100〜300万円くらい。
公開はできれば1か月以内。CMSは不要で、問い合わせフォームとCTAを重視。
競合LP：https://lp-rival.example.jp
  原稿作成も相談したいとのこと。`
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
