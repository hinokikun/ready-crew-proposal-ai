from typing import Dict, Iterable, List, Optional, Tuple

from .enums import Persona, PresentationPack, ProjectCategory, StoryType, StrategyType


SignalMap = Dict[ProjectCategory, List[str]]


CATEGORY_SIGNALS: SignalMap = {
    ProjectCategory.VISION_OCR: [
        "ai-ocr",
        "ocr",
        "画像認識",
        "画像",
        "認識",
        "帳票",
        "読取",
        "読み取り",
        "抽出",
        "検査",
        "分類",
        "等級",
        "品質チェック",
        "アノテーション",
    ],
    ProjectCategory.AUTOMATION: [
        "rpa",
        "自動化",
        "ボット",
        "bot",
        "定型",
        "反復",
        "ワークフロー",
        "キュー",
        "例外処理",
    ],
    ProjectCategory.CONVERSATIONAL_AI: [
        "チャットボット",
        "chatbot",
        "問い合わせ",
        "会話",
        "faq",
        "エスカレーション",
        "サポート",
    ],
    ProjectCategory.KNOWLEDGE_AI: [
        "ナレッジ",
        "検索",
        "rag",
        "社内文書",
        "引用",
        "根拠",
        "knowledge",
    ],
    ProjectCategory.CRM_SALES_INTELLIGENCE: [
        "crm",
        "sfa",
        "営業",
        "顧客",
        "商談",
        "パイプライン",
        "フォローアップ",
    ],
    ProjectCategory.GENERATIVE_AI_TRANSFORMATION: [
        "生成ai",
        "生成AI",
        "llm",
        "プロンプト",
        "文章生成",
        "ドラフト",
        "aiワークベンチ",
    ],
    ProjectCategory.DIGITAL_EXPERIENCE: [
        "web",
        "webサイト",
        "サイト",
        "cms",
        "seo",
        "ux",
        "ec",
        "cv",
        "導線",
        "リニューアル",
    ],
}


PERSONA_SIGNALS: Dict[Persona, List[str]] = {
    Persona.CEO: ["ceo", "経営者", "社長"],
    Persona.EXECUTIVE: ["役員", "経営層", "投資判断", "全社", "取締役"],
    Persona.DEPARTMENT_HEAD: ["部長", "部門", "事業責任者", "部署"],
    Persona.MANAGER: ["課長", "マネージャー", "管理者", "チーム"],
    Persona.FIELD_LEADER: ["現場", "運用", "担当者", "作業", "日次"],
    Persona.INFORMATION_SYSTEMS: ["情報システム", "情シス", "api", "db", "セキュリティ", "sso"],
    Persona.QUALITY_ASSURANCE: ["品質保証", "qa", "検査", "監査", "トレーサビリティ"],
    Persona.SALES: ["営業", "商談", "顧客", "提案", "フォロー"],
}


STRATEGY_SIGNALS: Dict[StrategyType, List[str]] = {
    StrategyType.ROI: ["roi", "投資", "費用対効果", "回収", "経営判断"],
    StrategyType.OPERATIONAL_IMPROVEMENT: ["業務改善", "工数", "負荷", "手作業", "効率"],
    StrategyType.QUALITY_IMPROVEMENT: ["品質", "精度", "ばらつき", "誤り", "再作業", "検査"],
    StrategyType.RISK_REDUCTION: ["リスク", "障害", "監査", "セキュリティ", "コンプライアンス"],
    StrategyType.DIGITAL_TRANSFORMATION: ["dx", "デジタル", "全社", "データ連携"],
    StrategyType.AI_ENABLEMENT: ["ai", "生成ai", "画像認識", "llm", "ocr"],
    StrategyType.COMPETITIVE_ADVANTAGE: ["競争優位", "差別化", "市場", "顧客価値"],
    StrategyType.COST_REDUCTION: ["コスト削減", "削減", "外注費", "人件費"],
    StrategyType.SPEED: ["短納期", "スピード", "迅速", "リードタイム"],
    StrategyType.CUSTOMER_EXPERIENCE: ["顧客体験", "cx", "問い合わせ", "満足", "導線"],
    StrategyType.GOVERNANCE: ["ガバナンス", "権限", "ルール", "統制"],
}


CATEGORY_TO_PACK = {
    ProjectCategory.VISION_OCR: PresentationPack.VISION_OCR,
    ProjectCategory.AUTOMATION: PresentationPack.AUTOMATION,
    ProjectCategory.CONVERSATIONAL_AI: PresentationPack.CONVERSATIONAL_AI,
    ProjectCategory.KNOWLEDGE_AI: PresentationPack.KNOWLEDGE_AI,
    ProjectCategory.CRM_SALES_INTELLIGENCE: PresentationPack.CRM_SALES_INTELLIGENCE,
    ProjectCategory.GENERATIVE_AI_TRANSFORMATION: PresentationPack.GENERATIVE_AI_TRANSFORMATION,
    ProjectCategory.DIGITAL_EXPERIENCE: PresentationPack.DIGITAL_EXPERIENCE,
    ProjectCategory.GENERIC_CONSULTING: PresentationPack.GENERIC_CONSULTING,
}


def score_signals(text: str, signals: SignalMap) -> Dict[ProjectCategory, int]:
    return {category: _score(text, words) for category, words in signals.items()}


def choose_category(text: str) -> Tuple[ProjectCategory, Optional[ProjectCategory], List[str], bool]:
    scores = score_signals(text, CATEGORY_SIGNALS)
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    primary, primary_score = ranked[0]
    secondary, secondary_score = ranked[1]
    reasons = [f"{primary.value} signal score {primary_score}"]
    conflict = False
    if primary_score < 2:
        return (
            ProjectCategory.GENERIC_CONSULTING,
            None,
            ["insufficient category evidence"],
            False,
        )
    if secondary_score >= 2:
        reasons.append(f"{secondary.value} secondary signal score {secondary_score}")
        conflict = primary_score == secondary_score
        return primary, secondary, reasons, conflict
    return primary, None, reasons, False


def choose_persona(text: str, audience_hint: Optional[Persona]) -> Tuple[Persona, List[Persona], Persona, List[str], bool]:
    if audience_hint:
        return audience_hint, _secondary_personas(audience_hint, text), _decision_maker(audience_hint), ["explicit audience hint"], False
    scores = {persona: _score(text, words) for persona, words in PERSONA_SIGNALS.items()}
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    persona, score = ranked[0]
    if score <= 0:
        return Persona.UNKNOWN, [], Persona.UNKNOWN, ["audience not specified"], True
    return persona, _secondary_personas(persona, text), _decision_maker(persona), [f"{persona.value} inferred from text"], False


def choose_strategy_and_story(
    text: str, category: ProjectCategory, persona: Persona
) -> Tuple[StrategyType, List[StrategyType], StoryType, List[str]]:
    strategy_scores = {strategy: _score(text, words) for strategy, words in STRATEGY_SIGNALS.items()}
    category_default = _category_default_strategy(category)
    strategy_scores[category_default] = strategy_scores.get(category_default, 0) + 2
    if persona in {Persona.CEO, Persona.EXECUTIVE}:
        strategy_scores[StrategyType.ROI] += 1
    if persona == Persona.QUALITY_ASSURANCE:
        strategy_scores[StrategyType.QUALITY_IMPROVEMENT] += 2
    ranked = sorted(strategy_scores.items(), key=lambda item: item[1], reverse=True)
    primary = ranked[0][0]
    secondary = [strategy for strategy, score in ranked[1:4] if score >= 2 and strategy != primary]
    story = _story_for(primary, category, persona)
    return primary, secondary[:2], story, [f"{primary.value} selected from category and persona signals"]


def category_to_pack(category: ProjectCategory) -> PresentationPack:
    return CATEGORY_TO_PACK.get(category, PresentationPack.GENERIC_CONSULTING)


def kpi_pack_for(category: ProjectCategory, strategy: StrategyType) -> str:
    if strategy == StrategyType.ROI:
        return "roi_measurement"
    if strategy == StrategyType.QUALITY_IMPROVEMENT:
        return "quality_measurement"
    if category == ProjectCategory.AUTOMATION:
        return "operational_efficiency"
    if category in {ProjectCategory.CRM_SALES_INTELLIGENCE, ProjectCategory.DIGITAL_EXPERIENCE}:
        return "customer_experience_metrics"
    if category in {ProjectCategory.GENERATIVE_AI_TRANSFORMATION, ProjectCategory.KNOWLEDGE_AI}:
        return "adoption_governance"
    return "generic_decision_metrics"


def estimate_pack_for(category: ProjectCategory, text: str) -> str:
    if "poc" in text or "実証" in text:
        return "poc_to_implementation"
    if category == ProjectCategory.DIGITAL_EXPERIENCE:
        return "discovery_design_build"
    if category == ProjectCategory.AUTOMATION:
        return "process_pilot_rollout"
    if category == ProjectCategory.CRM_SALES_INTELLIGENCE:
        return "configuration_enablement_operations"
    return "discovery_and_plan"


def _score(text: str, words: Iterable[str]) -> int:
    lowered = text.lower()
    return sum(1 for word in words if word.lower() in lowered)


def _secondary_personas(primary: Persona, text: str) -> List[Persona]:
    secondaries: List[Persona] = []
    if primary != Persona.INFORMATION_SYSTEMS and any(word in text for word in ["api", "db", "連携", "セキュリティ"]):
        secondaries.append(Persona.INFORMATION_SYSTEMS)
    if primary != Persona.FIELD_LEADER and any(word in text for word in ["現場", "運用", "担当者"]):
        secondaries.append(Persona.FIELD_LEADER)
    if primary != Persona.QUALITY_ASSURANCE and any(word in text for word in ["品質", "検査", "精度"]):
        secondaries.append(Persona.QUALITY_ASSURANCE)
    return secondaries[:2]


def _decision_maker(persona: Persona) -> Persona:
    if persona in {Persona.CEO, Persona.EXECUTIVE, Persona.DEPARTMENT_HEAD}:
        return persona
    if persona == Persona.UNKNOWN:
        return Persona.UNKNOWN
    return Persona.DEPARTMENT_HEAD


def _category_default_strategy(category: ProjectCategory) -> StrategyType:
    return {
        ProjectCategory.VISION_OCR: StrategyType.QUALITY_IMPROVEMENT,
        ProjectCategory.AUTOMATION: StrategyType.OPERATIONAL_IMPROVEMENT,
        ProjectCategory.CONVERSATIONAL_AI: StrategyType.CUSTOMER_EXPERIENCE,
        ProjectCategory.KNOWLEDGE_AI: StrategyType.OPERATIONAL_IMPROVEMENT,
        ProjectCategory.CRM_SALES_INTELLIGENCE: StrategyType.CUSTOMER_EXPERIENCE,
        ProjectCategory.GENERATIVE_AI_TRANSFORMATION: StrategyType.AI_ENABLEMENT,
        ProjectCategory.DIGITAL_EXPERIENCE: StrategyType.CUSTOMER_EXPERIENCE,
        ProjectCategory.GENERIC_CONSULTING: StrategyType.OPERATIONAL_IMPROVEMENT,
    }.get(category, StrategyType.OPERATIONAL_IMPROVEMENT)


def _story_for(strategy: StrategyType, category: ProjectCategory, persona: Persona) -> StoryType:
    if strategy == StrategyType.ROI or persona in {Persona.CEO, Persona.EXECUTIVE}:
        return StoryType.ROI
    if strategy in {StrategyType.DIGITAL_TRANSFORMATION, StrategyType.GOVERNANCE}:
        return StoryType.DX
    if strategy == StrategyType.QUALITY_IMPROVEMENT:
        return StoryType.QUALITY
    if strategy == StrategyType.OPERATIONAL_IMPROVEMENT or category == ProjectCategory.AUTOMATION:
        return StoryType.AUTOMATION
    if strategy == StrategyType.CUSTOMER_EXPERIENCE:
        return StoryType.CUSTOMER_EXPERIENCE
    if strategy == StrategyType.AI_ENABLEMENT:
        return StoryType.AI
    return StoryType.GENERIC
