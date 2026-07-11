"use client";

import { memo, useEffect, useMemo, useState } from "react";
import {
  createReleaseRecord,
  getReleases,
  publishReleaseRecord,
  updateReleaseRecord,
  type ReleaseRecordPayload
} from "@/lib/api";
import { toFriendlyError } from "@/lib/errorMessage";
import type { ReleaseRecord, ReleaseRecordStatus } from "@/types/app";

const ROLLOUT_CHECKLIST = [
  "GitHub Actions成功",
  "Vercel Build成功",
  "Render /health 正常",
  "ログイン確認",
  "admin/member/viewer権限確認",
  "提案書作成確認",
  "要約PPT確認",
  "詳細PPT確認",
  "見積PDF確認",
  "品質ゲート確認",
  "上司レビュー確認",
  "監査ログ確認",
  "フィードバック送信確認"
];

const STATUS_LABELS: Record<string, string> = {
  draft: "下書き",
  internal_test: "社内テスト",
  released: "社内公開",
  archived: "アーカイブ"
};

const DEFAULT_ROLLBACK = [
  "GitHubで前回コミットを確認",
  "Vercelで過去DeploymentをPromote",
  "Renderで前回Deployを確認",
  "環境変数を変更した場合は戻す"
].join("\n");

export const AdminReleaseManagementPanel = memo(function AdminReleaseManagementPanel() {
  const [releases, setReleases] = useState<ReleaseRecord[]>([]);
  const [statusMessage, setStatusMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [version, setVersion] = useState("9.5");
  const [releaseDate, setReleaseDate] = useState(new Date().toISOString().slice(0, 10));
  const [releaseStatus, setReleaseStatus] = useState<ReleaseRecordStatus>("internal_test");
  const [summary, setSummary] = useState("Release Management & Internal Rollout");
  const [changes, setChanges] = useState("リリース管理、社内展開チェックリスト、公開承認、ロールバックメモを追加");
  const [impactScope, setImpactScope] = useState("管理者・上司による正式運用前の確認と社内公開フロー");
  const [knownIssues, setKnownIssues] = useState("自動ロールバックは未実装。Vercel/Renderの手動切り戻し手順で対応。");
  const [rollbackNote, setRollbackNote] = useState(DEFAULT_ROLLBACK);
  const [checkedItems, setCheckedItems] = useState<Record<string, boolean>>({});
  const [publishComments, setPublishComments] = useState<Record<number, string>>({});

  const selectedChecklist = useMemo(
    () => ROLLOUT_CHECKLIST.filter((item) => checkedItems[item]),
    [checkedItems]
  );

  async function loadReleases() {
    setIsLoading(true);
    setStatusMessage("");
    try {
      const response = await getReleases(50);
      setReleases(response.releases);
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setStatusMessage(`${friendly.title} ${friendly.action}`);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadReleases();
  }, []);

  function toggleChecklist(item: string) {
    setCheckedItems((current) => ({ ...current, [item]: !current[item] }));
  }

  async function createRelease() {
    if (!version.trim()) {
      setStatusMessage("バージョンを入力してください。");
      return;
    }
    const payload: ReleaseRecordPayload = {
      version,
      release_date: releaseDate,
      status: releaseStatus,
      summary,
      changes,
      impact_scope: impactScope,
      checklist: selectedChecklist,
      known_issues: knownIssues,
      rollback_note: rollbackNote
    };
    try {
      await createReleaseRecord(payload);
      setStatusMessage("リリース記録を保存しました。");
      await loadReleases();
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setStatusMessage(`${friendly.title} ${friendly.action}`);
    }
  }

  async function publishRelease(release: ReleaseRecord) {
    try {
      await publishReleaseRecord(release.id, publishComments[release.id] || "社内公開を承認");
      setStatusMessage(`v${release.version} を社内公開しました。`);
      await loadReleases();
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setStatusMessage(`${friendly.title} ${friendly.action}`);
    }
  }

  async function archiveRelease(release: ReleaseRecord) {
    try {
      await updateReleaseRecord(release.id, { status: "archived" });
      setStatusMessage(`v${release.version} をアーカイブしました。`);
      await loadReleases();
    } catch (caught) {
      const friendly = toFriendlyError(caught);
      setStatusMessage(`${friendly.title} ${friendly.action}`);
    }
  }

  return (
    <section className="release-management-panel">
      <div className="section-heading-row">
        <div>
          <p className="eyebrow">Version 9.5</p>
          <h3>リリース管理</h3>
          <p className="helper-text">社内公開前の確認、公開承認、変更履歴、ロールバックメモを管理します。</p>
        </div>
        <button className="secondary-button" type="button" onClick={() => void loadReleases()} disabled={isLoading}>
          {isLoading ? "読み込み中" : "再読み込み"}
        </button>
      </div>

      {statusMessage ? <p className="status-note">{statusMessage}</p> : null}

      <div className="release-note-form release-management-form">
        <label className="field">
          <span>バージョン</span>
          <input value={version} onChange={(event) => setVersion(event.target.value)} placeholder="9.5" />
        </label>
        <label className="field">
          <span>リリース日</span>
          <input type="date" value={releaseDate} onChange={(event) => setReleaseDate(event.target.value)} />
        </label>
        <label className="field">
          <span>公開状態</span>
          <select value={releaseStatus} onChange={(event) => setReleaseStatus(event.target.value as ReleaseRecordStatus)}>
            <option value="draft">下書き</option>
            <option value="internal_test">社内テスト</option>
            <option value="released">社内公開</option>
            <option value="archived">アーカイブ</option>
          </select>
        </label>
        <label className="field">
          <span>変更内容</span>
          <textarea rows={3} value={changes} onChange={(event) => setChanges(event.target.value)} />
        </label>
        <label className="field">
          <span>影響範囲</span>
          <textarea rows={2} value={impactScope} onChange={(event) => setImpactScope(event.target.value)} />
        </label>
        <label className="field">
          <span>既知の注意点</span>
          <textarea rows={2} value={knownIssues} onChange={(event) => setKnownIssues(event.target.value)} />
        </label>
        <label className="field release-field-wide">
          <span>要約</span>
          <textarea rows={2} value={summary} onChange={(event) => setSummary(event.target.value)} />
        </label>
        <label className="field release-field-wide">
          <span>ロールバック方法</span>
          <textarea rows={4} value={rollbackNote} onChange={(event) => setRollbackNote(event.target.value)} />
        </label>
      </div>

      <div className="release-checklist-panel">
        <strong>社内展開チェックリスト</strong>
        <div className="release-checklist-grid">
          {ROLLOUT_CHECKLIST.map((item) => (
            <label key={item} className={checkedItems[item] ? "is-checked" : ""}>
              <input checked={Boolean(checkedItems[item])} onChange={() => toggleChecklist(item)} type="checkbox" />
              <span>{item}</span>
            </label>
          ))}
        </div>
      </div>

      <button className="primary-button" type="button" onClick={() => void createRelease()}>
        リリース記録を保存
      </button>

      <div className="release-record-list">
        {releases.map((release) => (
          <article key={release.id} className={`release-record-card is-${release.status}`}>
            <div>
              <span>{STATUS_LABELS[release.status] ?? release.status}</span>
              <strong>v{release.version} / {release.release_date || "日付未設定"}</strong>
              <p>{release.summary || release.changes}</p>
              <small>公開者: {release.released_by_email || "未公開"} / 公開日時: {release.released_at || "-"}</small>
            </div>
            <details>
              <summary>詳細を見る</summary>
              <dl>
                <div><dt>変更内容</dt><dd>{release.changes || "-"}</dd></div>
                <div><dt>影響範囲</dt><dd>{release.impact_scope || "-"}</dd></div>
                <div><dt>既知の注意点</dt><dd>{release.known_issues || "-"}</dd></div>
                <div><dt>チェック</dt><dd>{release.checklist.join("、") || "-"}</dd></div>
                <div><dt>ロールバック</dt><dd>{release.rollback_note || "-"}</dd></div>
              </dl>
            </details>
            <div className="release-actions">
              <input
                value={publishComments[release.id] || ""}
                onChange={(event) => setPublishComments((current) => ({ ...current, [release.id]: event.target.value }))}
                placeholder="公開コメント"
              />
              <button className="primary-button" type="button" onClick={() => void publishRelease(release)} disabled={release.status === "released"}>
                社内公開
              </button>
              <button className="secondary-button" type="button" onClick={() => void archiveRelease(release)} disabled={release.status === "archived"}>
                アーカイブ
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
});
