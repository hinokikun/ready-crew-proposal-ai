"use client";

import { memo } from "react";
import { ArrowRight, Plus } from "lucide-react";
import type { QuickAction } from "./types";

type QuickActionsProps = {
  actions: QuickAction[];
  isAdmin: boolean;
  onOpenPanel: (panelId: string) => void;
};

export const QuickActions = memo(function QuickActions({ actions, isAdmin, onOpenPanel }: QuickActionsProps) {
  const visibleActions = actions.filter((action) => !action.adminOnly || isAdmin);

  return (
    <nav className="operations-quick-actions" aria-label="ショートカット">
      {visibleActions.map((action) => (
        <button
          className="operations-shortcut-button"
          key={action.label}
          onClick={() => onOpenPanel(action.target)}
          type="button"
          title={action.label}
        >
          {action.label.startsWith("＋") ? <Plus size={14} aria-hidden="true" /> : <ArrowRight size={14} aria-hidden="true" />}
          {action.label}
        </button>
      ))}
    </nav>
  );
});
