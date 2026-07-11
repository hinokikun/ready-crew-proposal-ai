"use client";

import { memo } from "react";
import type { KpiMetric } from "./types";

type KpiCardsProps = {
  metrics: KpiMetric[];
};

export const KpiCards = memo(function KpiCards({ metrics }: KpiCardsProps) {
  return (
    <section className="operations-kpi-panel" aria-label="KPI">
      <div className="operations-section-heading">
        <div>
          <p className="eyebrow">KPI Dashboard</p>
          <h2>運用KPI</h2>
        </div>
      </div>
      <div className="operations-kpi-grid">
        {metrics.map((metric) => (
          <article key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
            <small>{metric.note}</small>
          </article>
        ))}
      </div>
    </section>
  );
});
