"use client";

import { useEffect, useState } from "react";
import { Activity, AlertCircle, CheckCircle2 } from "lucide-react";
import { API_BASE_URL } from "@/lib/config";

type HealthResponse = {
  status?: string;
  auth_configured?: boolean;
  mock_ai?: boolean;
  ai_api?: string;
  pptx?: string;
  pdf?: string;
};

export type HealthSnapshot = {
  backendOk: boolean;
  aiStatus: string;
  mockMode: boolean | null;
  authConfigured: boolean | null;
  checkedAt: string;
};

type HealthStatusProps = {
  onChange?: (snapshot: HealthSnapshot) => void;
};

export function HealthStatus({ onChange }: HealthStatusProps) {
  const [health, setHealth] = useState<HealthSnapshot>({
    backendOk: false,
    aiStatus: "確認中",
    mockMode: null,
    authConfigured: null,
    checkedAt: ""
  });

  async function checkHealth() {
    const checkedAt = new Date().toLocaleString("ja-JP");
    try {
      const response = await fetch(`${API_BASE_URL}/health`, { cache: "no-store" });
      if (!response.ok) throw new Error("health failed");
      const body = (await response.json()) as HealthResponse;
      const snapshot: HealthSnapshot = {
        backendOk: body.status === "ok",
        aiStatus: body.ai_api === "missing" ? "要確認" : "利用可能",
        mockMode: Boolean(body.mock_ai),
        authConfigured: Boolean(body.auth_configured),
        checkedAt
      };
      setHealth(snapshot);
      onChange?.(snapshot);
    } catch {
      const snapshot: HealthSnapshot = {
        backendOk: false,
        aiStatus: "要確認",
        mockMode: null,
        authConfigured: null,
        checkedAt
      };
      setHealth(snapshot);
      onChange?.(snapshot);
    }
  }

  useEffect(() => {
    void checkHealth();
  }, []);

  return (
    <section className="health-panel" aria-label="接続状態">
      <div className="health-heading">
        <div>
          <p className="eyebrow">Health</p>
          <h2>接続状態</h2>
        </div>
        <button className="secondary-button" type="button" onClick={() => void checkHealth()}>
          <Activity size={16} aria-hidden="true" />
          再確認
        </button>
      </div>
      <div className="health-grid">
        <StatusItem label="Backend接続" ok={health.backendOk} value={health.backendOk ? "正常" : "異常"} />
        <StatusItem label="AI API" ok={health.aiStatus === "利用可能"} value={health.aiStatus} />
        <StatusItem label="PPTX生成" ok={health.backendOk} value={health.backendOk ? "利用可能" : "要確認"} />
        <StatusItem label="PDF生成" ok={health.backendOk} value={health.backendOk ? "利用可能" : "要確認"} />
      </div>
    </section>
  );
}

function StatusItem({ label, ok, value }: { label: string; ok: boolean; value: string }) {
  return (
    <article className={ok ? "is-ok" : "is-alert"}>
      {ok ? <CheckCircle2 size={18} aria-hidden="true" /> : <AlertCircle size={18} aria-hidden="true" />}
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}
