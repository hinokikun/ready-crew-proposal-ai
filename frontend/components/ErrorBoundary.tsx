"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertCircle, RotateCcw } from "lucide-react";
import { reportError } from "@/lib/errorReporter";

type ErrorBoundaryProps = {
  children: ReactNode;
};

type ErrorBoundaryState = {
  hasError: boolean;
};

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = {
    hasError: false
  };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    reportError(error, {
      source: "react_error_boundary",
      componentStack: errorInfo.componentStack
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <main className="auth-shell">
          <section className="app-error-card" role="alert">
            <AlertCircle size={24} aria-hidden="true" />
            <div>
              <p className="eyebrow">エラー</p>
              <h1>画面の一部を表示できませんでした</h1>
              <p>一時的な通信または画面表示の問題が発生しました。再読み込みしても解決しない場合は、管理者へお問い合わせください。</p>
              <button className="primary-button" type="button" onClick={() => window.location.reload()}>
                <RotateCcw size={16} aria-hidden="true" />
                再読み込み
              </button>
            </div>
          </section>
        </main>
      );
    }

    return this.props.children;
  }
}
