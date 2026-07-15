"use client";

import { FormEvent, useMemo, useState } from "react";
import type { ManagedUser } from "@/lib/api";
import { getRoleLabel, type CreatableUserRole } from "@/lib/roles";

type UserUpdatePayload = Partial<{
  display_name: string;
  role: CreatableUserRole;
  password: string;
  password_change_required: boolean;
  is_active: boolean;
  pilot_enabled: boolean;
  pilot_completed: boolean;
  pilot_note: string;
}>;

type AdminUsersPanelProps = {
  users: ManagedUser[];
  onCreateUser: (payload: { email: string; password: string; role: CreatableUserRole; display_name?: string }) => Promise<void>;
  onDeleteUser: (userId: number) => Promise<void>;
  onToggleUser: (userId: number, isActive: boolean) => Promise<void>;
  onTogglePilot: (userId: number, pilotEnabled: boolean) => Promise<void>;
  onUpdateUser: (userId: number, payload: UserUpdatePayload) => Promise<void>;
};

const creatableRoles: Array<{ value: CreatableUserRole; label: string }> = [
  { value: "member", label: "一般利用者" },
  { value: "admin", label: "管理者" },
  { value: "viewer", label: "閲覧者" }
];

function formatDateTime(value?: string | null) {
  if (!value) return "未記録";
  return value.replace("T", " ").slice(0, 19);
}

export function AdminUsersPanel({
  users,
  onCreateUser,
  onDeleteUser,
  onToggleUser,
  onTogglePilot,
  onUpdateUser
}: AdminUsersPanelProps) {
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<CreatableUserRole>("member");
  const [message, setMessage] = useState("");
  const [busyUserId, setBusyUserId] = useState<number | null>(null);
  const [newPasswords, setNewPasswords] = useState<Record<number, string>>({});
  const [nameEdits, setNameEdits] = useState<Record<number, string>>({});
  const [roleEdits, setRoleEdits] = useState<Record<number, CreatableUserRole>>({});

  const activeAdminCount = useMemo(
    () => users.filter((user) => user.role === "admin" && Boolean(user.is_active) && !user.deleted_at).length,
    [users]
  );

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    await onCreateUser({ display_name: displayName, email, password, role });
    setDisplayName("");
    setEmail("");
    setPassword("");
    setRole("member");
    setMessage("ユーザーを追加しました。必要に応じてPilot対象へ切り替えてください。");
  }

  async function runForUser(userId: number, action: () => Promise<void>) {
    setBusyUserId(userId);
    setMessage("");
    try {
      await action();
      setMessage("ユーザー情報を更新しました。");
    } finally {
      setBusyUserId(null);
    }
  }

  return (
    <section className="admin-users-panel">
      <strong>ユーザー管理</strong>
      <p className="status-note">
        パスワードはハッシュ保存されます。既存パスワードは表示できません。最後の有効な管理者は無効化・削除できません。
      </p>
      <form className="admin-user-form" onSubmit={handleSubmit}>
        <input
          aria-label="氏名"
          value={displayName}
          onChange={(event) => setDisplayName(event.target.value)}
          placeholder="氏名"
          maxLength={160}
        />
        <input
          aria-label="メールアドレス"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="email@example.com"
          type="email"
          required
        />
        <input
          aria-label="仮パスワード"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="8文字以上の仮パスワード"
          type="password"
          required
          minLength={8}
        />
        <select aria-label="ロール" value={role} onChange={(event) => setRole(event.target.value as CreatableUserRole)}>
          {creatableRoles.map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
        </select>
        <button className="secondary-button" type="submit">追加</button>
      </form>
      {message && <p className="status-note success">{message}</p>}
      <div className="admin-user-list">
        {users.map((user) => {
          const editedName = nameEdits[user.id] ?? user.display_name ?? "";
          const editedRole = roleEdits[user.id] ?? (["admin", "member", "viewer"].includes(user.role) ? user.role : "member");
          const resetPassword = newPasswords[user.id] ?? "";
          const isLastAdmin = user.role === "admin" && Boolean(user.is_active) && activeAdminCount <= 1;
          const busy = busyUserId === user.id;
          return (
            <article key={user.id}>
              <div>
                <strong>{user.display_name || user.email}</strong>
                <span>{user.email}</span>
                <span>
                  {getRoleLabel(user.role)} / {user.is_active ? "有効" : "無効"} / {user.pilot_enabled ? "Pilot対象" : "Pilot対象外"}
                </span>
                <small>
                  Organization: {user.organization_name || user.current_organization_id || "-"} / Workspace: {user.workspace_name || user.current_workspace_id || "-"}
                </small>
                <small>最終ログイン: {formatDateTime(user.last_login_at || user.pilot_last_used_at)}</small>
                <small>作成: {formatDateTime(user.created_at)} / 更新: {formatDateTime(user.updated_at)}</small>
                {user.password_change_required && <small>次回ログイン後にパスワード変更が必要です</small>}
              </div>
              <div className="admin-user-actions">
                <input
                  aria-label={`${user.email} の氏名`}
                  value={editedName}
                  onChange={(event) => setNameEdits((current) => ({ ...current, [user.id]: event.target.value }))}
                  placeholder="氏名"
                />
                <select
                  aria-label={`${user.email} のロール`}
                  value={editedRole}
                  onChange={(event) => setRoleEdits((current) => ({ ...current, [user.id]: event.target.value as CreatableUserRole }))}
                >
                  {creatableRoles.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
                <button
                  className="secondary-button"
                  type="button"
                  disabled={busy || (isLastAdmin && editedRole !== "admin")}
                  onClick={() => void runForUser(user.id, () => onUpdateUser(user.id, { display_name: editedName, role: editedRole }))}
                >
                  基本情報を保存
                </button>
                <button className="secondary-button" type="button" disabled={busy} onClick={() => void onTogglePilot(user.id, !Boolean(user.pilot_enabled))}>
                  {user.pilot_enabled ? "Pilot対象外にする" : "Pilot対象にする"}
                </button>
                <button
                  className="secondary-button"
                  type="button"
                  disabled={busy || isLastAdmin}
                  onClick={() => void onToggleUser(user.id, !Boolean(user.is_active))}
                >
                  {user.is_active ? "無効化" : "有効化"}
                </button>
                <input
                  aria-label={`${user.email} の新しい仮パスワード`}
                  value={resetPassword}
                  onChange={(event) => setNewPasswords((current) => ({ ...current, [user.id]: event.target.value }))}
                  placeholder="新しい仮パスワード"
                  type="password"
                  minLength={8}
                />
                <button
                  className="secondary-button"
                  type="button"
                  disabled={busy || resetPassword.length < 8}
                  onClick={() =>
                    void runForUser(user.id, async () => {
                      await onUpdateUser(user.id, { password: resetPassword, password_change_required: true });
                      setNewPasswords((current) => ({ ...current, [user.id]: "" }));
                    })
                  }
                >
                  パスワード再設定
                </button>
                <button
                  className="secondary-button danger"
                  type="button"
                  disabled={busy || isLastAdmin}
                  onClick={() => void runForUser(user.id, () => onDeleteUser(user.id))}
                >
                  論理削除
                </button>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
