from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class EvaluationDatasetCase:
    case_id: str
    category: str
    fixture_name: str
    title: str
    expected_engine_modes: tuple[str, ...] = ("strategy_v1", "legacy")


CATEGORY_LABELS: Dict[str, str] = {
    "vision_ocr": "Vision / OCR",
    "automation": "Automation",
    "crm_sales_intelligence": "CRM",
    "knowledge_ai": "Knowledge AI",
    "conversational_ai": "Conversational AI",
    "digital_experience": "Digital Experience",
    "generative_ai_transformation": "Generative AI",
    "generic_consulting": "Generic",
}


EVALUATION_DATASET: List[EvaluationDatasetCase] = [
    EvaluationDatasetCase("vision-ocr-001", "vision_ocr", "ai_ocr", "AI-OCR invoice processing"),
    EvaluationDatasetCase("vision-ocr-002", "vision_ocr", "image_recognition", "Flower image recognition"),
    EvaluationDatasetCase("automation-001", "automation", "rpa", "RPA order registration"),
    EvaluationDatasetCase("automation-002", "automation", "field_operations", "Field operations improvement"),
    EvaluationDatasetCase("crm-001", "crm_sales_intelligence", "crm", "CRM sales activity management"),
    EvaluationDatasetCase("crm-002", "crm_sales_intelligence", "crm_generative_ai", "CRM and generative AI sales support"),
    EvaluationDatasetCase("knowledge-001", "knowledge_ai", "knowledge_search", "Internal knowledge search"),
    EvaluationDatasetCase("knowledge-002", "knowledge_ai", "it_security", "Secure AI governance for IT"),
    EvaluationDatasetCase("conversation-001", "conversational_ai", "chatbot", "Internal inquiry chatbot"),
    EvaluationDatasetCase("conversation-002", "conversational_ai", "web_chatbot", "Web and chatbot inquiry support"),
    EvaluationDatasetCase("digital-001", "digital_experience", "web_renewal", "Corporate website renewal"),
    EvaluationDatasetCase("digital-002", "digital_experience", "web_chatbot", "Website chatbot conversion support"),
    EvaluationDatasetCase("genai-001", "generative_ai_transformation", "generative_ai", "Generative AI adoption support"),
    EvaluationDatasetCase("genai-002", "generative_ai_transformation", "crm_generative_ai", "Generative AI sales drafting"),
    EvaluationDatasetCase("generic-001", "generic_consulting", "generic_consulting", "Business improvement consulting"),
    EvaluationDatasetCase("generic-002", "generic_consulting", "sparse", "Sparse proposal input"),
]


def benchmark_category_choices() -> list[str]:
    return sorted(CATEGORY_LABELS)


def dataset_cases(category: str | None = None) -> list[EvaluationDatasetCase]:
    if category is None:
        return list(EVALUATION_DATASET)
    if category not in CATEGORY_LABELS:
        raise KeyError(f"Unknown evaluation category: {category}")
    return [case for case in EVALUATION_DATASET if case.category == category]
