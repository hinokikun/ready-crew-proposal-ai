type StatusBadgeProps = {
  children: string;
  tone?: "neutral" | "info" | "success" | "warning" | "danger";
};

export function StatusBadge({ children, tone = "neutral" }: StatusBadgeProps) {
  return <span className={`pp-status-badge pp-status-${tone}`}>{children}</span>;
}
