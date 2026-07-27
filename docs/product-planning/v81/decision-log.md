# Decision Log

| ID | Date | Status | Context | Decision | Alternatives | Consequences | Revisit |
|---|---|---|---|---|---|---|---|
| ADR-001 | 2026-07-23 | Accepted | PowerPoint完全編集は重い | 汎用PPT editorを目指さない | 完全互換editor | 開発範囲を営業提案に集中 | Studio要件拡大時 |
| ADR-002 | 2026-07-23 | Accepted | 営業提案が主用途 | 営業提案特化にする | 汎用プレゼン生成 | Story/見積/Qualityに集中 | ターゲット変更時 |
| ADR-003 | 2026-07-23 | Accepted | PPTX描画は複雑 | HTML近似Previewを採用 | PPTX直接編集 | 高速な確認が可能 | 差異が大きい時 |
| ADR-004 | 2026-07-23 | Accepted | 顧客が編集する | PPTXは編集可能Shape優先 | ラスター化 | 提出後編集しやすい | 表現力不足時 |
| ADR-005 | 2026-07-23 | Accepted | AIだけだと不安定 | AIとルールを組み合わせる | LLM単独 | 再現性と品質を両立 | 評価精度不足時 |
| ADR-006 | 2026-07-23 | Proposed | 生成が長い | Job化を検討 | 同期API継続 | 進捗/再試行が可能 | Version83 |
| ADR-007 | 2026-07-23 | Accepted | PPT品質が最優先 | Knowledge AIは後段 | 先にRAG | 資料品質へ集中 | V84開始時 |
| ADR-008 | 2026-07-23 | Accepted | Version71が研修提出基準 | V71を安定基準として維持 | 最新だけ追う | 既存研修機能を壊さない | V90 |

