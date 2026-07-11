"use client";

import { memo, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { Send } from "lucide-react";
import { CopilotCommands } from "./CopilotCommands";
import type { CopilotChatMessage, CopilotModel } from "./types";

type CopilotChatProps = {
  model: CopilotModel;
  onOpenPanel: (panelId: string) => void;
};

const initialMessages: CopilotChatMessage[] = [
  {
    id: "assistant-initial",
    role: "assistant",
    text: "今日何から進めるか、CRM・レビュー・品質ゲート・利用状況から答えます。"
  }
];

export const CopilotChat = memo(function CopilotChat({ model, onOpenPanel }: CopilotChatProps) {
  const [messages, setMessages] = useState<CopilotChatMessage[]>(initialMessages);
  const [draft, setDraft] = useState("");
  const commands = useMemo(() => Object.keys(model.commandMap), [model.commandMap]);

  function answerQuestion(text: string) {
    const normalized = text.trim().toLowerCase();
    const matchedCommand = commands.find((command) => normalized.includes(command.toLowerCase()));
    if (matchedCommand) {
      onOpenPanel(model.commandMap[matchedCommand]);
      return `${matchedCommand}を開きます。必要な画面へ移動しました。`;
    }
    if (/優先|今日|何から|todo|to do/.test(normalized)) {
      return `${model.headline}\nおすすめは「${model.recommendation}」です。`;
    }
    if (/失注|低い|危険|リスク/.test(normalized)) {
      const risk = model.recommendations.find((item) => item.id.includes("low-win") || item.id.includes("stagnant"));
      return risk ? `${risk.title}\n理由: ${risk.reasons.join(" / ")}` : "現時点では明確な失注リスクは見つかっていません。CRMの受注確率を確認してください。";
    }
    if (/レビュー/.test(normalized)) {
      const review = model.recommendations.find((item) => item.id.includes("review"));
      return review ? `${review.title}\n${review.detail}` : "レビュー待ちは多くありません。次は品質ゲートと停滞案件を確認してください。";
    }
    if (/品質|ゲート/.test(normalized)) {
      const gate = model.recommendations.find((item) => item.id.includes("quality"));
      return gate ? `${gate.title}\n${gate.detail}` : "品質ゲートの未完了はありません。";
    }
    if (/受注率|理由|分析/.test(normalized)) {
      return `受注率に影響しそうな根拠は、${model.reasons.join("、")}です。詳細はAnalyticsとCRMを確認してください。`;
    }
    return "CRM、Review、Quality Gate、Analyticsの範囲で見ると、まずAction Centerの上位項目から進めるのがおすすめです。";
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = draft.trim();
    if (!text) return;
    const userMessage: CopilotChatMessage = { id: `user-${Date.now()}`, role: "user", text };
    const assistantMessage: CopilotChatMessage = {
      id: `assistant-${Date.now()}`,
      role: "assistant",
      text: answerQuestion(text)
    };
    setMessages((current) => [...current, userMessage, assistantMessage].slice(-30));
    setDraft("");
  }

  function runCommand(command: string) {
    setDraft(command);
    const panelId = model.commandMap[command];
    if (panelId) onOpenPanel(panelId);
    const assistantMessage: CopilotChatMessage = {
      id: `assistant-command-${Date.now()}`,
      role: "assistant",
      text: `${command}を開きます。`
    };
    setMessages((current) => [...current, assistantMessage].slice(-30));
  }

  return (
    <section className="copilot-chat" aria-label="Ask Sales Copilot">
      <div className="copilot-section-title">
        <span>Ask Sales Copilot</span>
        <small>既存DBのみ参照</small>
      </div>
      <div className="copilot-chat-log">
        {messages.map((message) => (
          <article className={`copilot-message is-${message.role}`} key={message.id}>
            <span>{message.role === "assistant" ? "AI営業" : "あなた"}</span>
            <p>{message.text}</p>
          </article>
        ))}
      </div>
      <CopilotCommands commands={commands.slice(0, 5)} onCommand={runCommand} />
      <form className="copilot-chat-form" onSubmit={submit}>
        <input
          aria-label="Sales Copilotに質問"
          onChange={(event) => setDraft(event.target.value)}
          placeholder="例：今日何からやればいい？"
          value={draft}
        />
        <button type="submit" aria-label="送信">
          <Send size={15} aria-hidden="true" />
        </button>
      </form>
    </section>
  );
});
