"use client";

import { memo, useEffect, useMemo, useState } from "react";
import {
  createKnowledgeEntry,
  createProposalTemplate,
  getKnowledgeBestPractices,
  getKnowledgeEntries,
  getProposalTemplates,
  recalculateKnowledgeQuality,
  updateKnowledgeEvaluation,
  updateKnowledgeStatus,
  updateProposalTemplateActive,
  type CreateKnowledgePayload,
  type CreateTemplatePayload
} from "@/lib/api";
import { toFriendlyError } from "@/lib/errorMessage";
import type {
  KnowledgeApprovalStatus,
  KnowledgeBestPractices,
  ProposalKnowledgeEntry,
  ProposalTemplateCategory,
  ProposalTemplateEntry
} from "@/types/app";

const categoryLabels: Record<ProposalTemplateCategory, string> = {
  web: "Web制作",
  recruiting: "採用",
  lp: "LP",
  seo: "SEO",
  dx: "DX",
  other: "その他"
};

const statusLabels: Record<KnowledgeApprovalStatus, string> = {
  draft: "下書き",
  pending_review: "要確認",
  approved: "承認済み",
  rejected: "却下",
  archived: "アーカイブ"
};

const riskLabels: Record<string, string> = {
  low: "低",
  medium: "中",
  high: "高"
};

const flagLabels: Record<string, string> = {
  email: "メール",
  phone: "電話番号",
  postal_code: "郵便番号",
  url: "URL",
  api_key: "APIキー",
  address: "住所",
  personal_name: "個人名",
  amount_or_contract: "金額・契約条件"
};

const emptyKnowledgeForm: CreateKnowledgePayload = {
  industry: "",
  company_size: "",
  project_summary: "",
  adopted_proposal: "",
  proposal_story: "",
  adoption_reason: "",
  lost_reason: "",
  result: "",
  owner_memo: "",
  outcome: "unknown",
  rating: 3,
  evaluation_status: "effective",
  tags: "",
  source_type: "admin_created",
  source_note: ""
};

const emptyTemplateForm: CreateTemplatePayload = {
  category: "web",
  title: "",
  template_summary: "",
  structure: "",
  recommended_for: "",
  is_active: true
};

function formatDate(value: string | undefined) {
  return value ? value.replace("T", " ").slice(0, 16) : "-";
}

function stars(rating: number) {
  return "★".repeat(rating) + "☆".repeat(Math.max(0, 5 - rating));
}

function shortText(value: string, maxLength = 80) {
  return value.length > maxLength ? `${value.slice(0, maxLength)}...` : value;
}

function formatFlags(entry: ProposalKnowledgeEntry) {
  const flags = entry.confidential_flags_list?.length
    ? entry.confidential_flags_list
    : String(entry.confidential_flags || "").split(",").filter(Boolean);
  return flags.length ? flags.map((flag) => flagLabels[flag] ?? flag).join(" / ") : "検出なし";
}

export const AdminKnowledgePanel = memo(function AdminKnowledgePanel() {
  const [entries, setEntries] = useState<ProposalKnowledgeEntry[]>([]);
  const [templates, setTemplates] = useState<ProposalTemplateEntry[]>([]);
  const [bestPractices, setBestPractices] = useState<KnowledgeBestPractices | null>(null);
  const [knowledgeForm, setKnowledgeForm] = useState<CreateKnowledgePayload>(emptyKnowledgeForm);
  const [templateForm, setTemplateForm] = useState<CreateTemplatePayload>(emptyTemplateForm);
  const [statusMessage, setStatusMessage] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  const reviewEntries = useMemo(
    () => entries.filter((entry) => entry.approval_status === "pending_review" || entry.approval_status === "draft"),
    [entries]
  );
  const approvedCount = useMemo(() => entries.filter((entry) => entry.approval_status === "approved").length, [entries]);
  const highQualityCount = useMemo(
    () => entries.filter((entry) => entry.quality_score >= 70 && entry.approval_status === "approved").length,
    [entries]
  );

  async function loadKnowledge() {
    setIsLoading(true);
    setStatusMessage("");
    try {
      const [entryResponse, templateResponse, practiceResponse] = await Promise.all([
        getKnowledgeEntries(50, 0),
        getProposalTemplates("", true, 50, 0),
        getKnowledgeBestPractices()
      ]);
      const practices = practiceResponse.best_practices;
      setEntries(Array.isArray(entryResponse.entries) ? entryResponse.entries : []);
      setTemplates(Array.isArray(templateResponse.templates) ? templateResponse.templates : []);
      setBestPractices(
        practices
          ? {
              winning_structures: Array.isArray(practices.winning_structures) ? practices.winning_structures : [],
              frequent_proposals: Array.isArray(practices.frequent_proposals) ? practices.frequent_proposals : [],
              industry_success_examples: Array.isArray(practices.industry_success_examples) ? practices.industry_success_examples : []
            }
          : null
      );
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setStatusMessage(`${friendly.title} ${friendly.action}`);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadKnowledge();
  }, []);

  async function saveKnowledge() {
    if (!knowledgeForm.project_summary?.trim()) {
      setStatusMessage("案件概要の要約を入力してください。本文全文ではなく、再利用できる要約だけを保存します。");
      return;
    }
    try {
      const response = await createKnowledgeEntry(knowledgeForm);
      setKnowledgeForm(emptyKnowledgeForm);
      await loadKnowledge();
      setStatusMessage(`ナレッジを保存しました。状態: ${statusLabels[response.entry.approval_status as KnowledgeApprovalStatus] ?? response.entry.approval_status}`);
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setStatusMessage(`${friendly.title} ${friendly.action}`);
    }
  }

  async function saveTemplate() {
    if (!templateForm.title.trim()) {
      setStatusMessage("テンプレート名を入力してください。");
      return;
    }
    try {
      await createProposalTemplate(templateForm);
      setTemplateForm(emptyTemplateForm);
      await loadKnowledge();
      setStatusMessage("提案テンプレートを保存しました。");
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setStatusMessage(`${friendly.title} ${friendly.action}`);
    }
  }

  async function updateRating(entry: ProposalKnowledgeEntry, rating: number) {
    try {
      await updateKnowledgeEvaluation(entry.id, {
        rating,
        evaluation_status: entry.evaluation_status === "needs_improvement" ? "needs_improvement" : "effective"
      });
      await loadKnowledge();
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setStatusMessage(`${friendly.title} ${friendly.action}`);
    }
  }

  async function changeStatus(entry: ProposalKnowledgeEntry, approvalStatus: KnowledgeApprovalStatus) {
    try {
      await updateKnowledgeStatus(entry.id, approvalStatus);
      await loadKnowledge();
      setStatusMessage(`ナレッジを${statusLabels[approvalStatus]}に変更しました。`);
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setStatusMessage(`${friendly.title} ${friendly.action}`);
    }
  }

  async function recalculateQuality(entry: ProposalKnowledgeEntry) {
    try {
      const response = await recalculateKnowledgeQuality(entry.id);
      await loadKnowledge();
      setStatusMessage(`品質スコアを再計算しました。現在のスコア: ${response.entry.quality_score}点`);
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setStatusMessage(`${friendly.title} ${friendly.action}`);
    }
  }

  async function toggleTemplate(template: ProposalTemplateEntry) {
    try {
      await updateProposalTemplateActive(template.id, !template.is_active);
      await loadKnowledge();
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setStatusMessage(`${friendly.title} ${friendly.action}`);
    }
  }

  if (isLoading) {
    return (
      <section className="admin-usage-dashboard-panel">
        <p className="helper-text">ナレッジ管理を読み込んでいます。</p>
      </section>
    );
  }

  return (
    <section className="admin-usage-dashboard-panel">
      <div className="section-heading-row">
        <div>
          <p className="eyebrow">Version 8.1</p>
          <h3>Knowledge Quality Control</h3>
          <p className="helper-text">承認済みナレッジだけをAIが参照します。保存時に機密情報リスクと品質スコアを確認します。</p>
        </div>
        <button className="secondary-button" type="button" onClick={() => void loadKnowledge()}>
          再読み込み
        </button>
      </div>

      {statusMessage ? <p className="status-note">{statusMessage}</p> : null}

      <div className="usage-dashboard-grid">
        <article>
          <span>レビュー待ち</span>
          <strong>{reviewEntries.length}</strong>
          <p>承認前のナレッジ</p>
        </article>
        <article>
          <span>承認済み</span>
          <strong>{approvedCount}</strong>
          <p>AI参照対象</p>
        </article>
        <article>
          <span>高品質</span>
          <strong>{highQualityCount}</strong>
          <p>70点以上かつ承認済み</p>
        </article>
        <article>
          <span>テンプレート</span>
          <strong>{templates.length}</strong>
          <p>提案構成の再利用</p>
        </article>
      </div>

      <details className="advanced-foldout" open>
        <summary>レビュー待ちナレッジ</summary>
        <div className="table-scroll">
          <table className="usage-dashboard-table">
            <thead>
              <tr>
                <th>タイトル</th>
                <th>業種</th>
                <th>状態</th>
                <th>品質</th>
                <th>機密リスク</th>
                <th>最終更新</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {reviewEntries.length ? reviewEntries.map((entry) => (
                <tr key={entry.id}>
                  <td>{shortText(entry.project_summary, 70)}</td>
                  <td>{entry.industry || "other"}</td>
                  <td>{statusLabels[entry.approval_status as KnowledgeApprovalStatus] ?? entry.approval_status}</td>
                  <td>{entry.quality_score}点</td>
                  <td>
                    {riskLabels[entry.confidential_risk] ?? entry.confidential_risk}
                    <br />
                    <small>{formatFlags(entry)}</small>
                  </td>
                  <td>{formatDate(entry.updated_at)}</td>
                  <td>
                    <div className="button-row">
                      <button className="secondary-button compact-button" type="button" onClick={() => void changeStatus(entry, "approved")}>
                        承認
                      </button>
                      <button className="secondary-button compact-button" type="button" onClick={() => void changeStatus(entry, "rejected")}>
                        却下
                      </button>
                      <button className="secondary-button compact-button" type="button" onClick={() => void changeStatus(entry, "archived")}>
                        保管
                      </button>
                      <button className="secondary-button compact-button" type="button" onClick={() => void recalculateQuality(entry)}>
                        再計算
                      </button>
                    </div>
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={7}>レビュー待ちのナレッジはありません。</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </details>

      <details className="advanced-foldout">
        <summary>ナレッジを登録</summary>
        <div className="release-note-form">
          <label className="field">
            <span>案件業種</span>
            <input value={knowledgeForm.industry ?? ""} onChange={(event) => setKnowledgeForm({ ...knowledgeForm, industry: event.target.value })} />
          </label>
          <label className="field">
            <span>会社規模</span>
            <input value={knowledgeForm.company_size ?? ""} onChange={(event) => setKnowledgeForm({ ...knowledgeForm, company_size: event.target.value })} />
          </label>
          <label className="field">
            <span>案件概要（要約のみ）</span>
            <textarea rows={3} value={knowledgeForm.project_summary} onChange={(event) => setKnowledgeForm({ ...knowledgeForm, project_summary: event.target.value })} />
          </label>
          <label className="field">
            <span>採用した提案</span>
            <textarea rows={3} value={knowledgeForm.adopted_proposal ?? ""} onChange={(event) => setKnowledgeForm({ ...knowledgeForm, adopted_proposal: event.target.value })} />
          </label>
          <label className="field">
            <span>提案ストーリー</span>
            <textarea rows={3} value={knowledgeForm.proposal_story ?? ""} onChange={(event) => setKnowledgeForm({ ...knowledgeForm, proposal_story: event.target.value })} />
          </label>
          <label className="field">
            <span>結果・メモ</span>
            <textarea rows={4} value={knowledgeForm.owner_memo ?? ""} onChange={(event) => setKnowledgeForm({ ...knowledgeForm, owner_memo: event.target.value })} />
          </label>
          <label className="field">
            <span>出典メモ</span>
            <input value={knowledgeForm.source_note ?? ""} onChange={(event) => setKnowledgeForm({ ...knowledgeForm, source_note: event.target.value })} placeholder="例: 2026年7月の社内レビューより" />
          </label>
          <div className="button-row">
            <select value={knowledgeForm.source_type} onChange={(event) => setKnowledgeForm({ ...knowledgeForm, source_type: event.target.value as CreateKnowledgePayload["source_type"] })}>
              <option value="admin_created">管理者登録</option>
              <option value="imported">インポート</option>
              <option value="feedback_based">フィードバック由来</option>
              <option value="proposal_generated">提案書作成由来</option>
            </select>
            <select value={knowledgeForm.outcome} onChange={(event) => setKnowledgeForm({ ...knowledgeForm, outcome: event.target.value as CreateKnowledgePayload["outcome"] })}>
              <option value="unknown">未分類</option>
              <option value="success">成功</option>
              <option value="lost">失注</option>
            </select>
            <select value={knowledgeForm.rating} onChange={(event) => setKnowledgeForm({ ...knowledgeForm, rating: Number(event.target.value) })}>
              {[1, 2, 3, 4, 5].map((value) => (
                <option key={value} value={value}>{stars(value)}</option>
              ))}
            </select>
            <button className="primary-button" type="button" onClick={() => void saveKnowledge()}>
              保存
            </button>
          </div>
        </div>
      </details>

      <details className="advanced-foldout">
        <summary>類似案件とベストプラクティス</summary>
        <div className="insight-list">
          <article className="insight-card">
            <span>よく受注する構成</span>
            {(bestPractices?.winning_structures.length ? bestPractices.winning_structures : ["承認済みナレッジがまだありません。"]).map((item) => (
              <p key={item}>{item}</p>
            ))}
          </article>
          <article className="insight-card">
            <span>よく使われる提案</span>
            <p>{bestPractices?.frequent_proposals.length ? bestPractices.frequent_proposals.join(" / ") : "承認待ち"}</p>
          </article>
          <article className="insight-card">
            <span>業種別成功例</span>
            <p>
              {bestPractices?.industry_success_examples.length
                ? bestPractices.industry_success_examples.map((item) => `${item.industry}: ${item.count}件`).join(" / ")
                : "承認待ち"}
            </p>
          </article>
        </div>
      </details>

      <details className="advanced-foldout">
        <summary>Knowledge一覧</summary>
        <div className="table-scroll">
          <table className="usage-dashboard-table">
            <thead>
              <tr>
                <th>業種</th>
                <th>要約</th>
                <th>状態</th>
                <th>品質</th>
                <th>評価</th>
                <th>出典</th>
                <th>更新日</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr key={entry.id}>
                  <td>{entry.industry}</td>
                  <td>{shortText(entry.project_summary, 90)}</td>
                  <td>{statusLabels[entry.approval_status as KnowledgeApprovalStatus] ?? entry.approval_status}</td>
                  <td>{entry.quality_score}点 / {riskLabels[entry.confidential_risk] ?? entry.confidential_risk}</td>
                  <td>
                    <button className="secondary-button compact-button" type="button" onClick={() => void updateRating(entry, Math.min(entry.rating + 1, 5))}>
                      {stars(entry.rating)}
                    </button>
                  </td>
                  <td>{entry.source_type}</td>
                  <td>{formatDate(entry.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>

      <details className="advanced-foldout">
        <summary>提案テンプレート管理</summary>
        <div className="release-note-form">
          <label className="field">
            <span>カテゴリ</span>
            <select value={templateForm.category} onChange={(event) => setTemplateForm({ ...templateForm, category: event.target.value as ProposalTemplateCategory })}>
              {Object.entries(categoryLabels).map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>テンプレート名</span>
            <input value={templateForm.title} onChange={(event) => setTemplateForm({ ...templateForm, title: event.target.value })} />
          </label>
          <label className="field">
            <span>概要</span>
            <textarea rows={3} value={templateForm.template_summary ?? ""} onChange={(event) => setTemplateForm({ ...templateForm, template_summary: event.target.value })} />
          </label>
          <label className="field">
            <span>構成</span>
            <textarea rows={4} value={templateForm.structure ?? ""} onChange={(event) => setTemplateForm({ ...templateForm, structure: event.target.value })} />
          </label>
          <button className="primary-button" type="button" onClick={() => void saveTemplate()}>
            テンプレート保存
          </button>
        </div>
        <div className="table-scroll">
          <table className="usage-dashboard-table">
            <thead>
              <tr>
                <th>カテゴリ</th>
                <th>テンプレート</th>
                <th>概要</th>
                <th>状態</th>
              </tr>
            </thead>
            <tbody>
              {templates.map((template) => (
                <tr key={template.id}>
                  <td>{categoryLabels[template.category as ProposalTemplateCategory] ?? template.category}</td>
                  <td>{template.title}</td>
                  <td>{shortText(template.template_summary, 80)}</td>
                  <td>
                    <button className="secondary-button compact-button" type="button" onClick={() => void toggleTemplate(template)}>
                      {template.is_active ? "有効" : "無効"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </section>
  );
});
