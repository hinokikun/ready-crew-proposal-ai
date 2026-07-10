"use client";

import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, Loader2, RotateCcw } from "lucide-react";

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

type AgentCard = {
  key: AiWorkspaceAgentKey;
  name: string;
  role: string;
  task: string;
  comment: string;
  status: AgentStatus;
  rerunLabel: string;
};

const agentOrder: AiWorkspaceAgentKey[] = ["secretary", "sales", "director", "pm", "president"];

const agentContent: Record<AiWorkspaceAgentKey, Omit<AgentCard, "status">> = {
  secretary: {
    key: "secretary",
    name: "AI秘書",
    role: "情報整理",
    task: "案件メールから会社名・目的・予算・納期を整理します",
    comment: "貼り付け内容を読み取り、提案準備の土台を作ります。",
    rerunLabel: "AI秘書だけ再整理"
  },
  sales: {
    key: "sales",
    name: "AI営業",
    role: "提案作成",
    task: "顧客課題に合わせて提案方針と提案書初稿を作ります",
    comment: "営業提案として伝わる構成へ整えます。",
    rerunLabel: "AI営業だけ再実行"
  },
  director: {
    key: "director",
    name: "AIディレクター",
    role: "品質確認",
    task: "課題・解決策・見積・資料構成の整合性を確認します",
    comment: "提案として抜け漏れがないかをレビューします。",
    rerunLabel: "AIディレクターだけ再レビュー"
  },
  pm: {
    key: "pm",
    name: "AI PM",
    role: "スケジュール確認",
    task: "納期・体制・費用感の実行可能性を確認します",
    comment: "次回確認事項と進行リスクを整理します。",
    rerunLabel: "AI PMだけ再確認"
  },
  president: {
    key: "president",
    name: "AI社長",
    role: "最終レビュー",
    task: "顧客へ出せる内容か最終判断します",
    comment: "全AI社員の作業を確認し、承認します。",
    rerunLabel: "AI社長だけ最終レビュー"
  }
};

function getActiveAgent(status: AiWorkspaceStatus, hasInput: boolean, isLoading: boolean, stageIndex: number): AiWorkspaceAgentKey | null {
  if (!hasInput) return null;
  if (["typing", "analyzing", "question"].includes(status)) return "secretary";
  if (isLoading || ["reviewing", "generating"].includes(status)) return agentOrder[stageIndex] ?? "sales";
  return null;
}

function buildAgentCards(activeAgent: AiWorkspaceAgentKey | null, hasResult: boolean): AgentCard[] {
  const activeIndex = activeAgent ? agentOrder.indexOf(activeAgent) : -1;

  return agentOrder.map((key, index) => {
    const base = agentContent[key];
    let cardStatus: AgentStatus = "waiting";

    if (hasResult) {
      cardStatus = "done";
    } else if (key === activeAgent) {
      cardStatus = "active";
    } else if (activeIndex > index) {
      cardStatus = "done";
    }

    return {
      ...base,
      status: cardStatus
    };
  });
}

export function AiWorkspacePanel({ status, hasInput, hasResult, isLoading, canAdminRerun, onRerunAgent }: AiWorkspacePanelProps) {
  const [rerunAgent, setRerunAgent] = useState<AiWorkspaceAgentKey | null>(null);
  const [stageIndex, setStageIndex] = useState(1);

  useEffect(() => {
    if (!(isLoading || ["reviewing", "generating"].includes(status)) || hasResult) {
      setStageIndex(1);
      return;
    }

    const timer = window.setInterval(() => {
      setStageIndex((current) => (current >= agentOrder.length - 1 ? current : current + 1));
    }, 1100);

    return () => window.clearInterval(timer);
  }, [hasResult, isLoading, status]);

  const activeAgentKey = getActiveAgent(status, hasInput, isLoading, stageIndex);
  const agents = useMemo(() => buildAgentCards(activeAgentKey, hasResult), [activeAgentKey, hasResult]);
  const activeAgent = activeAgentKey ? agentContent[activeAgentKey] : null;

  function handleRerun(agent: AiWorkspaceAgentKey) {
    setRerunAgent(agent);
    onRerunAgent(agent);
    window.setTimeout(() => setRerunAgent(null), 1600);
  }

  return (
    <section className="ai-workspace-panel" aria-label="AI Workspace">
      <div className="ai-workspace-header">
        <div>
          <p className="eyebrow">Version 5.0 / AI Workspace</p>
          <h2>5人のAI社員が順番に提案準備を進めます</h2>
          <p>案件メールを貼ると、AI秘書、AI営業、AIディレクター、AI PM、AI社長が分担して作業します。</p>
        </div>
        {hasResult && (
          <div className="ai-president-approval">
            <CheckCircle2 size={18} aria-hidden="true" />
            <strong>AI社長が承認しました</strong>
          </div>
        )}
      </div>

      <div className="ai-workspace-status" aria-live="polite">
        {activeAgent ? (
          <>
            <Loader2 className="spin" size={16} aria-hidden="true" />
            <span>
              {activeAgent.name}が作業中：{activeAgent.role}
            </span>
          </>
        ) : hasResult ? (
          <>
            <CheckCircle2 size={16} aria-hidden="true" />
            <span>全AI社員の作業が完了しました。</span>
          </>
        ) : (
          <span>案件メールを貼るとAI社員が作業を開始します。</span>
        )}
      </div>

      <div className="ai-employee-board">
        {agents.map((agent, index) => (
          <article className={`ai-employee-card is-${agent.status}`} key={agent.key}>
            <div className="ai-employee-index">{agent.status === "done" ? "✔" : index + 1}</div>
            <div className="ai-employee-body">
              <div className="ai-employee-title">
                <div>
                  <strong>{agent.name}</strong>
                  <span>{agent.role}</span>
                </div>
                <small>{agent.status === "done" ? "完了" : agent.status === "active" ? "作業中" : "待機"}</small>
              </div>
              <dl>
                <div>
                  <dt>現在やっていること</dt>
                  <dd>{agent.task}</dd>
                </div>
                <div>
                  <dt>コメント</dt>
                  <dd>{agent.status === "done" && agent.key === "president" ? "承認しました。要約PPTを確認してください。" : agent.comment}</dd>
                </div>
              </dl>
              {canAdminRerun && (
                <button className="ai-rerun-button" type="button" onClick={() => handleRerun(agent.key)} disabled={isLoading && agent.key !== "sales"}>
                  {rerunAgent === agent.key ? <Loader2 className="spin" size={14} aria-hidden="true" /> : <RotateCcw size={14} aria-hidden="true" />}
                  {rerunAgent === agent.key ? "再実行中" : agent.rerunLabel}
                </button>
              )}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
