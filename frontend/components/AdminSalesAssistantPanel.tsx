"use client";

import { AlertTriangle, ClipboardCopy, FileJson, Loader2, Plus, Sparkles, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  generateSalesAssistantBrief,
  getSalesAssistantStatus,
  type SalesAssistantBrief,
  type SalesAssistantGeneratePayload,
  type SalesAssistantGenerateResponse,
  type SalesAssistantMeetingStage,
  type SalesAssistantStatus
} from "@/lib/api";
import { SalesAssistantProposalPreview } from "./SalesAssistantProposalPreview";

type ListField = "known_requirements" | "known_constraints" | "previous_interactions" | "evidence_items";

const meetingStageOptions: Array<{ value: SalesAssistantMeetingStage; label: string }> = [
  { value: "preparation", label: "商談前準備" },
  { value: "first_meeting", label: "初回商談" },
  { value: "discovery", label: "ヒアリング" },
  { value: "proposal", label: "提案" },
  { value: "negotiation", label: "条件調整" },
  { value: "closing", label: "クロージング" },
  { value: "follow_up", label: "フォローアップ" }
];

const emptyForm: SalesAssistantGeneratePayload = {
  project_title: "",
  project_summary: "",
  client_name: "",
  known_requirements: [""],
  known_constraints: [""],
  budget_information: "",
  schedule_information: "",
  meeting_stage: "preparation",
  previous_interactions: [""],
  evidence_items: [""]
};

const sampleForm: SalesAssistantGeneratePayload = {
  project_title: "生花オークション向けAI画像認識導入支援",
  project_summary:
    "生花の商品画像と商品データの対応確認、品質チェック、花の種類・色・等級・状態の分類を人手で行っている。AI画像認識により候補を提示し、担当者が最終確認する運用を構築したい。",
  client_name: "株式会社サンプルフラワー",
  known_requirements: ["AIは候補提示に限定し、人が最終確認する", "APIまたはCSVで既存の商品管理システムへ連携する"],
  known_constraints: ["まずPoCで精度と現場適合性を評価する", "入力されていない実績値は断定しない"],
  budget_information: "予算上限は1,000万円",
  schedule_information: "2027年5月頃の導入を想定",
  meeting_stage: "preparation",
  previous_interactions: ["現場担当者から繁忙時の確認工数が課題と共有済み"],
  evidence_items: ["対象業務: 商品画像、ロット情報、種類、色、等級、状態の確認"]
};

export function AdminSalesAssistantPanel() {
  const [status, setStatus] = useState<SalesAssistantStatus | null>(null);
  const [form, setForm] = useState<SalesAssistantGeneratePayload>(emptyForm);
  const [result, setResult] = useState<SalesAssistantGenerateResponse | null>(null);
  const [lastGeneratedPayload, setLastGeneratedPayload] = useState<SalesAssistantGeneratePayload | null>(null);
  const [showJson, setShowJson] = useState(false);
  const [isStatusLoading, setIsStatusLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    setIsStatusLoading(true);
    getSalesAssistantStatus()
      .then((nextStatus) => {
        if (mounted) setStatus(nextStatus);
      })
      .catch((caught) => {
        if (mounted) setError(toErrorMessage(caught));
      })
      .finally(() => {
        if (mounted) setIsStatusLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  const trimmedForm = useMemo(() => normalizePayload(form), [form]);
  const canSubmit = Boolean(trimmedForm.project_title && trimmedForm.project_summary && status?.enabled && !isGenerating);

  async function handleGenerate() {
    setError("");
    setNotice("");
    setResult(null);
    setLastGeneratedPayload(null);
    if (!trimmedForm.project_title || !trimmedForm.project_summary) {
      setError("案件名と案件概要を入力してください。");
      return;
    }
    if (!status?.enabled) {
      setError("AI営業アシスタントはFeature Flagで無効です。");
      return;
    }
    setIsGenerating(true);
    try {
      const response = await generateSalesAssistantBrief(trimmedForm);
      setResult(response);
      setLastGeneratedPayload(trimmedForm);
      setNotice("Sales Assistant Briefを生成しました。内容を確認してから営業利用してください。");
    } catch (caught) {
      setError(toErrorMessage(caught));
    } finally {
      setIsGenerating(false);
    }
  }

  function updateField<K extends keyof SalesAssistantGeneratePayload>(key: K, value: SalesAssistantGeneratePayload[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function updateList(field: ListField, index: number, value: string) {
    setForm((current) => ({
      ...current,
      [field]: current[field].map((item, itemIndex) => (itemIndex === index ? value : item))
    }));
  }

  function addListItem(field: ListField) {
    setForm((current) => ({ ...current, [field]: [...current[field], ""] }));
  }

  function removeListItem(field: ListField, index: number) {
    setForm((current) => {
      const next = current[field].filter((_, itemIndex) => itemIndex !== index);
      return { ...current, [field]: next.length ? next : [""] };
    });
  }

  async function copyText(label: string, text: string) {
    setError("");
    setNotice("");
    try {
      await navigator.clipboard.writeText(text);
      setNotice(`${label}をコピーしました。`);
    } catch {
      setError("コピーできませんでした。ブラウザの権限を確認してください。");
    }
  }

  return (
    <section className="sales-assistant-panel" aria-label="AI営業アシスタント">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Version 50</p>
          <h2>AI営業アシスタント</h2>
          <p>Strategy Briefをもとに、営業担当が商談前に確認できるSales Assistant Briefを生成します。</p>
        </div>
        <span>{status?.enabled ? "有効" : "無効"}</span>
      </div>

      <div className="sales-assistant-status-row">
        <StatusPill label="Feature Flag" value={status?.enabled ? "ON" : "OFF"} tone={status?.enabled ? "ok" : "muted"} />
        <StatusPill label="Version" value={status?.version ?? "未取得"} tone="muted" />
        <StatusPill label="Admin Required" value={status?.requires_admin ? "Yes" : "No"} tone={status?.requires_admin ? "ok" : "warn"} />
        <StatusPill label="DB Save" value={status?.persistence_enabled ? "Enabled" : "Disabled"} tone="muted" />
        <StatusPill label="External AI" value={status?.external_ai_enabled ? "Enabled" : "Disabled"} tone="muted" />
        <StatusPill label="Proposal Preview" value={status?.proposal_preview_enabled ? "ON" : "OFF"} tone={status?.proposal_preview_enabled ? "ok" : "muted"} />
        <StatusPill label="Proposal Export" value={status?.proposal_export_enabled ? "ON" : "OFF"} tone={status?.proposal_export_enabled ? "ok" : "muted"} />
        <StatusPill label="Beautiful.ai Export" value={status?.beautiful_ai_export_enabled ? "ON" : "OFF"} tone={status?.beautiful_ai_export_enabled ? "ok" : "muted"} />
      </div>

      {isStatusLoading && (
        <p className="sales-assistant-inline-status">
          <Loader2 size={16} aria-hidden="true" /> 状態を確認しています。
        </p>
      )}
      {status && !status.enabled && (
        <div className="sales-assistant-warning" role="status">
          <AlertTriangle size={18} aria-hidden="true" />
          <p>AI営業アシスタントはFeature Flagで無効です。BackendのSALES_ASSISTANT_ENABLEDをtrueにした場合のみ利用できます。</p>
        </div>
      )}
      {notice && <p className="sales-assistant-notice">{notice}</p>}
      {error && <p className="sales-assistant-error" role="alert">{error}</p>}

      <div className="sales-assistant-layout">
        <form className="sales-assistant-form" onSubmit={(event) => event.preventDefault()}>
          <div className="sales-assistant-actions">
            <button className="secondary-action" type="button" onClick={() => setForm(sampleForm)}>
              サンプルを使う
            </button>
            <button
              className="secondary-action"
              type="button"
              onClick={() => {
                setForm(emptyForm);
                setResult(null);
                setLastGeneratedPayload(null);
                setError("");
                setNotice("");
              }}
            >
              クリア
            </button>
          </div>
          <TextInput label="案件名" required value={form.project_title} maxLength={200} onChange={(value) => updateField("project_title", value)} />
          <TextInput label="顧客名" value={form.client_name ?? ""} maxLength={200} onChange={(value) => updateField("client_name", value)} />
          <TextArea
            label="案件概要"
            required
            value={form.project_summary}
            maxLength={10000}
            onChange={(value) => updateField("project_summary", value)}
          />
          <div className="sales-assistant-field">
            <label htmlFor="sales-assistant-meeting-stage">商談段階</label>
            <select
              id="sales-assistant-meeting-stage"
              value={form.meeting_stage}
              onChange={(event) => updateField("meeting_stage", event.target.value as SalesAssistantMeetingStage)}
            >
              {meetingStageOptions.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>
          <TextArea
            label="予算情報"
            value={form.budget_information ?? ""}
            maxLength={2000}
            onChange={(value) => updateField("budget_information", value)}
          />
          <TextArea
            label="スケジュール情報"
            value={form.schedule_information ?? ""}
            maxLength={2000}
            onChange={(value) => updateField("schedule_information", value)}
          />
          <ListEditor title="既知の要件" field="known_requirements" items={form.known_requirements} onAdd={addListItem} onRemove={removeListItem} onChange={updateList} />
          <ListEditor title="制約条件" field="known_constraints" items={form.known_constraints} onAdd={addListItem} onRemove={removeListItem} onChange={updateList} />
          <ListEditor title="過去のやり取り" field="previous_interactions" items={form.previous_interactions} onAdd={addListItem} onRemove={removeListItem} onChange={updateList} />
          <ListEditor title="根拠・確認済み情報" field="evidence_items" items={form.evidence_items} onAdd={addListItem} onRemove={removeListItem} onChange={updateList} />
          <button className="primary-action sales-assistant-submit" type="button" disabled={!canSubmit} onClick={() => void handleGenerate()}>
            {isGenerating ? <Loader2 size={16} aria-hidden="true" /> : <Sparkles size={16} aria-hidden="true" />}
            Sales Assistant Briefを生成
          </button>
        </form>

        <div className="sales-assistant-output">
          {result ? (
            <>
              <ResultView result={result} showJson={showJson} onToggleJson={() => setShowJson((current) => !current)} onCopy={(label, text) => void copyText(label, text)} />
              {lastGeneratedPayload && (
                <SalesAssistantProposalPreview
                  sourcePayload={lastGeneratedPayload}
                  salesAssistantResult={result}
                  enabled={Boolean(status?.proposal_preview_enabled)}
                  exportEnabled={Boolean(status?.proposal_export_enabled)}
                  beautifulAiEnabled={Boolean(status?.beautiful_ai_export_enabled)}
                />
              )}
            </>
          ) : (
            <div className="sales-assistant-empty">
              <Sparkles size={24} aria-hidden="true" />
              <h3>商談準備用のBriefをここに表示します</h3>
              <p>入力内容はDBへ保存されず、外部AIにも送信されません。生成後は人が確認してから営業利用してください。</p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function ResultView({
  result,
  showJson,
  onToggleJson,
  onCopy
}: {
  result: SalesAssistantGenerateResponse;
  showJson: boolean;
  onToggleJson: () => void;
  onCopy: (label: string, text: string) => void;
}) {
  const brief = result.sales_assistant_brief;
  return (
    <>
      {result.human_review_required && (
        <div className="sales-assistant-warning" role="status">
          <AlertTriangle size={18} aria-hidden="true" />
          <div>
            <strong>Human Reviewが必要です</strong>
            <List items={result.human_review_reasons} />
          </div>
        </div>
      )}
      <div className="sales-assistant-copy-grid">
        <CopyButton label="サマリー" text={formatSummary(brief)} onCopy={onCopy} />
        <CopyButton label="質問" text={brief.discovery_questions.map((item) => item.question).join("\n")} onCopy={onCopy} />
        <CopyButton label="トーク" text={formatTalkTrack(brief)} onCopy={onCopy} />
        <CopyButton label="反論対応" text={brief.objection_handling.map((item) => `${item.expected_objection}\n${item.recommended_response}`).join("\n\n")} onCopy={onCopy} />
        <CopyButton label="次アクション" text={brief.next_actions.map((item) => `${item.action} (${item.owner})`).join("\n")} onCopy={onCopy} />
        <CopyButton label="フォロー" text={brief.follow_up.email_body} onCopy={onCopy} />
        <CopyButton label="全文" text={formatFullBrief(brief)} onCopy={onCopy} />
      </div>
      <Section title="1. Summary">
        <KeyValue label="案件" value={brief.summary.project_title} />
        <KeyValue label="顧客" value={brief.summary.client_name} />
        <KeyValue label="カテゴリ" value={brief.summary.category} />
        <KeyValue label="Persona" value={brief.summary.persona} />
        <KeyValue label="主メッセージ" value={brief.summary.primary_message} />
        <List items={brief.summary.summary_notes} />
      </Section>
      <Section title="2. Meeting Plan">
        <KeyValue label="目的" value={brief.meeting_plan.objective} />
        <KeyValue label="推奨時間" value={`${brief.meeting_plan.recommended_duration_minutes}分`} />
        <List items={brief.meeting_plan.agenda} />
      </Section>
      <Section title="3. Discovery Questions">
        <List items={brief.discovery_questions.map((item) => `${item.question} / ${item.purpose}`)} />
      </Section>
      <Section title="4. Talk Track">
        <p>{formatTalkTrack(brief)}</p>
      </Section>
      <Section title="5. Objection Handling">
        <List items={brief.objection_handling.map((item) => `${item.expected_objection}: ${item.recommended_response}`)} />
      </Section>
      <Section title="6. Decision Maker Support">
        <List items={brief.decision_maker_support.decision_points.concat(brief.decision_maker_support.materials_to_prepare)} />
      </Section>
      <Section title="7. Evidence Guidance">
        <List items={brief.evidence_guidance.available_evidence.concat(brief.evidence_guidance.evidence_gaps)} />
      </Section>
      <Section title="8. Next Actions">
        <List items={brief.next_actions.map((item) => `${item.action} - ${item.reason}`)} />
      </Section>
      <Section title="9. Follow-up">
        <KeyValue label="件名" value={brief.follow_up.email_subject} />
        <p>{brief.follow_up.email_body}</p>
      </Section>
      <Section title="10. Term Guard / Risk">
        <KeyValue label="重要度" value={brief.risk_and_guardrails.review_severity} />
        <List items={brief.risk_and_guardrails.guardrails.concat(brief.risk_and_guardrails.removed_or_replaced_terms)} />
      </Section>
      <Section title="11. Metadata">
        <KeyValue label="Generator" value={brief.generation_metadata.generator_version} />
        <KeyValue label="Deterministic" value={brief.generation_metadata.deterministic ? "true" : "false"} />
        <List items={brief.generation_metadata.selected_rules} />
      </Section>
      <button className="secondary-action sales-assistant-json-button" type="button" onClick={onToggleJson}>
        <FileJson size={16} aria-hidden="true" />
        JSON表示を{showJson ? "閉じる" : "開く"}
      </button>
      {showJson && <pre className="sales-assistant-json">{JSON.stringify(result, null, 2)}</pre>}
    </>
  );
}

function StatusPill({ label, value, tone }: { label: string; value: string; tone: "ok" | "warn" | "muted" }) {
  return (
    <span className={`sales-assistant-status-pill ${tone}`}>
      <small>{label}</small>
      <strong>{value}</strong>
    </span>
  );
}

function TextInput({ label, value, required, maxLength, onChange }: { label: string; value: string; required?: boolean; maxLength: number; onChange: (value: string) => void }) {
  const id = `sales-assistant-${label}`;
  return (
    <div className="sales-assistant-field">
      <label htmlFor={id}>{label}{required ? " *" : ""}</label>
      <input id={id} value={value} maxLength={maxLength} onChange={(event) => onChange(event.target.value)} />
      <small>{value.length}/{maxLength}</small>
    </div>
  );
}

function TextArea({ label, value, required, maxLength, onChange }: { label: string; value: string; required?: boolean; maxLength: number; onChange: (value: string) => void }) {
  const id = `sales-assistant-${label}`;
  return (
    <div className="sales-assistant-field">
      <label htmlFor={id}>{label}{required ? " *" : ""}</label>
      <textarea id={id} value={value} maxLength={maxLength} onChange={(event) => onChange(event.target.value)} />
      <small>{value.length}/{maxLength}</small>
    </div>
  );
}

function ListEditor({
  title,
  field,
  items,
  onAdd,
  onRemove,
  onChange
}: {
  title: string;
  field: ListField;
  items: string[];
  onAdd: (field: ListField) => void;
  onRemove: (field: ListField, index: number) => void;
  onChange: (field: ListField, index: number, value: string) => void;
}) {
  return (
    <div className="sales-assistant-list-editor">
      <div className="sales-assistant-list-title">
        <span>{title}</span>
        <button className="icon-button" type="button" aria-label={`${title}を追加`} onClick={() => onAdd(field)}>
          <Plus size={15} aria-hidden="true" />
        </button>
      </div>
      {items.map((item, index) => (
        <div className="sales-assistant-list-row" key={`${field}-${index}`}>
          <input value={item} maxLength={1000} onChange={(event) => onChange(field, index, event.target.value)} aria-label={`${title} ${index + 1}`} />
          <button className="icon-button" type="button" aria-label={`${title} ${index + 1}を削除`} onClick={() => onRemove(field, index)}>
            <Trash2 size={15} aria-hidden="true" />
          </button>
        </div>
      ))}
    </div>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <article className="sales-assistant-section">
      <h3>{title}</h3>
      {children}
    </article>
  );
}

function KeyValue({ label, value }: { label: string; value: string }) {
  return (
    <p className="sales-assistant-key-value">
      <strong>{label}</strong>
      <span>{value || "未設定"}</span>
    </p>
  );
}

function List({ items }: { items: string[] }) {
  const filtered = items.filter(Boolean);
  if (!filtered.length) return <p className="sales-assistant-muted">該当項目はありません。</p>;
  return (
    <ul className="sales-assistant-list">
      {filtered.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}
    </ul>
  );
}

function CopyButton({ label, text, onCopy }: { label: string; text: string; onCopy: (label: string, text: string) => void }) {
  return (
    <button className="secondary-action" type="button" onClick={() => onCopy(label, text)}>
      <ClipboardCopy size={15} aria-hidden="true" />
      {label}
    </button>
  );
}

function normalizePayload(payload: SalesAssistantGeneratePayload): SalesAssistantGeneratePayload {
  return {
    ...payload,
    project_title: payload.project_title.trim(),
    project_summary: payload.project_summary.trim(),
    client_name: (payload.client_name ?? "").trim(),
    budget_information: (payload.budget_information ?? "").trim(),
    schedule_information: (payload.schedule_information ?? "").trim(),
    known_requirements: payload.known_requirements.map((item) => item.trim()).filter(Boolean),
    known_constraints: payload.known_constraints.map((item) => item.trim()).filter(Boolean),
    previous_interactions: payload.previous_interactions.map((item) => item.trim()).filter(Boolean),
    evidence_items: payload.evidence_items.map((item) => item.trim()).filter(Boolean)
  };
}

function formatSummary(brief: SalesAssistantBrief) {
  return [
    `案件: ${brief.summary.project_title}`,
    `顧客: ${brief.summary.client_name}`,
    `カテゴリ: ${brief.summary.category}`,
    `主メッセージ: ${brief.summary.primary_message}`,
    `推奨ポジション: ${brief.summary.recommended_positioning}`
  ].join("\n");
}

function formatTalkTrack(brief: SalesAssistantBrief) {
  return [
    brief.talk_track.opening_talk,
    brief.talk_track.problem_confirmation,
    brief.talk_track.proposal_explanation,
    brief.talk_track.value_explanation,
    brief.talk_track.closing_talk
  ].join("\n\n");
}

function formatFullBrief(brief: SalesAssistantBrief) {
  return [
    "# Sales Assistant Brief",
    formatSummary(brief),
    "## Meeting Plan",
    brief.meeting_plan.agenda.join("\n"),
    "## Discovery Questions",
    brief.discovery_questions.map((item) => item.question).join("\n"),
    "## Talk Track",
    formatTalkTrack(brief),
    "## Next Actions",
    brief.next_actions.map((item) => item.action).join("\n"),
    "## Follow-up",
    brief.follow_up.email_body
  ].join("\n\n");
}

function toErrorMessage(caught: unknown) {
  return caught instanceof Error ? caught.message : "AI営業アシスタントの処理に失敗しました。";
}
