"use client";

import { FormEvent, ReactNode, useEffect, useState } from "react";
import { Lock, Loader2 } from "lucide-react";
import { clearAuthToken, loginWithPassword, verifyAuthToken } from "@/lib/auth";
import { toFriendlyError } from "@/lib/errorMessage";

type AuthGateProps = {
  children: ReactNode;
};

export function AuthGate({ children }: AuthGateProps) {
  const [isChecking, setIsChecking] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [password, setPassword] = useState("");
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    verifyAuthToken()
      .then((authenticated) => {
        if (!mounted) return;
        setIsAuthenticated(authenticated);
      })
      .catch(() => {
        if (!mounted) return;
        setIsAuthenticated(false);
        setError("Backendへ接続できません。Backend起動後に再読み込みしてください。");
      })
      .finally(() => {
        if (mounted) setIsChecking(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoggingIn(true);
    setError("");
    try {
      await loginWithPassword(password);
      setPassword("");
      setIsAuthenticated(true);
    } catch (caught) {
      clearAuthToken();
      const friendly = toFriendlyError(caught);
      setError(`${friendly.title}。${friendly.action}`);
    } finally {
      setIsLoggingIn(false);
    }
  }

  if (isChecking) {
    return (
      <main className="auth-shell">
        <div className="auth-card">
          <Loader2 className="spin" size={22} aria-hidden="true" />
          <p>ログイン状態を確認しています。</p>
        </div>
      </main>
    );
  }

  if (!isAuthenticated) {
    return (
      <main className="auth-shell">
        <form className="auth-card" onSubmit={handleLogin}>
          <div className="auth-icon">
            <Lock size={22} aria-hidden="true" />
          </div>
          <p className="eyebrow">Internal Trial Access</p>
          <h1>Ready Crew Proposal AI</h1>
          <p>社内試験導入用の簡易ログインです。管理者から共有されたパスワードを入力してください。</p>
          <label className="field">
            <span>アクセスパスワード</span>
            <input
              autoComplete="current-password"
              onChange={(event) => setPassword(event.target.value)}
              placeholder="APP_ACCESS_PASSWORD"
              type="password"
              value={password}
            />
          </label>
          {error && <div className="auth-error">{error}</div>}
          <button className="primary-button" disabled={isLoggingIn || !password.trim()} type="submit">
            {isLoggingIn ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <Lock size={18} aria-hidden="true" />}
            {isLoggingIn ? "ログイン中" : "ログイン"}
          </button>
          <small>パスワードはFrontendには保存しません。ログイン後は認証トークンのみブラウザに保存します。</small>
        </form>
      </main>
    );
  }

  return <>{children}</>;
}
