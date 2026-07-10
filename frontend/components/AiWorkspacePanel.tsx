"use client";

import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, ChevronDown, Loader2, PlayCircle, RotateCcw, SendHorizonal } from "lucide-react";

export type AiWorkspaceAgentKey = "secretary" | "sales" | "director" | "pm" | "president";
type AiWorkspaceStatus = "idle" | "typing" | "analyzing" | "question" | "reviewing" | "generating" | "complete";
type AgentStatus = "waiting" | "active" | "done";

type AiWorkspacePanelProps = {
  status: AiWorkspaceStatus;
  hasInput: boolean;
  hasResult: boolean;
  isLoading: boolean;
  canAdminRerun: boolean;
  onRerunAgent: (agent: AiWorkspaceAgentKey) => void;
};

type AgentContent = {
  key: AiWorkspaceAgentKey;
  name: string;
  role: string;
  iconLabel: string;
  colorClass: string;
  headline: string;
  task: string;
  comment: string;
  activeComment: string;
  doneComment: string;
  chatMessage: string;
  activeLog: string;
  rerunLabel: string;
};

type AgentRow = AgentContent & {
  status: AgentStatus;
  progress: number;
};

type AgentChatMessage = {
  id: string;
  agentKey: AiWorkspaceAgentKey;
  speaker: string;
  message: string;
  tone?: "normal" | "active" | "done" | "request";
};

type AgentWorkLog = {
  id: string;
  time: string;
  agentKey: AiWorkspaceAgentKey;
  text: string;
};

const agentOrder: AiWorkspaceAgentKey[] = ["secretary", "sales", "director", "pm", "president"];

const agentContent: Record<AiWorkspaceAgentKey, AgentContent> = {
  secretary: {
    key: "secretary",
    name: "AI秘書",
    role: "情報整理",
    iconLabel: "秘",
    colorClass: "secretary",
    headline: "案件情報を整理しています",
    task: "会社名、目的、予算、納期、不足情報を整理します。",
    comment: "案件メールを貼ると、提案準備に必要な情報を抽出します。",
    activeComment: "案件メールを受け取りました。必要な情報を整理しています。",
    doneComment: "案件情報を整理しました。",
    chatMessage: "案件メールを受け取りました。",
    activeLog: "AI秘書が案件を受付",
    rerunLabel: "AI秘書だけ再整理"
  },
  sales: {
    key: "sales",
    name: "AI営業",
    role: "提案作成",
    iconLabel: "営",
    colorClass: "sales",
    headline: "提案書を作成しています",
    task: "顧客課題に合わせて提案方針、勝ち筋、資料構成を作ります。",
    comment: "営業提案として伝わるストーリーへ整えます。",
    activeComment: "競合分析を開始します。提案ストーリーも組み立てています。",
    doneComment: "提案書の初稿を作成しました。",
    chatMessage: "競合分析を開始します。",
    activeLog: "AI営業が競合分析開始",
    rerunLabel: "AI営業だけ再実行"
  },
  director: {
    key: "director",
    name: "AIディレクター",
    role: "品質確認",
    iconLabel: "品",
    colorClass: "director",
    headline: "提案品質を確認しています",
    task: "課題、解決策、見積、スライド構成の整合性を確認します。",
    comment: "抜け漏れやテンプレート感が残っていないかを確認します。",
    activeComment: "提案ストーリーを確認しています。",
    doneComment: "提案内容の品質確認が完了しました。",
    chatMessage: "提案ストーリーを確認しています。",
    activeLog: "AIディレクターがレビュー開始",
    rerunLabel: "AIディレクターだけ再レビュー"
  },
  pm: {
    key: "pm",
    name: "AI PM",
    role: "スケジュール確認",
    iconLabel: "PM",
    colorClass: "pm",
    headline: "実行計画を確認しています",
    task: "納期、体制、費用感、次回確認事項を確認します。",
    comment: "実行時のリスクと進め方を整理します。",
    activeComment: "納期とスケジュールを整理しています。",
    doneComment: "進行計画の確認が完了しました。",
    chatMessage: "納期とスケジュールを整理しています。",
    activeLog: "AI PMがスケジュール確認開始",
    rerunLabel: "AI PMだけ再確認"
  },
  president: {
    key: "president",
    name: "AI社長",
    role: "最終レビュー",
    iconLabel: "承",
    colorClass: "president",
    headline: "最終レビューをしています",
    task: "顧客へ提出できる内容か、経営目線で最終判断します。",
    comment: "提案価値、見積、受注可能性をまとめて確認します。",
    activeComment: "最後に品質を確認します。",
    doneComment: "確認しました。このままお客様へ提出できます。",
    chatMessage: "最後に品質を確認します。",
    activeLog: "AI社長が最終レビュー開始",
    rerunLabel: "AI社長だけ最終レビュー"
  }
};

const progressByAgent: Record<AiWorkspaceAgentKey, number> = {
  secretary: 18,
  sales: 45,
  director: 65,
  pm: 82,
  president: 94
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
    let status: AgentStatus = "waiting";
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

function getStatusLabel(status: AgentStatus) {
  if (status === "done") return "✔ 完了";
  if (status === "active") return "▶ 作業中";
  return "待機";
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
  if (!hasInput) return logs;

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

function AgentProgress({ progress, isDone }: { progress: number; isDone: boolean }) {
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

function AgentCard({ agent, activeAgentKey, hasInput, hasResult, progress }: { agent: AgentContent; activeAgentKey: AiWorkspaceAgentKey | null; hasInput: boolean; hasResult: boolean; progress: number }) {
  const isActive = Boolean(activeAgentKey) && !hasResult;
  const headline = !hasInput ? "案件メールの貼り付けを待っています" : hasResult ? "🎉 提案書が完成しました" : agent.headline;
  const comment = !hasInput ? "入力されると、5人のAI社員が順番に作業を始めます。" : hasResult ? agent.doneComment : agent.activeComment;

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
        <span className="ai-main-status-chip">{hasResult ? "完了" : isActive ? "作業中" : "待機"}</span>
      </div>

      <div className="ai-main-message">
        {isActive && <Loader2 className="spin" size={20} aria-hidden="true" />}
        {hasResult && <CheckCircle2 size={22} aria-hidden="true" />}
        {!isActive && !hasResult && <PlayCircle size={22} aria-hidden="true" />}
        <p>{headline}</p>
      </div>

      <AgentProgress progress={progress} isDone={hasResult} />

      <div className="ai-main-comment">
        <strong>コメント</strong>
        <p>{comment}</p>
      </div>
    </section>
  );
}

function AgentChat({ messages, requestText, reply, onReplyChange, onSubmitReply, hasRequest }: { messages: AgentChatMessage[]; requestText: string; reply: string; onReplyChange: (value: string) => void; onSubmitReply: () => void; hasRequest: boolean }) {
  return (
    <section className="agent-chat-panel" aria-label="AI社員との会話">
      <div className="agent-chat-heading">
        <strong>AI社員の会話</strong>
        <span>必要な時だけ確認します</span>
      </div>

      <div className="agent-chat-stream">
        {messages.map((message) => {
          const agent = agentContent[message.agentKey];
          return (
            <article className={`agent-chat-message is-${message.tone ?? "normal"} ai-agent-theme-${agent.colorClass}`} key={message.id}>
              <span className="agent-chat-avatar">{agent.iconLabel}</span>
              <div>
                <strong>{message.speaker}</strong>
                <p>{message.message}</p>
              </div>
            </article>
          );
        })}
      </div>

      {hasRequest && (
        <div className="agent-human-request">
          <strong>AIからの確認</strong>
          <p>{requestText}</p>
          <div className="agent-human-reply">
            <input value={reply} onChange={(event) => onReplyChange(event.target.value)} placeholder="例：300〜500万円程度です" />
            <button type="button" onClick={onSubmitReply} disabled={!reply.trim()}>
              <SendHorizonal size={16} aria-hidden="true" />
              伝える
            </button>
          </div>
        </div>
      )}
    </section>
  );
}

function AgentLog({ logs }: { logs: AgentWorkLog[] }) {
  return (
    <section className="agent-log-panel" aria-label="作業ログ">
      <div className="agent-log-heading">
        <strong>作業ログ</strong>
        <span>自動更新</span>
      </div>
      <div className="agent-log-list">
        {logs.map((log) => {
          const agent = agentContent[log.agentKey];
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

function AgentTimeline({ agents, expandedAgent, rerunAgent, canAdminRerun, isLoading, onToggleAgent, onRerunAgent }: { agents: AgentRow[]; expandedAgent: AiWorkspaceAgentKey | null; rerunAgent: AiWorkspaceAgentKey | null; canAdminRerun: boolean; isLoading: boolean; onToggleAgent: (agent: AiWorkspaceAgentKey) => void; onRerunAgent: (agent: AiWorkspaceAgentKey) => void }) {
  return (
    <div className="ai-agent-list" aria-label="AI社員の作業状況">
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
                    <dt>現在やっていること</dt>
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
