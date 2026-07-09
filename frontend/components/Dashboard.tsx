"use client";

import { memo } from "react";

type DashboardMetric = {
  label: string;
  value: string;
  note: string;
};

type DashboardProps = {
  dashboardMetrics: DashboardMetric[];
  monthlyDashboardMetrics: DashboardMetric[];
  operationDashboardMetrics: DashboardMetric[];
};

function DashboardBase({ dashboardMetrics, monthlyDashboardMetrics, operationDashboardMetrics }: DashboardProps) {
  const primaryMetrics = dashboardMetrics.slice(0, 3);
  const detailMetrics = [...dashboardMetrics.slice(3), ...monthlyDashboardMetrics, ...operationDashboardMetrics];

  return (
    <section className="compact-dashboard" aria-label="ダッシュボード">
      <MetricGrid metrics={primaryMetrics} label="今日使うダッシュボード" />
      <details className="dashboard-details">
        <summary>詳細を見る</summary>
        <MetricGrid metrics={detailMetrics} label="詳細ダッシュボード" className="dashboard-detail-grid" />
      </details>
    </section>
  );
}

export const Dashboard = memo(DashboardBase);

function MetricGrid({ metrics, label, className = "" }: { metrics: DashboardMetric[]; label: string; className?: string }) {
  return (
    <section className={`dashboard-grid ${className}`.trim()} aria-label={label}>
      {metrics.map((metric) => (
        <article className="dashboard-card" key={metric.label}>
          <span>{metric.label}</span>
          <strong>{metric.value}</strong>
          <small>{metric.note}</small>
        </article>
      ))}
    </section>
  );
}
