"use client";

import dynamic from "next/dynamic";

const AppShell = dynamic(() => import("@/components/AppShell"), {
  ssr: false,
  loading: () => (
    <main className="auth-shell">
      <div className="auth-card">
        <p className="eyebrow">読み込み中</p>
        <h1>AI Workspace</h1>
        <p>AI社員の作業画面を読み込んでいます。</p>
      </div>
    </main>
  )
});

export default function Page() {
  return <AppShell />;
}
