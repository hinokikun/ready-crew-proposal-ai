"use client";

import { memo } from "react";
import { CheckCircle2, Loader2, PlayCircle } from "lucide-react";
import { AgentProgress } from "@/components/ai-workspace/AgentProgress";
import type { AgentContent, AiWorkspaceAgentKey } from "@/components/ai-workspace/types";

type AgentCardProps = {
  agent: AgentContent;
  activeAgentKey: AiWorkspaceAgentKey | null;
  hasInput: boolean;
  hasResult: boolean;
  progress: number;
  thinkingText: string;
  explanation?: string[];
};

function AgentCardBase({ agent, activeAgentKey, hasInput, hasResult, progress, thinkingText, explanation = [] }: AgentCardProps) {
  const isActive = Boolean(activeAgentKey) && !hasResult;
  const headline = !hasInput ? "案件メールの貼り付けを待っています" : hasResult ? "提案書が完成しました" : agent.headline;
  const comment = !hasInput ? "案件メールを貼ると、AI社員が順番に作業を進めます。" : hasResult ? agent.doneComment : thinkingText || agent.activeComment;

  return (
    <section className={`ai-workspace-main is-${hasResult ? "done" : isActive ? "active" : "idle"} ai-agent-theme-${agent.colorClass}`} aria-live="polite">
      <div className="ai-main-agent-meta">
        <div className="ai-main-agent-name">
          <span className="ai-main-avatar">{agent.iconLabel}</span>
          <div>
            <span>{agent.role}</span>
            <h3>{agent.name}</h3>
          </div>
        </div>
        <span className="ai-main-status-chip">{hasResult ? "承認済み" : isActive ? "作業中" : "待機"}</span>
      </div>

      <div className="ai-main-message">
        {isActive && <Loader2 className="spin" size={20} aria-hidden="true" />}
        {hasResult && <CheckCircle2 size={22} aria-hidden="true" />}
        {!isActive && !hasResult && <PlayCircle size={22} aria-hidden="true" />}
        <p>{headline}</p>
      </div>

      <AgentProgress progress={progress} isDone={hasResult} />

      <div className="ai-main-comment">
        <strong>{isActive ? "考えていること" : "コメント"}</strong>
        <p>{comment}</p>
      </div>

      {hasResult && explanation.length > 0 && (
        <div className="ai-president-explanation">
          <strong>AI社長の説明</strong>
          <ol>
            {explanation.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ol>
        </div>
      )}
    </section>
  );
}

export const AgentCard = memo(AgentCardBase);
