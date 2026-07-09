"use client";

import type { CrmCustomer, CrmProject } from "@/lib/api";

type CrmPanelProps = {
  customers: CrmCustomer[];
  projects: CrmProject[];
};

export function CrmPanel({ customers, projects }: CrmPanelProps) {
  return (
    <section className="crm-panel" aria-label="簡易CRM">
      <div className="section-heading">
        <p className="eyebrow">CRM</p>
        <h2>顧客・案件管理</h2>
        <p>DBに保存された顧客、案件、作成履歴の概要を確認します。本文全文や機密情報は保存しません。</p>
      </div>
      <div className="crm-grid">
        <article>
          <strong>顧客一覧</strong>
          <div className="crm-list">
            {customers.length ? customers.map((customer) => (
              <div key={customer.id}>
                <span>{customer.company_name}</span>
                <small>業種: {customer.industry || "未設定"} / 担当者: {customer.contact_person || "未設定"} / 更新: {formatDate(customer.updated_at)}</small>
              </div>
            )) : <p>まだ顧客は保存されていません。</p>}
          </div>
        </article>
        <article>
          <strong>案件一覧</strong>
          <div className="crm-list">
            {projects.length ? projects.map((project) => (
              <div key={project.id}>
                <span>{project.name}</span>
                <small>顧客: {project.customer_name || "未設定"} / 状態: {project.status} / 受注確率: {project.win_probability}% / 更新: {formatDate(project.updated_at)}</small>
                <p>{project.next_action || project.summary || "次回アクションは未設定です。"}</p>
              </div>
            )) : <p>まだ案件は保存されていません。</p>}
          </div>
        </article>
      </div>
    </section>
  );
}

function formatDate(value: string) {
  if (!value) return "未設定";
  return new Date(value).toLocaleString("ja-JP");
}
