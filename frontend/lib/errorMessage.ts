export type FriendlyError = {
  category: string;
  title: string;
  cause: string;
  action: string;
};

export function toFriendlyError(error: unknown): FriendlyError {
  const message = error instanceof Error ? error.message : String(error ?? "");
  const normalized = message.toLowerCase();

  if (/beautiful\.ai|beautiful_ai/.test(normalized)) {
    if (/401|unauthorized|apiキー|api key/.test(normalized)) {
      return {
        category: "Beautiful.ai認証エラー",
        title: "Beautiful.ai APIキーを確認してください",
        cause: "Beautiful.ai APIキーが未設定、または無効になっている可能性があります。",
        action: "RenderのBeautiful.ai APIキー設定を確認してください。既存PPTXも利用できます。"
      };
    }
    if (/403|forbidden|権限/.test(normalized)) {
      return {
        category: "Beautiful.ai権限エラー",
        title: "Beautiful.ai APIの利用権限が有効になっていません",
        cause: "Beautiful.ai側のAPI利用権限、プラン、またはワークスペース設定に問題がある可能性があります。",
        action: "Beautiful.aiの契約・API権限を確認してください。既存PPTXも利用できます。"
      };
    }
    if (/429|rate|limit|上限/.test(normalized)) {
      return {
        category: "Beautiful.ai利用上限",
        title: "Beautiful.aiの利用上限に達しました",
        cause: "Beautiful.ai APIの利用回数または処理制限に達した可能性があります。",
        action: "時間を置くか、既存PPTXをご利用ください。"
      };
    }
    if (/timeout|504/.test(normalized)) {
      return {
        category: "Beautiful.aiタイムアウト",
        title: "Beautiful.aiの処理に時間がかかっています",
        cause: "Beautiful.ai側のスライド生成処理がタイムアウトしました。",
        action: "時間を置いて再試行してください。既存PPTXも利用できます。"
      };
    }
    return {
      category: "Beautiful.ai連携エラー",
      title: "Beautiful.ai提案書を作成できませんでした",
      cause: "Beautiful.ai連携設定、通信、または外部サービス側で問題が発生しました。",
      action: "既存PPTXをご利用ください。設定は管理者に確認してください。"
    };
  }

  if (/401|403|auth|login|password|unauthorized|forbidden|認証|ログイン/.test(normalized)) {
    return {
      category: "認証エラー",
      title: "ログイン状態を確認してください",
      cause: "ログイン期限切れ、権限不足、または認証設定に問題がある可能性があります。",
      action: "一度ログアウトして再ログインしてください。管理者の場合はadmin権限とRenderの認証環境変数を確認してください。"
    };
  }

  if (/429|rate|quota|openai|api limit|api制限|利用上限/.test(normalized)) {
    return {
      category: "OpenAI API制限",
      title: "AI APIの利用上限に達した可能性があります",
      cause: "短時間の利用回数、API利用上限、またはリクエスト設定が原因の可能性があります。",
      action: "時間を置いて再実行してください。研修やデモではRenderでUSE_MOCK_AI=trueにしてモックモードで確認できます。"
    };
  }

  if (/maintenance|maintenance_mode|メンテナンス|新規作成.*停止|一時停止/.test(normalized)) {
    return {
      category: "メンテナンス中",
      title: "現在、新規作成は一時停止中です",
      cause: "管理者、または環境変数によりMaintenance Modeが有効になっています。",
      action: "閲覧や履歴確認は利用できます。新規作成、PPT/PDF作成は管理者の解除後に再実行してください。"
    };
  }

  if (/failed to fetch|network|cors|timeout|502|503|504|backend|render|通信|接続/.test(normalized)) {
    return {
      category: "通信エラー",
      title: "Backendへ接続できません",
      cause: "Backend未起動、Renderのスリープ、CORS設定、またはNEXT_PUBLIC_API_URLの設定差異が考えられます。",
      action: "画面を再読み込みし、数十秒待って再試行してください。続く場合はRender起動状態、VercelのNEXT_PUBLIC_API_URL、BackendのCORS設定を確認してください。"
    };
  }

  if (/400|422|validation|min_length|input|入力不足/.test(normalized)) {
    return {
      category: "入力不足",
      title: "入力内容を確認してください",
      cause: "案件概要が短い、必須情報が不足している、または送信形式が想定と異なる可能性があります。",
      action: "案件メール、会社名、困りごと、予算、納期のうち分かる範囲を追記してください。不明な項目は「未定」「要確認」で問題ありません。"
    };
  }

  if (/ppt|powerpoint|pptx/.test(normalized)) {
    return {
      category: "PPTX作成失敗",
      title: "PowerPointの作成に失敗しました",
      cause: "スライド生成処理、入力データ、またはBackend側の一時的な問題の可能性があります。",
      action: "提案書作成が完了しているか確認し、もう一度ダウンロードしてください。続く場合は入力文字数を減らし、Renderログを確認してください。"
    };
  }

  if (/pdf|estimate/.test(normalized)) {
    return {
      category: "PDF作成失敗",
      title: "見積書PDFの作成に失敗しました",
      cause: "PDF生成処理、見積データ、またはBackend側の一時的な問題の可能性があります。",
      action: "もう一度PDFを作成してください。続く場合は見積条件の入力を短くし、Renderログを確認してください。"
    };
  }

  return {
    category: "不明なエラー",
    title: "処理中にエラーが発生しました",
    cause: "一時的な通信問題、入力内容、またはBackend側の問題の可能性があります。",
    action: "再実行してください。解決しない場合はBackendログと環境変数を確認してください。"
  };
}
