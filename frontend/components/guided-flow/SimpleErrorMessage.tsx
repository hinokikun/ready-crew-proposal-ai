"use client";

import { memo } from "react";
import { AlertCircle, RotateCw } from "lucide-react";

type SimpleErrorMessageProps = {
  message: string;
  onRetry?: () => void;
};

function SimpleErrorMessageBase({ message, onRetry }: SimpleErrorMessageProps) {
  if (!message) return null;

  return (
    <div className="guided-error-message" role="alert">
      <AlertCircle size={18} aria-hidden="true" />
      <div>
        <strong>処理を完了できませんでした</strong>
        <p>{message}</p>
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
