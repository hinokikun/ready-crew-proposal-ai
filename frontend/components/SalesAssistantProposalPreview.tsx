"use client";

import { AlertTriangle, ClipboardCopy, FileJson, Loader2, RefreshCcw, Sparkles } from "lucide-react";
import { useState, type ReactNode } from "react";
import {
  generateSalesAssistantProposalPreview,
  type SalesAssistantGeneratePayload,
  type SalesAssistantGenerateResponse,
  type SalesAssistantProposalPreviewResponse
} from "@/lib/api";
import { SalesAssistantExportCard } from "./SalesAssistantExportCard";

type Props = {
  sourcePayload: SalesAssistantGeneratePayload;
  salesAssistantResult: SalesAssistantGenerateResponse;
  enabled: boolean;
  exportEnabled: boolean;
  beautifulAiEnabled?: boolean;
};

export function SalesAssistantProposalPreview({ sourcePayload, salesAssistantResult, enabled, exportEnabled, beautifulAiEnabled }: Props) {
  const [preview, setPreview] = useState<SalesAssistantProposalPreviewResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [showJson, setShowJson] = useState(false);

  async function handleGenerate() {
    setError("");
    setNotice("");
    setIsLoading(true);
    try {
      const response = await generateSalesAssistantProposalPreview({
        source_request: sourcePayload,
        sales_assistant_brief: salesAssistantResult.sales_assistant_brief,
        strategy_brief: salesAssistantResult.strategy_brief
      });
      setPreview(response);
      setNotice("Proposal Previewを生成しました。Version52でPPTX接続予定です。");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Proposal Previewの生成に失敗しました。");
    } finally {
      setIsLoading(false);
    }
  }

  function copyText(label: string, text: string) {
    navigator.clipboard.writeText(text)
      .then(() => setNotice(`${label}をコピーしました。`))
      .catch(() => setError("コピーできませんでした。ブラウザの権限を確認してください。"));
  }

  const disabledReason = !enabled
    ? "Proposal Preview連携はFeature Flagで無効です。"
    : "";
  const humanReviewRequired = salesAssistantResult.human_review_required || Boolean(preview?.human_review_required);
  const humanReviewReasons = preview?.human_review_reasons.length
    ? preview.human_review_reasons
    : salesAssistantResult.human_review_reasons;

  return (
    <section className="sales-assistant-proposal-preview" aria-label="Proposal Preview">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Version 51</p>
          <h2>Proposal Preview</h2>
          <p>Sales Assistantの結果を既存Proposal Generatorへ渡し、提案書プレビューだけを生成します。</p>
        </div>
        <span>PPTX未接続</span>
      </div>
      {humanReviewRequired && (
        <div className="sales-assistant-warning" role="status">
          <AlertTriangle size={18} aria-hidden="true" />
          <div>
            <strong>Human Reviewが必要です</strong>
            <ul className="sales-assistant-list">
              {humanReviewReasons.map((reason, index) => <li key={`${reason}-${index}`}>{reason}</li>)}
            </ul>
          </div>
        </div>
      )}
      {disabledReason && <p className="sales-assistant-inline-status">{disabledReason}</p>}
      {notice && <p className="sales-assistant-notice">{notice}</p>}
      {error && (
        <div className="sales-assistant-error" role="alert">
          <AlertTriangle size={18} aria-hidden="true" />
          <div>
            <strong>Proposal Previewを生成できませんでした</strong>
            <p>{error}</p>
            <button className="secondary-action" type="button" disabled={!enabled || isLoading} onClick={() => void handleGenerate()}>
              <RefreshCcw size={15} aria-hidden="true" />
              Proposalだけ再生成
            </button>
          </div>
        </div>
      )}
      <button className="primary-action sales-assistant-submit" type="button" disabled={!enabled || isLoading} onClick={() => void handleGenerate()}>
        {isLoading ? <Loader2 size={16} aria-hidden="true" /> : <Sparkles size={16} aria-hidden="true" />}
        {preview ? "Proposal Previewを再生成" : "提案書を生成"}
      </button>
      {preview ? (
        <>
          <PreviewBody preview={preview} onCopy={copyText} showJson={showJson} onToggleJson={() => setShowJson((current) => !current)} />
          <SalesAssistantExportCard
            sourcePayload={sourcePayload}
            salesAssistantResult={salesAssistantResult}
            previewResponse={preview}
            enabled={exportEnabled}
            beautifulAiEnabled={beautifulAiEnabled}
          />
        </>
      ) : (
        <p className="sales-assistant-muted">Sales Assistant結果は保持されます。Preview生成に失敗した場合も、このボタンからProposalだけ再生成できます。</p>
      )}
    </section>
  );
}

function PreviewBody({
  preview,
  onCopy,
  showJson,
  onToggleJson
}: {
  preview: SalesAssistantProposalPreviewResponse;
  onCopy: (label: string, text: string) => void;
  showJson: boolean;
  onToggleJson: () => void;
}) {
  const body = preview.proposal_preview;
  const outlineText = body.slide_outline.map((slide) => `${slide.slide_no}. ${slide.title}\n- ${slide.bullets.join("\n- ")}`).join("\n\n");
  const summaryText = [body.deck_title, body.proposal_summary, body.proposal_policy].join("\n\n");
  return (
    <div className="sales-assistant-preview-body">
      <div className="sales-assistant-copy-grid">
        <button className="secondary-action" type="button" onClick={() => onCopy("Proposal概要", summaryText)}>
          <ClipboardCopy size={15} aria-hidden="true" />
          Proposal概要コピー
        </button>
        <button className="secondary-action" type="button" onClick={() => onCopy("スライド構成", outlineText)}>
          <ClipboardCopy size={15} aria-hidden="true" />
          スライド構成コピー
        </button>
        <button className="secondary-action" type="button" onClick={() => onCopy("Proposal全文", formatFullPreview(preview))}>
          <ClipboardCopy size={15} aria-hidden="true" />
          全文コピー
        </button>
      </div>
      <PreviewSection title="提案概要">
        <p>{body.proposal_summary}</p>
      </PreviewSection>
      <PreviewSection title="課題">
        <ul className="sales-assistant-list">
          {body.issues.map((item, index) => (
            <li key={`${item.issue}-${index}`}>
              <strong>{item.issue}</strong>
              <span>{item.proposed_response || item.background}</span>
            </li>
          ))}
        </ul>
      </PreviewSection>
      <PreviewSection title="提案ストーリー">
        <p>{body.proposal_story}</p>
      </PreviewSection>
      <PreviewSection title="主要スライド構成">
        <ol className="sales-assistant-slide-outline">
          {body.slide_outline.map((slide) => (
            <li key={slide.slide_no}>
              <strong>{slide.title}</strong>
              <span>{slide.bullets.join(" / ")}</span>
            </li>
          ))}
        </ol>
      </PreviewSection>
      <PreviewSection title="KPI">
        <ul className="sales-assistant-list">
          {body.kpis.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}
        </ul>
      </PreviewSection>
      <PreviewSection title="見積概要">
        <p>{body.estimate_summary}</p>
      </PreviewSection>
      <button className="secondary-action sales-assistant-json-button" type="button" onClick={onToggleJson}>
        <FileJson size={16} aria-hidden="true" />
        Proposal Preview JSONを{showJson ? "閉じる" : "開く"}
      </button>
      {showJson && <pre className="sales-assistant-json">{JSON.stringify(preview, null, 2)}</pre>}
    </div>
  );
}

function PreviewSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <article className="sales-assistant-section">
      <h3>{title}</h3>
      {children}
    </article>
  );
}

function formatFullPreview(preview: SalesAssistantProposalPreviewResponse) {
  const body = preview.proposal_preview;
  return [
    "# Proposal Preview",
    `## 提案概要\n${body.proposal_summary}`,
    `## 課題\n${body.issues.map((item) => `- ${item.issue}: ${item.proposed_response || item.background}`).join("\n")}`,
    `## 提案ストーリー\n${body.proposal_story}`,
    `## 主要スライド構成\n${body.slide_outline.map((slide) => `${slide.slide_no}. ${slide.title}`).join("\n")}`,
    `## KPI\n${body.kpis.map((item) => `- ${item}`).join("\n")}`,
    `## 見積概要\n${body.estimate_summary}`
  ].join("\n\n");
}
