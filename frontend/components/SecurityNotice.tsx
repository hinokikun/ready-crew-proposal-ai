"use client";

import { ShieldAlert } from "lucide-react";

export function SecurityNotice() {
  return (
    <section className="security-notice-panel" aria-label="社内利用向け注意">
      <ShieldAlert size={20} aria-hidden="true" />
      <div>
        <strong>社内試験利用の注意</strong>
        <p>
          顧客の機密情報、個人情報、パスワードは入力しない / 提案書や見積はAI生成のため提出前に必ず人が確認する /
          外部送信、削除、公開作業はAIに任せない / 社外共有前に上長または担当者が確認する。
        </p>
      </div>
    </section>
  );
}
