"use client";

import { memo, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CheckCircle2 } from "lucide-react";
import { AgentCard as WorkspaceAgentCard } from "@/components/ai-workspace/agents/AgentCard";
import { agentContent, agentOrder, progressByAgent, thinkingMessages } from "@/components/ai-workspace/agents/data";
import { AgentChat as WorkspaceAgentChat } from "@/components/ai-workspace/chat/AgentChat";
import { AgentLog as WorkspaceAgentLog } from "@/components/ai-workspace/timeline/AgentLog";
import { AgentTimeline as WorkspaceAgentTimeline } from "@/components/ai-workspace/timeline/AgentTimeline";
import type {
  AgentChatMessage,
  AgentRow,
  AgentStatus,
  AgentWorkLog,
  AiWorkspaceAgentKey
} from "@/components/ai-workspace/types";
import {
  applyReviewFeedback,
  bypassQualityGate,
  completeQualityGate,
  getQualityGate,
  getProposalReview,
  getProposalReviewRevisions,
  getWorkspaceConversation,
  getWorkspaceSummary,
  rerequestProposalReview,
  requestProposalReview,
  saveQualityGate,
  saveWorkspaceConversation,
  type ProposalReviewEntry,
  type ProposalReviewRevision,
  type QualityGateRecord,
  type WorkspaceConversationRecord,
  type WorkspaceSummary,
  type WorkspaceWorkLogRecord
} from "@/lib/api";
export type { AiWorkspaceAgentKey } from "@/components/ai-workspace/types";

type AiWorkspaceStatus = "idle" | "typing" | "analyzing" | "question" | "reviewing" | "generating" | "complete";

type AiWorkspacePanelProps = {
  status: AiWorkspaceStatus;
  hasInput: boolean;
  hasResult: boolean;
  isLoading: boolean;
  canAdminRerun: boolean;
  canPersist?: boolean;
  canRequestReview?: boolean;
  canCompleteQualityGate?: boolean;
  canBypassQualityGate?: boolean;
  onQualityGateChange?: (unlocked: boolean, gate?: QualityGateRecord | null) => void;
  onRerunAgent: (agent: AiWorkspaceAgentKey) => void;
  workspaceSeed?: string;
  workspaceTitle?: string;
};

const STORAGE_PREFIX = "ai-sales-secretary-workspace";

const reviewStatusLabels: Record<string, string> = {
  draft: "下書き",
  review_requested: "レビュー依頼中",
  approved: "承認済み",
  changes_requested: "修正依頼",
  rejected: "却下"
};

const QUALITY_GATE_ITEMS = [
  "会社名・担当者名に誤りがない",
  "金額・見積条件を確認した",
  "納期・スケジュールを確認した",
  "AI推測ラベルの項目を確認した",
  "実績・事例表記を確認した",
  "法務・契約条件に問題がない",
  "上司レビュー状態を確認した",
  "社外提出前に人間が最終確認した"
];

function hashWorkspaceSeed(value: string) {
  let hash = 0;
  for (let index = 0; index < value.length; index += 1) {
    hash = (hash << 5) - hash + value.charCodeAt(index);
    hash |= 0;
  }
  return Math.abs(hash).toString(36);
}

function nowLabel(offsetMinutes = 0) {
  const date = new Date(Date.now() + offsetMinutes * 60000);
  return date.toLocaleTimeString("ja-JP", { hour: "2-digit", minute: "2-digit" });
}

function formatHistoryTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleTimeString("ja-JP", { hour: "2-digit", minute: "2-digit" });
}

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

function getNextAgent(activeAgent: AiWorkspaceAgentKey | null, hasResult: boolean): AiWorkspaceAgentKey | null {
  if (!activeAgent || hasResult) return null;
  const nextIndex = agentOrder.indexOf(activeAgent) + 1;
  return agentOrder[nextIndex] ?? null;
}

export function getStatusLabel(status: AgentStatus) {
  if (status === "done") return "完了";
  if (status === "active") return "作業中";
  return "待機";
}

function mergeMessages(stored: AgentChatMessage[], current: AgentChatMessage[]) {
  const map = new Map<string, AgentChatMessage>();
  [...stored, ...current].forEach((message) => {
    map.set(message.id, message);
  });
  return Array.from(map.values()).sort((a, b) => a.id.localeCompare(b.id));
}

function getAgentKeyByName(agentName: string): AiWorkspaceAgentKey {
  const match = agentOrder.find((key) => agentContent[key].name === agentName);
  return match ?? "sales";
}

function dbConversationToMessage(record: WorkspaceConversationRecord): AgentChatMessage {
  const agentKey = getAgentKeyByName(record.agent_name);
  return {
    id: record.client_message_id || `db-${record.id}`,
    agentKey,
    speaker: record.agent_name || agentContent[agentKey].name,
    time: formatHistoryTime(record.created_at),
    message: record.message_body,
    tone: record.message_type as AgentChatMessage["tone"]
  };
}

function buildPersistencePayload(projectId: string, messages: AgentChatMessage[], logs: AgentWorkLog[]) {
  return {
    project_id: projectId,
    conversations: messages
      .filter((message) => message.id !== "000-welcome")
      .slice(-60)
      .map((message) => ({
        client_message_id: message.id,
        agent_name: message.speaker,
        message_type: message.tone ?? "normal",
        message_body: message.message,
        status: message.tone === "done" || message.tone === "explanation" ? "done" : "active"
      })),
    work_logs: logs.slice(-60).map((log) => ({
      client_log_id: log.id,
      agent_name: agentContent[log.agentKey].name,
      action_summary: log.text,
      status: "active"
    }))
  };
}

function splitSummaryLines(value: string) {
  return value
    .split(/\r?\n/)
    .map((item) => item.replace(/^[-・\s]+/, "").trim())
    .filter(Boolean)
    .slice(0, 5);
}

function buildChatMessages(
  hasInput: boolean,
  hasResult: boolean,
  activeAgent: AiWorkspaceAgentKey | null,
  submittedReply: string,
  thinkingText: string,
  reviewStatus = "",
  reviewComment = ""
): AgentChatMessage[] {
  if (!hasInput) {
    return [
      {
        id: "000-welcome",
        agentKey: "secretary",
        speaker: "AI秘書",
        time: nowLabel(),
        message: "こんにちは。まず案件メール、議事録、URLを貼り付けてください。貼るだけでAI社員が順番に進めます。"
      }
    ];
  }

  const activeIndex = activeAgent ? agentOrder.indexOf(activeAgent) : hasResult ? agentOrder.length - 1 : 0;
  const messages: AgentChatMessage[] = [
    {
      id: "010-secretary-received",
      agentKey: "secretary",
      speaker: "AI秘書",
      time: nowLabel(0),
      message: "案件メールを受付しました。会社名、目的、予算、納期、競合、CMS希望を整理します。",
      tone: "done"
    },
    {
      id: "020-secretary-thinking",
      agentKey: "secretary",
      speaker: "AI秘書",
      time: nowLabel(0),
      message: activeAgent === "secretary" ? thinkingText : "必要情報を整理しました。AI営業へ提案作成を依頼します。",
      tone: activeAgent === "secretary" ? "thinking" : "handoff",
      targetAgentKey: activeAgent === "secretary" ? undefined : "sales"
    }
  ];

  if (activeIndex >= 1 || hasResult) {
    messages.push(
      {
        id: "030-sales-start",
        agentKey: "sales",
        speaker: "AI営業",
        time: nowLabel(1),
        message: activeAgent === "sales" ? thinkingText : "提案方針を作成しました。競合比較、問い合わせ導線、SEOの勝ち筋を入れています。",
        tone: activeAgent === "sales" ? "thinking" : "done"
      },
      {
        id: "040-sales-to-director",
        agentKey: "sales",
        speaker: "AI営業",
        targetAgentKey: "director",
        time: nowLabel(1),
        message: "AIディレクターへレビュー依頼しました。提案ストーリーと資料品質の確認をお願いします。",
        tone: "handoff"
      }
    );
  }

  if (submittedReply) {
    messages.push({
      id: "045-human-confirmed",
      agentKey: "sales",
      speaker: "あなた",
      time: nowLabel(1),
      message: `確認しました：${submittedReply}`,
      tone: "human"
    });
  }

  if (activeIndex >= 2 || hasResult) {
    messages.push(
      {
        id: "050-director-review",
        agentKey: "director",
        speaker: "AIディレクター",
        time: nowLabel(2),
        message: activeAgent === "director" ? thinkingText : "提案ストーリーを改善しました。課題、解決策、KPIがつながる流れに整えています。",
        tone: activeAgent === "director" ? "thinking" : "done"
      },
      {
        id: "060-director-to-pm",
        agentKey: "director",
        speaker: "AIディレクター",
        targetAgentKey: "pm",
        time: nowLabel(2),
        message: "AI PMへ確認を依頼しました。見積、納期、体制に無理がないか見てください。",
        tone: "handoff"
      }
    );
  }

  if (activeIndex >= 3 || hasResult) {
    messages.push(
      {
        id: "070-pm-check",
        agentKey: "pm",
        speaker: "AI PM",
        time: nowLabel(3),
        message: activeAgent === "pm" ? thinkingText : "見積とスケジュールを確認しました。必須対応とオプション対応を分けています。",
        tone: activeAgent === "pm" ? "thinking" : "done"
      },
      {
        id: "080-pm-to-president",
        agentKey: "pm",
        speaker: "AI PM",
        targetAgentKey: "president",
        time: nowLabel(3),
        message: "AI社長へ最終確認を依頼しました。顧客へ提出できる品質か確認お願いします。",
        tone: "handoff"
      }
    );
  }

  if (activeIndex >= 4 || hasResult) {
    messages.push({
      id: "090-president-review",
      agentKey: "president",
      speaker: "AI社長",
      time: nowLabel(4),
      message: activeAgent === "president" && !hasResult ? thinkingText : "品質確認します。提案価値、費用感、受注可能性を最後に見ています。",
      tone: activeAgent === "president" && !hasResult ? "thinking" : "done"
    });
  }

  if (hasResult) {
    messages.push(
      {
        id: "100-president-approved",
        agentKey: "president",
        speaker: "AI社長",
        time: nowLabel(5),
        message: "承認しました。要約PowerPointをダウンロードし、提出前に人が最終確認してください。",
        tone: "done"
      },
      {
        id: "110-president-explanation",
        agentKey: "president",
        speaker: "AI社長",
        time: nowLabel(5),
        message: "なぜこの提案にしたか：顧客課題に直結する導線改善を優先しました。予算と納期に合わせて必須範囲を絞りました。競合との差別化は実績訴求とSEO導線で作ります。",
        tone: "explanation"
      }
    );
  }

  if (hasResult && reviewStatus === "changes_requested") {
    messages.push(
      {
        id: "120-sales-review-change-requested",
        agentKey: "sales",
        speaker: "AI営業",
        time: nowLabel(6),
        message: reviewComment ? `上司コメントを受け取りました。「${reviewComment}」に合わせて提案メッセージを補強します。` : "修正依頼を受け取りました。提案メッセージを補強します。",
        tone: "request"
      },
      {
        id: "130-director-review-change-requested",
        agentKey: "director",
        speaker: "AIディレクター",
        time: nowLabel(6),
        message: "提案ストーリーを修正依頼に合わせて見直します。特に説得力、費用対効果、次アクションを確認します。",
        tone: "request"
      }
    );
  }

  if (hasResult && reviewStatus === "approved") {
    messages.push({
      id: "140-president-human-approved",
      agentKey: "president",
      speaker: "AI社長",
      time: nowLabel(6),
      message: "上司レビューも承認済みです。提出前チェックだけ確認してください。",
      tone: "done"
    });
  }

  return messages;
}

function buildWorkLogs(hasInput: boolean, hasResult: boolean, agents: AgentRow[], submittedReply: string): AgentWorkLog[] {
  if (!hasInput) return [];
  const logs: AgentWorkLog[] = agents
    .filter((agent) => agent.status === "done" || agent.status === "active")
    .map((agent, index) => ({
      id: `${agent.key}-log`,
      time: nowLabel(index),
      agentKey: agent.key,
      text: agent.activeLog
    }));

  if (submittedReply) {
    logs.push({
      id: "human-confirmed-log",
      time: nowLabel(logs.length),
      agentKey: "sales",
      text: "予算・納期の確認回答を受け取り"
    });
  }

  if (hasResult) {
    logs.push({
      id: "approved-log",
      time: nowLabel(logs.length),
      agentKey: "president",
      text: "AI社長が提案書を承認"
    });
  }

  return logs;
}

function AiWorkspacePanelBase({
  status,
  hasInput,
  hasResult,
  isLoading,
  canAdminRerun,
  canPersist = true,
  canRequestReview = false,
  canCompleteQualityGate = false,
  canBypassQualityGate = false,
  onQualityGateChange,
  onRerunAgent,
  workspaceSeed = "",
  workspaceTitle = "AI Workspace提案"
}: AiWorkspacePanelProps) {
  const [rerunAgent, setRerunAgent] = useState<AiWorkspaceAgentKey | null>(null);
  const [expandedAgent, setExpandedAgent] = useState<AiWorkspaceAgentKey | null>(null);
  const [stageIndex, setStageIndex] = useState(1);
  const [humanReply, setHumanReply] = useState("");
  const [submittedReply, setSubmittedReply] = useState("");
  const [storedMessages, setStoredMessages] = useState<AgentChatMessage[]>([]);
  const [thinkingIndex, setThinkingIndex] = useState(0);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [historyConversations, setHistoryConversations] = useState<WorkspaceConversationRecord[]>([]);
  const [historyLogs, setHistoryLogs] = useState<WorkspaceWorkLogRecord[]>([]);
  const [historyError, setHistoryError] = useState("");
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [workspaceSummary, setWorkspaceSummary] = useState<WorkspaceSummary | null>(null);
  const [summaryCopyState, setSummaryCopyState] = useState<"idle" | "copied" | "failed">("idle");
  const [proposalReview, setProposalReview] = useState<ProposalReviewEntry | null>(null);
  const [reviewRevisions, setReviewRevisions] = useState<ProposalReviewRevision[]>([]);
  const [aiImprovementPolicy, setAiImprovementPolicy] = useState("");
  const [diffSummary, setDiffSummary] = useState<string[]>([]);
  const [reviewNotice, setReviewNotice] = useState("");
  const [isReviewRequesting, setIsReviewRequesting] = useState(false);
  const [isApplyingFeedback, setIsApplyingFeedback] = useState(false);
  const [isRerequestingReview, setIsRerequestingReview] = useState(false);
  const [qualityGate, setQualityGate] = useState<QualityGateRecord | null>(null);
  const [checkedGateItems, setCheckedGateItems] = useState<Record<string, boolean>>({});
  const [bypassReason, setBypassReason] = useState("");
  const [qualityGateNotice, setQualityGateNotice] = useState("");
  const [isQualityGateSaving, setIsQualityGateSaving] = useState(false);
  const [isQualityGateBypassing, setIsQualityGateBypassing] = useState(false);
  const lastLoadedProjectRef = useRef("");
  const lastPersistSignatureRef = useRef("");

  const workspaceId = useMemo(() => hashWorkspaceSeed(workspaceSeed || "default"), [workspaceSeed]);
  const storageKey = `${STORAGE_PREFIX}:${workspaceId}`;

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(storageKey);
      setStoredMessages(raw ? (JSON.parse(raw) as AgentChatMessage[]) : []);
    } catch {
      setStoredMessages([]);
    }
  }, [storageKey]);

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

  useEffect(() => {
    const timer = window.setInterval(() => {
      setThinkingIndex((current) => current + 1);
    }, 1600);
    return () => window.clearInterval(timer);
  }, []);

  const activeAgentKey = getActiveAgent(status, hasInput, isLoading, stageIndex);
  const agents = useMemo(() => buildAgentRows(activeAgentKey, hasResult), [activeAgentKey, hasResult]);
  const nextAgentKey = useMemo(() => getNextAgent(activeAgentKey, hasResult), [activeAgentKey, hasResult]);
  const mainAgentKey = hasResult ? "president" : activeAgentKey ?? "secretary";
  const mainAgent = agentContent[mainAgentKey];
  const mainProgress = hasResult ? 100 : activeAgentKey ? progressByAgent[activeAgentKey] : 0;
  const thinkingText = useMemo(() => {
    const candidates = thinkingMessages[mainAgentKey];
    return candidates[thinkingIndex % candidates.length] ?? mainAgent.activeComment;
  }, [mainAgent.activeComment, mainAgentKey, thinkingIndex]);
  const generatedMessages = useMemo(
    () => buildChatMessages(hasInput, hasResult, activeAgentKey, submittedReply, thinkingText, proposalReview?.status, proposalReview?.review_comment),
    [activeAgentKey, hasInput, hasResult, proposalReview?.review_comment, proposalReview?.status, submittedReply, thinkingText]
  );
  const chatMessages = useMemo(() => mergeMessages(storedMessages, generatedMessages), [generatedMessages, storedMessages]);
  const workLogs = useMemo(() => buildWorkLogs(hasInput, hasResult, agents, submittedReply), [agents, hasInput, hasResult, submittedReply]);
  const hasStoredHumanReply = useMemo(() => storedMessages.some((message) => message.id === "045-human-confirmed"), [storedMessages]);
  const shouldAskHuman = hasInput && !hasResult && activeAgentKey === "sales" && !submittedReply && !hasStoredHumanReply;
  const reviewFeedbackVisible = proposalReview?.status === "changes_requested" || (proposalReview?.status === "draft" && diffSummary.length > 0);
  const selectedGateItems = useMemo(
    () => QUALITY_GATE_ITEMS.filter((item) => checkedGateItems[item]),
    [checkedGateItems]
  );
  const isQualityGateComplete = Boolean(qualityGate?.completed || qualityGate?.bypassed);
  const qualityGateStatusLabel = qualityGate?.bypassed ? "管理者バイパス" : qualityGate?.completed ? "完了" : selectedGateItems.length > 0 ? "確認中" : "未確認";
  const reviewWarning = hasResult && proposalReview?.status !== "approved";
  const explanation = useMemo(
    () => [
      "顧客課題に直結する問い合わせ導線とSEO改善を優先しました。",
      "予算・納期に合わせて必須範囲とオプションを分けました。",
      "競合との差別化は実績訴求、CMS運用、KPI設計で作ります。"
    ],
    []
  );
  const persistenceSignature = useMemo(
    () =>
      [
        workspaceId,
        status,
        hasResult ? "done" : "active",
        submittedReply ? "human-confirmed" : "human-empty",
        chatMessages.map((message) => `${message.id}:${message.tone ?? "normal"}`).join("|"),
        workLogs.map((log) => log.id).join("|")
      ].join("::"),
    [chatMessages, hasResult, status, submittedReply, workLogs, workspaceId]
  );

  const loadWorkspaceHistory = useCallback(
    async (showPanel = true) => {
      if (showPanel) {
        setHistoryOpen(true);
      }
      if (!workspaceId) return;

      setIsHistoryLoading(true);
      setHistoryError("");
      try {
        const [history, summaryResponse] = await Promise.all([getWorkspaceConversation(workspaceId), getWorkspaceSummary(workspaceId)]);
        setHistoryConversations(history.conversations);
        setHistoryLogs(history.work_logs);
        setWorkspaceSummary(summaryResponse.summary);
        const dbMessages = history.conversations.map(dbConversationToMessage);
        setStoredMessages((current) => mergeMessages(current, dbMessages));
      } catch {
        setHistoryError("会話履歴を読み込めませんでした。時間を置いて再度お試しください。");
      } finally {
        setIsHistoryLoading(false);
      }
    },
    [workspaceId]
  );

  const loadProposalReview = useCallback(async () => {
    if (!workspaceId) return;
    try {
      const response = await getProposalReview(workspaceId);
      setProposalReview(response.review);
      if (response.review?.id) {
        const revisionsResponse = await getProposalReviewRevisions(response.review.id);
        setReviewRevisions(revisionsResponse.revisions);
        const latest = revisionsResponse.revisions[0];
        if (latest?.ai_improvement_policy) setAiImprovementPolicy(latest.ai_improvement_policy);
        if (latest?.diff_summary) setDiffSummary(splitSummaryLines(latest.diff_summary));
      } else {
        setReviewRevisions([]);
        setAiImprovementPolicy("");
        setDiffSummary([]);
      }
      if (response.review?.status === "approved") setReviewNotice("承認されました。");
      else if (response.review?.status === "changes_requested") setReviewNotice("修正依頼があります。");
      else if (response.review?.status === "rejected") setReviewNotice("却下されました。");
    } catch {
      // Review status is secondary; keep the main Workspace flow available.
    }
  }, [workspaceId]);

  const loadQualityGate = useCallback(async () => {
    if (!workspaceId) return;
    try {
      const response = await getQualityGate(workspaceId);
      setQualityGate(response.gate);
      const nextChecked: Record<string, boolean> = {};
      response.gate?.checklist_items.forEach((item) => {
        nextChecked[item] = true;
      });
      setCheckedGateItems(nextChecked);
      onQualityGateChange?.(Boolean(response.gate?.download_unlocked), response.gate ?? null);
    } catch {
      setQualityGateNotice("提出前確認ゲートを読み込めませんでした。Backend接続を確認してください。");
      onQualityGateChange?.(false, null);
    }
  }, [onQualityGateChange, workspaceId]);

  useEffect(() => {
    if (!hasInput) return;
    try {
      window.localStorage.setItem(storageKey, JSON.stringify(chatMessages.slice(-80)));
    } catch {
      // localStorage is best-effort only.
    }
  }, [chatMessages, hasInput, storageKey]);

  useEffect(() => {
    if (!hasInput || !workspaceId || lastLoadedProjectRef.current === workspaceId) return;
    lastLoadedProjectRef.current = workspaceId;
    void loadWorkspaceHistory(false);
    void loadProposalReview();
    void loadQualityGate();
  }, [hasInput, loadProposalReview, loadQualityGate, loadWorkspaceHistory, workspaceId]);

  useEffect(() => {
    if (!hasResult) return;
    void loadProposalReview();
    void loadQualityGate();
  }, [hasResult, loadProposalReview, loadQualityGate]);

  useEffect(() => {
    if (!hasInput || !canPersist || chatMessages.length <= 1) return;
    if (lastPersistSignatureRef.current === persistenceSignature) return;

    const timer = window.setTimeout(() => {
      lastPersistSignatureRef.current = persistenceSignature;
      void saveWorkspaceConversation(buildPersistencePayload(workspaceId, chatMessages, workLogs)).catch(() => {
        // Persistence is helpful, but the proposal flow should keep working if it fails.
      });
    }, 900);

    return () => window.clearTimeout(timer);
  }, [canPersist, chatMessages, hasInput, persistenceSignature, workLogs, workspaceId]);

  const handleRerun = useCallback(
    (agent: AiWorkspaceAgentKey) => {
      setRerunAgent(agent);
      onRerunAgent(agent);
      window.setTimeout(() => setRerunAgent(null), 1600);
    },
    [onRerunAgent]
  );

  const submitHumanReply = useCallback(() => {
    if (!humanReply.trim()) return;
    setSubmittedReply(humanReply.trim());
    setHumanReply("");
  }, [humanReply]);

  const copyWorkspaceSummary = useCallback(async () => {
    try {
      const summaryResponse = workspaceSummary ? { summary: workspaceSummary } : await getWorkspaceSummary(workspaceId);
      setWorkspaceSummary(summaryResponse.summary);
      await navigator.clipboard.writeText(summaryResponse.summary.markdown);
      setSummaryCopyState("copied");
      window.setTimeout(() => setSummaryCopyState("idle"), 1800);
    } catch {
      setSummaryCopyState("failed");
      window.setTimeout(() => setSummaryCopyState("idle"), 2400);
    }
  }, [workspaceId, workspaceSummary]);

  const requestHumanReview = useCallback(async () => {
    if (!canRequestReview || !hasResult) return;
    setIsReviewRequesting(true);
    setReviewNotice("");
    try {
      const response = await requestProposalReview({
        project_id: workspaceId,
        project_name: workspaceTitle || "AI Workspace提案"
      });
      setProposalReview(response.review);
      setReviewNotice("レビュー依頼を送信しました。");
    } catch {
      setReviewNotice("レビュー依頼を送信できませんでした。権限またはBackend接続を確認してください。");
    } finally {
      setIsReviewRequesting(false);
    }
  }, [canRequestReview, hasResult, workspaceId, workspaceTitle]);

  const applyHumanReviewFeedback = useCallback(async () => {
    if (!proposalReview?.id || !canRequestReview) return;
    setIsApplyingFeedback(true);
    setReviewNotice("");
    try {
      const response = await applyReviewFeedback(proposalReview.id, {
        current_summary: workspaceSummary?.proposal_policy || workspaceSummary?.markdown || workspaceTitle
      });
      setProposalReview(response.review);
      setAiImprovementPolicy(response.ai_improvement_policy);
      setDiffSummary(response.diff_summary);
      setReviewNotice("修正内容を反映して再作成しました。");
      await loadProposalReview();
    } catch {
      setReviewNotice("修正内容を反映できませんでした。権限またはBackend接続を確認してください。");
    } finally {
      setIsApplyingFeedback(false);
    }
  }, [canRequestReview, loadProposalReview, proposalReview?.id, workspaceSummary?.markdown, workspaceSummary?.proposal_policy, workspaceTitle]);

  const requestReviewAgain = useCallback(async () => {
    if (!proposalReview?.id || !canRequestReview) return;
    setIsRerequestingReview(true);
    setReviewNotice("");
    try {
      const response = await rerequestProposalReview(proposalReview.id);
      setProposalReview(response.review);
      setReviewNotice("再レビューを依頼しました。");
      await loadProposalReview();
    } catch {
      setReviewNotice("再レビュー依頼を送信できませんでした。権限またはBackend接続を確認してください。");
    } finally {
      setIsRerequestingReview(false);
    }
  }, [canRequestReview, loadProposalReview, proposalReview?.id]);

  const toggleQualityGateItem = useCallback((item: string) => {
    setCheckedGateItems((current) => ({ ...current, [item]: !current[item] }));
    setQualityGateNotice("");
  }, []);

  const saveQualityGateProgress = useCallback(async () => {
    if (!canCompleteQualityGate) return;
    setIsQualityGateSaving(true);
    setQualityGateNotice("");
    try {
      const response = await saveQualityGate(workspaceId, selectedGateItems);
      setQualityGate(response.gate);
      onQualityGateChange?.(Boolean(response.gate?.download_unlocked), response.gate ?? null);
      setQualityGateNotice("確認状況を保存しました。");
    } catch {
      setQualityGateNotice("確認状況を保存できませんでした。Backend接続を確認してください。");
    } finally {
      setIsQualityGateSaving(false);
    }
  }, [canCompleteQualityGate, onQualityGateChange, selectedGateItems, workspaceId]);

  const completeGate = useCallback(async () => {
    if (!canCompleteQualityGate) return;
    if (selectedGateItems.length !== QUALITY_GATE_ITEMS.length) {
      setQualityGateNotice("すべての提出前確認項目をチェックしてください。");
      return;
    }
    setIsQualityGateSaving(true);
    setQualityGateNotice("");
    try {
      const response = await completeQualityGate(workspaceId, selectedGateItems);
      setQualityGate(response.gate);
      onQualityGateChange?.(Boolean(response.gate?.download_unlocked), response.gate ?? null);
      setQualityGateNotice("ダウンロード可能になりました。");
    } catch {
      setQualityGateNotice("品質ゲートを完了できませんでした。権限またはBackend接続を確認してください。");
      onQualityGateChange?.(false, null);
    } finally {
      setIsQualityGateSaving(false);
    }
  }, [canCompleteQualityGate, onQualityGateChange, selectedGateItems, workspaceId]);

  const bypassGate = useCallback(async () => {
    if (!canBypassQualityGate) return;
    if (bypassReason.trim().length < 3) {
      setQualityGateNotice("管理者バイパスには理由を入力してください。");
      return;
    }
    setIsQualityGateBypassing(true);
    setQualityGateNotice("");
    try {
      const response = await bypassQualityGate(workspaceId, bypassReason);
      setQualityGate(response.gate);
      onQualityGateChange?.(Boolean(response.gate?.download_unlocked), response.gate ?? null);
      setQualityGateNotice("管理者バイパスを記録しました。ダウンロード可能です。");
    } catch {
      setQualityGateNotice("管理者バイパスに失敗しました。権限またはBackend接続を確認してください。");
      onQualityGateChange?.(false, null);
    } finally {
      setIsQualityGateBypassing(false);
    }
  }, [bypassReason, canBypassQualityGate, onQualityGateChange, workspaceId]);

  return (
    <section className="ai-workspace-panel" aria-label="AI Workspace">
      <div className="ai-workspace-header">
        <div>
          <p className="eyebrow">Version 9.0 / Collaborative AI Workspace</p>
          <h2>AI社員と一緒に提案準備を進めます</h2>
        </div>
        {hasResult && (
          <div className="ai-president-approval">
            <CheckCircle2 size={18} aria-hidden="true" />
            <strong>AI社長が承認しました</strong>
          </div>
        )}
      </div>

      <WorkspaceAgentCard
        agent={mainAgent}
        activeAgentKey={activeAgentKey}
        hasInput={hasInput}
        hasResult={hasResult}
        progress={mainProgress}
        thinkingText={thinkingText}
        explanation={explanation}
      />

      <div className="workspace-next-agent" aria-label="AI Orchestrator next agent">
        <span>現在</span>
        <strong>{agentContent[mainAgentKey].name}</strong>
        <span>次</span>
        <strong>{nextAgentKey ? agentContent[nextAgentKey].name : hasResult ? "完了" : "待機"}</strong>
      </div>

      <div className={`workspace-human-review-card is-${proposalReview?.status ?? "draft"}`}>
        <div>
          <span>上司レビュー</span>
          <strong>{reviewStatusLabels[proposalReview?.status ?? "draft"] ?? "下書き"}</strong>
          {proposalReview?.review_comment && <p>{proposalReview.review_comment}</p>}
          {!proposalReview && <p>提案書作成後に、上司レビューを依頼できます。</p>}
          {proposalReview?.status === "changes_requested" && <p>修正依頼があります。AI営業またはAIディレクターの見直しコメントを確認してください。</p>}
        </div>
        <div className="workspace-human-review-actions">
          {hasResult && canRequestReview && proposalReview?.status !== "review_requested" && proposalReview?.status !== "approved" && (
            <button type="button" className="primary-button" onClick={() => void requestHumanReview()} disabled={isReviewRequesting}>
              {isReviewRequesting ? "送信中" : "上司レビューを依頼"}
            </button>
          )}
          {hasResult && (
            <button type="button" className="secondary-button" onClick={() => void loadProposalReview()} disabled={isReviewRequesting}>
              状態を更新
            </button>
          )}
        </div>
        {reviewNotice && <p className="workspace-review-notice">{reviewNotice}</p>}
      </div>

      {hasResult && (
        <div className={`workspace-quality-gate-card is-${qualityGate?.bypassed ? "bypassed" : qualityGate?.completed ? "complete" : "pending"}`}>
          <div className="section-heading">
            <div>
              <p className="eyebrow">Human-in-the-loop Quality Gate</p>
              <h3>提出前確認ゲート</h3>
            </div>
            <span>{qualityGateStatusLabel}</span>
          </div>
          <p className="quality-gate-lead">
            社外提出前に、人間が確認すべき項目を通します。完了すると要約PPT・詳細PPT・見積PDFをダウンロードできます。
          </p>
          {reviewWarning && (
            <p className="quality-gate-warning">上司レビューが未承認です（社内試験導入中のため警告のみ）。</p>
          )}
          <div className="quality-gate-checklist" aria-label="提出前確認項目">
            {QUALITY_GATE_ITEMS.map((item) => (
              <label key={item} className={checkedGateItems[item] ? "is-checked" : ""}>
                <input
                  checked={Boolean(checkedGateItems[item])}
                  disabled={!canCompleteQualityGate || isQualityGateComplete}
                  onChange={() => toggleQualityGateItem(item)}
                  type="checkbox"
                />
                <span>{item}</span>
              </label>
            ))}
          </div>
          {isQualityGateComplete ? (
            <p className="quality-gate-success">
              {qualityGate?.bypassed ? "管理者バイパスによりダウンロード可能です。" : "ダウンロード可能になりました。"}
            </p>
          ) : (
            <div className="quality-gate-actions">
              {canCompleteQualityGate ? (
                <>
                  <button type="button" className="secondary-button" onClick={() => void saveQualityGateProgress()} disabled={isQualityGateSaving}>
                    {isQualityGateSaving ? "保存中" : "確認状況を保存"}
                  </button>
                  <button type="button" className="primary-button" onClick={() => void completeGate()} disabled={isQualityGateSaving}>
                    品質ゲートを完了
                  </button>
                </>
              ) : (
                <p>閲覧のみ権限では品質ゲートを完了できません。</p>
              )}
            </div>
          )}
          {canBypassQualityGate && !isQualityGateComplete && (
            <div className="quality-gate-bypass">
              <label>
                <span>管理者バイパス理由</span>
                <input
                  value={bypassReason}
                  onChange={(event) => setBypassReason(event.target.value)}
                  placeholder="例：社内確認用に緊急で出力するため"
                />
              </label>
              <button type="button" className="secondary-button danger" onClick={() => void bypassGate()} disabled={isQualityGateBypassing}>
                {isQualityGateBypassing ? "記録中" : "確認未完了でダウンロード許可"}
              </button>
            </div>
          )}
          {qualityGateNotice && <p className="workspace-review-notice">{qualityGateNotice}</p>}
        </div>
      )}

      {reviewFeedbackVisible && (
        <div className="workspace-feedback-loop-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Review Feedback Loop</p>
              <h3>修正依頼をAI Workspaceへ反映</h3>
            </div>
            <span>{proposalReview?.status === "changes_requested" ? "修正依頼中" : "再作成済み"}</span>
          </div>

          <div className="feedback-loop-grid">
            <article>
              <strong>上司コメント</strong>
              <p>{proposalReview?.review_comment || "上司コメントは未入力です。"}</p>
            </article>
            <article>
              <strong>AI改善方針</strong>
              <p>{aiImprovementPolicy || "修正内容を反映すると、AI営業・AIディレクター・AI PMの改善方針が表示されます。"}</p>
            </article>
          </div>

          {diffSummary.length > 0 && (
            <div className="feedback-diff-summary">
              <strong>差分サマリー</strong>
              <ul>
                {diffSummary.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {reviewRevisions.length > 0 && (
            <details className="feedback-revision-history">
              <summary>修正履歴を見る</summary>
              {reviewRevisions.slice(0, 5).map((revision) => (
                <p key={revision.id}>
                  {formatHistoryTime(revision.created_at)} / {reviewStatusLabels[revision.previous_status] ?? revision.previous_status} → {reviewStatusLabels[revision.next_status] ?? revision.next_status}
                </p>
              ))}
            </details>
          )}

          <div className="feedback-loop-actions">
            {proposalReview?.status === "changes_requested" && (
              <button type="button" className="primary-button" onClick={() => void applyHumanReviewFeedback()} disabled={isApplyingFeedback}>
                {isApplyingFeedback ? "再作成中" : "修正内容を反映して再作成"}
              </button>
            )}
            {proposalReview?.status === "draft" && diffSummary.length > 0 && (
              <button type="button" className="primary-button" onClick={() => void requestReviewAgain()} disabled={isRerequestingReview}>
                {isRerequestingReview ? "依頼中" : "再レビューを依頼"}
              </button>
            )}
          </div>
        </div>
      )}

      <div className="ai-workspace-collaboration">
        <WorkspaceAgentChat
          messages={chatMessages}
          agentsByKey={agentContent}
          requestText="予算と納期だけ教えてください。分からなければ「未定」「要確認」で進めます。"
          reply={humanReply}
          onReplyChange={setHumanReply}
          onSubmitReply={submitHumanReply}
          hasRequest={shouldAskHuman}
        />
        <WorkspaceAgentLog logs={workLogs} agentsByKey={agentContent} />
      </div>

      <div className="workspace-history-tools">
        <button type="button" className="secondary-button" onClick={() => void loadWorkspaceHistory(true)}>
          会話履歴を見る
        </button>
        <button type="button" className="secondary-button" onClick={() => void copyWorkspaceSummary()}>
          作業まとめをコピー
        </button>
        {summaryCopyState === "copied" && <span className="workspace-history-note">コピーしました</span>}
        {summaryCopyState === "failed" && <span className="workspace-history-note is-error">コピーできませんでした</span>}
      </div>

      {historyOpen && (
        <details className="workspace-history-panel" open>
          <summary>保存済みの会話履歴</summary>
          {isHistoryLoading && <p>会話履歴を読み込んでいます。</p>}
          {historyError && <p className="workspace-history-error">{historyError}</p>}
          {!isHistoryLoading && !historyError && (
            <>
              {workspaceSummary && (
                <div className="workspace-summary-card">
                  <strong>AI Workspace作業まとめ</strong>
                  <ul>
                    <li>受付内容：{workspaceSummary.reception}</li>
                    <li>提案方針：{workspaceSummary.proposal_policy}</li>
                    <li>レビュー内容：{workspaceSummary.review}</li>
                    <li>スケジュール確認：{workspaceSummary.schedule_check}</li>
                    <li>最終判断：{workspaceSummary.final_decision}</li>
                    <li>次アクション：{workspaceSummary.next_action}</li>
                  </ul>
                </div>
              )}
              <div className="workspace-history-list">
                {historyConversations.length === 0 && historyLogs.length === 0 && <p>まだDBに保存された会話履歴はありません。</p>}
                {historyConversations.slice(-12).map((item) => (
                  <article key={`conversation-${item.id}`}>
                    <span>{formatHistoryTime(item.created_at)}</span>
                    <strong>{item.agent_name}</strong>
                    <p>{item.message_body}</p>
                  </article>
                ))}
                {historyLogs.slice(-8).map((item) => (
                  <article key={`log-${item.id}`} className="is-log">
                    <span>{formatHistoryTime(item.created_at)}</span>
                    <strong>{item.agent_name}</strong>
                    <p>{item.action_summary}</p>
                  </article>
                ))}
              </div>
            </>
          )}
        </details>
      )}

      <WorkspaceAgentTimeline
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

export const AiWorkspacePanel = memo(AiWorkspacePanelBase);
