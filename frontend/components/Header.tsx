"use client";

import { memo } from "react";
import { CheckCircle2, Moon, Sun } from "lucide-react";

type HeaderProps = {
  isDarkMode: boolean;
  onToggleDarkMode: () => void;
};

function HeaderBase({ isDarkMode, onToggleDarkMode }: HeaderProps) {
  return (
    <section className="workspace-header" aria-label="アプリ概要">
      <div>
        <p className="eyebrow">AI社員</p>
        <h1>AI営業秘書</h1>
      </div>
      <div className="header-actions">
        <button className="status-pill mode-toggle" type="button" onClick={onToggleDarkMode}>
          {isDarkMode ? <Sun size={16} aria-hidden="true" /> : <Moon size={16} aria-hidden="true" />}
          {isDarkMode ? "ライト" : "ダーク"}
        </button>
        <div className="status-pill">
          <CheckCircle2 size={16} aria-hidden="true" />
          バージョン 4.0
        </div>
      </div>
    </section>
  );
}

export const Header = memo(HeaderBase);
