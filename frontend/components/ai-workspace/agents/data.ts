import type { AgentContent, AiWorkspaceAgentKey } from "@/components/ai-workspace/types";

export const agentOrder: AiWorkspaceAgentKey[] = ["secretary", "sales", "director", "pm", "president"];

export const agentContent: Record<AiWorkspaceAgentKey, AgentContent> = {
  secretary: {
    key: "secretary",
    name: "AI秘書",
    role: "受付",
    responsibility: "案件メールを受け取り、会社名・目的・不足情報を整理します。",
    iconLabel: "秘",
    colorClass: "secretary",
    headline: "案件を受け付けています",
    task: "案件メール、議事録、URLから提案準備に必要な情報を整理します。",
    comment: "案件メールが貼られると、必要な情報だけを抜き出します。",
    activeComment: "案件メールを読み取り、会社名・目的・予算・納期を確認しています。",
    doneComment: "案件受付と情報整理が完了しました。",
    chatMessage: "案件メールを受付しました。必要な情報を整理します。",
    activeLog: "AI秘書が案件を受付",
    rerunLabel: "AI秘書だけ再整理"
  },
  sales: {
    key: "sales",
    name: "AI営業",
    role: "提案",
    responsibility: "顧客課題、競合、勝ち筋を踏まえて提案方針を作ります。",
    iconLabel: "営",
    colorClass: "sales",
    headline: "提案方針を作成しています",
    task: "課題、競合、KPI、勝ち筋を整理し、営業提案の骨子を作ります。",
    comment: "顧客に刺さる提案コンセプトを組み立てます。",
    activeComment: "比較対象を確認中。導入効果と運用定着の勝ち筋を見ています。",
    doneComment: "提案方針と勝ち筋を作成しました。",
    chatMessage: "競合を調査しています。検索導線と実績訴求で勝てる構成にします。",
    activeLog: "AI営業が競合分析と提案作成を開始",
    rerunLabel: "AI営業だけ再実行"
  },
  director: {
    key: "director",
    name: "AIディレクター",
    role: "レビュー",
    responsibility: "提案ストーリー、情報設計、資料品質を確認します。",
    iconLabel: "D",
    colorClass: "director",
    headline: "提案ストーリーをレビューしています",
    task: "提案の流れ、課題との整合性、資料としての読みやすさを確認します。",
    comment: "テンプレート感が残らないように内容を磨きます。",
    activeComment: "提案ストーリーを改善中。課題と解決策がつながるよう整えています。",
    doneComment: "提案ストーリーのレビューが完了しました。",
    chatMessage: "提案ストーリーを確認しています。営業向けに伝わる順番へ整えます。",
    activeLog: "AIディレクターが提案ストーリーをレビュー",
    rerunLabel: "AIディレクターだけ再レビュー"
  },
  pm: {
    key: "pm",
    name: "AI PM",
    role: "見積",
    responsibility: "スケジュール、体制、費用、リスクを確認します。",
    iconLabel: "PM",
    colorClass: "pm",
    headline: "見積とスケジュールを確認しています",
    task: "予算、納期、体制、見積範囲、次回確認事項を整理します。",
    comment: "実行できる提案かどうかを現実的に確認します。",
    activeComment: "ROIを計算中。費用感とスケジュールの整合性を見ています。",
    doneComment: "見積とスケジュールの確認が完了しました。",
    chatMessage: "納期と見積を見直しています。無理のある範囲がないか確認します。",
    activeLog: "AI PMが見積とスケジュールを確認",
    rerunLabel: "AI PMだけ再確認"
  },
  president: {
    key: "president",
    name: "AI社長",
    role: "承認",
    responsibility: "顧客へ出せる提案か、経営視点で最終判断します。",
    iconLabel: "承",
    colorClass: "president",
    headline: "最終承認をしています",
    task: "提案価値、受注可能性、提出前リスクを最終確認します。",
    comment: "お客様へ提出できる品質かを確認します。",
    activeComment: "品質確認中。提案理由と提出前チェックをまとめています。",
    doneComment: "承認しました。提出前に人が最終確認してください。",
    chatMessage: "最後に品質確認します。なぜこの提案にしたかも説明します。",
    activeLog: "AI社長が最終レビューを開始",
    rerunLabel: "AI社長だけ最終レビュー"
  }
};

export const progressByAgent: Record<AiWorkspaceAgentKey, number> = {
  secretary: 18,
  sales: 45,
  director: 65,
  pm: 82,
  president: 94
};

export const thinkingMessages: Record<AiWorkspaceAgentKey, string[]> = {
  secretary: ["案件情報を読み取り中...", "導入要件を推定中...", "不足情報を確認中..."],
  sales: ["比較対象を確認中...", "導入効果を設計中...", "勝ち筋を整理中..."],
  director: ["提案ストーリーを確認中...", "テンプレート感を減らしています...", "課題と解決策のつながりを確認中..."],
  pm: ["ROIを計算中...", "見積範囲を確認中...", "納期リスクを確認中..."],
  president: ["品質確認中...", "提出前リスクを確認中...", "提案理由を3行で整理中..."]
};
