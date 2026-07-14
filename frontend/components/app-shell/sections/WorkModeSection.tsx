"use client";

import { ExternalIntegrationsPanel } from "@/components/ExternalIntegrationsPanel";
import type { WorkMode } from "@/components/app-shell/types";
import type { UserRole } from "@/types/app";

type WorkModeTab = {
  key: WorkMode;
  label: string;
  note: string;
};

type WorkModeGroup = {
  category: string;
  modes: WorkMode[];
};

export type WorkModeSectionProps = {
  activeMode: WorkMode;
  canGenerate: boolean;
  canShowExternalIntakeCandidates: boolean;
  canSubmit: boolean;
  currentRole?: UserRole;
  recentFeatures: string[];
  setActiveMode: (mode: WorkMode) => void;
  setIsConfirmOpen: (isOpen: boolean) => void;
  workModeGroups: WorkModeGroup[];
  workModeMap: Map<WorkMode, WorkModeTab>;
};

export function WorkModeSection({
  activeMode,
  canGenerate,
  canShowExternalIntakeCandidates,
  canSubmit,
  currentRole,
  recentFeatures,
  setActiveMode,
  setIsConfirmOpen,
  workModeGroups,
  workModeMap
}: WorkModeSectionProps) {
  return (
    <details className="advanced-foldout ai-functions-menu" id="ai-functions-panel">
      <summary>他のAI機能を開く</summary>
      <section className="work-mode-panel" aria-label="業務モード切り替え">
        <div className="section-heading">
          <p className="eyebrow">バージョン 4.0</p>
          <h2>使う機能を選ぶ</h2>
          <p>まずは「提案作成」から始め、必要に応じて商談支援・社内業務へ切り替えます。</p>
        </div>
        <div className="work-mode-tabs" role="tablist" aria-label="業務モード">
          {workModeGroups.map((group) => (
            <div className="work-mode-group" key={group.category}>
              <span>{group.category}</span>
              <div>
                {group.modes.map((modeKey) => {
                  const mode = workModeMap.get(modeKey);
                  if (!mode) return null;
                  return (
                    <button
                      aria-selected={activeMode === mode.key}
                      className={activeMode === mode.key ? "is-active" : ""}
                      key={mode.key}
                      onClick={() => setActiveMode(mode.key)}
                      role="tab"
                      type="button"
                    >
                      <strong>{mode.label}</strong>
                      <small>{mode.note}</small>
                    </button>
                  );
                })}
                {group.category === "提案作成" && (
                  <>
                    <button
                      className="shortcut-mode-button"
                      onClick={() => {
                        setActiveMode("sales");
                        const panel = document.getElementById("company-research-panel") as HTMLDetailsElement | null;
                        if (panel) panel.open = true;
                        panel?.scrollIntoView({ behavior: "smooth" });
                      }}
                      type="button"
                    >
                      <strong>会社調査</strong>
                      <small>URLから調査観点を整理</small>
                    </button>
                    <button className="shortcut-mode-button" onClick={() => setIsConfirmOpen(true)} type="button" disabled={!canSubmit || !canGenerate}>
                      <strong>提案書作成</strong>
                      <small>原稿・PPT・PDFへ</small>
                    </button>
                  </>
                )}
                {group.category === "商談支援" && (
                  <button className="shortcut-mode-button" onClick={() => setActiveMode("coach")} type="button">
                    <strong>ロールプレイ</strong>
                    <small>お客様役と模擬商談</small>
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
        <div className="recent-feature-row">
          <strong>最近使った機能</strong>
          <span>{recentFeatures.length ? recentFeatures.join(" / ") : "まだ作成履歴はありません"}</span>
        </div>
        {canShowExternalIntakeCandidates && (
          <details className="advanced-foldout" id="external-intake-candidates-panel-detail">
            <summary>外部連携の案件候補を見る</summary>
            <ExternalIntegrationsPanel currentRole={currentRole} showSettings={false} />
          </details>
        )}
      </section>
    </details>
  );
}
