from enum import Enum


class StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class BudgetType(StrEnum):
    CONFIRMED = "confirmed"
    UPPER_LIMIT = "upper_limit"
    REFERENCE = "reference"
    UNKNOWN = "unknown"


class ProjectCategory(StrEnum):
    VISION_OCR = "vision_ocr"
    AUTOMATION = "automation"
    CONVERSATIONAL_AI = "conversational_ai"
    KNOWLEDGE_AI = "knowledge_ai"
    CRM_SALES_INTELLIGENCE = "crm_sales_intelligence"
    GENERATIVE_AI_TRANSFORMATION = "generative_ai_transformation"
    DIGITAL_EXPERIENCE = "digital_experience"
    GENERIC_CONSULTING = "generic_consulting"
    MIXED = "mixed"


class Persona(StrEnum):
    CEO = "ceo"
    EXECUTIVE = "executive"
    DEPARTMENT_HEAD = "department_head"
    MANAGER = "manager"
    FIELD_LEADER = "field_leader"
    INFORMATION_SYSTEMS = "information_systems"
    QUALITY_ASSURANCE = "quality_assurance"
    SALES = "sales"
    UNKNOWN = "unknown"


class StrategyType(StrEnum):
    ROI = "roi"
    OPERATIONAL_IMPROVEMENT = "operational_improvement"
    QUALITY_IMPROVEMENT = "quality_improvement"
    RISK_REDUCTION = "risk_reduction"
    DIGITAL_TRANSFORMATION = "digital_transformation"
    AI_ENABLEMENT = "ai_enablement"
    COMPETITIVE_ADVANTAGE = "competitive_advantage"
    COST_REDUCTION = "cost_reduction"
    SPEED = "speed"
    CUSTOMER_EXPERIENCE = "customer_experience"
    GOVERNANCE = "governance"


class StoryType(StrEnum):
    ROI = "roi"
    DX = "dx"
    AI = "ai"
    AUTOMATION = "automation"
    QUALITY = "quality"
    CUSTOMER_EXPERIENCE = "customer_experience"
    GENERIC = "generic"


class PresentationPack(StrEnum):
    VISION_OCR = "vision_ocr"
    AUTOMATION = "automation"
    CONVERSATIONAL_AI = "conversational_ai"
    KNOWLEDGE_AI = "knowledge_ai"
    CRM_SALES_INTELLIGENCE = "crm_sales_intelligence"
    GENERATIVE_AI_TRANSFORMATION = "generative_ai_transformation"
    DIGITAL_EXPERIENCE = "digital_experience"
    GENERIC_CONSULTING = "generic_consulting"


class EvidenceLevel(StrEnum):
    CONFIRMED = "confirmed"
    PROVIDED = "provided"
    INFERRED = "inferred"
    MISSING = "missing"


class ReviewDecision(StrEnum):
    APPROVE = "approve"
    APPROVE_WITH_CHANGES = "approve_with_changes"
    REJECT = "reject"
    RE_EVALUATE = "re_evaluate"
