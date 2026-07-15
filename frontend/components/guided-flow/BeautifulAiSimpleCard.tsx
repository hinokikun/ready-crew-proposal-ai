"use client";

import { memo } from "react";
import { CheckCircle2, Loader2, Sparkles } from "lucide-react";
import type { BeautifulAiSimpleRequirement } from "@/components/guided-flow/types";

type BeautifulAiSimpleCardProps = {
  canCreate: boolean;
  disabledReason: string;
  isCreating: boolean;
  onCreate: () => void;
  requirements: BeautifulAiSimpleRequirement[];
  resultLinks?: {
    editorUrl?: string;
    playerUrl?: string;
    onOpen: (url: string) => void;
  };
};

function BeautifulAiSimpleCardBase({
  canCreate,
  disabledReason,
  isCreating,
  onCreate,
  requirements,
  resultLinks
}: BeautifulAiSimpleCardProps) {
  const remaining = requirements.filter((item) => !item.passed);

  return (
    <article className={`guided-output-option guided-beautiful-card ${canCreate ? "is-ready" : "is-blocked"}`}>
      <div>
        <span className="guided-option-label">Beautiful.ai</span>
        <h3>{canCreate ? "Beautiful.aiでプレゼンを作成できます" : "Beautiful.aiを利用するには確認が必要です"}</h3>
        <p>スライドの構成をBeautiful.aiへ送り、デザインされた営業提案プレゼンを作成します。</p>
      </div>

      {!canCreate && (
        <ul className="guided-requirement-list" aria-label="Beautiful.aiの利用条件">
          {requirements.map((item) => (
            <li className={item.passed ? "is-passed" : "is-missing"} key={item.label}>
              <CheckCircle2 size={15} aria-hidden="true" />
              <span>{item.label}</span>
            </li>
          ))}
        </ul>
      )}

      {!canCreate && <p className="guided-disabled-reason">{disabledReason || `あと${remaining.length}項目の確認が必要です`}</p>}

      <button
        className="primary-button"
        data-testid="beautiful-ai-create-button"
        disabled={!canCreate || isCreating}
        onClick={onCreate}
        type="button"
      >
        {isCreating ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <Sparkles size={18} aria-hidden="true" />}
        {isCreating ? "Beautiful.aiで作成中" : "Beautiful.aiで提案書を作成"}
      </button>

      {resultLinks && (resultLinks.editorUrl || resultLinks.playerUrl) && (
        <div className="guided-beautiful-links" aria-live="polite">
          <strong>Beautiful.ai提案書を作成しました</strong>
          <div>
            {resultLinks.editorUrl && (
              <button className="text-button" onClick={() => resultLinks.onOpen(resultLinks.editorUrl || "")} type="button">
                Beautiful.aiで編集
              </button>
            )}
            {resultLinks.playerUrl && (
              <button className="text-button" onClick={() => resultLinks.onOpen(resultLinks.playerUrl || "")} type="button">
                プレゼンテーションを表示
              </button>
            )}
          </div>
        </div>
      )}
    </article>
  );
}

export const BeautifulAiSimpleCard = memo(BeautifulAiSimpleCardBase);
