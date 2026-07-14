"use client";

import { memo } from "react";
import { Building2, RefreshCcw } from "lucide-react";
import type { WorkspaceContext } from "@/types/app";

type WorkspaceSwitcherProps = {
  context: WorkspaceContext | null;
  isLoading?: boolean;
  error?: string;
  onSwitch: (organizationId: number, workspaceId: number) => void;
  onRefresh: () => void;
};

function WorkspaceSwitcherBase({ context, isLoading = false, error = "", onSwitch, onRefresh }: WorkspaceSwitcherProps) {
  const current = context?.current;
  const available = context?.available ?? [];
  const selectedValue = current ? `${current.organization_id}:${current.workspace_id}` : "";

  return (
    <section className="workspace-context-card" aria-label="現在のOrganizationとWorkspace">
      <div className="workspace-context-title">
        <Building2 size={18} aria-hidden="true" />
        <div>
          <span>Organization</span>
          <strong>{current?.organization_name || "Ready Crew"}</strong>
        </div>
        <div>
          <span>Workspace</span>
          <strong>{current?.workspace_name || "営業部"}</strong>
        </div>
      </div>
      <div className="workspace-context-actions">
        <label>
          <span className="sr-only">Workspaceを切り替える</span>
          <select
            value={selectedValue}
            disabled={isLoading || available.length <= 1}
            onChange={(event) => {
              const [organizationId, workspaceId] = event.target.value.split(":").map((value) => Number(value));
              if (organizationId && workspaceId) {
                onSwitch(organizationId, workspaceId);
              }
            }}
          >
            {available.length === 0 && <option value="">現在のWorkspace</option>}
            {available.map((item) => (
              <option key={`${item.organization_id}:${item.workspace_id}`} value={`${item.organization_id}:${item.workspace_id}`}>
                {item.organization_name} / {item.workspace_name}
              </option>
            ))}
          </select>
        </label>
        <button className="secondary-button compact-button" type="button" onClick={onRefresh} disabled={isLoading}>
          <RefreshCcw size={15} aria-hidden="true" />
          更新
        </button>
      </div>
      {error && <p className="workspace-context-error">{error}</p>}
    </section>
  );
}

export const WorkspaceSwitcher = memo(WorkspaceSwitcherBase);
