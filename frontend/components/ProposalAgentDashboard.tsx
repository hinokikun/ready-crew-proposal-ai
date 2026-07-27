"use client";

import { FormEvent, KeyboardEvent, useEffect, useMemo, useState } from "react";
import {
  Bell,
  Bot,
  Briefcase,
  CheckCircle2,
  Command,
  Download,
  FileText,
  Moon,
  Pin,
  Search,
  Send,
  Sparkles,
  Star,
  Sun,
  Wand2,
  Zap
} from "lucide-react";
import {
  downloadProposalAgentDashboard,
  getProposalAgentDashboard,
  saveProposalAgentMemory,
  type ProposalAgentMemoryPayload
} from "@/lib/api";
import type { ProposalAgentDashboardData, ProposalAgentProjectScore } from "@/types/app";

type ExportFormat = "markdown" | "csv" | "pdf" | "pptx";
type FlowStatus = "idle" | "running" | "done" | "blocked" | "error";
type SummaryItem = { label: string; value: string; inferred?: boolean };

type ProposalAgentDashboardProps = {
  sourceText?: string;
  onSourceTextChange?: (value: string) => void;
  onOneClickGenerate?: () => Promise<void> | void;
  onCreateBeautifulAi?: () => Promise<void> | void;
  onDownloadPdf?: () => Promise<void> | void;
  onDownloadPowerPoint?: () => Promise<void> | void;
  canCreateBeautifulAi?: boolean;
  canDownloadOutputs?: boolean;
  hasProposal?: boolean;
  isGenerating?: boolean;
  isCreatingBeautifulAi?: boolean;
  beautifulAiUrl?: string;
  summaryItems?: SummaryItem[];
  onOpenCrm?: () => void;
};

const emptyMemory: ProposalAgentMemoryPayload = {
  project_id: null,
  project_name: "",
  hearing_notes: "",
  confirmation_items: "",
  proposal_content: "",
  competitor_analysis: "",
  improvement_history: ""
};

const exportFiles: Array<{ format: ExportFormat; label: string; filename: string }> = [
  { format: "markdown", label: "Markdown", filename: "proposal-intelligence-dashboard.md" },
  { format: "csv", label: "CSV", filename: "proposal-intelligence-dashboard.csv" },
  { format: "pdf", label: "PDF", filename: "proposal-intelligence-dashboard.pdf" },
  { format: "pptx", label: "PowerPoint", filename: "proposal-intelligence-dashboard.pptx" }
];

const enterpriseStatusLabels = ["提案待ち", "提案書作成中", "提案完了", "見積作成待ち", "Beautiful.ai生成待ち", "顧客送付待ち"];
const draftStorageKey = "ready-crew-v70-enterprise-draft";
const pinnedStorageKey = "ready-crew-v70-pinned-projects";
const templates = [
  "Web制作",
  "EC",
  "採用",
  "AI",
  "DX",
  "SaaS",
  "製造業"
] as const;

const flowSeed: Array<{ key: string; label: string; detail: string }> = [
  { key: "thinking", label: "Thinking...", detail: "案件の目的と不足情報を整理しています" },
  { key: "analyzing", label: "Analyzing...", detail: "課題、競合、勝ち筋を確認しています" },
  { key: "proposal", label: "Creating Proposal...", detail: "既存Proposal Generatorで提案プレビューを作成します" },
  { key: "beautiful", label: "Building Beautiful.ai...", detail: "提出前チェック後にBeautiful.aiへ送信します" },
  { key: "pdf", label: "Generating PDF...", detail: "見積PDFを作成します" },
  { key: "pptx", label: "Generating PowerPoint...", detail: "PowerPointを作成します" },
  { key: "completed", label: "Completed", detail: "提案作成フローが完了しました" }
];

function saveBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(url);
}

function wait(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function templateDraft(template: string) {
  return `${template}向けの提案書を作成してください。

顧客名:
案件背景:
現在の課題:
提案したい内容:
予算:
希望納期:
競合:
補足:`;
}

function getFallbackStatusCards() {
  return enterpriseStatusLabels.map((label, index) => ({
    key: label,
    label,
    count: 0,
    tone: index === 0 ? "info" : index === 2 ? "ok" : "warn"
  }));
}

const emptyDashboard: ProposalAgentDashboardData = {
  status_cards: [],
  todo: [],
  scores: [],
  timeline: [],
  memories: [],
  review: {
    improvements: [],
    risks: [],
    missing_information: []
  },
  summaries: {
    executive_30s: "",
    sales_3m: "",
    detail: ""
  },
  priorities: [],
  win_probabilities: [],
  competitors: [],
  sales_actions: [],
  health: [],
  kpi: {
    proposal_count: 0,
    proposal_success_rate: 0,
    average_proposal_score: 0,
    average_win_probability: 0,
    average_generation_time_seconds: 0,
    total_saved_minutes: 0,
    beautiful_ai_count: 0
  },
  insights: []
};

function ensureArray<T>(value: T[] | null | undefined): T[] {
  return Array.isArray(value) ? value : [];
}

function normalizeDashboard(value: Partial<ProposalAgentDashboardData> | null | undefined): ProposalAgentDashboardData {
  return {
    status_cards: ensureArray(value?.status_cards),
    todo: ensureArray(value?.todo),
    scores: ensureArray(value?.scores),
    timeline: ensureArray(value?.timeline),
    memories: ensureArray(value?.memories),
    review: {
      improvements: ensureArray(value?.review?.improvements),
      risks: ensureArray(value?.review?.risks),
      missing_information: ensureArray(value?.review?.missing_information)
    },
    summaries: {
      executive_30s: value?.summaries?.executive_30s ?? "",
      sales_3m: value?.summaries?.sales_3m ?? "",
      detail: value?.summaries?.detail ?? ""
    },
    priorities: ensureArray(value?.priorities),
    win_probabilities: ensureArray(value?.win_probabilities),
    competitors: ensureArray(value?.competitors),
    sales_actions: ensureArray(value?.sales_actions),
    health: ensureArray(value?.health),
    kpi: value?.kpi ?? emptyDashboard.kpi,
    insights: ensureArray(value?.insights)
  };
}

function buildCopilotReply(question: string, dashboard: ProposalAgentDashboardData | null) {
  const topProject = dashboard?.scores?.[0];
  const topWin = dashboard?.win_probabilities?.[0];
  const topPriority = dashboard?.priorities?.[0];
  if (/競合/.test(question)) {
    const competitor = dashboard?.competitors?.[0];
    return competitor
      ? `${competitor.project_name}では、${competitor.competitor_name}との差別化を明確にすると強くなります。特に「${competitor.differentiation[0] ?? "導入後の成果"}」を1枚で伝えるのがおすすめです。`
      : "競合情報がまだ少ないため、比較対象、選定理由、価格以外の評価軸を追加すると提案が強くなります。";
  }
  if (/受注|確率/.test(question)) {
    return topWin
      ? `${topWin.project_name}の受注確率は${topWin.probability}%です。理由は「${topWin.reasons.join("、")}」。次は決裁者と予算条件を確認しましょう。`
      : "受注率を上げるには、決裁者、予算、競合、導入後KPIの4点を先に埋めるのが近道です。";
  }
  if (/強く|改善/.test(question)) {
    const insight = dashboard?.insights?.[0] ?? "課題、効果、次のアクションを1ページずつ明確にすると説得力が上がります。";
    return `改善ポイントは「${insight}」です。提案ストーリーは、現状課題、解決策、KPI、導入ステップの順で整理すると伝わりやすくなります。`;
  }
  return topProject
    ? `${topProject.project_name}はProposal Score ${topProject.score}点です。${topPriority ? `優先度は${topPriority.grade}で、${topPriority.reasons[0] ?? "提案価値が見込めます"}。` : ""}不足情報を埋めると、提案の精度がさらに上がります。`
    : "案件概要を入力すると、優先度、受注確率、改善ポイント、次アクションを一緒に整理できます。";
}

export function ProposalAgentDashboard({
  sourceText = "",
  onSourceTextChange,
  onOneClickGenerate,
  onCreateBeautifulAi,
  onDownloadPdf,
  onDownloadPowerPoint,
  canCreateBeautifulAi = false,
  canDownloadOutputs = false,
  hasProposal = false,
  isGenerating = false,
  isCreatingBeautifulAi = false,
  beautifulAiUrl = "",
  summaryItems = [],
  onOpenCrm
}: ProposalAgentDashboardProps) {
  const [dashboard, setDashboard] = useState<ProposalAgentDashboardData | null>(null);
  const [memory, setMemory] = useState<ProposalAgentMemoryPayload>(emptyMemory);
  const [loading, setLoading] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isDark, setIsDark] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const [notificationOpen, setNotificationOpen] = useState(false);
  const [copilotOpen, setCopilotOpen] = useState(false);
  const [copilotDraft, setCopilotDraft] = useState("");
  const [copilotMessages, setCopilotMessages] = useState([
    { role: "assistant", text: "Proposal Copilotです。案件の勝ち筋、競合、改善ポイントを一緒に整理できます。" }
  ]);
  const [pinnedProjects, setPinnedProjects] = useState<number[]>([]);
  const [history, setHistory] = useState<string[]>([]);
  const [future, setFuture] = useState<string[]>([]);
  const [flowSteps, setFlowSteps] = useState(() => flowSeed.map((step) => ({ ...step, status: "idle" as FlowStatus })));
  const [oneClickRunning, setOneClickRunning] = useState(false);

  const projects = dashboard?.scores ?? [];
  const primaryScore = projects[0];
  const selectedProject = useMemo(
    () => projects.find((project) => project.project_id === memory.project_id),
    [memory.project_id, projects]
  );
  const statusCards = useMemo(() => {
    const cards = dashboard?.status_cards?.length ? dashboard.status_cards : getFallbackStatusCards();
    return cards.slice(0, 6).map((card, index) => ({ ...card, label: enterpriseStatusLabels[index] ?? card.label }));
  }, [dashboard?.status_cards]);
  const notifications = useMemo(
    () => [
      "AIから改善提案があります",
      hasProposal ? "提案プレビューが作成済みです" : "案件概要を入力すると提案を開始できます",
      canCreateBeautifulAi ? "Beautiful.aiを作成できます" : "Beautiful.aiは提出前チェック後に有効になります",
      ...(dashboard?.insights ?? []).slice(0, 2)
    ],
    [canCreateBeautifulAi, dashboard?.insights, hasProposal]
  );
  const pinned = projects.filter((project) => pinnedProjects.includes(project.project_id));
  const kpi = dashboard?.kpi ?? emptyDashboard.kpi;
  const review = dashboard?.review ?? emptyDashboard.review;
  const summaries = dashboard?.summaries ?? emptyDashboard.summaries;
  const slidePreview = summaryItems.length
    ? summaryItems.slice(0, 6)
    : [
        { label: "提案概要", value: "生成後に表示されます" },
        { label: "課題", value: "生成後に表示されます" },
        { label: "提案方針", value: "生成後に表示されます" },
        { label: "KPI", value: "生成後に表示されます" },
        { label: "見積", value: "生成後に表示されます" },
        { label: "次のアクション", value: "生成後に表示されます" }
      ];

  async function loadDashboard() {
    setLoading("load");
    setError("");
    try {
      const response = await getProposalAgentDashboard();
      const nextDashboard = normalizeDashboard(response.dashboard);
      setDashboard(nextDashboard);
      const firstProject = nextDashboard.scores[0];
      if (firstProject && !memory.project_id && !memory.project_name) {
        setMemory((current) => ({ ...current, project_id: firstProject.project_id, project_name: firstProject.project_name }));
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Proposal Intelligence Dashboardを取得できませんでした。");
    } finally {
      setLoading("");
    }
  }

  async function handleSaveMemory(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading("save");
    setMessage("");
    setError("");
    try {
      await saveProposalAgentMemory(memory);
      setMessage("Agent Memoryを保存しました。次回同じ案件を開いたときに参照されます。");
      setMemory((current) => ({ ...emptyMemory, project_id: current.project_id, project_name: current.project_name }));
      await loadDashboard();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Agent Memoryを保存できませんでした。");
    } finally {
      setLoading("");
    }
  }

  async function handleExport(format: ExportFormat, filename: string) {
    setLoading(`export-${format}`);
    setMessage("");
    setError("");
    try {
      const blob = await downloadProposalAgentDashboard(format);
      saveBlob(blob, filename);
      setMessage(`${filename}を作成しました。`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "ダッシュボードを出力できませんでした。");
    } finally {
      setLoading("");
    }
  }

  function updateMemory<K extends keyof ProposalAgentMemoryPayload>(key: K, value: ProposalAgentMemoryPayload[K]) {
    setMemory((current) => ({ ...current, [key]: value }));
  }

  function updateSource(value: string) {
    setHistory((current) => [...current.slice(-24), sourceText]);
    setFuture([]);
    onSourceTextChange?.(value);
  }

  function handleSourceKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (!event.ctrlKey || event.key.toLowerCase() !== "z") return;
    event.preventDefault();
    if (event.shiftKey) {
      const next = future.at(-1);
      if (next === undefined) return;
      setFuture((current) => current.slice(0, -1));
      setHistory((current) => [...current, sourceText]);
      onSourceTextChange?.(next);
      return;
    }
    const previous = history.at(-1);
    if (previous === undefined) return;
    setHistory((current) => current.slice(0, -1));
    setFuture((current) => [...current, sourceText]);
    onSourceTextChange?.(previous);
  }

  function handleProjectChange(value: string) {
    const projectId = Number(value);
    const project = projects.find((item) => item.project_id === projectId);
    setMemory((current) => ({
      ...current,
      project_id: Number.isFinite(projectId) && projectId > 0 ? projectId : null,
      project_name: project?.project_name ?? current.project_name
    }));
  }

  function togglePin(projectId: number) {
    setPinnedProjects((current) =>
      current.includes(projectId) ? current.filter((item) => item !== projectId) : [...current, projectId]
    );
  }

  function setFlowStatus(key: string, status: FlowStatus) {
    setFlowSteps((current) => current.map((step) => (step.key === key ? { ...step, status } : step)));
  }

  async function runOneClickProposal() {
    if (!sourceText.trim()) {
      setError("案件概要を入力してください。");
      return;
    }
    setOneClickRunning(true);
    setError("");
    setMessage("");
    setFlowSteps(flowSeed.map((step) => ({ ...step, status: "idle" as FlowStatus })));
    try {
      setFlowStatus("thinking", "running");
      await wait(240);
      setFlowStatus("thinking", "done");
      setFlowStatus("analyzing", "running");
      await wait(240);
      setFlowStatus("analyzing", "done");
      setFlowStatus("proposal", "running");
      await onOneClickGenerate?.();
      setFlowStatus("proposal", "done");
      if (canCreateBeautifulAi && onCreateBeautifulAi) {
        setFlowStatus("beautiful", "running");
        await onCreateBeautifulAi();
        setFlowStatus("beautiful", "done");
      } else {
        setFlowStatus("beautiful", "blocked");
      }
      if (canDownloadOutputs && onDownloadPdf) {
        setFlowStatus("pdf", "running");
        await onDownloadPdf();
        setFlowStatus("pdf", "done");
      } else {
        setFlowStatus("pdf", "blocked");
      }
      if (canDownloadOutputs && onDownloadPowerPoint) {
        setFlowStatus("pptx", "running");
        await onDownloadPowerPoint();
        setFlowStatus("pptx", "done");
      } else {
        setFlowStatus("pptx", "blocked");
      }
      setFlowStatus("completed", "done");
      setMessage("ワンクリック提案書フローを実行しました。安全確認が必要な出力は既存の提出前チェック後に有効になります。");
    } catch (caught) {
      setFlowSteps((current) => current.map((step) => (step.status === "running" ? { ...step, status: "error" } : step)));
      setError(caught instanceof Error ? caught.message : "ワンクリック提案書を実行できませんでした。");
    } finally {
      setOneClickRunning(false);
    }
  }

  function submitCopilot(question = copilotDraft.trim()) {
    if (!question) return;
    const answer = buildCopilotReply(question, dashboard);
    setCopilotMessages((current) => [...current, { role: "user", text: question }, { role: "assistant", text: answer }]);
    setCopilotDraft("");
  }

  useEffect(() => {
    void loadDashboard();
  }, []);

  useEffect(() => {
    const saved = window.localStorage.getItem(draftStorageKey);
    const savedPins = window.localStorage.getItem(pinnedStorageKey);
    if (saved && !sourceText && onSourceTextChange) onSourceTextChange(saved);
    if (savedPins) setPinnedProjects(JSON.parse(savedPins) as number[]);
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => {
      window.localStorage.setItem(draftStorageKey, sourceText);
    }, 5000);
    return () => window.clearInterval(timer);
  }, [sourceText]);

  useEffect(() => {
    window.localStorage.setItem(pinnedStorageKey, JSON.stringify(pinnedProjects));
  }, [pinnedProjects]);

  useEffect(() => {
    const handler = (event: globalThis.KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommandOpen((current) => !current);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  return (
    <section className={`proposal-agent-dashboard proposal-copilot-enterprise ${isDark ? "is-enterprise-dark" : ""}`} aria-label="Proposal Copilot Enterprise">
      <div className="proposal-copilot-topbar">
        <div>
          <p className="eyebrow">Version 70 / Proposal Copilot Enterprise</p>
          <h1>営業提案を、次の一手まで動かす。</h1>
          <p>案件入力から提案、出力、改善までを1つのホームで扱える営業AIワークスペースです。</p>
        </div>
        <div className="proposal-copilot-actions">
          <button className="icon-text-button" type="button" onClick={() => setCommandOpen(true)}>
            <Command size={16} /> Ctrl+K
          </button>
          <button className="icon-text-button" type="button" onClick={() => setNotificationOpen((current) => !current)}>
            <Bell size={16} /> 通知 {notifications.length}
          </button>
          <button className="icon-button" type="button" onClick={() => setIsDark((current) => !current)} aria-label={isDark ? "ライトモード" : "ダークモード"}>
            {isDark ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </div>
        {notificationOpen && (
          <div className="proposal-notification-panel" role="dialog" aria-label="Notification Center">
            {notifications.map((item) => (
              <p key={item}>{item}</p>
            ))}
          </div>
        )}
      </div>

      <div className="proposal-copilot-hero">
        <div className="proposal-copilot-hero-copy">
          <span className="proposal-copilot-badge"><Sparkles size={16} /> Proposal Copilot</span>
          <h2>ワンクリックで提案作成を開始</h2>
          <p>案件概要を貼り付けるだけで、分析、提案、見積、Beautiful.ai、PDF、PowerPointまで同じ導線で進められます。</p>
        </div>
        <div className="proposal-copilot-score" aria-label="代表案件スコア">
          <span>Proposal Score</span>
          <strong>{primaryScore?.score ?? 0}</strong>
          <small>{primaryScore?.project_name ?? "案件未登録"}</small>
        </div>
      </div>

      <div className="proposal-copilot-composer">
        <div>
          <div className="section-heading-row">
            <div>
              <p className="eyebrow">One Click Proposal</p>
              <h2>案件概要</h2>
            </div>
            <small>5秒ごとに自動保存 / Ctrl+Z・Ctrl+Shift+Z対応</small>
          </div>
          <textarea
            aria-label="案件概要"
            rows={8}
            value={sourceText}
            onChange={(event) => updateSource(event.target.value)}
            onKeyDown={handleSourceKeyDown}
            placeholder="案件メール、議事録、ヒアリングメモをそのまま貼り付けてください。"
          />
          <div className="proposal-template-strip" aria-label="業種別テンプレート">
            {templates.map((template) => (
              <button key={template} type="button" onClick={() => updateSource(templateDraft(template))}>
                {template}
              </button>
            ))}
          </div>
          <button className="proposal-one-click-button" type="button" onClick={() => void runOneClickProposal()} disabled={oneClickRunning || isGenerating || isCreatingBeautifulAi}>
            <Wand2 size={18} />
            {oneClickRunning || isGenerating ? "提案書を作成中" : "ワンクリック提案書"}
          </button>
        </div>
        <ol className="proposal-copilot-progress" aria-label="リアルタイムAI進捗">
          {flowSteps.map((step) => (
            <li key={step.key} className={step.status}>
              <span>{step.status === "done" ? <CheckCircle2 size={16} /> : <Zap size={16} />}</span>
              <div>
                <strong>{step.label}</strong>
                <p>{step.detail}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>

      {(message || error) && (
        <div className={error ? "status-note error" : "status-note success"} role={error ? "alert" : "status"}>
          {error || message}
        </div>
      )}

      <div className="proposal-agent-status-grid">
        {statusCards.map((item) => (
          <article className={`proposal-agent-status ${item.tone}`} key={item.key}>
            <span>{item.label}</span>
            <strong>{item.count}</strong>
            <small>件</small>
          </article>
        ))}
      </div>

      <div className="proposal-agent-layout">
        <section className="proposal-agent-panel">
          <PanelTitle eyebrow="Sales Dashboard" title="今日やること" />
          <ul className="proposal-agent-todo">
            {(dashboard?.todo ?? []).slice(0, 6).map((item) => (
              <li key={item.label} className={item.checked ? "done" : ""}>
                <input type="checkbox" checked={item.checked} readOnly aria-label={item.label} />
                <div>
                  <strong>{item.label}</strong>
                  <span>{item.priority}</span>
                  <p>{item.reason}</p>
                </div>
              </li>
            ))}
          </ul>
        </section>

        <section className="proposal-agent-panel">
          <PanelTitle eyebrow="Priority & Deadlines" title="優先案件" />
          <div className="proposal-agent-intel-list">
            {(dashboard?.priorities ?? []).slice(0, 5).map((item) => (
              <article key={item.project_id}>
                <div>
                  <span>{item.grade} / {item.stars}</span>
                  <strong>{item.project_name}</strong>
                </div>
                <b>{item.priority_score}</b>
                <p>{item.reasons.join(" / ") || "優先度を高める理由を確認してください。"}</p>
              </article>
            ))}
          </div>
        </section>
      </div>

      <div className="proposal-agent-layout">
        <section className="proposal-agent-panel">
          <PanelTitle eyebrow="Win Probability" title="受注確率ランキング" />
          <div className="proposal-agent-intel-list">
            {(dashboard?.win_probabilities ?? []).slice(0, 5).map((item) => (
              <article key={item.project_id}>
                <div>
                  <span>受注確率</span>
                  <strong>{item.project_name}</strong>
                </div>
                <b>{item.probability}%</b>
                <p>{item.reasons.join(" / ")}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="proposal-agent-panel">
          <PanelTitle eyebrow="Smart Recommendation" title="おすすめ改善" />
          <ul className="proposal-agent-insights">
            {(dashboard?.insights ?? ["競合比較、価格説明、導入後KPIを確認してください。"]).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
      </div>

      <section className="proposal-agent-panel">
        <PanelTitle eyebrow="Recently Used" title="最近使った案件" />
        <div className="proposal-agent-score-grid">
          {projects.slice(0, 4).map((project) => (
            <RecentProjectCard key={project.project_id} project={project} pinned={pinnedProjects.includes(project.project_id)} onPin={() => togglePin(project.project_id)} />
          ))}
          {!projects.length && <p className="empty-note">案件が登録されると、最近使った案件として表示されます。</p>}
        </div>
        {pinned.length > 0 && (
          <div className="proposal-pinned-projects">
            <strong><Star size={16} /> お気に入り</strong>
            {pinned.map((project) => (
              <button key={project.project_id} type="button" onClick={() => updateMemory("project_id", project.project_id)}>
                {project.project_name}
              </button>
            ))}
          </div>
        )}
      </section>

      <section className="proposal-agent-panel">
        <PanelTitle eyebrow="Beautiful.ai Preview" title="スライド構成プレビュー" />
        <div className="proposal-beautiful-preview">
          <div className="proposal-beautiful-preview-status">
            <FileText size={20} />
            <div>
              <strong>{beautifulAiUrl ? "Beautiful.ai生成済み" : "Beautiful.ai生成後にプレビュー表示"}</strong>
              <p>{beautifulAiUrl ? "取得済みURLから開けます。" : "提案生成後、提出前チェックを完了すると作成できます。"}</p>
            </div>
          </div>
          <div className="proposal-slide-thumbnails">
            {slidePreview.map((item, index) => (
              <article key={`${item.label}-${index}`}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <strong>{item.label}</strong>
                <p>{item.value}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <div className="proposal-agent-layout">
        <section className="proposal-agent-panel">
          <PanelTitle eyebrow="Competitive Dashboard" title="競合比較" />
          <div className="proposal-agent-competitor-grid">
            {(dashboard?.competitors ?? []).slice(0, 3).map((item, index) => (
              <article key={`${item.competitor_name}-${index}`}>
                <span>{item.project_name}</span>
                <h3>{item.competitor_name}</h3>
                <DetailList title="強み" items={item.strengths} />
                <DetailList title="弱み" items={item.weaknesses} />
                <DetailList title="差別化ポイント" items={item.differentiation} />
                <DetailList title="注意点" items={item.cautions} />
              </article>
            ))}
          </div>
        </section>

        <section className="proposal-agent-panel">
          <PanelTitle eyebrow="Sales Actions" title="次にやること" />
          <div className="proposal-agent-action-grid">
            {(dashboard?.sales_actions ?? []).slice(0, 6).map((item) => (
              <article key={`${item.project_id}-${item.action}`}>
                <span>{item.priority}</span>
                <strong>{item.action}</strong>
                <p>{item.project_name}</p>
                <small>{item.reason}</small>
              </article>
            ))}
          </div>
        </section>
      </div>

      <section className="proposal-agent-panel">
        <PanelTitle eyebrow="KPI Dashboard" title="営業KPI" />
        <div className="proposal-agent-kpi-grid">
          <KpiCard label="提案数" value={`${kpi.proposal_count}件`} />
          <KpiCard label="提案成功率" value={`${kpi.proposal_success_rate}%`} />
          <KpiCard label="平均Proposal Score" value={`${kpi.average_proposal_score}点`} />
          <KpiCard label="平均受注確率" value={`${kpi.average_win_probability}%`} />
          <KpiCard label="平均作成時間" value={`${kpi.average_generation_time_seconds}秒`} />
          <KpiCard label="累計削減時間" value={`${kpi.total_saved_minutes}分`} />
          <KpiCard label="Beautiful.ai生成数" value={`${kpi.beautiful_ai_count}件`} />
        </div>
      </section>

      <div className="proposal-agent-layout">
        <section className="proposal-agent-panel">
          <PanelTitle eyebrow="Deal Health" title="案件健康度" />
          <div className="proposal-agent-health-grid">
            {(dashboard?.health ?? []).slice(0, 6).map((item) => (
              <article className={item.status.toLowerCase()} key={item.project_id}>
                <span>{item.status}</span>
                <strong>{item.project_name}</strong>
                <p>{item.reason}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="proposal-agent-panel">
          <PanelTitle eyebrow="Proposal Review" title="AIレビュー" />
          <ReviewBlock title="改善点" items={review.improvements} />
          <ReviewBlock title="リスク" items={review.risks} />
          <ReviewBlock title="不足情報" items={review.missing_information} />
        </section>
      </div>

      <section className="proposal-agent-panel">
        <PanelTitle eyebrow="Timeline" title="案件タイムライン" />
        <ol className="proposal-agent-timeline">
          {(dashboard?.timeline ?? []).slice(0, 8).map((item, index) => (
            <li key={`${item.project_id}-${item.created_at}-${index}`}>
              <span>{item.label}</span>
              <strong>{item.project_name}</strong>
              <p>{item.detail}</p>
              <small>{item.created_at}</small>
            </li>
          ))}
          {!dashboard?.timeline?.length && <li>案件登録、AI分析、提案生成などの履歴がここに表示されます。</li>}
        </ol>
      </section>

      <section className="proposal-agent-panel">
        <PanelTitle eyebrow="Agent Memory" title="案件メモリ" />
        <form className="proposal-agent-memory-form" onSubmit={handleSaveMemory}>
          <label>
            対象案件
            <select value={memory.project_id ?? ""} onChange={(event) => handleProjectChange(event.target.value)}>
              <option value="">案件を選択しない</option>
              {projects.map((project) => (
                <option value={project.project_id} key={project.project_id}>
                  {project.project_name}
                </option>
              ))}
            </select>
          </label>
          <input aria-label="案件名" value={memory.project_name} onChange={(event) => updateMemory("project_name", event.target.value)} placeholder="案件名" />
          <textarea aria-label="ヒアリング内容" rows={3} value={memory.hearing_notes} onChange={(event) => updateMemory("hearing_notes", event.target.value)} placeholder="ヒアリング内容" />
          <textarea aria-label="確認事項" rows={3} value={memory.confirmation_items} onChange={(event) => updateMemory("confirmation_items", event.target.value)} placeholder="確認事項" />
          <textarea aria-label="提案内容" rows={3} value={memory.proposal_content} onChange={(event) => updateMemory("proposal_content", event.target.value)} placeholder="提案内容" />
          <textarea aria-label="競合分析" rows={3} value={memory.competitor_analysis} onChange={(event) => updateMemory("competitor_analysis", event.target.value)} placeholder="競合分析" />
          <textarea aria-label="改善履歴" rows={3} value={memory.improvement_history} onChange={(event) => updateMemory("improvement_history", event.target.value)} placeholder="改善履歴" />
          <button className="primary-action" type="submit" disabled={loading === "save"}>
            {loading === "save" ? "保存中" : "Agent Memoryを保存"}
          </button>
        </form>
        {selectedProject && <p className="status-note">選択中: {selectedProject.project_name} / 現在スコア {selectedProject.score}点</p>}
      </section>

      <section className="proposal-agent-panel">
        <PanelTitle eyebrow="Executive Summary" title="提案要約" />
        <div className="proposal-agent-summary-grid">
          <SummaryCard title="経営者向け 30秒版" body={summaries.executive_30s} />
          <SummaryCard title="営業向け 3分版" body={summaries.sales_3m} />
          <SummaryCard title="詳細版" body={summaries.detail} />
        </div>
      </section>

      <div className="proposal-agent-toolbar">
        <button className="secondary-button" type="button" onClick={() => void loadDashboard()} disabled={loading === "load"}>
          {loading === "load" ? "更新中" : "再読み込み"}
        </button>
        <button className="secondary-button" type="button" onClick={onOpenCrm}>
          <Briefcase size={16} /> 管理情報を見る
        </button>
        <div className="proposal-agent-export-actions" aria-label="ダッシュボード出力">
          {exportFiles.map((item) => (
            <button className="secondary-button" key={item.format} type="button" onClick={() => void handleExport(item.format, item.filename)} disabled={loading === `export-${item.format}`}>
              <Download size={16} /> {loading === `export-${item.format}` ? "出力中" : `${item.label}出力`}
            </button>
          ))}
        </div>
      </div>

      {commandOpen && (
        <div className="proposal-command-overlay" role="dialog" aria-modal="true" aria-label="Command Palette">
          <div className="proposal-command-palette">
            <label>
              <Search size={18} />
              <input autoFocus placeholder="機能、案件、操作を検索" onKeyDown={(event) => event.key === "Escape" && setCommandOpen(false)} />
            </label>
            <button type="button" onClick={() => { setCommandOpen(false); void runOneClickProposal(); }}>Proposal生成を開始</button>
            <button type="button" onClick={() => { setCommandOpen(false); onOpenCrm?.(); }}>管理情報を見る</button>
            <button type="button" onClick={() => { setCommandOpen(false); void loadDashboard(); }}>ダッシュボード更新</button>
            <button type="button" onClick={() => { setCommandOpen(false); setCopilotOpen(true); }}>Proposal Copilotを開く</button>
          </div>
        </div>
      )}

      <div className={`proposal-copilot-chat ${copilotOpen ? "open" : ""}`}>
        <button className="proposal-copilot-launcher" type="button" onClick={() => setCopilotOpen((current) => !current)} aria-expanded={copilotOpen}>
          <Bot size={22} /> Proposal Copilot
        </button>
        {copilotOpen && (
          <div className="proposal-copilot-panel" role="dialog" aria-label="Proposal Copilot">
            <div className="proposal-copilot-chat-header">
              <strong>Proposal Copilot</strong>
              <button type="button" onClick={() => setCopilotOpen(false)}>閉じる</button>
            </div>
            <div className="proposal-copilot-suggestions">
              {["この案件どう思う？", "もっと提案を強くしたい", "競合は？", "受注率を上げるには？"].map((item) => (
                <button key={item} type="button" onClick={() => submitCopilot(item)}>{item}</button>
              ))}
            </div>
            <div className="proposal-copilot-messages">
              {copilotMessages.map((item, index) => (
                <p key={`${item.role}-${index}`} className={item.role}>{item.text}</p>
              ))}
            </div>
            <form onSubmit={(event) => { event.preventDefault(); submitCopilot(); }}>
              <input value={copilotDraft} onChange={(event) => setCopilotDraft(event.target.value)} placeholder="相談内容を入力" />
              <button type="submit" aria-label="送信"><Send size={16} /></button>
            </form>
          </div>
        )}
      </div>
    </section>
  );
}

function PanelTitle({ eyebrow, title }: { eyebrow: string; title: string }) {
  return (
    <div className="section-heading-row">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
      </div>
    </div>
  );
}

function ReviewBlock({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="proposal-agent-review-block">
      <strong>{title}</strong>
      <ul>
        {(items.length ? items : ["確認対象の案件が増えると表示されます。"]).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function KpiCard({ label, value }: { label: string; value: string }) {
  return (
    <article>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function DetailList({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <strong>{title}</strong>
      <ul>
        {(items.length ? items : ["追加情報を確認してください。"]).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function RecentProjectCard({ project, pinned, onPin }: { project: ProposalAgentProjectScore; pinned: boolean; onPin: () => void }) {
  return (
    <article className="proposal-agent-score-card proposal-recent-project-card">
      <div>
        <span>{project.customer_name || "顧客未設定"}</span>
        <h3>{project.project_name}</h3>
      </div>
      <strong>{project.score}</strong>
      <button type="button" onClick={onPin} aria-pressed={pinned}>
        <Pin size={16} /> {pinned ? "Pinned" : "Pin"}
      </button>
      {project.improvements.length > 0 && (
        <ul>
          {project.improvements.slice(0, 2).map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}
    </article>
  );
}

function SummaryCard({ title, body }: { title: string; body: string }) {
  return (
    <article className="proposal-agent-summary-card">
      <h3>{title}</h3>
      <p>{body || "案件データが増えると要約が表示されます。"}</p>
    </article>
  );
}
