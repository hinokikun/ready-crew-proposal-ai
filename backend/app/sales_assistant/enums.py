from enum import Enum


class StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class MeetingStage(StrEnum):
    PREPARATION = "preparation"
    FIRST_MEETING = "first_meeting"
    DISCOVERY = "discovery"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSING = "closing"
    FOLLOW_UP = "follow_up"


class QuestionPriority(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ObjectionType(StrEnum):
    PRICE = "price"
    SCHEDULE = "schedule"
    COMPETITOR = "competitor"
    IMPLEMENTATION_RISK = "implementation_risk"
    INTERNAL_APPROVAL = "internal_approval"
    SECURITY = "security"
    OPERATION = "operation"
    EFFECTIVENESS = "effectiveness"
    SCOPE = "scope"
    OTHER = "other"


class ActionPriority(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ActionOwner(StrEnum):
    SALES = "sales"
    CLIENT = "client"
    TECHNICAL = "technical"
    MANAGER = "manager"
    JOINT = "joint"


class ReviewSeverity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
