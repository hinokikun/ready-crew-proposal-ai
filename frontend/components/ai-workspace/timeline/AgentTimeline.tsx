"use client";

import { memo } from "react";
import { ChevronDown, Loader2, RotateCcw } from "lucide-react";
import type { AgentRow, AgentStatus, AiWorkspaceAgentKey } from "@/components/ai-workspace/types";

type AgentTimelineProps = {
  agents: AgentRow[];
  expandedAgent: AiWorkspaceAgentKey | null;
  rerunAgent: AiWorkspaceAgentKey | null;
  canAdminRerun: boolean;
  isLoading: boolean;
  onToggleAgent: (agent: AiWorkspaceAgentKey) => void;
  onRerunAgent: (agent: AiWorkspaceAgentKey) => void;
};

function getStatusLabel(status: AgentStatus) {
  if (status === "done") return "完了";
  if (status === "active") return "作業中";
  return "待機";
}

function AgentTimelineBase({ agents, expandedAgent, rerunAgent, canAdminRerun, isLoading, onToggleAgent, onRerunAgent }: AgentTimelineProps) {
  return (
    <div className="ai-agent-list" aria-label="AI社員の作業状態">
      {agents.map((agent) => {
        const isExpanded = expandedAgent === agent.key;
        return (
          <article className={`ai-agent-row is-${agent.status} ai-agent-theme-${agent.colorClass}`} key={agent.key}>
            <button className="ai-agent-toggle" type="button" onClick={() => onToggleAgent(agent.key)} aria-expanded={isExpanded}>
              <span className="ai-agent-row-title">
                <span className="ai-row-avatar">{agent.iconLabel}</span>
                <span>
                  <strong>{agent.name}</strong>
                  <small>{agent.role}</small>
                </span>
              </span>
              <span className="ai-agent-row-summary">{agent.status === "done" ? agent.doneComment : agent.status === "active" ? agent.activeComment : agent.comment}</span>
              <span className={`ai-agent-status is-${agent.status}`}>{getStatusLabel(agent.status)}</span>
              <ChevronDown className={isExpanded ? "is-open" : ""} size={18} aria-hidden="true" />
            </button>

            {isExpanded && (
              <div className="ai-agent-detail">
                <dl>
                  <div>
                    <dt>担当</dt>
                    <dd>{agent.responsibility}</dd>
                  </div>
                  <div>
                    <dt>現在の作業</dt>
                    <dd>{agent.task}</dd>
                  </div>
                  <div>
                    <dt>コメント</dt>
                    <dd>{agent.status === "done" ? agent.doneComment : agent.status === "active" ? agent.activeComment : agent.comment}</dd>
                  </div>
                </dl>
                {canAdminRerun && (
                  <button className="ai-rerun-button" type="button" onClick={() => onRerunAgent(agent.key)} disabled={isLoading && agent.key !== "sales"}>
                    {rerunAgent === agent.key ? <Loader2 className="spin" size={14} aria-hidden="true" /> : <RotateCcw size={14} aria-hidden="true" />}
                    {rerunAgent === agent.key ? "再実行中" : agent.rerunLabel}
                  </button>
                )}
              </div>
            )}
          </article>
        );
      })}
    </div>
  );
}

export const AgentTimeline = memo(AgentTimelineBase);
