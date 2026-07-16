import type { EstimateLine } from "@/components/app-shell/types";

export type ProposalCategory = "ai_ocr" | "rpa" | "crm_sfa" | "web" | "generic";

export type FrontProposalProfile = {
  category: ProposalCategory;
  label: string;
  requirementLabel: string;
  structureLabel: string;
  winningStrategy: string;
  competitorNameFallback: string;
  competitorPoints: Array<{ label: string; point: string }>;
  estimatePageCount: number;
  estimateLines: EstimateLine[];
  positiveKeywords: string[];
  qualityHints: string[];
};

const webTerms = /Webサイト|サイトリニューアル|コーポレートサイト|ホームページ|LP|ランディングページ|CMS|SEO|WordPress|問い合わせフォーム|サイトマップ/i;

const profiles: Record<ProposalCategory, FrontProposalProfile> = {
  ai_ocr: {
    category: "ai_ocr",
    label: "AI-OCR提案",
    requirementLabel: "読取対象・連携要件",
    structureLabel: "導入構成",
    winningStrategy: "読取精度と運用定着で勝つ",
    competitorNameFallback: "比較対象サービス",
    competitorPoints: [
      { label: "読取精度", point: "帳票ごとの項目抽出精度と例外確認フローを明確化" },
      { label: "連携性", point: "CSV/API連携で既存システムへ安全に渡せる構成を提示" },
      { label: "運用負荷", point: "人手確認を残す箇所と自動化する箇所を分けて現場定着を重視" },
      { label: "改善体制", point: "PoC後に誤読パターンを分析し、精度改善を継続できる体制を示す" }
    ],
    estimatePageCount: 6,
    estimateLines: [
      { name: "AI-OCR PoC設計・検証", min: 80, max: 140, priority: "必須対応", enabled: true },
      { name: "帳票項目定義・サンプル整備", min: 40, max: 80, priority: "必須対応", enabled: true },
      { name: "AIモデル学習・精度改善", min: 90, max: 180, priority: "必須対応", enabled: true },
      { name: "API/CSV連携", min: 60, max: 120, priority: "推奨対応", enabled: true },
      { name: "例外確認フロー設計", min: 30, max: 70, priority: "推奨対応", enabled: true },
      { name: "運用支援・改善レポート", min: 30, max: 60, priority: "オプション対応", enabled: true }
    ],
    positiveKeywords: ["AI-OCR", "OCR", "帳票", "請求書", "読取", "項目抽出", "CSV", "API"],
    qualityHints: ["読取対象帳票", "抽出項目", "精度目標", "連携先", "例外確認フロー"]
  },
  rpa: {
    category: "rpa",
    label: "RPA・業務自動化提案",
    requirementLabel: "自動化対象業務",
    structureLabel: "自動化フロー",
    winningStrategy: "業務削減効果と例外処理で勝つ",
    competitorNameFallback: "比較対象ツール",
    competitorPoints: [
      { label: "自動化範囲", point: "繰り返し作業と人の判断が必要な作業を分けて整理" },
      { label: "例外処理", point: "エラー時の通知、手戻り、再実行ルールを明確化" },
      { label: "運用性", point: "担当者が保守できる手順書と監視方法を提案" },
      { label: "削減効果", point: "処理時間、作業件数、ミス削減を定量化" }
    ],
    estimatePageCount: 5,
    estimateLines: [
      { name: "業務棚卸し・自動化診断", min: 40, max: 80, priority: "必須対応", enabled: true },
      { name: "RPAシナリオ設計", min: 60, max: 110, priority: "必須対応", enabled: true },
      { name: "自動化実装・テスト", min: 100, max: 220, priority: "必須対応", enabled: true },
      { name: "例外処理・監視設計", min: 40, max: 90, priority: "推奨対応", enabled: true },
      { name: "運用マニュアル・教育", min: 30, max: 60, priority: "推奨対応", enabled: true }
    ],
    positiveKeywords: ["RPA", "自動化", "定型作業", "転記", "入力作業", "作業時間"],
    qualityHints: ["対象業務", "処理件数", "例外処理", "削減時間", "運用担当"]
  },
  crm_sfa: {
    category: "crm_sfa",
    label: "CRM/SFA導入提案",
    requirementLabel: "管理対象・運用要件",
    structureLabel: "運用設計",
    winningStrategy: "営業プロセス定着で勝つ",
    competitorNameFallback: "比較対象CRM",
    competitorPoints: [
      { label: "営業プロセス", point: "案件管理、活動履歴、商談ステージを標準化" },
      { label: "入力定着", point: "現場が入力しやすい項目と運用ルールを設計" },
      { label: "可視化", point: "受注率、停滞案件、レビュー状況を管理者が見られる状態にする" },
      { label: "連携性", point: "既存顧客データや外部ツールとの連携前提を整理" }
    ],
    estimatePageCount: 6,
    estimateLines: [
      { name: "要件整理・業務設計", min: 60, max: 120, priority: "必須対応", enabled: true },
      { name: "CRM/SFA初期設定", min: 80, max: 160, priority: "必須対応", enabled: true },
      { name: "データ移行・項目設計", min: 50, max: 110, priority: "推奨対応", enabled: true },
      { name: "レポート・ダッシュボード設計", min: 50, max: 100, priority: "推奨対応", enabled: true },
      { name: "定着支援・操作研修", min: 40, max: 80, priority: "オプション対応", enabled: true }
    ],
    positiveKeywords: ["CRM", "SFA", "案件管理", "営業管理", "顧客管理", "商談"],
    qualityHints: ["管理項目", "利用部門", "既存データ", "運用ルール", "定着方法"]
  },
  web: {
    category: "web",
    label: "Web制作提案",
    requirementLabel: "CMS・更新要件",
    structureLabel: "サイト構成",
    winningStrategy: "導線と訴求で勝つ",
    competitorNameFallback: "競合サイト",
    competitorPoints: [
      { label: "デザイン", point: "第一印象、信頼感、問い合わせ導線の見つけやすさを強化" },
      { label: "SEO", point: "検索流入を獲得するページ構造とキーワード設計で差別化" },
      { label: "導線設計", point: "比較検討から問い合わせまでのクリック数を減らし、CTAを明確化" },
      { label: "コンテンツ量", point: "サービス、実績、FAQ、導入事例を厚くして検討材料を増やす" },
      { label: "更新性", point: "公開後に情報鮮度を維持できる更新領域を設計" }
    ],
    estimatePageCount: 10,
    estimateLines: [],
    positiveKeywords: ["Webサイト", "CMS", "SEO", "問い合わせ", "リニューアル"],
    qualityHints: ["ページ数", "CMS", "SEO", "問い合わせ導線", "公開時期"]
  },
  generic: {
    category: "generic",
    label: "業務提案",
    requirementLabel: "導入要件",
    structureLabel: "導入構成",
    winningStrategy: "課題解決効果で勝つ",
    competitorNameFallback: "比較対象",
    competitorPoints: [
      { label: "課題適合", point: "入力された課題に対して提案範囲と効果を明確化" },
      { label: "導入しやすさ", point: "現場負荷、スケジュール、役割分担を整理" },
      { label: "効果測定", point: "導入後に確認するKPIと評価タイミングを設定" },
      { label: "運用性", point: "初期導入後も継続改善できる運用体制を示す" }
    ],
    estimatePageCount: 5,
    estimateLines: [
      { name: "要件整理・導入設計", min: 50, max: 100, priority: "必須対応", enabled: true },
      { name: "初期構築・設定", min: 80, max: 180, priority: "必須対応", enabled: true },
      { name: "検証・テスト", min: 40, max: 90, priority: "推奨対応", enabled: true },
      { name: "運用設計・マニュアル", min: 30, max: 70, priority: "推奨対応", enabled: true },
      { name: "定着支援", min: 30, max: 60, priority: "オプション対応", enabled: true }
    ],
    positiveKeywords: ["改善", "導入", "効率化", "削減", "標準化", "運用"],
    qualityHints: ["導入範囲", "成果指標", "運用体制", "スケジュール", "費用"]
  }
};

export function detectProposalCategory(text: string): ProposalCategory {
  if (/AI[-\s]?OCR|OCR|文書認識|帳票|請求書|領収書|納品書|注文書|スキャン|読み取り|読取|項目抽出/i.test(text)) {
    return "ai_ocr";
  }
  if (/RPA|ロボティック|自動化|定型作業|転記|入力作業|バッチ処理/i.test(text)) {
    return "rpa";
  }
  if (/CRM|SFA|顧客管理|案件管理|商談管理|営業管理|Salesforce|HubSpot/i.test(text)) {
    return "crm_sfa";
  }
  if (webTerms.test(text)) {
    return "web";
  }
  return "generic";
}

export function getProposalProfile(text: string): FrontProposalProfile {
  return profiles[detectProposalCategory(text)];
}

export function isWebProposalText(text: string): boolean {
  return detectProposalCategory(text) === "web";
}
