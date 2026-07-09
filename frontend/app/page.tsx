"use client";

import dynamic from "next/dynamic";

const AppShell = dynamic(() => import("@/components/AppShell"), {
  ssr: false,
  loading: () => (
    <main className="auth-shell">
      <div className="auth-card">
        <p className="eyebrow">Loading</p>
        <h1>Ready Crew Proposal AI</h1>
        <p>AI Digital Coworker を読み込んでいます。</p>
      </div>
    </main>
  )
});

export default function Page() {
  return <AppShell />;
}
