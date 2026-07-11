"use client";

import { memo } from "react";
import type { ExecutiveMetric } from "./types";

type ExecutiveCardsProps = {
  metrics: ExecutiveMetric[];
};

export const ExecutiveCards = memo(function ExecutiveCards({ metrics }: ExecutiveCardsProps) {
  return (
    <section className="operations-executive-cards" aria-label="主要指標">
      {metrics.map((metric) => (
        <article className={`operations-card tone-${metric.tone ?? "normal"}`} key={metric.label}>
          <span>{metric.label}</span>
          <strong>{metric.value}</strong>
          <small>{metric.note}</small>
        </article>
      ))}
    </section>
  );
});
