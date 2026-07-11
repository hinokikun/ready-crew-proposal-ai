"use client";

import { memo } from "react";
import { ArrowRight } from "lucide-react";
import { CopilotConfidence } from "./CopilotConfidence";
import { CopilotExplain } from "./CopilotExplain";
import type { CopilotRecommendation } from "./types";

type CopilotRecommendationsProps = {
  recommendations: CopilotRecommendation[];
  onOpenPanel: (panelId: string) => void;
};

export const CopilotRecommendations = memo(function CopilotRecommendations({ recommendations, onOpenPanel }: CopilotRecommendationsProps) {
  return (
    <section className="copilot-recommendations" aria-label="AIおすすめアクション">
      <div className="copilot-section-title">
        <span>AIおすすめアクション</span>
        <small>最大5件</small>
      </div>
      <div className="copilot-recommendation-list">
        {recommendations.map((item) => (
          <article className="copilot-recommendation" key={item.id}>
            <div className="copilot-recommendation-head">
              <span>{item.stars}</span>
              <strong>{item.title}</strong>
            </div>
            <p>{item.detail}</p>
            <CopilotConfidence confidence={item.confidence} signals={item.signals} />
            <CopilotExplain reasons={item.reasons} />
            <button className="secondary-button compact-button" type="button" onClick={() => onOpenPanel(item.targetPanelId)}>
              {item.actionLabel}
              <ArrowRight size={14} aria-hidden="true" />
            </button>
          </article>
        ))}
      </div>
    </section>
  );
});
