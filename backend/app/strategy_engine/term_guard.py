from typing import Dict, Iterable, List, Optional, Tuple

from .enums import PresentationPack


CATEGORY_TERMS: Dict[PresentationPack, List[str]] = {
    PresentationPack.VISION_OCR: [
        "OCR",
        "画像認識",
        "帳票読取",
        "抽出精度",
        "アノテーション",
        "分類",
        "等級判定",
    ],
    PresentationPack.AUTOMATION: [
        "RPA",
        "自動実行",
        "例外処理",
        "キュー",
        "定型業務",
    ],
    PresentationPack.CONVERSATIONAL_AI: [
        "チャットボット",
        "会話",
        "エスカレーション",
    ],
    PresentationPack.KNOWLEDGE_AI: [
        "ナレッジ検索",
        "RAG",
        "引用",
        "根拠提示",
    ],
    PresentationPack.CRM_SALES_INTELLIGENCE: [
        "CRM",
        "SFA",
        "商談",
        "パイプライン",
        "フォローアップ",
    ],
    PresentationPack.GENERATIVE_AI_TRANSFORMATION: [
        "生成AI",
        "LLM",
        "プロンプト",
        "文章生成",
        "AIワークベンチ",
    ],
    PresentationPack.DIGITAL_EXPERIENCE: [
        "Webサイト",
        "UX",
        "CMS",
        "SEO",
        "サイトマップ",
        "CV導線",
        "回遊",
    ],
    PresentationPack.GENERIC_CONSULTING: [
        "課題整理",
        "実行計画",
        "意思決定",
        "業務改善",
    ],
}


def build_term_rules(
    primary_pack: PresentationPack, secondary_pack: Optional[PresentationPack] = None
) -> Tuple[List[str], List[str], List[str]]:
    allowed = list(CATEGORY_TERMS.get(primary_pack, []))
    conditional: List[str] = []
    if secondary_pack:
        conditional = list(CATEGORY_TERMS.get(secondary_pack, []))
    prohibited: List[str] = []
    for pack, terms in CATEGORY_TERMS.items():
        if pack in {primary_pack, secondary_pack}:
            continue
        if pack == PresentationPack.GENERIC_CONSULTING:
            continue
        prohibited.extend(terms)
    if primary_pack == PresentationPack.GENERIC_CONSULTING and not secondary_pack:
        prohibited = [
            term
            for pack, terms in CATEGORY_TERMS.items()
            if pack != PresentationPack.GENERIC_CONSULTING
            for term in terms
        ]
    return _unique(allowed), _unique(conditional), _unique(prohibited)


def find_prohibited_terms(text: str, prohibited_terms: Iterable[str]) -> List[str]:
    lowered = (text or "").lower()
    hits = []
    for term in prohibited_terms:
        if term.lower() in lowered:
            hits.append(term)
    return _unique(hits)


def _unique(items: Iterable[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
