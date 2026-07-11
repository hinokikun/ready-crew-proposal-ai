"use client";

import { memo } from "react";
import type { PromptVersion } from "@/types/app";
import { groupPromptVersions, promptStatusLabel, sortPromptVersions } from "@/components/prompts/PromptVersionManager";

type PromptHistoryProps = {
  versions: PromptVersion[];
  updatingId: number | null;
  onSetStatus: (versionId: number, status: "draft" | "testing" | "active" | "archived") => void;
  onRollback: (promptName: string, version: string) => void;
};

export const PromptHistory = memo(function PromptHistory({ versions, updatingId, onSetStatus, onRollback }: PromptHistoryProps) {
  const groups = groupPromptVersions(sortPromptVersions(versions));
  const promptNames = Object.keys(groups);
  if (!promptNames.length) {
    return <p className="learning-empty">Prompt Versionはまだ登録されていません。</p>;
  }

  return (
    <div className="prompt-history-list">
      {promptNames.map((promptName) => (
        <article className="prompt-history-card" key={promptName}>
          <div className="prompt-history-card__header">
            <div>
              <span>Prompt</span>
              <strong>{promptName}</strong>
            </div>
            <small>{groups[promptName].length} versions</small>
          </div>
          <div className="table-scroll">
            <table className="usage-dashboard-table compact-table">
              <thead>
                <tr>
                  <th>Version</th>
                  <th>AI社員</th>
                  <th>状態</th>
                  <th>説明</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {groups[promptName].map((version) => (
                  <tr key={version.id}>
                    <td>{version.version}</td>
                    <td>{version.target_agent || "-"}</td>
                    <td><span className={`status-pill ${version.status}`}>{promptStatusLabel(version.status)}</span></td>
                    <td>{version.description || "-"}</td>
                    <td>
                      <div className="inline-action-row">
                        <button
                          className="secondary-button compact-action"
                          type="button"
                          onClick={() => onSetStatus(version.id, "active")}
                          disabled={updatingId === version.id || version.status === "active"}
                        >
                          有効化
                        </button>
                        <button
                          className="secondary-button compact-action"
                          type="button"
                          onClick={() => onRollback(version.prompt_name, version.version)}
                          disabled={updatingId === version.id}
                        >
                          戻す
                        </button>
                        <button
                          className="secondary-button compact-action"
                          type="button"
                          onClick={() => onSetStatus(version.id, "archived")}
                          disabled={updatingId === version.id || version.status === "archived"}
                        >
                          保管
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>
      ))}
    </div>
  );
});
