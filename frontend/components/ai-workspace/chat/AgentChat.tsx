"use client";

import { memo, useMemo } from "react";
import { SendHorizonal } from "lucide-react";
import type { AgentChatMessage, AgentContent } from "@/components/ai-workspace/types";

type AgentChatProps = {
  messages: AgentChatMessage[];
  agentsByKey: Record<string, AgentContent>;
  requestText: string;
  reply: string;
  onReplyChange: (value: string) => void;
  onSubmitReply: () => void;
  hasRequest: boolean;
};

const VIRTUAL_WINDOW_SIZE = 24;

function AgentChatBase({ messages, agentsByKey, requestText, reply, onReplyChange, onSubmitReply, hasRequest }: AgentChatProps) {
  const visibleMessages = useMemo(() => messages.slice(-VIRTUAL_WINDOW_SIZE), [messages]);
  const hiddenCount = Math.max(messages.length - visibleMessages.length, 0);

  return (
    <section className="agent-chat-panel" aria-label="AI社員との会話">
      <div className="agent-chat-heading">
        <strong>AI社員の会話</strong>
        <span>時系列で保存</span>
      </div>

      <div className="agent-chat-stream" role="list" aria-label="AI社員の会話履歴">
        {hiddenCount > 0 && <div className="agent-chat-window-note">以前の会話 {hiddenCount} 件を折りたたんでいます。</div>}
        {visibleMessages.map((message) => {
          const agent = agentsByKey[message.agentKey];
          const targetAgent = message.targetAgentKey ? agentsByKey[message.targetAgentKey] : null;
          return (
            <article className={`agent-chat-message is-${message.tone ?? "normal"} ai-agent-theme-${agent.colorClass}`} key={message.id} role="listitem">
              <span className="agent-chat-avatar">{agent.iconLabel}</span>
              <div>
                <strong>
                  {message.speaker}
                  {targetAgent ? <small> → {targetAgent.name}</small> : null}
                </strong>
                {message.time ? <time>{message.time}</time> : null}
                <p>{message.message}</p>
              </div>
            </article>
          );
        })}
      </div>

      {hasRequest && (
        <div className="agent-human-request">
          <strong>確認はここだけです</strong>
          <p>{requestText}</p>
          <div className="agent-human-reply">
            <input value={reply} onChange={(event) => onReplyChange(event.target.value)} placeholder="例：予算300〜500万円、納期は3か月以内" />
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

export const AgentChat = memo(AgentChatBase);
