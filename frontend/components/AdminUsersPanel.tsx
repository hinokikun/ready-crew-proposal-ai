"use client";

import { FormEvent, useState } from "react";
import type { ManagedUser } from "@/lib/api";
import { getRoleLabel, type CreatableUserRole } from "@/lib/roles";

type AdminUsersPanelProps = {
  users: ManagedUser[];
  onCreateUser: (payload: { email: string; password: string; role: CreatableUserRole }) => Promise<void>;
  onToggleUser: (userId: number, isActive: boolean) => Promise<void>;
  onTogglePilot: (userId: number, pilotEnabled: boolean) => Promise<void>;
};

export function AdminUsersPanel({ users, onCreateUser, onToggleUser, onTogglePilot }: AdminUsersPanelProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<CreatableUserRole>("member");
  const [message, setMessage] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    await onCreateUser({ email, password, role });
    setEmail("");
    setPassword("");
    setRole("member");
    setMessage("ユーザーを追加しました。Pilot対象にする場合は一覧から切り替えてください。");
  }

  return (
    <section className="admin-users-panel">
      <strong>ユーザー管理（管理者のみ）</strong>
      <p className="status-note">
        新規作成では「管理者」「一般利用者」「閲覧者」を選択します。既存のmanagerなどの互換ロールは既存ユーザーとして維持します。
      </p>
      <form className="admin-user-form" onSubmit={handleSubmit}>
        <input aria-label="メールアドレス" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="email@example.com" type="email" required />
        <input
          aria-label="一時パスワード"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="8文字以上の一時パスワード"
          type="password"
          required
          minLength={8}
        />
        <select aria-label="ロール" value={role} onChange={(event) => setRole(event.target.value as CreatableUserRole)}>
          <option value="member">一般利用者</option>
          <option value="admin">管理者</option>
          <option value="viewer">閲覧者</option>
        </select>
        <button className="secondary-button" type="submit">追加</button>
      </form>
      {message && <p className="status-note success">{message}</p>}
      <div className="admin-user-list">
        {users.map((user) => (
          <article key={user.id}>
            <div>
              <strong>{user.email}</strong>
              <span>
                {getRoleLabel(user.role)} / {user.is_active ? "有効" : "無効"} / {user.pilot_enabled ? "Pilot対象" : "Pilot対象外"}
              </span>
              {user.role !== "admin" && user.role !== "member" && user.role !== "viewer" && (
                <small>互換ロール: {getRoleLabel(user.role)}</small>
              )}
              <small>最終利用: {user.pilot_last_used_at || "未利用"}</small>
              {user.pilot_completed && <small>試験利用完了済み</small>}
            </div>
            <div className="admin-user-actions">
              <button className="secondary-button" type="button" onClick={() => void onTogglePilot(user.id, !Boolean(user.pilot_enabled))}>
                {user.pilot_enabled ? "Pilot解除" : "Pilot対象にする"}
              </button>
              <button className="secondary-button" type="button" onClick={() => void onToggleUser(user.id, !Boolean(user.is_active))}>
                {user.is_active ? "無効化" : "有効化"}
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
