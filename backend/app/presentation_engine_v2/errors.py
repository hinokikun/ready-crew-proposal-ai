"""Presentation Engine 2.0 error types and codes."""


SUPPORTED_BLUEPRINT_VERSION = "pe2_slide_blueprint_v1"


class PresentationEngineV2Error(Exception):
    """Base exception for the isolated Presentation Engine 2.0 module."""


class BlueprintValidationError(PresentationEngineV2Error):
    """Raised when a blueprint cannot be parsed or validated."""


class BlueprintNormalizationError(PresentationEngineV2Error):
    """Raised when a payload cannot be normalized safely."""


class ErrorCode:
    SCHEMA_REQUIRED = "PE2-SCHEMA-001"
    SCHEMA_ENUM = "PE2-SCHEMA-002"
    SCHEMA_LENGTH = "PE2-SCHEMA-003"
    SCHEMA_DUPLICATE_ID = "PE2-SCHEMA-004"
    MESSAGE_EMPTY = "PE2-MESSAGE-001"
    MESSAGE_PLACEHOLDER = "PE2-MESSAGE-002"
    MESSAGE_OVERLAP = "PE2-MESSAGE-003"
    VISUAL_MISMATCH = "PE2-VISUAL-001"
    VISUAL_MISSING_DATA = "PE2-VISUAL-002"
    LAYOUT_OVERFLOW = "PE2-LAYOUT-001"
    LAYOUT_SAFE_AREA = "PE2-LAYOUT-002"
    QUALITY_ONE_MESSAGE = "PE2-QUALITY-001"
    QUALITY_CTA_MISSING = "PE2-QUALITY-002"
    SAFETY_NUMERIC_EVIDENCE = "PE2-SAFETY-001"
    SAFETY_RENDERING = "PE2-SAFETY-002"
