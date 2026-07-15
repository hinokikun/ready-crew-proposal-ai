import type { ReactNode } from "react";

type EmptyStateProps = {
  action?: ReactNode;
  description: string;
  title: string;
};

export function EmptyState({ action, description, title }: EmptyStateProps) {
  return (
    <div className="pp-empty-state">
      <strong>{title}</strong>
      <p>{description}</p>
      {action}
    </div>
  );
}
