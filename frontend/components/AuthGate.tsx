"use client";

import { FormEvent, ReactNode, useEffect, useState } from "react";
import { Lock, Loader2, ShieldCheck, UserRound } from "lucide-react";
import { clearAuthToken, getStoredLoginMode, loginWithPassword, saveLoginMode, verifyAuthToken, type LoginMode } from "@/lib/auth";
import { toFriendlyError } from "@/lib/errorMessage";

type AuthGateProps = {
  children: ReactNode;
};

const loginModeCopy: Record<LoginMode, { label: string; description: string; icon: typeof UserRound }> = {
  user: {
    label: "利用者ログイン",
    description: "提案書作成や案件管理を行う方",
    icon: UserRound
  },
  admin: {
    label: "管理者ログイン",
    description: "ユーザー管理やシステム設定を行う方",
    icon: ShieldCheck
  }
};

function getInitialLoginMode(): LoginMode {
  if (typeof window === "undefined") return "user";
  const params = new URLSearchParams(window.location.search);
  if (params.get("login") === "admin") return "admin";
  return getStoredLoginMode();
}

export function AuthGate({ children }: AuthGateProps) {
  const [isChecking, setIsChecking] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loginMode, setLoginMode] = useState<LoginMode>("user");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoginMode(getInitialLoginMode());
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

  function handleModeChange(nextMode: LoginMode) {
    setLoginMode(nextMode);
    saveLoginMode(nextMode);
    setError("");
  }

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoggingIn(true);
    setError("");
    try {
      await loginWithPassword(password, email, loginMode);
      window.dispatchEvent(new Event("ready-crew-auth-changed"));
      setEmail("");
      setPassword("");
      setIsAuthenticated(true);
    } catch (caught) {
      clearAuthToken();
      const message = caught instanceof Error ? caught.message : "";
      if (
        message.includes("管理者ログイン") ||
        message.includes("管理者権限") ||
        message.includes("利用者ログイン") ||
        message.includes("無効") ||
        message.includes("試験利用") ||
        message.includes("パスワード") ||
        message.includes("試行回数") ||
        message.includes("しばらく待って")
      ) {
        setError(message);
      } else {
        const friendly = toFriendlyError(caught);
        setError(`${friendly.title}。${friendly.action}`);
      }
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
    const CurrentIcon = loginModeCopy[loginMode].icon;
    return (
      <main className="auth-shell">
        <form className="auth-card" data-testid="login-form" onSubmit={handleLogin}>
          <div className="auth-icon">
            <Lock size={22} aria-hidden="true" />
          </div>
          <p className="eyebrow">Internal Trial Access</p>
          <h1>AI営業秘書</h1>
          <p>ログイン入口を選んでください。権限に合わない入口を選んだ場合は、安全のためログインを止めます。</p>

          <div className="auth-mode-grid" role="tablist" aria-label="ログイン入口">
            {(["user", "admin"] as const).map((mode) => {
              const Icon = loginModeCopy[mode].icon;
              return (
                <button
                  aria-selected={loginMode === mode}
                  className={loginMode === mode ? "auth-mode-card is-active" : "auth-mode-card"}
                  data-testid={`login-mode-${mode}`}
                  key={mode}
                  onClick={() => handleModeChange(mode)}
                  role="tab"
                  type="button"
                >
                  <Icon size={18} aria-hidden="true" />
                  <span>{loginModeCopy[mode].label}</span>
                  <small>{loginModeCopy[mode].description}</small>
                </button>
              );
            })}
          </div>

          <div className="auth-selected-mode" aria-live="polite">
            <CurrentIcon size={16} aria-hidden="true" />
            現在選択中: {loginModeCopy[loginMode].label}
          </div>

          <label className="field" htmlFor="login-email">
            <span>メールアドレス</span>
            <input
              autoComplete="username"
              id="login-email"
              onChange={(event) => setEmail(event.target.value)}
              placeholder={loginMode === "admin" ? "admin@example.com" : "member@example.com"}
              type="email"
              value={email}
            />
          </label>
          <label className="field" htmlFor="login-password">
            <span>アクセスパスワード</span>
            <input
              autoComplete="current-password"
              id="login-password"
              onChange={(event) => setPassword(event.target.value)}
              placeholder="パスワードを入力"
              type="password"
              value={password}
            />
          </label>
          {error && <div className="auth-error">{error}</div>}
          <button className="primary-button" data-testid="login-submit" disabled={isLoggingIn || !password.trim()} type="submit">
            {isLoggingIn ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <Lock size={18} aria-hidden="true" />}
            {isLoggingIn ? "ログイン中" : loginModeCopy[loginMode].label}
          </button>
          <small>パスワードはFrontendに保存しません。ログアウト後に保存されるのは、次回表示用のログイン入口だけです。</small>
        </form>
      </main>
    );
  }

  return <>{children}</>;
}
