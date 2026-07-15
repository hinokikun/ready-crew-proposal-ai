"use client";

import { FormEvent, useState } from "react";
import { changeOwnPassword } from "@/lib/api";
import { clearAuthToken, type AuthUser } from "@/lib/auth";

type AccountSecurityPanelProps = {
  currentUser: AuthUser | null;
};

export function AccountSecurityPanel({ currentUser }: AccountSecurityPanelProps) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    setError("");
    if (newPassword !== confirmPassword) {
      setError("新しいパスワードが一致しません。");
      return;
    }
    setIsSubmitting(true);
    try {
      const result = await changeOwnPassword({
        current_password: currentPassword,
        new_password: newPassword,
        new_password_confirm: confirmPassword
      });
      setMessage(result.message || "パスワードを変更しました。再ログインしてください。");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      clearAuthToken();
      window.dispatchEvent(new Event("ready-crew-auth-changed"));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "パスワードを変更できませんでした。");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <details className="advanced-foldout account-security-panel" id="account-security-panel">
      <summary>アカウント設定を開く</summary>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Account</p>
          <h2>パスワード変更</h2>
        </div>
        <span>{currentUser?.email || "未ログイン"}</span>
      </div>
      {currentUser?.password_change_required && (
        <p className="status-note warning">管理者により、次回利用前のパスワード変更が必要です。</p>
      )}
      <form className="admin-user-form" onSubmit={handleSubmit}>
        <input
          aria-label="現在のパスワード"
          value={currentPassword}
          onChange={(event) => setCurrentPassword(event.target.value)}
          placeholder="現在のパスワード"
          type="password"
          required
        />
        <input
          aria-label="新しいパスワード"
          value={newPassword}
          onChange={(event) => setNewPassword(event.target.value)}
          placeholder="新しいパスワード（8文字以上）"
          type="password"
          required
          minLength={8}
        />
        <input
          aria-label="新しいパスワード確認"
          value={confirmPassword}
          onChange={(event) => setConfirmPassword(event.target.value)}
          placeholder="新しいパスワード確認"
          type="password"
          required
          minLength={8}
        />
        <button className="secondary-button" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "変更中" : "パスワードを変更"}
        </button>
      </form>
      <p className="status-note">パスワード、APIキー、Tokenは画面・ログ・DBに平文保存しません。</p>
      {message && <p className="status-note success">{message}</p>}
      {error && <p className="status-note error">{error}</p>}
    </details>
  );
}
