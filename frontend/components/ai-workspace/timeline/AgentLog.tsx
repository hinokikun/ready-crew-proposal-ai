"use client";

import { memo } from "react";
import type { AgentContent, AgentWorkLog } from "@/components/ai-workspace/types";

type AgentLogProps = {
  logs: AgentWorkLog[];
  agentsByKey: Record<string, AgentContent>;
};

function AgentLogBase({ logs, agentsByKey }: AgentLogProps) {
  return (
    <section className="agent-log-panel" aria-label="作業ログ">
      <div className="agent-log-heading">
        <strong>作業ログ</strong>
        <span>自動更新</span>
      </div>
      <div className="agent-log-list">
        {logs.map((log) => {
          const agent = agentsByKey[log.agentKey];
          return (
            <div className={`agent-log-item ai-agent-theme-${agent.colorClass}`} key={log.id}>
              <time>{log.time}</time>
              <span>{log.text}</span>
            </div>
          );
        })}
      </div>
    </section>
  );
}

export const AgentLog = memo(AgentLogBase);
