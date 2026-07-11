"use client";

import { memo, useEffect, useState } from "react";
import { getReleases } from "@/lib/api";
import type { ReleaseRecord } from "@/types/app";

export const ReleaseUpdatesPanel = memo(function ReleaseUpdatesPanel() {
  const [releases, setReleases] = useState<ReleaseRecord[]>([]);

  useEffect(() => {
    let active = true;
    getReleases(5)
      .then((response) => {
        if (active) {
          setReleases(response.releases.filter((release) => release.status === "released").slice(0, 3));
        }
      })
      .catch(() => {
        if (active) setReleases([]);
      });
    return () => {
      active = false;
    };
  }, []);

  if (releases.length === 0) {
    return null;
  }

  return (
    <details className="release-updates-panel">
      <summary>今回の変更点を見る</summary>
      <div className="release-update-list">
        {releases.map((release) => (
          <article key={release.id}>
            <span>v{release.version} / {release.release_date}</span>
            <strong>{release.summary || "社内向けアップデート"}</strong>
            <p>{release.changes}</p>
            {release.known_issues && <small>注意点: {release.known_issues}</small>}
          </article>
        ))}
      </div>
    </details>
  );
});
