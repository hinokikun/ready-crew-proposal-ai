# Diagram Composer

Diagram Composer designs diagrams as editable PowerPoint structures.

It must not rely on SmartArt as the primary expression.

---

## Diagram Types

| Diagram | Use |
|---|---|
| Process Flow | Work steps, handoffs, approvals |
| Layered Architecture | Systems, data, responsibilities |
| Feedback Loop | Learning, improvement, operations |
| Comparison Matrix | Options, competitors, before/after |
| KPI Dashboard | Metrics, targets, confidence |
| Roadmap | Phased adoption |
| Pyramid | Strategic hierarchy |
| Risk Map | Impact and likelihood |
| Funnel | Pipeline or conversion |

---

## Diagram Definition

```json
{
  "type": "process_flow",
  "nodes": [
    {"id": "input", "label": "案件入力", "role": "start"},
    {"id": "strategy", "label": "Sales Strategy AI", "role": "analysis"},
    {"id": "review", "label": "Human Review", "role": "control"}
  ],
  "edges": [
    {"from": "input", "to": "strategy", "label": ""},
    {"from": "strategy", "to": "review", "label": "確認"}
  ],
  "emphasis": ["review"],
  "notes": ["AI初期案ではなく、人間が確定したStrategyを使う"]
}
```

---

## Rules

- Diagrams must be editable PowerPoint shapes.
- Labels must be concise.
- Connectors should not cross through labels.
- Diagram must support the slide headline.
- Do not create decorative diagrams with no explanatory value.
- Complex diagrams must include reading order.

