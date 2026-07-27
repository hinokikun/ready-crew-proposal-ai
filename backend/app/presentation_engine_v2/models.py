"""Pydantic models for Presentation Engine 2.0 slide blueprints."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from .enums import (
    AlignmentType,
    AnimationHint,
    AudienceType,
    BlueprintStatus,
    ContentPriority,
    CTAType,
    DataConfidence,
    DensityLevel,
    DiagramType,
    EmphasisLevel,
    EvidenceType,
    HierarchyLevel,
    LayoutDirection,
    OverflowStrategy,
    SlideGoal,
    SlideType,
    ThemeType,
    ValidationSeverity,
    VisualType,
)
from .errors import SUPPORTED_BLUEPRINT_VERSION


MAX_HEADLINE_CHARS = 90
MAX_MAIN_MESSAGE_CHARS = 240
MAX_SUPPORTING_MESSAGES = 6
MAX_CONTENT_BLOCKS = 8
MAX_METRICS = 8
MAX_COMPARISON_ITEMS = 8
MAX_TIMELINE_ITEMS = 12
MAX_PROCESS_STEPS = 12
MAX_TABLE_COLUMNS = 5
MAX_TABLE_ROWS = 10
MAX_READING_ORDER_ITEMS = 16


def _clean_text(value: Optional[str]) -> str:
    return str(value or "").strip()


def _clean_optional_text(value: Optional[str]) -> Optional[str]:
    text = _clean_text(value)
    return text or None


def _clean_text_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


class _BaseModel(BaseModel):
    class Config:
        use_enum_values = True
        extra = "forbid"
        allow_population_by_field_name = True


class SourceReference(_BaseModel):
    source_id: str = Field(..., min_length=1, max_length=80)
    source_type: EvidenceType = EvidenceType.USER_INPUT
    label: str = Field(..., min_length=1, max_length=120)
    url: Optional[str] = Field(default=None, max_length=500)
    page: Optional[str] = Field(default=None, max_length=40)
    confidence: DataConfidence = DataConfidence.MEDIUM

    _normalize_label = validator("source_id", "label", "url", "page", pre=True, allow_reuse=True)(_clean_optional_text)


class EvidenceBlock(_BaseModel):
    evidence_id: str = Field(..., min_length=1, max_length=80)
    evidence_type: EvidenceType = EvidenceType.USER_INPUT
    text: str = Field(..., min_length=1, max_length=280)
    confidence: DataConfidence = DataConfidence.MEDIUM
    source_reference_ids: list[str] = Field(default_factory=list, max_items=6)
    is_assumption: bool = False

    _normalize_text = validator("evidence_id", "text", pre=True, allow_reuse=True)(_clean_optional_text)
    _normalize_refs = validator("source_reference_ids", pre=True, always=True, allow_reuse=True)(_clean_text_list)


class TextBlock(_BaseModel):
    block_id: str = Field(..., min_length=1, max_length=80)
    role: str = Field(default="body", min_length=1, max_length=40)
    text: str = Field(..., min_length=1, max_length=520)
    priority: ContentPriority = ContentPriority.MEDIUM
    emphasis: EmphasisLevel = EmphasisLevel.NONE
    evidence_ids: list[str] = Field(default_factory=list, max_items=6)

    _normalize_text = validator("block_id", "role", "text", pre=True, allow_reuse=True)(_clean_optional_text)
    _normalize_ids = validator("evidence_ids", pre=True, always=True, allow_reuse=True)(_clean_text_list)


class MetricBlock(_BaseModel):
    metric_id: str = Field(..., min_length=1, max_length=80)
    label: str = Field(..., min_length=1, max_length=80)
    value: str = Field(..., min_length=1, max_length=80)
    unit: Optional[str] = Field(default=None, max_length=40)
    context: Optional[str] = Field(default=None, max_length=160)
    evidence_id: Optional[str] = Field(default=None, max_length=80)
    confidence: DataConfidence = DataConfidence.MEDIUM

    _normalize = validator("metric_id", "label", "value", "unit", "context", "evidence_id", pre=True, allow_reuse=True)(
        _clean_optional_text
    )


class ComparisonItem(_BaseModel):
    item_id: str = Field(..., min_length=1, max_length=80)
    label: str = Field(..., min_length=1, max_length=100)
    current_state: Optional[str] = Field(default=None, max_length=220)
    proposed_state: Optional[str] = Field(default=None, max_length=220)
    difference: Optional[str] = Field(default=None, max_length=220)
    priority: ContentPriority = ContentPriority.MEDIUM

    _normalize = validator(
        "item_id",
        "label",
        "current_state",
        "proposed_state",
        "difference",
        pre=True,
        allow_reuse=True,
    )(_clean_optional_text)


class TimelineItem(_BaseModel):
    item_id: str = Field(..., min_length=1, max_length=80)
    label: str = Field(..., min_length=1, max_length=100)
    period: str = Field(..., min_length=1, max_length=80)
    description: Optional[str] = Field(default=None, max_length=220)
    milestone: bool = False

    _normalize = validator("item_id", "label", "period", "description", pre=True, allow_reuse=True)(_clean_optional_text)


class ProcessStep(_BaseModel):
    step_id: str = Field(..., min_length=1, max_length=80)
    label: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=220)
    owner: Optional[str] = Field(default=None, max_length=80)
    output: Optional[str] = Field(default=None, max_length=120)

    _normalize = validator("step_id", "label", "description", "owner", "output", pre=True, allow_reuse=True)(
        _clean_optional_text
    )


class TableColumn(_BaseModel):
    column_id: str = Field(..., min_length=1, max_length=60)
    label: str = Field(..., min_length=1, max_length=80)
    alignment: AlignmentType = AlignmentType.LEFT
    value_type: str = Field(default="text", max_length=40)

    _normalize = validator("column_id", "label", "value_type", pre=True, allow_reuse=True)(_clean_optional_text)


class TableRow(_BaseModel):
    row_id: str = Field(..., min_length=1, max_length=60)
    cells: Dict[str, str] = Field(default_factory=dict)

    @validator("cells", pre=True, always=True)
    def normalize_cells(cls, value: Any) -> Dict[str, str]:
        if not isinstance(value, dict):
            return {}
        return {str(key).strip(): str(cell).strip() for key, cell in value.items() if str(key).strip()}


class TableData(_BaseModel):
    columns: list[TableColumn] = Field(default_factory=list, max_items=MAX_TABLE_COLUMNS)
    rows: list[TableRow] = Field(default_factory=list, max_items=MAX_TABLE_ROWS)


class ColorPalette(_BaseModel):
    background: str = "#FFFFFF"
    text: str = "#0F172A"
    primary: str = "#2563EB"
    secondary: str = "#64748B"
    accent: str = "#06B6D4"
    muted: str = "#E2E8F0"
    success: str = "#10B981"
    warning: str = "#F59E0B"
    danger: str = "#EF4444"

    _normalize_colors = validator(
        "background",
        "text",
        "primary",
        "secondary",
        "accent",
        "muted",
        "success",
        "warning",
        "danger",
        pre=True,
        allow_reuse=True,
    )(_clean_optional_text)


class TypographyStyle(_BaseModel):
    font_family: str = Field(default="Noto Sans JP", max_length=80)
    font_size_pt: int = Field(default=18, ge=8, le=80)
    font_weight: int = Field(default=400, ge=100, le=900)
    line_height: float = Field(default=1.25, ge=1.0, le=2.0)
    color: Optional[str] = Field(default=None, max_length=20)

    _normalize = validator("font_family", "color", pre=True, allow_reuse=True)(_clean_optional_text)


class MarginSpec(_BaseModel):
    top: float = Field(default=0.42, ge=0.0, le=2.0)
    right: float = Field(default=0.48, ge=0.0, le=2.0)
    bottom: float = Field(default=0.42, ge=0.0, le=2.0)
    left: float = Field(default=0.48, ge=0.0, le=2.0)


class GridSpec(_BaseModel):
    columns: int = Field(default=12, ge=1, le=24)
    rows: int = Field(default=8, ge=1, le=16)
    gutter: float = Field(default=0.16, ge=0.0, le=1.0)
    margin: MarginSpec = Field(default_factory=MarginSpec)


class SafeAreaSpec(_BaseModel):
    x: float = Field(default=0.04, ge=0.0, le=1.0)
    y: float = Field(default=0.05, ge=0.0, le=1.0)
    w: float = Field(default=0.92, ge=0.1, le=1.0)
    h: float = Field(default=0.88, ge=0.1, le=1.0)


class CTAConfig(_BaseModel):
    cta_type: CTAType = CTAType.NONE
    cta_label: Optional[str] = Field(default=None, max_length=80)
    cta_detail: Optional[str] = Field(default=None, max_length=180)

    _normalize = validator("cta_label", "cta_detail", pre=True, allow_reuse=True)(_clean_optional_text)


class ImageRequirement(_BaseModel):
    required: bool = False
    image_role: Optional[str] = Field(default=None, max_length=80)
    description: Optional[str] = Field(default=None, max_length=180)
    source_type: str = Field(default="placeholder", max_length=40)
    license: str = Field(default="not_applicable", max_length=80)
    replaceable: bool = True

    _normalize = validator("image_role", "description", "source_type", "license", pre=True, allow_reuse=True)(
        _clean_optional_text
    )


class ChartRequirement(_BaseModel):
    required: bool = False
    chart_type: Optional[str] = Field(default=None, max_length=60)
    data_label: Optional[str] = Field(default=None, max_length=120)
    source_reference_id: Optional[str] = Field(default=None, max_length=80)

    _normalize = validator("chart_type", "data_label", "source_reference_id", pre=True, allow_reuse=True)(
        _clean_optional_text
    )


class DiagramNode(_BaseModel):
    node_id: str = Field(..., min_length=1, max_length=80)
    label: str = Field(..., min_length=1, max_length=100)
    role: str = Field(default="node", max_length=40)
    group_id: Optional[str] = Field(default=None, max_length=80)

    _normalize = validator("node_id", "label", "role", "group_id", pre=True, allow_reuse=True)(_clean_optional_text)


class DiagramConnector(_BaseModel):
    connector_id: str = Field(..., min_length=1, max_length=80)
    source_node_id: str = Field(..., min_length=1, max_length=80)
    target_node_id: str = Field(..., min_length=1, max_length=80)
    label: Optional[str] = Field(default=None, max_length=80)

    _normalize = validator(
        "connector_id",
        "source_node_id",
        "target_node_id",
        "label",
        pre=True,
        allow_reuse=True,
    )(_clean_optional_text)


class DiagramDefinition(_BaseModel):
    diagram_id: str = Field(..., min_length=1, max_length=80)
    diagram_type: DiagramType = DiagramType.NONE
    title: Optional[str] = Field(default=None, max_length=120)
    nodes: list[DiagramNode] = Field(default_factory=list, max_items=16)
    connectors: list[DiagramConnector] = Field(default_factory=list, max_items=20)
    axes: list[str] = Field(default_factory=list, max_items=4)
    legend: list[str] = Field(default_factory=list, max_items=8)
    reading_order: list[str] = Field(default_factory=list, max_items=MAX_READING_ORDER_ITEMS)

    _normalize = validator("diagram_id", "title", pre=True, allow_reuse=True)(_clean_optional_text)
    _normalize_lists = validator("axes", "legend", "reading_order", pre=True, always=True, allow_reuse=True)(
        _clean_text_list
    )


class RenderingMetadata(_BaseModel):
    editable_shapes_required: bool = True
    external_assets_allowed: bool = False
    page_number_required: bool = True
    footer_required: bool = False
    warnings: list[str] = Field(default_factory=list, max_items=20)
    renderer_notes: list[str] = Field(default_factory=list, max_items=20)

    _normalize_lists = validator("warnings", "renderer_notes", pre=True, always=True, allow_reuse=True)(
        _clean_text_list
    )


class ValidationIssue(_BaseModel):
    code: str = Field(..., min_length=1, max_length=40)
    severity: ValidationSeverity
    field_path: str = Field(..., min_length=1, max_length=160)
    message: str = Field(..., min_length=1, max_length=260)
    suggestion: Optional[str] = Field(default=None, max_length=260)
    blocking: bool = False
    source: str = Field(default="validator", max_length=80)

    _normalize = validator("code", "field_path", "message", "suggestion", "source", pre=True, allow_reuse=True)(
        _clean_optional_text
    )


class ValidationResult(_BaseModel):
    valid: bool
    status: BlueprintStatus
    issues: list[ValidationIssue] = Field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.ERROR.value]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.WARNING.value]


class SlideBlueprint(_BaseModel):
    blueprint_version: str = Field(default=SUPPORTED_BLUEPRINT_VERSION, const=True)
    blueprint_id: str = Field(..., min_length=1, max_length=100)
    slide_id: str = Field(..., min_length=1, max_length=100)
    slide_index: int = Field(..., ge=0, le=200)
    slide_type: SlideType
    status: BlueprintStatus = BlueprintStatus.DRAFT

    slide_goal: SlideGoal
    audience: AudienceType = AudienceType.GENERAL
    decision_question: Optional[str] = Field(default=None, max_length=180)
    desired_reaction: Optional[str] = Field(default=None, max_length=180)

    headline: str = Field(..., min_length=1, max_length=MAX_HEADLINE_CHARS)
    main_message: str = Field(..., min_length=1, max_length=MAX_MAIN_MESSAGE_CHARS)
    supporting_messages: list[str] = Field(default_factory=list, max_items=MAX_SUPPORTING_MESSAGES)
    supporting_evidence: list[EvidenceBlock] = Field(default_factory=list, max_items=10)
    speaker_note_summary: Optional[str] = Field(default=None, max_length=360)

    visual_type: VisualType
    diagram_type: DiagramType = DiagramType.NONE
    layout_direction: LayoutDirection = LayoutDirection.LEFT_TO_RIGHT
    visual_rationale: Optional[str] = Field(default=None, max_length=220)
    image_requirement: ImageRequirement = Field(default_factory=ImageRequirement)
    chart_requirement: ChartRequirement = Field(default_factory=ChartRequirement)

    content_blocks: list[TextBlock] = Field(default_factory=list, max_items=MAX_CONTENT_BLOCKS)
    metrics: list[MetricBlock] = Field(default_factory=list, max_items=MAX_METRICS)
    comparison_items: list[ComparisonItem] = Field(default_factory=list, max_items=MAX_COMPARISON_ITEMS)
    timeline_items: list[TimelineItem] = Field(default_factory=list, max_items=MAX_TIMELINE_ITEMS)
    process_steps: list[ProcessStep] = Field(default_factory=list, max_items=MAX_PROCESS_STEPS)
    table_data: Optional[TableData] = None
    citations: list[str] = Field(default_factory=list, max_items=12)
    source_references: list[SourceReference] = Field(default_factory=list, max_items=12)

    primary_element: str = Field(..., min_length=1, max_length=80)
    secondary_elements: list[str] = Field(default_factory=list, max_items=8)
    content_priority: ContentPriority = ContentPriority.HIGH
    emphasis: EmphasisLevel = EmphasisLevel.MEDIUM
    reading_order: list[str] = Field(default_factory=list, max_items=MAX_READING_ORDER_ITEMS)
    hierarchy_level: HierarchyLevel = HierarchyLevel.PRIMARY

    theme: ThemeType = ThemeType.CONSULTING
    color_palette: ColorPalette = Field(default_factory=ColorPalette)
    background_style: str = Field(default="clean", max_length=60)
    surface_style: str = Field(default="card", max_length=60)
    border_style: str = Field(default="subtle", max_length=60)
    icon_style: str = Field(default="line", max_length=60)

    title_style: TypographyStyle = Field(default_factory=lambda: TypographyStyle(font_size_pt=36, font_weight=700))
    subtitle_style: TypographyStyle = Field(default_factory=lambda: TypographyStyle(font_size_pt=22, font_weight=500))
    body_style: TypographyStyle = Field(default_factory=TypographyStyle)
    metric_style: TypographyStyle = Field(default_factory=lambda: TypographyStyle(font_family="Inter", font_size_pt=48, font_weight=700))
    caption_style: TypographyStyle = Field(default_factory=lambda: TypographyStyle(font_size_pt=12))
    footnote_style: TypographyStyle = Field(default_factory=lambda: TypographyStyle(font_size_pt=10))

    grid: GridSpec = Field(default_factory=GridSpec)
    safe_area: SafeAreaSpec = Field(default_factory=SafeAreaSpec)
    margins: MarginSpec = Field(default_factory=MarginSpec)
    gaps: float = Field(default=0.16, ge=0.0, le=1.0)
    alignment: AlignmentType = AlignmentType.LEFT
    density: DensityLevel = DensityLevel.MEDIUM

    overflow_strategy: OverflowStrategy = OverflowStrategy.REQUIRE_REVIEW
    split_allowed: bool = True
    fallback_visual_type: VisualType = VisualType.TEXT_ONLY
    animation_hint: AnimationHint = AnimationHint.NONE

    cta: CTAConfig = Field(default_factory=CTAConfig)

    generation_source: str = Field(default="offline_fixture", max_length=80)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    warnings: list[str] = Field(default_factory=list, max_items=20)
    validation_result: Optional[ValidationResult] = None
    rendering_metadata: RenderingMetadata = Field(default_factory=RenderingMetadata)
    diagram_definition: DiagramDefinition = Field(default_factory=lambda: DiagramDefinition(diagram_id="diagram-none"))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    _normalize_strings = validator(
        "blueprint_id",
        "slide_id",
        "decision_question",
        "desired_reaction",
        "headline",
        "main_message",
        "speaker_note_summary",
        "visual_rationale",
        "primary_element",
        "background_style",
        "surface_style",
        "border_style",
        "icon_style",
        "generation_source",
        pre=True,
        allow_reuse=True,
    )(_clean_optional_text)
    _normalize_lists = validator(
        "supporting_messages",
        "citations",
        "secondary_elements",
        "reading_order",
        "warnings",
        pre=True,
        always=True,
        allow_reuse=True,
    )(_clean_text_list)
