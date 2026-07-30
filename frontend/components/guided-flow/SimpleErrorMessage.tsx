"use client";

import { memo } from "react";
import { AlertCircle, RotateCw } from "lucide-react";

type SimpleErrorMessageProps = {
  message: string;
  onRetry?: () => void;
};

function userFriendlyMessage(message: string) {
  const normalized = message.toLowerCase();
  if (/maintenance|maintenance_mode|メンテナンス|新規作成.*停止/.test(normalized)) return "現在、新規作成は一時停止中です。履歴確認はできます。管理者の解除後にもう一度お試しください。";
  if (/429|rate|limit|quota|利用上限/.test(normalized)) return "AI APIの利用上限に達した可能性があります。少し時間を置いてからもう一度お試しください。";
  if (/401|unauthorized|認証|ログイン/.test(normalized)) return "ログイン情報の有効期限が切れた可能性があります。再度ログインしてください。";
  if (/403|forbidden|権限/.test(normalized)) return "この操作を行う権限がありません。管理者に権限を確認してください。";
  if (/404|not found|見つかり/.test(normalized)) return "必要な情報が見つかりませんでした。入力内容を確認して、もう一度お試しください。";
  if (/500|internal|server|backend|network|failed to fetch|timeout|通信|接続/.test(normalized)) return "通信が不安定、または一時的に処理できませんでした。少し時間を置いて再実行してください。";
  if (/ai|openai|生成|proposal|beautiful/.test(normalized)) return "AIによる作成を完了できませんでした。入力内容を確認して、もう一度お試しください。";
  return "入力内容または通信状況を確認して、もう一度お試しください。";
}

function SimpleErrorMessageBase({ message, onRetry }: SimpleErrorMessageProps) {
  if (!message) return null;
  const displayMessage = userFriendlyMessage(message);

  return (
    <div className="guided-error-message" role="alert">
      <AlertCircle size={18} aria-hidden="true" />
      <div>
        <strong>提案書を作成できませんでした</strong>
        <p>{displayMessage}</p>
        <small>時間をおいて再試行してください。解決しない場合は管理者へこの画面の内容をお知らせください。</small>
      </div>
      {onRetry && (
        <button className="secondary-button" onClick={onRetry} type="button">
          <RotateCw size={16} aria-hidden="true" />
          再試行
        </button>
      )}
    </div>
  );
}

export const SimpleErrorMessage = memo(SimpleErrorMessageBase);
