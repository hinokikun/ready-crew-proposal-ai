from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class EstimateLineTemplate:
    name: str
    min: int
    max: int
    priority: str
    optional: bool = False


@dataclass(frozen=True)
class ProposalProfile:
    category: str
    label: str
    deck_suffix: str
    concept: str
    summary: str
    sections: list[str]
    needs: list[str]
    services: list[str]
    journey: list[str]
    structure_items: list[str]
    kpis: list[str]
    competitor_axes: list[str]
    winning_strategy: str
    targets: list[str]
    content_items: list[str]
    strategy_items: list[str]
    estimate_lines: list[EstimateLineTemplate]
    confirmations: list[str]
    quality_items: list[str]
    schedule: list[str]
    team: list[str]
    cost_points: list[str]


@dataclass(frozen=True)
class ProjectSpecifics:
    facts: list[str]
    needs: list[str]
    services: list[str]
    journey: list[str]
    structure_items: list[str]
    kpis: list[str]
    targets: list[str]
    content_items: list[str]
    strategy_items: list[str]
    estimate_lines: list[EstimateLineTemplate]
    confirmations: list[str]
    quality_items: list[str]
    schedule: list[str]
    team: list[str]
    cost_points: list[str]
    scope_label: str
    premise_items: list[str]
    notes: list[str]


COMMON_SECTIONS = [
    "表紙",
    "提案サマリー",
    "現状理解",
    "想定される課題",
    "市場・競合分析",
    "競合比較分析",
    "ターゲット分析",
    "業務フロー",
    "導入戦略",
    "導入構成",
    "施策設計",
    "KPI設計",
    "実行方針",
    "スケジュール",
    "体制",
    "費用概算",
    "概算見積",
    "予算適合判定",
    "必須・推奨・オプション対応",
    "今後の進め方",
]

WEB_SECTIONS = [
    "表紙",
    "提案サマリー",
    "現状理解",
    "想定される課題",
    "市場・競合分析",
    "競合比較分析",
    "ターゲットユーザー分析",
    "カスタマージャーニー",
    "Web戦略",
    "サイトマップ",
    "コンテンツ設計",
    "KPI設計",
    "制作方針",
    "スケジュール",
    "体制",
    "費用概算",
    "概算見積",
    "予算適合判定",
    "必須・推奨・オプション対応",
    "今後の進め方",
]


def _lines(*items: tuple[str, int, int, str] | tuple[str, int, int, str, bool]) -> list[EstimateLineTemplate]:
    return [
        EstimateLineTemplate(
            name=item[0],
            min=item[1],
            max=item[2],
            priority=item[3],
            optional=bool(item[4]) if len(item) > 4 else False,
        )
        for item in items
    ]


PROFILES: dict[str, ProposalProfile] = {
    "ai_ocr": ProposalProfile(
        category="ai_ocr",
        label="AI-OCR",
        deck_suffix="AI-OCR導入支援ご提案書",
        concept="AI-OCR業務自動化",
        summary="帳票読み取り、項目抽出、業務システム連携、運用改善を段階的に進める提案です。",
        sections=COMMON_SECTIONS,
        needs=["帳票読み取り精度の向上", "項目抽出ルールの整理", "CSV/API連携による入力作業削減", "例外処理と人手確認フローの設計"],
        services=["AI-OCR PoC設計", "帳票項目定義", "AIモデル学習・精度改善", "API/CSV連携", "運用定着支援"],
        journey=["受付: 紙・PDF・画像を安全に取り込む", "抽出: 必要項目をAI-OCRで読み取る", "確認: 例外だけを人が確認する", "連携: 会計・基幹システムへ渡す"],
        structure_items=["対象帳票", "入力経路", "抽出項目", "確認画面", "CSV/API連携", "例外処理", "運用レポート"],
        kpis=["読取精度: 95%以上を目標", "手入力削減: 50%以上", "処理時間: 1件あたり半減", "例外率: 継続改善で低減"],
        competitor_axes=["読取精度", "帳票対応力", "連携容易性", "運用負荷", "セキュリティ", "改善支援"],
        winning_strategy="精度改善と運用定着で勝つ",
        targets=["主要ターゲット: 経理・事務・業務部門", "ニーズ: 手入力と確認作業を減らしたい", "不安: 読取精度と例外対応", "必要情報: 対象帳票、抽出項目、連携先、運用体制"],
        content_items=["対象帳票定義: 請求書・注文書などの範囲を整理", "項目抽出設計: 会社名、日付、金額、番号を定義", "例外処理: 読取不可時の確認フローを設計", "連携設計: CSV/APIで既存業務へ接続"],
        strategy_items=["PoC: 代表帳票で精度を検証", "学習: 誤読傾向を改善", "連携: CSV/API出力を設計", "運用: 例外確認と改善サイクルを定着"],
        estimate_lines=_lines(
            ("PoC設計・検証", 60, 120, "必須対応"),
            ("帳票項目定義", 40, 80, "必須対応"),
            ("AIモデル学習・精度改善", 80, 180, "推奨対応"),
            ("API/CSV連携", 70, 160, "必須対応"),
            ("例外確認フロー設計", 40, 90, "推奨対応"),
            ("運用支援・改善レポート", 20, 50, "オプション対応", True),
        ),
        confirmations=["対象帳票の種類と件数", "抽出項目と正解データ", "連携先システムと形式", "精度目標と例外処理", "運用担当と確認頻度"],
        quality_items=["対象帳票と抽出項目が正しい", "読取精度目標を確認した", "連携先と出力形式を確認した", "例外処理と人手確認フローを確認した", "個人情報・機密情報の扱いを確認した", "PoC範囲と本導入条件を確認した"],
        schedule=["PoC要件整理", "帳票収集・項目定義", "精度検証・改善", "連携・運用設計"],
        team=["PM/業務設計", "AI-OCRエンジニア", "連携エンジニア", "運用定着支援"],
        cost_points=["PoC範囲を先に確定", "帳票種類と件数で調整", "AI学習と連携は段階化", "運用支援は必要に応じて追加"],
    ),
    "rpa": ProposalProfile(
        category="rpa",
        label="RPA",
        deck_suffix="RPA業務自動化ご提案書",
        concept="定型業務自動化",
        summary="繰り返し作業を棚卸しし、RPAで安全に自動化する提案です。",
        sections=COMMON_SECTIONS,
        needs=["定型作業の削減", "入力ミスの低減", "業務手順の標準化", "例外処理の整理"],
        services=["業務棚卸し", "RPAシナリオ設計", "ロボット実装", "運用監視", "改善支援"],
        journey=["受付: 対象業務を洗い出す", "設計: 手順と例外を整理する", "実行: ロボットで処理する", "改善: 失敗ログから改善する"],
        structure_items=["対象業務", "入力データ", "処理手順", "例外条件", "監視方法", "運用担当"],
        kpis=["削減時間: 月間工数を削減", "処理成功率: 95%以上", "入力ミス: 大幅削減", "運用停止時間: 最小化"],
        competitor_axes=["自動化範囲", "保守性", "例外対応", "導入速度", "運用負荷", "費用対効果"],
        winning_strategy="業務標準化と運用保守で勝つ",
        targets=["主要ターゲット: 業務部門・バックオフィス", "ニーズ: 繰り返し作業を減らしたい", "不安: 例外発生時の対応", "必要情報: 対象業務、頻度、利用システム、承認フロー"],
        content_items=["業務棚卸し: 自動化対象を優先順位化", "シナリオ設計: 手順と例外を可視化", "実装: ロボット処理を構築", "運用監視: 成功率と失敗要因を確認"],
        strategy_items=["対象選定", "シナリオ設計", "小規模導入", "運用改善"],
        estimate_lines=_lines(("業務棚卸し", 40, 80, "必須対応"), ("RPAシナリオ設計", 50, 110, "必須対応"), ("ロボット実装", 80, 180, "必須対応"), ("テスト・運用設計", 40, 90, "推奨対応"), ("保守運用", 20, 50, "オプション対応", True)),
        confirmations=["対象業務と頻度", "利用システムと権限", "例外処理", "運用担当", "効果測定方法"],
        quality_items=["対象業務と手順を確認した", "例外処理を確認した", "利用システムの権限を確認した", "停止時の対応を確認した", "効果測定方法を確認した"],
        schedule=["業務棚卸し", "シナリオ設計", "実装・テスト", "運用開始・改善"],
        team=["業務設計", "RPAエンジニア", "テスト担当", "運用支援"],
        cost_points=["対象業務数で調整", "例外処理は段階化", "保守運用は月次範囲で検討", "スモールスタートを優先"],
    ),
    "crm_sfa": ProposalProfile(
        category="crm_sfa",
        label="CRM/SFA",
        deck_suffix="CRM/SFA導入ご提案書",
        concept="営業情報の一元管理",
        summary="顧客情報、商談、活動履歴を統合し、営業管理を標準化する提案です。",
        sections=COMMON_SECTIONS,
        needs=["顧客情報の一元管理", "商談状況の可視化", "営業活動の標準化", "レポート運用の整備"],
        services=["要件整理", "CRM/SFA設計", "データ移行", "ダッシュボード設計", "定着支援"],
        journey=["登録: 顧客・商談を記録", "活動: 接点とタスクを管理", "分析: Pipelineを可視化", "改善: 営業プロセスを見直す"],
        structure_items=["顧客マスタ", "商談管理", "活動履歴", "タスク管理", "レポート", "権限設計", "運用ルール"],
        kpis=["入力定着率: 90%以上", "商談更新率: 週次更新", "案件停滞検知: 早期化", "受注率: 継続改善"],
        competitor_axes=["入力しやすさ", "商談可視化", "分析機能", "連携性", "定着支援", "権限管理"],
        winning_strategy="定着支援と営業可視化で勝つ",
        targets=["主要ターゲット: 営業担当・営業管理者", "ニーズ: 商談と活動を見える化したい", "不安: 入力負荷と定着率", "必要情報: 既存管理方法、項目、権限、レポート"],
        content_items=["項目設計: 顧客・商談・活動項目を定義", "Pipeline設計: ステージと停滞条件を整理", "レポート: 受注率や活動量を可視化", "定着支援: 入力ルールとレビューを設計"],
        strategy_items=["現状棚卸し", "項目・権限設計", "移行・初期設定", "運用定着"],
        estimate_lines=_lines(("要件整理・設計", 50, 100, "必須対応"), ("CRM/SFA初期設定", 80, 180, "必須対応"), ("データ移行", 50, 140, "推奨対応"), ("ダッシュボード設計", 50, 120, "推奨対応"), ("定着支援", 20, 60, "オプション対応", True)),
        confirmations=["既存顧客データ", "必要管理項目", "権限と承認フロー", "レポート指標", "運用責任者"],
        quality_items=["顧客・商談項目を確認した", "権限設計を確認した", "データ移行範囲を確認した", "レポート指標を確認した", "運用定着方法を確認した"],
        schedule=["現状棚卸し", "項目・権限設計", "設定・移行", "運用開始・定着"],
        team=["PM/業務設計", "CRM設定担当", "データ移行担当", "定着支援"],
        cost_points=["管理項目数で調整", "移行範囲を段階化", "レポートは優先順位化", "定着支援は月次で検討"],
    ),
    "web": ProposalProfile(
        category="web",
        label="Web制作",
        deck_suffix="Webサイト制作ご提案書",
        concept="Web成果最大化",
        summary="Webサイトの成果改善に向け、情報設計、導線、運用を整理する提案です。",
        sections=WEB_SECTIONS,
        needs=["Webサイトの役割整理", "成果につながる導線設計", "公開後の改善方針整理"],
        services=["情報設計", "Webサイト制作", "公開後の改善運用支援"],
        journey=["認知: SEO・広告・紹介からの受け皿を整える", "比較検討: サービス内容・実績・FAQで不安を減らす", "問い合わせ: CTAとフォーム導線を最短化する"],
        structure_items=["トップ", "会社案内", "サービス", "実績", "お知らせ", "FAQ", "お問い合わせ"],
        kpis=["問い合わせ数: 月12件", "CV率: 2.0%", "自然検索流入: 月2500セッション", "資料DL数: 月15件"],
        competitor_axes=["デザイン", "SEO", "導線設計", "コンテンツ量", "更新性", "CTA"],
        winning_strategy="実績訴求とCTA改善で勝つ",
        targets=["主要ターゲット: サービス比較中の見込み顧客", "ニーズ: 強み、実績、費用感を短時間で把握したい", "不安: 自社に合うか、依頼後の進め方が分かりにくい", "必要コンテンツ: サービス、実績、FAQ、問い合わせ"],
        content_items=["サービス詳細: 強み、対象課題、提供範囲を明確化", "実績・事例: 比較検討を後押し", "FAQ: 費用、納期、運用の不安を解消", "お問い合わせ: CTAとフォーム項目を最短化"],
        strategy_items=["集客: SEO・広告・紹介流入の受け皿を整備", "比較検討: サービス、実績、FAQで判断材料を提供", "問い合わせ: CTAとフォーム導線を短く設計", "運用改善: CMS更新とアクセス解析で継続改善"],
        estimate_lines=_lines(("要件整理・ディレクション", 30, 50, "必須対応"), ("情報設計・ワイヤーフレーム", 35, 65, "必須対応"), ("デザイン制作", 70, 130, "必須対応"), ("フロントエンド実装", 90, 150, "必須対応"), ("CMS構築", 50, 90, "推奨対応", True), ("SEO初期設計", 20, 40, "推奨対応", True), ("運用保守", 10, 20, "オプション対応", True)),
        confirmations=["予算感・上限・見積粒度", "希望公開時期・社内確認フロー", "CMS要否・更新担当・更新頻度", "SEO対象キーワード・既存流入状況", "公開後の運用保守範囲"],
        quality_items=["会社名・担当者名に誤りがない", "金額・見積条件を確認した", "納期・スケジュールを確認した", "CMS/SEO/フォーム要件を確認した", "社外提出前に人間が最終確認した"],
        schedule=["要件整理", "情報設計・ワイヤーフレーム", "デザイン・実装", "公開・運用改善"],
        team=["PM/ディレクター", "デザイナー", "エンジニア", "運用・改善支援"],
        cost_points=["予算に合わせて必須範囲を優先", "ページ数・コンテンツ量で調整", "CMS・フォーム・SEOは要件に応じて別枠化", "運用保守・改善支援は月次範囲で検討"],
    ),
}


def _generic_profile(category: str = "other", label: str = "業務提案") -> ProposalProfile:
    return ProposalProfile(
        category=category,
        label=label,
        deck_suffix=f"{label}ご提案書",
        concept=f"{label}による業務改善",
        summary="案件内容に合わせて、課題、導入方針、効果測定、運用定着を整理する提案です。",
        sections=COMMON_SECTIONS,
        needs=["目的と課題の整理", "導入範囲の明確化", "効果測定方法の整理", "運用体制の設計"],
        services=["要件整理", "導入設計", "実装・連携", "運用支援"],
        journey=["現状把握: 課題と業務範囲を整理", "設計: 解決策と実行手順を決める", "導入: 小さく検証して拡張", "定着: 効果測定と改善を続ける"],
        structure_items=["対象業務", "課題", "導入範囲", "連携先", "運用体制", "効果測定"],
        kpis=["業務時間削減", "処理品質向上", "運用定着率", "改善サイクル継続"],
        competitor_axes=["課題適合度", "導入速度", "運用しやすさ", "拡張性", "費用対効果", "支援体制"],
        winning_strategy="課題適合と運用定着で勝つ",
        targets=["主要ターゲット: 業務改善を担う担当者", "ニーズ: 課題に合う解決策と費用感を知りたい", "不安: 導入後の運用負荷と効果", "必要情報: 対象業務、制約、予算、運用体制"],
        content_items=["課題整理: 現状と改善テーマを明確化", "導入範囲: 対象業務と優先順位を整理", "効果測定: KPIと確認方法を定義", "運用設計: 定着に必要な役割を整理"],
        strategy_items=["現状整理", "導入設計", "小規模検証", "運用改善"],
        estimate_lines=_lines(("要件整理", 40, 80, "必須対応"), ("導入設計", 50, 120, "必須対応"), ("実装・連携", 80, 180, "必須対応"), ("テスト・検証", 40, 90, "推奨対応"), ("運用支援", 20, 60, "オプション対応", True)),
        confirmations=["対象業務と範囲", "期待効果とKPI", "連携先と制約", "運用担当", "予算とスケジュール"],
        quality_items=["案件目的を確認した", "導入範囲を確認した", "見積条件を確認した", "スケジュールを確認した", "運用体制を確認した", "AI推測の項目を確認した"],
        schedule=["要件整理", "設計・計画", "実装・検証", "運用開始・改善"],
        team=["PM/業務設計", "実装担当", "連携担当", "運用支援"],
        cost_points=["必須範囲を優先", "連携範囲で調整", "検証後に拡張", "運用支援は必要に応じて追加"],
    )


GENERIC_LABELS = {
    "image_recognition": "画像認識",
    "ai_agent": "AIエージェント",
    "erp": "ERP",
    "generative_ai": "生成AI",
    "recruiting": "採用支援",
    "logistics": "物流改善",
    "manufacturing": "製造業務改善",
    "education": "教育支援",
    "medical": "医療業務支援",
    "retail": "小売業務改善",
    "other": "業務改善",
}


CATEGORY_KEYWORDS = {
    "ai_ocr": ["AI-OCR", "AIOCR", "OCR", "文書認識", "帳票", "請求書", "納品書", "注文書", "申込書", "スキャン", "読み取り", "読取", "項目抽出", "会計システム"],
    "image_recognition": ["画像認識", "画像解析", "物体検出", "カメラ", "外観検査", "検品"],
    "ai_agent": ["AIエージェント", "エージェント", "自律", "チャットボット", "問い合わせ自動応答"],
    "rpa": ["RPA", "定型業務", "ロボット", "入力作業", "自動化"],
    "erp": ["ERP", "基幹", "会計", "販売管理", "在庫管理", "生産管理"],
    "crm_sfa": ["CRM", "SFA", "顧客管理", "商談管理", "営業管理", "Salesforce", "HubSpot"],
    "generative_ai": ["生成AI", "ChatGPT", "LLM", "ナレッジ検索", "要約AI"],
    "web": ["Webサイト", "サイトリニューアル", "コーポレートサイト", "ホームページ", "LP", "CMS", "SEO", "WordPress", "問い合わせフォーム"],
    "recruiting": ["採用", "求人", "応募", "採用サイト", "求職"],
    "logistics": ["物流", "配送", "倉庫", "在庫", "配車"],
    "manufacturing": ["製造", "工場", "設備", "保全", "検査"],
    "education": ["教育", "研修", "学習", "授業", "学校"],
    "medical": ["医療", "病院", "クリニック", "診療", "介護"],
    "retail": ["小売", "店舗", "EC", "POS", "販売"],
}


PROFILES["image_recognition"] = ProposalProfile(
    category="image_recognition",
    label="画像認識",
    deck_suffix="画像認識AI提案書",
    concept="画像認識による業務判定支援",
    summary="商品画像や現場画像から必要な判定項目を抽出し、人の確認と既存システム連携を前提に段階導入する提案です。",
    sections=COMMON_SECTIONS,
    needs=["対象画像と判定対象の整理", "学習データと評価基準の整備", "人による確認フローの設計", "既存システムとのAPI/CSV連携"],
    services=["PoC設計", "画像データ調査", "学習データ準備", "画像認識モデル開発", "精度評価・チューニング", "API/CSV連携", "人手確認画面", "本番導入・再学習支援"],
    journey=["画像受付: 商品画像を対象業務から取り込む", "AI判定: 種類・色・等級・状態などの判定候補を提示する", "人手確認: 担当者が誤判定を確認し補正する", "連携: 商品管理システムへAPIまたはCSVで反映する"],
    structure_items=["対象画像", "判定カテゴリ", "学習データ", "画像認識モデル", "人手確認フロー", "API/CSV連携", "商品管理システム", "運用・再学習"],
    kpis=["認識精度", "誤判定率", "人手確認時間", "商品登録処理時間"],
    competitor_axes=["認識精度", "学習データ設計", "人手確認フロー", "既存システム連携", "運用・再学習", "セキュリティ"],
    winning_strategy="対象画像・判定カテゴリ・人手確認・既存連携を一体で設計して勝つ",
    targets=["主な対象: 商品画像を扱う業務担当者", "ニーズ: 画像から判定項目を速く正確に整理したい", "不安: 誤判定時の確認方法と精度改善の継続性", "必要情報: 対象画像、判定カテゴリ、学習データ、連携先、運用体制"],
    content_items=["対象画像定義: 商品画像と商品データの対応関係を整理", "判定カテゴリ設計: 種類・色・等級・状態などを定義", "人手確認設計: AI判定結果を担当者が確認できる流れを設計", "連携設計: APIまたはCSVで商品管理システムへ渡す"],
    strategy_items=["PoC: 代表画像と判定カテゴリで認識精度を検証", "学習データ: アノテーション基準と件数を整理", "連携: API/CSV出力を段階的に設計", "運用: 誤判定の蓄積と再学習で改善する"],
    estimate_lines=_lines(
        ("業務・要件整理", 60, 100, "必須対応"),
        ("PoC設計", 80, 140, "必須対応"),
        ("画像データ調査", 50, 100, "必須対応"),
        ("アノテーション設計", 60, 120, "必須対応"),
        ("学習データ準備", 80, 160, "必須対応"),
        ("画像認識モデル開発", 160, 280, "必須対応"),
        ("精度評価・チューニング", 80, 160, "必須対応"),
        ("推論APIまたはバッチ処理", 80, 160, "推奨対応"),
        ("API/CSV連携", 70, 140, "推奨対応"),
        ("人手確認画面", 80, 160, "推奨対応"),
        ("総合テスト・受入支援", 50, 100, "推奨対応"),
        ("本番導入", 80, 140, "オプション対応", True),
        ("運用監視", 30, 80, "オプション対応", True),
        ("再学習支援", 40, 100, "オプション対応", True),
    ),
    confirmations=["対象画像の種類と件数", "判定カテゴリと正解データ", "学習データの準備状況", "目標認識精度と評価方法", "人手確認フロー", "商品管理システムとの連携方式", "PoC範囲と本番範囲"],
    quality_items=["対象画像と判定カテゴリを確認した", "学習データとアノテーション方針を確認した", "目標認識精度と評価方法を確認した", "人による確認フローを確認した", "API/CSV連携先を確認した", "PoC範囲と本番導入条件を確認した"],
    schedule=["業務・要件整理", "画像データ調査・PoC設計", "学習データ準備・モデル検証", "精度評価・連携設計", "本番導入・運用改善"],
    team=["PM/業務設計", "画像認識エンジニア", "データ整備・アノテーション担当", "連携エンジニア", "運用支援"],
    cost_points=["PoC範囲を先に確定", "対象画像数と判定カテゴリ数で調整", "学習データ準備と精度評価を必須化", "API/CSV連携と人手確認画面は段階提案"],
)

CATEGORY_KEYWORDS["image_recognition"].extend(
    [
        "AI画像認識",
        "画像認識",
        "画像判定",
        "画像分類",
        "商品画像",
        "商品データ",
        "生花",
        "オークション",
        "花の種類",
        "等級",
        "状態",
        "色",
        "認識精度",
        "アノテーション",
    ]
)


def detect_proposal_category(text: str) -> str:
    normalized = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword.lower() in normalized for keyword in keywords):
            return category
    return "other"


def get_proposal_profile(category: str) -> ProposalProfile:
    if category in PROFILES:
        return PROFILES[category]
    return _generic_profile(category, GENERIC_LABELS.get(category, "業務改善"))


def proposal_profile_for_text(text: str) -> ProposalProfile:
    return get_proposal_profile(detect_proposal_category(text))


def extract_project_specifics(text: str, profile: ProposalProfile | None = None) -> ProjectSpecifics:
    profile = profile or proposal_profile_for_text(text)
    if profile.category == "image_recognition":
        return _extract_image_recognition_specifics(text, profile)
    return ProjectSpecifics(
        facts=[],
        needs=profile.needs[:4],
        services=profile.services[:6],
        journey=profile.journey[:4],
        structure_items=profile.structure_items[:8],
        kpis=profile.kpis[:4],
        targets=profile.targets[:4],
        content_items=profile.content_items[:4],
        strategy_items=profile.strategy_items[:4],
        estimate_lines=profile.estimate_lines,
        confirmations=profile.confirmations[:6],
        quality_items=profile.quality_items[:6],
        schedule=profile.schedule[:5],
        team=profile.team[:5],
        cost_points=profile.cost_points[:4],
        scope_label=f"対象範囲: {profile.label}導入範囲",
        premise_items=profile.confirmations[:5],
        notes=["外部サービス利用料、追加開発、運用支援は要件確定後に調整します。"],
    )


def _extract_image_recognition_specifics(text: str, profile: ProposalProfile) -> ProjectSpecifics:
    compact = re.sub(r"\s+", "", text)
    targets = _collect_present(
        text,
        [
            ("花の種類", ["花の種類", "種類"]),
            ("色", ["色"]),
            ("等級", ["等級", "グレード"]),
            ("状態", ["状態", "品質状態"]),
        ],
    )
    facts = _unique_texts(
        [
            "対象業務: 生花オークション" if _contains_any_text(text, ["生花", "オークション"]) else "",
            "対象画像: 商品画像" if _contains_any_text(text, ["商品画像", "画像"]) else "",
            f"認識対象: {'・'.join(targets)}" if targets else "",
            "現行作業: 商品画像と商品データの対応確認・品質チェック・カテゴリ分類を人手で実施" if _contains_any_text(text, ["商品データ", "品質チェック", "カテゴリ分類", "人手", "人による確認"]) else "",
            "確認フロー: AI判定結果を人による確認で補正" if _contains_any_text(text, ["人による確認", "人手", "確認"]) else "",
            "連携先: 商品管理システム" if "商品管理システム" in text else "",
            "連携方式: APIまたはCSV" if _contains_any_text(text, ["API", "CSV"]) else "",
            "導入方式: PoC後に本番導入" if _contains_any_text(text, ["PoC", "本番"]) else "",
            "学習データ: 準備・整備が必要" if _contains_any_text(text, ["学習データ", "教師データ", "アノテーション"]) else "",
            "評価指標: 認識精度" if _contains_any_text(text, ["認識精度", "精度"]) else "",
            _budget_fact(text),
            _timing_fact(text),
        ],
        14,
    )
    recognition_target = "・".join(targets) if targets else "判定カテゴリ"
    needs = _unique_texts(
        [
            f"商品画像から{recognition_target}をAIで判定する",
            "商品画像と商品データの対応確認を効率化する" if _contains_any_text(text, ["商品データ", "対応確認"]) else "",
            "人による確認フローを残して誤判定を抑える" if _contains_any_text(text, ["人", "確認"]) else "",
            "商品管理システムへAPIまたはCSVで連携する" if _contains_any_text(text, ["商品管理システム", "API", "CSV"]) else "",
            "商品管理システム連携を前提にPoCから本番導入へ進める" if "商品管理システム" in text else "",
            "PoCで認識精度と運用可否を検証する" if _contains_any_text(text, ["PoC", "精度"]) else "",
        ],
        5,
    )
    services = _unique_texts(
        [
            "業務・要件整理",
            "PoC設計",
            "画像データ調査",
            "アノテーション設計",
            "学習データ準備",
            "画像認識モデル開発",
            "精度評価・チューニング",
            "推論APIまたはバッチ処理",
            "API/CSV連携",
            "人手確認画面",
            "商品管理システム連携",
            "本番導入・再学習支援",
        ],
        12,
    )
    structure_items = _unique_texts(
        [
            "生花オークション業務" if _contains_any_text(text, ["生花", "オークション"]) else "",
            "商品画像",
            "商品管理システム連携" if "商品管理システム" in text else "",
            f"認識カテゴリ: {recognition_target}",
            "学習データ",
            "画像認識モデル",
            "認識精度評価",
            "人による確認",
            "API/CSV連携",
            "再学習・運用改善",
        ],
        10,
    )
    kpis = _unique_texts(["認識精度", "誤判定率", "人手確認時間", "商品登録処理時間", "再学習後の改善率"], 5)
    confirmations = _unique_texts(
        [
            "対象画像数",
            f"認識カテゴリ: {recognition_target}",
            "学習データ件数",
            "撮影条件・画像品質",
            "目標認識精度",
            "誤判定時の人手確認フロー",
            "商品管理システムの連携仕様",
            "APIまたはCSVのどちらで連携するか",
            "PoC範囲と本番範囲",
            "運用後の再学習方法",
        ],
        10,
    )
    premise_items = _unique_texts(
        [
            "対象画像数: 要確認",
            f"認識カテゴリ: {recognition_target}",
            "学習データ件数: 要確認",
            "目標認識精度: 要確認",
            "PoC対象範囲: 要確認",
            "連携先: 商品管理システム" if "商品管理システム" in text else "",
            "連携方式: APIまたはCSV" if _contains_any_text(text, ["API", "CSV"]) else "",
            _budget_fact(text).replace("予算:", "予算感:"),
            _timing_fact(text).replace("希望時期:", "希望時期:"),
        ],
        9,
    )
    return ProjectSpecifics(
        facts=facts,
        needs=needs or profile.needs[:4],
        services=services,
        journey=_unique_texts(
            [
                "商品画像を取り込む",
                f"AIが{recognition_target}を判定する",
                "担当者がAI判定結果を確認する",
                "APIまたはCSVで商品管理システムへ連携する",
                "誤判定を蓄積し再学習に回す",
            ],
            5,
        ),
        structure_items=structure_items,
        kpis=kpis,
        targets=_unique_texts(facts + profile.targets, 6),
        content_items=services[:6],
        strategy_items=_unique_texts(
            [
                "PoCで対象画像と判定カテゴリを絞って検証",
                "学習データとアノテーション基準を先に整備",
                "認識精度を測定し誤判定パターンを改善",
                "人による確認を残して本番リスクを抑制",
                "商品管理システム連携はAPI/CSVで段階実装",
            ],
            5,
        ),
        estimate_lines=profile.estimate_lines,
        confirmations=confirmations,
        quality_items=_unique_texts(profile.quality_items + confirmations, 8),
        schedule=_unique_texts(
            [
                "業務・要件整理",
                "画像データ調査・PoC設計",
                "学習データ準備・モデル検証",
                "認識精度評価・チューニング",
                "API/CSV連携・人手確認画面",
                "本番導入・再学習支援",
            ],
            6,
        ),
        team=profile.team,
        cost_points=_unique_texts(
            [
                "PoC範囲を先に確定",
                "対象画像数・認識カテゴリ数・学習データ件数で調整",
                "画像認識モデル開発と精度評価を必須化",
                "API/CSV連携と人手確認画面は段階提案",
                "撮影費は新規撮影を含む場合のみ別途確認",
            ],
            5,
        ),
        scope_label="対象範囲: 商品画像・認識カテゴリ・PoC/連携条件",
        premise_items=premise_items,
        notes=[
            "外部AI基盤、クラウド利用料、追加データ購入費は要件確定後に確認します。",
            "撮影費は新規の学習用画像撮影を含む場合のみ別途確認します。",
            "API/CSV連携は商品管理システム側の仕様確認後に確定します。",
        ],
    )


def _collect_present(text: str, items: list[tuple[str, list[str]]]) -> list[str]:
    return [label for label, patterns in items if _contains_any_text(text, patterns)]


def _contains_any_text(text: str, patterns: list[str]) -> bool:
    return any(pattern and pattern.lower() in text.lower() for pattern in patterns)


def _unique_texts(items: list[str], max_count: int) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for item in items:
        value = re.sub(r"\s+", " ", str(item or "")).strip()
        if not value:
            continue
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        values.append(value)
        if len(values) >= max_count:
            break
    return values


def _budget_fact(text: str) -> str:
    normalized = text.translate(str.maketrans("０１２３４５６７８９，", "0123456789,")).replace(",", "")
    match = re.search(r"(\d+(?:\.\d+)?)\s*万円", normalized)
    if match:
        return f"予算: 最大{match.group(1)}万円"
    match = re.search(r"予算[^\d]*(\d+(?:\.\d+)?)", normalized)
    return f"予算: {match.group(1)}万円" if match else ""


def _timing_fact(text: str) -> str:
    match = re.search(r"(20\d{2}年\s*\d{1,2}月(?:頃|ごろ)?)", text)
    if match:
        return f"希望時期: {match.group(1).replace(' ', '')}"
    match = re.search(r"(\d{1,2}か月後|\d{1,2}ヶ月後|\d{1,2}カ月後)", text)
    return f"希望時期: {match.group(1)}" if match else ""


def score_rows_for_axes(axes: list[str], text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for index, axis in enumerate(axes[:6]):
        current_score = 2 if _mentions_axis(text, axis) else 3
        proposed_score = 5 if index < 3 else 4
        rows.append([axis, f"{current_score}/5", "3/5", f"{proposed_score}/5"])
    return rows


def _mentions_axis(text: str, axis: str) -> bool:
    if not text:
        return False
    compact = re.sub(r"\s+", "", text)
    return axis in compact
