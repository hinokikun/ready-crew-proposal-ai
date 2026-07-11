"use client";

import { memo } from "react";

type CopilotExplainProps = {
  reasons: string[];
};

export const CopilotExplain = memo(function CopilotExplain({ reasons }: CopilotExplainProps) {
  return (
    <details className="copilot-explain">
      <summary>なぜこの判断か</summary>
      <ul>
        {reasons.map((reason) => (
          <li key={reason}>{reason}</li>
        ))}
      </ul>
    </details>
  );
});
