"use client";

import { memo } from "react";

type CopilotConfidenceProps = {
  confidence: number;
  signals: string[];
};

export const CopilotConfidence = memo(function CopilotConfidence({ confidence, signals }: CopilotConfidenceProps) {
  return (
    <div className="copilot-confidence" aria-label="信頼度">
      <div>
        <span>信頼度</span>
        <strong>{confidence}%</strong>
      </div>
      <ul>
        {signals.map((signal) => (
          <li key={signal}>{signal}</li>
        ))}
      </ul>
    </div>
  );
});
