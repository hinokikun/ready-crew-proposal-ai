"use client";

import { useEffect, useMemo, useState } from "react";
import { CheckCircle2 } from "lucide-react";
import { AgentCard } from "@/components/ai-workspace/AgentCard";
import { AgentChat } from "@/components/ai-workspace/AgentChat";
import { AgentLog } from "@/components/ai-workspace/AgentLog";
import { AgentTimeline } from "@/components/ai-workspace/AgentTimeline";
import { agentContent, agentOrder, progressByAgent } from "@/components/ai-workspace/data";
import type { AgentChatMessage, AgentRow, AgentWorkLog, AiWorkspaceAgentKey, AiWorkspaceStatus } from "@/components/ai-workspace/types";

export type { AiWorkspaceAgentKey } from "@/components/ai-workspace/types";

type AiWorkspacePanelProps = {
  status: AiWorkspaceStatus;
  hasInput: boolean;
  hasResult: boolean;
  isLoading: boolean;
  canAdminRerun: boolean;
  onRerunAgent: (agent: AiWorkspaceAgentKey) => void;
};

function getActiveAgent(status: AiWorkspaceStatus, hasInput: boolean, isLoading: boolean, stageIndex: number): AiWorkspaceAgentKey | null {
  if (!hasInput) return null;
  if (["typing", "analyzing", "question"].includes(status)) return "secretary";
  if (isLoading || ["reviewing", "generating"].includes(status)) return agentOrder[stageIndex] ?? "sales";
  return null;
}

function buildAgentRows(activeAgent: AiWorkspaceAgentKey | null, hasResult: boolean): AgentRow[] {
  const activeIndex = activeAgent ? agentOrder.indexOf(activeAgent) : -1;

  return agentOrder.map((key, index) => {
    let status: AgentRow["status"] = "waiting";
    if (hasResult) status = "done";
    else if (key === activeAgent) status = "active";
    else if (activeIndex > index) status = "done";

    return {
      ...agentContent[key],
      status,
      progress: progressByAgent[key]
    };
  });
}

function formatTime(offsetMinutes = 0) {
  const date = new Date(Date.now() + offsetMinutes * 60000);
  return date.toLocaleTimeString("ja-JP", { hour: "2-digit", minute: "2-digit" });
}

function buildChatMessages(hasInput: boolean, hasResult: boolean, agents: AgentRow[], humanReply: string): AgentChatMessage[] {
  if (!hasInput) {
    return [
      {
        id: "welcome",
        agentKey: "secretary",
        speaker: "AI秘書",
        message: "案件メールを貼ると、AI社員が順番に仕事を進めます。"
      }
    ];
  }

  const messages = agents
    .filter((agent) => agent.status === "done" || agent.status === "active")
    .map<AgentChatMessage>((agent) => ({
      id: `${agent.key}-${agent.status}`,
      agentKey: agent.key,
      speaker: agent.name,
      message: agent.status === "done" ? agent.doneComment : agent.chatMessage,
      tone: agent.status === "active" ? "active" : "done"
    }));

  if (!hasResult && agents.some((agent) => agent.key === "sales" && agent.status === "active")) {
    messages.push({
      id: "sales-request",
      agentKey: "sales",
      speaker: "AI営業",
      message: "予算だけ教えてください。分からなければ「未定」で大丈夫です。",
      tone: "request"
    });
  }

  if (humanReply) {
    messages.push({
      id: "human-reply-thanks",
      agentKey: "sales",
      speaker: "AI営業",
      message: "ありがとうございます。続きを進めます。",
      tone: "done"
    });
  }

  if (hasResult) {
    messages.push({
      id: "complete-president",
      agentKey: "president",
      speaker: "AI社長",
      message: "確認しました。このままお客様へ提出できます。",
      tone: "done"
    });
  }

  return messages;
}

function buildWorkLogs(hasInput: boolean, hasResult: boolean, agents: AgentRow[], humanReply: string): AgentWorkLog[] {
  const logs: AgentWorkLog[] = [];
  if (!hasInput) {
    return logs;
  }

  agents
    .filter((agent) => agent.status === "done" || agent.status === "active")
    .forEach((agent, index) => {
      logs.push({
        id: `${agent.key}-log`,
        time: formatTime(index),
        agentKey: agent.key,
        text: agent.activeLog
      });
    });

  if (humanReply) {
    logs.push({
      id: "human-reply-log",
      time: formatTime(logs.length),
      agentKey: "sales",
      text: "AI営業が人からの確認回答を受領"
    });
  }

  if (hasResult) {
    logs.push({
      id: "complete-log",
      time: formatTime(logs.length),
      agentKey: "president",
      text: "AI社長が提案書を承認"
    });
  }

  return logs;
}

export function AiWorkspacePanel({ status, hasInput, hasResult, isLoading, canAdminRerun, onRerunAgent }: AiWorkspacePanelProps) {
  const [rerunAgent, setRerunAgent] = useState<AiWorkspaceAgentKey | null>(null);
  const [expandedAgent, setExpandedAgent] = useState<AiWorkspaceAgentKey | null>(null);
  const [stageIndex, setStageIndex] = useState(1);
  const [humanReply, setHumanReply] = useState("");
  const [submittedReply, setSubmittedReply] = useState("");

  useEffect(() => {
    if (!(isLoading || ["reviewing", "generating"].includes(status)) || hasResult) {
      setStageIndex(1);
      return;
    }

    const timer = window.setInterval(() => {
      setStageIndex((current) => (current >= agentOrder.length - 1 ? current : current + 1));
    }, 1400);

    return () => window.clearInterval(timer);
  }, [hasResult, isLoading, status]);

  useEffect(() => {
    if (!hasInput) {
      setHumanReply("");
      setSubmittedReply("");
    }
  }, [hasInput]);

  const activeAgentKey = getActiveAgent(status, hasInput, isLoading, stageIndex);
  const agents = useMemo(() => buildAgentRows(activeAgentKey, hasResult), [activeAgentKey, hasResult]);
  const mainAgentKey = hasResult ? "president" : activeAgentKey ?? "secretary";
  const mainAgent = agentContent[mainAgentKey];
  const mainProgress = hasResult ? 100 : activeAgentKey ? progressByAgent[activeAgentKey] : 0;
  const chatMessages = useMemo(() => buildChatMessages(hasInput, hasResult, agents, submittedReply), [agents, hasInput, hasResult, submittedReply]);
  const workLogs = useMemo(() => buildWorkLogs(hasInput, hasResult, agents, submittedReply), [agents, hasInput, hasResult, submittedReply]);
  const shouldAskHuman = hasInput && !hasResult && activeAgentKey === "sales" && !submittedReply;

  function handleRerun(agent: AiWorkspaceAgentKey) {
    setRerunAgent(agent);
    onRerunAgent(agent);
    window.setTimeout(() => setRerunAgent(null), 1600);
  }

  function submitHumanReply() {
    if (!humanReply.trim()) return;
    setSubmittedReply(humanReply.trim());
    setHumanReply("");
  }

  return (
    <section className="ai-workspace-panel" aria-label="AI Workspace">
      <div className="ai-workspace-header">
        <div>
          <p className="eyebrow">Version 5.0 / AI Workspace</p>
          <h2>AI社員が一緒に提案準備を進めます</h2>
        </div>
        {hasResult && (
          <div className="ai-president-approval">
            <CheckCircle2 size={18} aria-hidden="true" />
            <strong>AI社長が承認しました</strong>
          </div>
        )}
      </div>

      <AgentCard agent={mainAgent} activeAgentKey={activeAgentKey} hasInput={hasInput} hasResult={hasResult} progress={mainProgress} />

      <div className="ai-workspace-collaboration">
        <AgentChat
          messages={chatMessages}
          requestText="予算だけ教えてください。分からなければ「未定」で大丈夫です。"
          reply={humanReply}
          onReplyChange={setHumanReply}
          onSubmitReply={submitHumanReply}
          hasRequest={shouldAskHuman}
        />
        <AgentLog logs={workLogs} />
      </div>

      <AgentTimeline
        agents={agents}
        expandedAgent={expandedAgent}
        rerunAgent={rerunAgent}
        canAdminRerun={canAdminRerun}
        isLoading={isLoading}
        onToggleAgent={(agent) => setExpandedAgent((current) => (current === agent ? null : agent))}
        onRerunAgent={handleRerun}
      />
    </section>
  );
}
