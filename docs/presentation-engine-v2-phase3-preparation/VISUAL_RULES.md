# Visual Rules

## Intent Mapping

Static rules map upstream Slide Intent visual patterns to future Visual Director
defaults.

Examples:

| Slide Intent Visual Pattern | Visual Strategy | Layout Strategy | Reading Order |
|---|---|---|---|
| `hero` | `executive_frame` | `hero_focus` | `center_out` |
| `comparison` | `comparison` | `split_comparison` | `before_after` |
| `kpi_cards` | `evidence_first` | `metric_focus` | `scan_cards` |
| `timeline` | `roadmap_story` | `roadmap_lane` | `timeline` |
| `process` | `process_explanation` | `process_lane` | `left_to_right` |
| `matrix` | `evidence_first` | `matrix_view` | `z_pattern` |

## Reading Order Rules

Each layout has allowed reading orders. For example:

- `split_comparison` allows `before_after` or `left_to_right`
- `roadmap_lane` allows `timeline`
- `hero_focus` allows `center_out` or `title_first`

## Evidence Rules

Chart strategies require numeric evidence ids. Visual Plans must not select a
chart while numeric evidence is missing.

## Diagram and Chart Conflict Rules

One slide should have one primary visual. Diagram and chart can coexist only
when one is clearly supporting. Known conflicts are treated as errors.

## Placeholder Rules

Placeholder-like text is blocked unless the component explicitly allows a
placeholder, such as an image placeholder.

## Boundary Rules

The contract blocks downstream generation flags:

- `generated_blueprint`
- `generated_theme`
- `generated_coordinates`
- `generated_diagram`
- `generated_chart`
- `generated_pptx`
- `connected_to_runtime`
