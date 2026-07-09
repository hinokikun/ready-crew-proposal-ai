export type FriendlyError = {
  category: string;
  title: string;
  cause: string;
  action: string;
};

export function toFriendlyError(error: unknown): FriendlyError {
  const message = error instanceof Error ? error.message : String(error ?? "");
  const normalized = message.toLowerCase();

  if (/401|403|ログイン|認証|password|unauthorized/.test(normalized)) {
    return {
      category: "認証エラー",
      title: "ログインが必要です",
      cause: "認証期限切れ、パスワード誤り、または管理者パスワード未設定の可能性があります。",
      action: "再ログインしてください。解消しない場合はRenderのAPP_ACCESS_PASSWORD設定を確認してください。"
    };
  }

  if (/429|rate|quota|制限|上限/.test(normalized)) {
    return {
      category: "OpenAI API制限",
      title: "AI APIの利用制限に達した可能性があります",
      cause: "短時間の利用回数、API利用上限、または請求設定が原因の可能性があります。",
      action: "少し時間を置いて再読み込みしてください。社内デモ中はBackendのUSE_MOCK_AI=trueで動作確認できます。"
    };
  }

  if (/failed to fetch|network|cors|通信|接続|timeout|タイムアウト|502|503|504/.test(normalized)) {
    return {
      category: "通信エラー",
      title: "Backendへ接続できません",
      cause: "Backend未起動、Renderのスリープ、CORS設定、またはNEXT_PUBLIC_API_URLの不一致が考えられます。",
      action: "Backendを起動するか、Renderが起きるまで待って再読み込みしてください。VercelのAPI URL設定も確認してください。"
    };
  }

  if (/400|422|入力|不足|min_length|validation|短く/.test(normalized)) {
    return {
      category: "入力不足",
      title: "入力内容を確認してください",
      cause: "案件概要が短い、必須情報が不足している、または送信形式が想定と異なる可能性があります。",
      action: "案件メール、会社名、困りごと、予算、納期のいずれかを追記してください。不明な項目は未定でも大丈夫です。"
    };
  }

  if (/ppt|powerpoint|pptx/.test(normalized)) {
    return {
      category: "PPTX生成失敗",
      title: "PowerPoint生成に失敗しました",
      cause: "スライド生成処理、入力データ、またはBackend側の一時的な問題の可能性があります。",
      action: "「その他」から再度ダウンロードしてください。繰り返す場合は入力文字量を減らし、Backendログを確認してください。"
    };
  }

  if (/pdf|見積書/.test(normalized)) {
    return {
      category: "PDF生成失敗",
      title: "見積書PDF生成に失敗しました",
      cause: "PDF生成処理、見積データ、またはBackend側の一時的な問題の可能性があります。",
      action: "Backendログを確認し、提案書生成後に再度PDFを出力してください。"
    };
  }

  return {
    category: "不明なエラー",
    title: "処理中にエラーが発生しました",
    cause: "一時的な通信問題、入力内容、またはBackend側の問題の可能性があります。",
    action: "再実行し、解消しない場合はBackendログと環境変数を確認してください。"
  };
}
