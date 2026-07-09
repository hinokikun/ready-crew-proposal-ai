"use client";

import dynamic from "next/dynamic";

const AppShell = dynamic(() => import("@/components/AppShell"), {
  ssr: false,
  loading: () => (
    <main className="auth-shell">
      <div className="auth-card">
        <p className="eyebrow">Loading</p>
        <h1>AI営業秘書</h1>
        <p>AI Digital Coworker を読み込んでいます。</p>
      </div>
    </main>
  )
});

export default function Page() {
  return <AppShell />;
}
