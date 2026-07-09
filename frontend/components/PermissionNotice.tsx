"use client";

export function PermissionNotice({ role }: { role?: string }) {
  if (role !== "viewer") return null;
  return (
    <section className="permission-notice" role="note">
      <strong>閲覧のみ権限です</strong>
      <p>viewerはDashboardと履歴の閲覧のみ利用できます。提案書生成、PPTX/PDF出力はadminまたはmemberでログインしてください。</p>
    </section>
  );
}
