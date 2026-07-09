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
        <p className="eyebrow">Ready Crew Proposal AI Version 4.0</p>
        <h1>AI Digital Coworker（AI社員）</h1>
      </div>
      <div className="header-actions">
        <button className="status-pill mode-toggle" type="button" onClick={onToggleDarkMode}>
          {isDarkMode ? <Sun size={16} aria-hidden="true" /> : <Moon size={16} aria-hidden="true" />}
          {isDarkMode ? "Light" : "Dark"}
        </button>
        <div className="status-pill">
          <CheckCircle2 size={16} aria-hidden="true" />
          Version 4.0
        </div>
      </div>
    </section>
  );
}

export const Header = memo(HeaderBase);
