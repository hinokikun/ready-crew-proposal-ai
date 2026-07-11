"use client";

import { memo } from "react";

type AgentProgressProps = {
  progress: number;
  isDone: boolean;
};

function AgentProgressBase({ progress, isDone }: AgentProgressProps) {
  return (
    <div className="ai-progress-block" aria-label={`進捗 ${progress}%`}>
      <div className="ai-progress-track">
        <span style={{ width: `${progress}%` }} />
      </div>
      <div className="ai-progress-meta">
        <span>{progress}%</span>
        <span>{isDone ? "完了" : "進行中"}</span>
      </div>
    </div>
  );
}

export const AgentProgress = memo(AgentProgressBase);
