"use client";

import { Loader2, Sparkles } from "lucide-react";
import type {
  AiEmployeeRole,
  AutomationSettings,
  CompanyResearch,
  DigitalAgentStep
} from "@/components/app-shell/types";

type AiEmployeeOption = {
  key: AiEmployeeRole;
  label: string;
  mission: string;
};

type AiEmployeeGuidance = {
  title: string;
  items: string[];
};

type AiCoworkerReview = {
  reviewer: string;
  comment: string;
  improvement: string;
};

export type DigitalCoworkerSectionProps = {
  agentSteps: DigitalAgentStep[];
  aiCoworkerReviews: AiCoworkerReview[];
  aiEmployeeGuidance: AiEmployeeGuidance;
  aiEmployeeRoles: AiEmployeeOption[];
  automationSettings: AutomationSettings;
  companyHomeUrl: string;
  companyResearch: CompanyResearch | null;
  isAgentRunning: boolean;
  mcpConnectorCards: string[];
  runCompanyResearch: () => void;
  runDigitalCoworkerAgent: () => void;
  selectedAiEmployee: AiEmployeeRole;
  setCompanyHomeUrl: (url: string) => void;
  setSelectedAiEmployee: (role: AiEmployeeRole) => void;
  toggleAutomation: (key: keyof AutomationSettings) => void;
};

export function DigitalCoworkerSection({
  agentSteps,
  aiCoworkerReviews,
  aiEmployeeGuidance,
  aiEmployeeRoles,
  automationSettings,
  companyHomeUrl,
  companyResearch,
  isAgentRunning,
  mcpConnectorCards,
  runCompanyResearch,
  runDigitalCoworkerAgent,
  selectedAiEmployee,
  setCompanyHomeUrl,
  setSelectedAiEmployee,
  toggleAutomation
}: DigitalCoworkerSectionProps) {
  return (
    <details className="digital-coworker-panel advanced-foldout" id="company-research-panel" aria-label="AI社員">
      <summary>会社調査・AI社員機能を開く</summary>
      <div className="digital-coworker-hero">
        <div>
          <p className="eyebrow">AI社員</p>
          <h2>案件を受けたら、AI社員が順番に進めます</h2>
          <p>会社調査、競合調査、提案書作成、見積、メール準備までを、進行状況つきで整理します。</p>
        </div>
        <button className="primary-button" type="button" onClick={runDigitalCoworkerAgent} disabled={isAgentRunning}>
          {isAgentRunning ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <Sparkles size={18} aria-hidden="true" />}
          {isAgentRunning ? "AI社員が実行中" : "AI社員に一括実行"}
        </button>
      </div>

      <div className="digital-grid">
        <article className="digital-card browser-use-card">
          <div className="card-title-row">
            <div>
              <span>Browser Use連携</span>
              <strong>会社URLから調査観点を作成</strong>
            </div>
            <button className="secondary-button" type="button" onClick={runCompanyResearch}>
              会社調査を実行
            </button>
          </div>
          <label className="field">
            <span>会社URL</span>
            <input
              value={companyHomeUrl}
              onChange={(event) => setCompanyHomeUrl(event.target.value)}
              placeholder="https://example.co.jp"
            />
          </label>
          {companyResearch ? (
            <div className="research-result-grid">
              <div><span>会社概要</span><p>{companyResearch.overview}</p></div>
              <div><span>競合</span><ul>{companyResearch.competitors.map((item) => <li key={item}>{item}</li>)}</ul></div>
              <div><span>採用</span><p>{companyResearch.recruitment}</p></div>
              <div><span>ニュース</span><ul>{companyResearch.news.map((item) => <li key={item}>{item}</li>)}</ul></div>
              <div><span>サービス</span><ul>{companyResearch.services.map((item) => <li key={item}>{item}</li>)}</ul></div>
              <div><span>SNS</span><ul>{companyResearch.sns.map((item) => <li key={item}>{item}</li>)}</ul></div>
            </div>
          ) : (
            <p className="helper-text">現時点では自動送信やログイン操作は行いません。公開情報を確認する観点をAIが整理します。</p>
          )}
        </article>

        <article className="digital-card">
          <div className="card-title-row">
            <div>
              <span>AIエージェント進行状況</span>
              <strong>順番に業務を実行</strong>
            </div>
          </div>
          <div className="agent-step-list">
            {agentSteps.map((step, index) => (
              <div className={`agent-step is-${step.status}`} key={step.label}>
                <span>{index + 1}</span>
                <div>
                  <strong>{step.label}</strong>
                  <p>{step.detail}</p>
                </div>
                <small>{step.status === "done" ? "完了" : step.status === "running" ? "実行中" : "待機"}</small>
              </div>
            ))}
          </div>
        </article>
      </div>

      <details className="advanced-foldout digital-advanced-foldout">
        <summary>高度なAI社員機能を開く</summary>
        <div className="digital-grid digital-grid-wide">
          <article className="digital-card ai-employee-card">
            <div className="card-title-row">
              <div>
                <span>AI社員</span>
                <strong>役割を選ぶと提案の見方が変わります</strong>
              </div>
            </div>
            <div className="ai-employee-grid">
              {aiEmployeeRoles.map((role) => (
                <button
                  className={selectedAiEmployee === role.key ? "is-active" : ""}
                  key={role.key}
                  onClick={() => setSelectedAiEmployee(role.key)}
                  type="button"
                >
                  <strong>{role.label}</strong>
                  <span>{role.mission}</span>
                </button>
              ))}
            </div>
            <div className="role-guidance-box">
              <strong>{aiEmployeeGuidance.title}</strong>
              <ul>{aiEmployeeGuidance.items.map((item) => <li key={item}>{item}</li>)}</ul>
            </div>
          </article>

          <article className="digital-card automation-card">
            <div className="card-title-row">
              <div>
                <span>自動確認</span>
                <strong>定期確認の設定UI</strong>
              </div>
            </div>
            <div className="automation-list">
              {[
                { key: "morning" as const, label: "毎朝確認", note: "Ready Crew案件と優先度を毎朝整理" },
                { key: "weekly" as const, label: "毎週確認", note: "提案中案件、未対応タスク、失注リスクを確認" },
                { key: "deadline" as const, label: "締切前通知", note: "公開希望日・提案期限前に確認事項を通知" }
              ].map((item) => (
                <button className={automationSettings[item.key] ? "is-active" : ""} key={item.key} onClick={() => toggleAutomation(item.key)} type="button">
                  <span>{automationSettings[item.key] ? "ON" : "OFF"}</span>
                  <div>
                    <strong>{item.label}</strong>
                    <p>{item.note}</p>
                  </div>
                </button>
              ))}
            </div>
          </article>
        </div>

        <div className="digital-grid digital-grid-wide">
          <article className="digital-card mcp-settings-card">
            <div className="card-title-row">
              <div>
                <span>MCP対応UI</span>
                <strong>将来接続する社内・営業ツール</strong>
              </div>
            </div>
            <div className="mcp-card-grid">
              {mcpConnectorCards.map((connector, index) => (
                <article key={connector}>
                  <strong>{connector}</strong>
                  <span>{index < 3 ? "未接続" : "接続予定"}</span>
                </article>
              ))}
            </div>
          </article>

          <article className="digital-card review-chain-card">
            <div className="card-title-row">
              <div>
                <span>AIレビュー</span>
                <strong>AI社員同士で作成物を改善</strong>
              </div>
            </div>
            <div className="review-chain">
              {aiCoworkerReviews.map((review, index) => (
                <div key={review.reviewer}>
                  <span>{index + 1}</span>
                  <div>
                    <strong>{review.reviewer}</strong>
                    <p>{review.comment}</p>
                    <small>{review.improvement}</small>
                  </div>
                </div>
              ))}
            </div>
          </article>
        </div>
      </details>
    </details>
  );
}
