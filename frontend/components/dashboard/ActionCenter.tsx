"use client";

import { memo } from "react";
import { AlertTriangle, ArrowRight, CheckCircle2 } from "lucide-react";
import type { ActionItem } from "./types";

type ActionCenterProps = {
  actions: ActionItem[];
  onOpenPanel: (panelId: string) => void;
};

export const ActionCenter = memo(function ActionCenter({ actions, onOpenPanel }: ActionCenterProps) {
  return (
    <section className="operations-action-center" aria-label="今やるべきこと">
      <div className="operations-section-heading">
        <div>
          <p className="eyebrow">Action Center</p>
          <h2>今やるべきこと</h2>
        </div>
        <span>{actions.length}件</span>
      </div>

      {actions.length ? (
        <div className="operations-action-list">
          {actions.map((action) => (
            <article className={`operations-action-item priority-${action.priority}`} key={action.id}>
              <div className="operations-action-icon">
                <AlertTriangle size={18} aria-hidden="true" />
              </div>
              <div>
                <span>{action.stars}</span>
                <strong>{action.title}</strong>
                <p>{action.detail}</p>
              </div>
              <button className="secondary-button compact-button" type="button" onClick={() => onOpenPanel(action.targetPanelId)}>
                {action.actionLabel}
                <ArrowRight size={14} aria-hidden="true" />
              </button>
            </article>
          ))}
        </div>
      ) : (
        <div className="operations-empty-state">
          <CheckCircle2 size={18} aria-hidden="true" />
          <p>今すぐ対応が必要な項目はありません。</p>
        </div>
      )}
    </section>
  );
});
