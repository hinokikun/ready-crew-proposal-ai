# Diagram Catalog

This catalog constrains Visual Director AI and Diagram Composer decisions. The AI may select from this catalog, but the PowerPoint Renderer draws only the blueprint definition.

Minimum required catalog size: 50. This document defines 60 diagram types.

---

## 1. Diagram Selection Rules

- Select the simplest diagram that explains the slide goal.
- Do not use a diagram when a single metric, quote, or decision is clearer.
- Prefer one primary diagram per slide.
- Do not mix more than two diagram types on one slide.
- Diagram Composer defines nodes, groups, connectors, labels, and evidence mapping.
- Renderer does not choose a diagram type.

---

## 2. Diagram Types

| ID | Diagram type | Best for | Required data | Renderer note |
|---|---|---|---|---|
| D001 | Linear Timeline | chronological plan | phases, dates, milestones | horizontal or vertical axis |
| D002 | Roadmap Lanes | multi-stream rollout | lanes, phases, owners | lane bands plus milestone cards |
| D003 | Process Flow | step-by-step work | steps, sequence, outputs | connected rounded rectangles |
| D004 | Swimlane Process | cross-team process | lanes, steps, handoffs | lane labels plus connectors |
| D005 | Before After Flow | transformation | before steps, after steps | paired flows with contrast |
| D006 | 2x2 Matrix | prioritization | x-axis, y-axis, items | quadrant labels required |
| D007 | Risk Matrix | impact/probability | risks, impact, probability | severity color scale |
| D008 | Comparison Table | option comparison | options, criteria, ratings | max 5 columns |
| D009 | Feature Matrix | product feature comparison | features, vendors, support | check/partial/none states |
| D010 | KPI Dashboard | metric overview | metrics, labels, targets | card grid with charts optional |
| D011 | Metric Cards | few key numbers | metric, value, context | large-number cards |
| D012 | Waterfall | value bridge | baseline, increments | bar sequence with totals |
| D013 | Funnel | narrowing stages | stages, volumes | proportional or symbolic funnel |
| D014 | Pyramid | hierarchy | levels, labels | stacked trapezoids |
| D015 | Layered Architecture | systems and layers | layers, components | horizontal layer bands |
| D016 | Hub and Spoke | central capability | hub, spokes | central node and radial links |
| D017 | Network Map | many-to-many relations | nodes, relationships | node groups required |
| D018 | Tree | hierarchy breakdown | root, branches, leaves | left-to-right or top-down |
| D019 | Organization Chart | team structure | roles, reporting | role cards and connectors |
| D020 | Stakeholder Map | influence mapping | stakeholders, influence | quadrants or ring map |
| D021 | Value Chain | business flow | activities, value steps | linked stage cards |
| D022 | Customer Journey | experience stages | stages, emotions, touchpoints | journey line plus cards |
| D023 | Service Blueprint | front/backstage work | user actions, systems | layered swimlane |
| D024 | Data Flow | data movement | sources, transforms, outputs | arrows with data labels |
| D025 | System Integration Map | APIs and systems | systems, APIs, direction | connector labels mandatory |
| D026 | AI Pipeline | AI processing | input, model, review, output | model stage highlighted |
| D027 | Human-in-the-loop Loop | AI plus human review | AI action, review, feedback | loop connector required |
| D028 | Feedback Loop | continuous improvement | cycle steps, signals | circular arrows |
| D029 | Cycle | recurring process | stages | circular or radial cycle |
| D030 | Flywheel | compounding growth | loop stages, momentum | circular stages with emphasis |
| D031 | Maturity Model | capability growth | levels, current, target | level ladder |
| D032 | Capability Map | capability grouping | domains, capabilities | domain cards |
| D033 | Portfolio Map | investment distribution | initiatives, value, effort | matrix or bubble map |
| D034 | Bubble Chart | relative position | x, y, size | axes and legend required |
| D035 | Heatmap | intensity by category | rows, columns, values | color scale legend |
| D036 | Scorecard | evaluation summary | criteria, score, notes | score cells and summary |
| D037 | Radar Chart | multi-axis profile | dimensions, scores | optional; avoid dense labels |
| D038 | Bar Chart | category comparison | categories, values | labeled bars |
| D039 | Stacked Bar | composition | categories, segments | legend required |
| D040 | Line Chart | trend | dates, values | max 4 series |
| D041 | Area Chart | cumulative trend | dates, values | use sparingly |
| D042 | Donut Chart | part-to-whole | segments, values | max 5 segments |
| D043 | Gauge | status vs target | value, range, target | single metric only |
| D044 | Checklist | readiness or tasks | items, status | status icon per item |
| D045 | Decision Tree | decision path | conditions, outcomes | branch labels required |
| D046 | Assumption Map | assumptions and validation | assumptions, confidence | confidence markers |
| D047 | Evidence Stack | proof hierarchy | claims, evidence | stacked proof blocks |
| D048 | ROI Bridge | investment to outcome | cost, benefit, risk | bridge with evidence |
| D049 | Cost Breakdown | estimate categories | categories, ranges | avoid 10+ row tables |
| D050 | Pricing Ladder | plan comparison | tiers, values | tier cards |
| D051 | Scenario Comparison | scenarios | scenarios, outcomes | scenario cards or table |
| D052 | Dependency Map | dependent tasks | tasks, dependencies | arrow graph |
| D053 | Milestone Gate | phased approval | gates, criteria | stage gate markers |
| D054 | Risk Control Map | risks and controls | risks, mitigations | paired risk-control cards |
| D055 | Problem Cause Tree | root cause | problem, causes | tree with levels |
| D056 | Issue Cluster | grouped issues | issues, clusters | cluster labels required |
| D057 | Priority Ranking | ranked recommendations | items, priority | ranked cards or bars |
| D058 | Message Pyramid | executive story | main point, reasons, proof | pyramid or stack |
| D059 | One-page Business Case | decision summary | case, cost, benefit, risk | structured executive panel |
| D060 | Next Action Board | action plan | actions, owner, timing | board columns |

---

## 3. Diagram Definition Contract

Every diagram blueprint must provide:

```json
{
  "diagram_id": "diagram-slide-05",
  "diagram_type": "system_integration_map",
  "title": "API and CSV integration flow",
  "nodes": [],
  "groups": [],
  "connectors": [],
  "labels": [],
  "legend": [],
  "data": {},
  "evidence_refs": [],
  "layout_constraints": {
    "max_nodes": 12,
    "max_depth": 4,
    "reading_order": "left_to_right"
  },
  "fallback": {
    "diagram_type": "process_flow",
    "reason": "Renderer does not support requested diagram."
  }
}
```

---

## 4. Renderer Constraints

- Maximum node count should be 12 for standard slides.
- Tables should not exceed 5 columns in proposal decks.
- Charts must include source labels if data is externally derived.
- When data is missing, use placeholders marked as assumptions rather than invented values.
- Diagram labels must fit inside renderer-safe text boxes.
