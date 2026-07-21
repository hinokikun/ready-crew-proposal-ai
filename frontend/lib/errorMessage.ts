export type FriendlyError = {
  category: string;
  title: string;
  cause: string;
  action: string;
};

const userFriendlyErrorMessages: Record<string, string> = {
  BEAUTIFUL_AI_NOT_CONFIGURED: "Beautiful.aiの設定が完了していません。管理者に設定内容の確認を依頼してください。",
  BEAUTIFUL_AI_INVALID_API_KEY: "Beautiful.aiのAPIキーが無効です。管理者に設定内容の確認を依頼してください。",
  BEAUTIFUL_AI_ACCESS_DENIED: "Beautiful.aiのWorkspaceまたはAPI利用権限を確認してください。",
  BEAUTIFUL_AI_API_ERROR: "Beautiful.aiでプレゼンテーションを作成できませんでした。時間を置いて再度お試しください。",
  BEAUTIFUL_AI_RATE_LIMIT: "Beautiful.aiの利用上限に達しました。時間を置いて再度お試しください。",
  BEAUTIFUL_AI_URL_MISSING: "プレゼンテーションは作成されましたが、表示用URLを取得できませんでした。",
  BEAUTIFUL_AI_VIEW_ONLY_URL: "編集用URLは取得できなかったため、閲覧用URLを開きます。",
  AUTH_REQUIRED: "ログイン情報の有効期限が切れました。再度ログインしてください。",
  BACKEND_UNREACHABLE: "Backendに接続できません。Backendが起動しているか確認してください。",
  REQUEST_TIMEOUT: "通信がタイムアウトしました。時間を置いて再度お試しください。",
  POPUP_BLOCKED: "新しいタブを開けませんでした。ブラウザでlocalhostのポップアップを許可してください。"
};

export function getUserFriendlyErrorMessage(error: unknown, fallback = "処理を完了できませんでした。時間を置いて再度お試しください。") {
  const raw = error instanceof Error ? error.message : String(error ?? "");
  const normalized = raw.toLowerCase();
  for (const [code, message] of Object.entries(userFriendlyErrorMessages)) {
    if (raw.includes(code) || normalized.includes(code.toLowerCase())) {
      return message;
    }
  }
  if (/beautiful_ai_disabled|beautiful_ai_missing_api_key|beautiful_ai_not_configured|not configured|未設定|設定.*不足/.test(normalized)) {
    return userFriendlyErrorMessages.BEAUTIFUL_AI_NOT_CONFIGURED;
  }
  if (/beautiful_ai_invalid_api_key/i.test(raw)) {
    return userFriendlyErrorMessages.BEAUTIFUL_AI_INVALID_API_KEY;
  }
  if (/beautiful_ai_rate_limit|rate limit|429/i.test(raw)) {
    return userFriendlyErrorMessages.BEAUTIFUL_AI_RATE_LIMIT;
  }
  if (/401|unauthorized|auth_required/.test(normalized)) {
    return userFriendlyErrorMessages.AUTH_REQUIRED;
  }
  if (/beautiful_ai_access_not_enabled|403|forbidden/.test(normalized)) {
    return "このアカウントまたはWorkspaceではBeautiful.aiを利用できません。権限を確認してください。";
  }
  if (/beautiful_ai_timeout|timeout|abort/.test(normalized)) {
    return userFriendlyErrorMessages.REQUEST_TIMEOUT;
  }
  if (/failed to fetch|network|cors|backend|502|503|504/.test(normalized)) {
    return userFriendlyErrorMessages.BACKEND_UNREACHABLE;
  }
  if (/beautiful_ai|beautiful\.ai/.test(normalized)) {
    return userFriendlyErrorMessages.BEAUTIFUL_AI_API_ERROR;
  }
  return fallback;
}

export function toFriendlyError(error: unknown): FriendlyError {
  const message = error instanceof Error ? error.message : String(error ?? "");
  const normalized = message.toLowerCase();

  if (/beautiful\.ai|beautiful_ai/.test(normalized)) {
    if (/invalid_api_key|401|api key|apiキー/.test(normalized)) {
      return {
        category: "Beautiful.ai認証エラー",
        title: "Beautiful.ai APIキーが無効です",
        cause: "Beautiful.ai APIキーが未設定、無効、または期限切れの可能性があります。",
        action: "管理者にRenderのBeautiful.ai APIキー設定を確認してもらってください。既存PPTXは利用できます。"
      };
    }
    if (/access_not_enabled|403|workspace|forbidden/.test(normalized)) {
      return {
        category: "Beautiful.ai権限エラー",
        title: "Beautiful.ai Workspaceにアクセスできません",
        cause: "Beautiful.ai側のAPI権限、契約、またはWorkspace設定に問題がある可能性があります。",
        action: "管理者にBeautiful.aiのWorkspace IDとAPI権限を確認してもらってください。"
      };
    }
    if (/rate_limit|429|rate|limit/.test(normalized)) {
      return {
        category: "Beautiful.ai利用上限",
        title: "Beautiful.aiの利用上限に達しました",
        cause: "短時間の利用回数、またはBeautiful.ai側の処理制限に達した可能性があります。",
        action: "時間を置いて再試行してください。急ぎの場合は既存PPTXをご利用ください。"
      };
    }
    if (/redirect|endpoint_not_found|404/.test(normalized)) {
      return {
        category: "Beautiful.ai接続先エラー",
        title: "Beautiful.ai APIの接続先を確認してください",
        cause: "BackendのBeautiful.ai接続先URLがBeautiful.ai側の期待するURLと異なる可能性があります。",
        action: "管理者にBeautiful.ai診断情報のResolved Endpointを確認してもらってください。"
      };
    }
    if (/timeout|504|network|failed to fetch/.test(normalized)) {
      return {
        category: "Beautiful.ai通信エラー",
        title: "Beautiful.aiへ接続できません",
        cause: "ネットワーク、Render、Beautiful.ai側の一時的な通信問題が考えられます。",
        action: "時間を置いて再試行してください。解決しない場合は管理者に通信履歴を確認してもらってください。"
      };
    }
    if (/service_error|500|502|503/.test(normalized)) {
      return {
        category: "Beautiful.aiサーバーエラー",
        title: "Beautiful.aiサーバー側でエラーが発生しました",
        cause: "Beautiful.ai側の一時的な障害、またはAPI応答の形式が想定と異なる可能性があります。",
        action: "既存PPTXを利用し、管理者にBeautiful.ai診断情報のHTTP StatusとResponse Textを確認してもらってください。"
      };
    }
    if (/400|bad_request/.test(normalized)) {
      return {
        category: "Beautiful.ai送信内容エラー",
        title: "Beautiful.aiへ送信した内容を確認してください",
        cause: "Beautiful.ai APIが送信内容を受け付けませんでした。",
        action: "提案内容を短くするか、既存PPTXをご利用ください。"
      };
    }
    if (/401|unauthorized|invalid_api_key|api key|apiキー/.test(normalized)) {
      return {
        category: "Beautiful.ai認証エラー",
        title: "Beautiful.ai APIキーを確認してください",
        cause: "Beautiful.ai APIキーが未設定、または無効になっている可能性があります。",
        action: "RenderのBeautiful.ai APIキー設定を確認してください。既存PPTXも利用できます。"
      };
    }
    if (/403|forbidden|access_not_enabled|権限/.test(normalized)) {
      return {
        category: "Beautiful.ai権限エラー",
        title: "Beautiful.ai APIの利用権限が有効になっていません",
        cause: "Beautiful.ai側のAPI利用権限、プラン、またはワークスペース設定に問題がある可能性があります。",
        action: "Beautiful.aiの契約・API権限を確認してください。既存PPTXも利用できます。"
      };
    }
    if (/404|endpoint_not_found/.test(normalized)) {
      return {
        category: "Beautiful.ai接続先エラー",
        title: "Beautiful.ai APIの接続先が見つかりません",
        cause: "BackendのBeautiful.ai接続先設定、またはBeautiful.ai側のAPIエンドポイントが想定と異なる可能性があります。",
        action: "RenderのBEAUTIFUL_AI_BASE_URLを確認してください。既存PPTXも利用できます。"
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
      action: "一度ログアウトして再ログインしてください。管理者は権限とRenderの認証環境変数を確認してください。"
    };
  }

  if (/429|rate|quota|openai|api limit|api制限|利用上限/.test(normalized)) {
    return {
      category: "OpenAI API制限",
      title: "AI APIの利用上限に達した可能性があります",
      cause: "短時間の利用集中、API利用上限、またはリクエスト設定が原因の可能性があります。",
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
      cause: "案件概要が短い、必要情報が不足している、または送信形式が想定と異なる可能性があります。",
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
