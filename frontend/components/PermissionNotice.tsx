"use client";

import { canViewOnly } from "@/lib/roles";

export function PermissionNotice({ role }: { role?: string }) {
  if (!canViewOnly(role)) return null;
  return (
    <section className="permission-notice" role="note">
      <strong>閲覧のみの一般利用者です</strong>
      <p>このアカウントでは履歴や状態確認のみ利用できます。提案書作成やPPT/PDF出力が必要な場合は、管理者へ権限変更を依頼してください。</p>
    </section>
  );
}
