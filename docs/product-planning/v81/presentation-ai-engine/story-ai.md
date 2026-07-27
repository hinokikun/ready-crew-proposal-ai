# Story AI

- 責務: StoryPlanの営業文脈を読み、各スライドの主メッセージを明確化する。
- 入力: StoryPlan, Persona, Evidence.
- 出力: Slide objective refinement, transition notes.
- ルール処理: 根拠なし断定の検出。
- LLM処理: メッセージの短文化、決裁者向け言い換え。
- フォールバック: 元のStoryPlanを保持。
- Human Review: Evidence不足またはConfidence低の場合。
- テスト: Golden fixtureでStory TypeとSlide objectiveを比較。

