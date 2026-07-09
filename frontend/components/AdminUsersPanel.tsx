"use client";

import { FormEvent, useState } from "react";
import type { ManagedUser } from "@/lib/api";

type AdminUsersPanelProps = {
  users: ManagedUser[];
  onCreateUser: (payload: { email: string; password: string; role: "admin" | "member" | "viewer" }) => Promise<void>;
  onToggleUser: (userId: number, isActive: boolean) => Promise<void>;
};

export function AdminUsersPanel({ users, onCreateUser, onToggleUser }: AdminUsersPanelProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"admin" | "member" | "viewer">("member");
  const [message, setMessage] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    await onCreateUser({ email, password, role });
    setEmail("");
    setPassword("");
    setRole("member");
    setMessage("ユーザーを追加しました。");
  }

  return (
    <section className="admin-users-panel">
      <strong>ユーザー管理（adminのみ）</strong>
      <form className="admin-user-form" onSubmit={handleSubmit}>
        <input value={email} onChange={(event) => setEmail(event.target.value)} placeholder="email@example.com" type="email" required />
        <input value={password} onChange={(event) => setPassword(event.target.value)} placeholder="8文字以上のパスワード" type="password" required minLength={8} />
        <select value={role} onChange={(event) => setRole(event.target.value as "admin" | "member" | "viewer")}>
          <option value="member">member</option>
          <option value="viewer">viewer</option>
          <option value="admin">admin</option>
        </select>
        <button className="secondary-button" type="submit">追加</button>
      </form>
      {message && <p>{message}</p>}
      <div className="admin-user-list">
        {users.map((user) => (
          <article key={user.id}>
            <div>
              <strong>{user.email}</strong>
              <span>{user.role} / {user.is_active ? "有効" : "無効"}</span>
            </div>
            <button className="secondary-button" type="button" onClick={() => void onToggleUser(user.id, !Boolean(user.is_active))}>
              {user.is_active ? "無効化" : "有効化"}
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}
