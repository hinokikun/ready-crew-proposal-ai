"use client";

import { memo } from "react";
import { CheckCircle2, LogOut, MonitorPlay, Moon, Sun } from "lucide-react";

type HeaderProps = {
  isDarkMode: boolean;
  isPresentationMode?: boolean;
  onTogglePresentationMode?: () => void;
  onToggleDarkMode: () => void;
  onLogout: () => void;
};

function HeaderBase({ isDarkMode, isPresentationMode = false, onTogglePresentationMode, onToggleDarkMode, onLogout }: HeaderProps) {
  return (
    <section className="workspace-header" aria-label="アプリ概要">
      <div>
        <p className="eyebrow">AI営業支援</p>
        <h1>AI営業秘書</h1>
      </div>
      <div className="header-actions">
        {onTogglePresentationMode && (
          <button
            className={`status-pill mode-toggle ${isPresentationMode ? "is-active" : ""}`}
            type="button"
            onClick={onTogglePresentationMode}
            aria-pressed={isPresentationMode}
          >
            <MonitorPlay size={16} aria-hidden="true" />
            発表モード
          </button>
        )}
        <button className="status-pill mode-toggle" type="button" onClick={onToggleDarkMode}>
          {isDarkMode ? <Sun size={16} aria-hidden="true" /> : <Moon size={16} aria-hidden="true" />}
          {isDarkMode ? "ライト" : "ダーク"}
        </button>
        <button className="status-pill mode-toggle" type="button" onClick={onLogout}>
          <LogOut size={16} aria-hidden="true" />
          ログアウト
        </button>
        <div className="status-pill">
          <CheckCircle2 size={16} aria-hidden="true" />
          v1.0 RC
        </div>
      </div>
    </section>
  );
}

export const Header = memo(HeaderBase);
