"use client";

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

export function Dashboard({ dashboardMetrics, monthlyDashboardMetrics, operationDashboardMetrics }: DashboardProps) {
  return (
    <>
      <MetricGrid metrics={dashboardMetrics} label="営業ダッシュボード" />
      <MetricGrid metrics={monthlyDashboardMetrics} label="今月の営業ダッシュボード" className="monthly-dashboard" />
      <MetricGrid metrics={operationDashboardMetrics} label="社内業務AIダッシュボード" className="operations-dashboard" />
    </>
  );
}

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
