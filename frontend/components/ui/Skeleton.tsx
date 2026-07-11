"use client";

import { memo } from "react";

type SkeletonProps = {
  lines?: number;
  title?: boolean;
};

function SkeletonBase({ lines = 3, title = false }: SkeletonProps) {
  return (
    <div className="skeleton-block" aria-hidden="true">
      {title && <span className="skeleton-line skeleton-title" />}
      {Array.from({ length: lines }).map((_, index) => (
        <span className="skeleton-line" key={index} />
      ))}
    </div>
  );
}

export const Skeleton = memo(SkeletonBase);

export function AppLoadingSkeleton() {
  return (
    <main className="auth-shell">
      <section className="auth-card app-loading-card" aria-label="読み込み中">
        <p className="eyebrow">読み込み中</p>
        <h1>AI Workspace</h1>
        <Skeleton title lines={4} />
      </section>
    </main>
  );
}
