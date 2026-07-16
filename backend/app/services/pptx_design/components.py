from __future__ import annotations

from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN

from app.services.pptx_parts.content import _trim, unique_items
from app.services.pptx_parts.drawing import add_card, add_shape, add_text
from app.services.pptx_theme import COLORS, SECTION_COLORS


def add_metric_card(slide, label: str, value: str, x: float, y: float, w: float, h: float, accent: str) -> None:
    add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill=COLORS["white"], line=COLORS["line"])
    add_shape(slide, MSO_SHAPE.RECTANGLE, x, y, w, 0.08, fill=accent, line=accent)
    add_text(slide, _trim(label, 22), x + 0.24, y + 0.26, w - 0.48, 0.22, size=13, color=COLORS["muted"], bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, _trim(value, 18), x + 0.24, y + 0.74, w - 0.48, 0.42, size=24, color=accent, bold=True, align=PP_ALIGN.CENTER)


def add_process_step(slide, index: int, title: str, body: str, x: float, y: float, w: float, accent: str) -> None:
    add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, 1.28, fill=COLORS["white"], line=COLORS["line"])
    add_shape(slide, MSO_SHAPE.OVAL, x + 0.22, y + 0.28, 0.48, 0.48, fill=accent, line=accent)
    add_text(slide, str(index), x + 0.22, y + 0.39, 0.48, 0.14, size=11, color=COLORS["white"], bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, _trim(title, 20), x + 0.86, y + 0.26, w - 1.05, 0.24, size=16, color=COLORS["navy"], bold=True)
    add_text(slide, _trim(body, 42), x + 0.86, y + 0.72, w - 1.05, 0.34, size=14, color=COLORS["text"])


def add_architecture_diagram(slide, nodes: list[str], x: float, y: float, w: float, h: float) -> None:
    clean_nodes = unique_items(nodes, 5)
    if len(clean_nodes) < 4:
        clean_nodes = unique_items(clean_nodes + ["INPUT", "AI", "CHECK", "OUTPUT"], 5)
    node_w = min(2.25, (w - 0.55 * (len(clean_nodes) - 1)) / len(clean_nodes))
    for idx, node in enumerate(clean_nodes):
        sx = x + idx * (node_w + 0.55)
        accent = SECTION_COLORS[idx % len(SECTION_COLORS)]
        add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, sx, y, node_w, h, fill=COLORS["white"], line=COLORS["line"])
        add_shape(slide, MSO_SHAPE.OVAL, sx + node_w / 2 - 0.28, y + 0.28, 0.56, 0.56, fill=accent, line=accent)
        add_text(slide, str(idx + 1), sx + node_w / 2 - 0.28, y + 0.41, 0.56, 0.14, size=11, color=COLORS["white"], bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, _trim(node, 24), sx + 0.2, y + 1.05, node_w - 0.4, 0.42, size=14, color=COLORS["navy"], bold=True, align=PP_ALIGN.CENTER)
        if idx < len(clean_nodes) - 1:
            add_shape(slide, MSO_SHAPE.CHEVRON, sx + node_w + 0.12, y + 0.72, 0.34, 0.42, fill=COLORS["line_dark"], line=COLORS["line_dark"])


def add_timeline(slide, phases: list[str], x: float, y: float, w: float) -> None:
    clean_phases = unique_items(phases, 5)
    phase_count = min(len(clean_phases), 5)
    if phase_count == 0:
        return
    segment_w = w / phase_count
    add_shape(slide, MSO_SHAPE.RECTANGLE, x + 0.2, y + 0.68, w - 0.4, 0.05, fill=COLORS["line_dark"], line=COLORS["line_dark"])
    for idx, phase in enumerate(clean_phases[:phase_count]):
        sx = x + idx * segment_w
        accent = SECTION_COLORS[idx % len(SECTION_COLORS)]
        add_shape(slide, MSO_SHAPE.OVAL, sx + segment_w / 2 - 0.2, y + 0.5, 0.4, 0.4, fill=accent, line=accent)
        add_text(slide, _trim(phase, 22), sx + 0.1, y + 1.06, segment_w - 0.2, 0.38, size=14, color=COLORS["text"], bold=True, align=PP_ALIGN.CENTER)


def add_estimate_overview(slide, total: str, fit: str, scope: str) -> None:
    add_metric_card(slide, "Estimate Range", total, 0.95, 1.48, 3.45, 1.55, COLORS["blue"])
    add_metric_card(slide, "Budget Fit", fit, 4.78, 1.48, 3.45, 1.55, COLORS["green"])
    add_card(slide, "Scope", scope, 8.62, 1.48, 3.65, 1.55, COLORS["teal"], COLORS["white"])


def add_next_action_cards(slide, items: list[str], x: float, y: float, w: float) -> None:
    clean_items = unique_items(items, 4)
    for idx, item in enumerate(clean_items[:4]):
        add_process_step(slide, idx + 1, f"Action {idx + 1}", item, x + idx * (w / 4), y, w / 4 - 0.2, SECTION_COLORS[idx])
