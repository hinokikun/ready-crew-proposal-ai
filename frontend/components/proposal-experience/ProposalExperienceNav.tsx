"use client";

import {
  BarChart3,
  Briefcase,
  ChevronLeft,
  ChevronRight,
  FileClock,
  Home,
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
  PenTool,
  Settings,
  ShieldCheck,
  Sparkles,
  Wand2,
  Wrench
} from "lucide-react";
import type { ProposalExperienceView } from "@/components/proposal-experience/types";
import { isAdminRole, isManagerCompatibleRole } from "@/lib/roles";

type ProposalExperienceNavProps = {
  activeView: ProposalExperienceView;
  collapsed: boolean;
  mobileOpen: boolean;
  role?: string | null;
  workspaceName: string;
  organizationName: string;
  onChangeView: (view: ProposalExperienceView) => void;
  onToggleCollapsed: () => void;
  onToggleMobile: () => void;
};

type NavItem = {
  id: ProposalExperienceView;
  label: string;
  description: string;
  icon: typeof Home;
  managerOnly?: boolean;
  adminOnly?: boolean;
};

const userNavItems: NavItem[] = [
  { id: "home", label: "ホーム", description: "最初にやること", icon: Home },
  { id: "new-proposal", label: "提案書を作る", description: "案件情報を貼り付け", icon: Wand2 },
  { id: "history", label: "作成履歴", description: "過去の提案書", icon: FileClock },
  { id: "improvement", label: "分析・レポート", description: "効果測定とCSV", icon: BarChart3 },
  { id: "settings", label: "設定", description: "アカウント確認", icon: Settings }
];

const managerNavItems: NavItem[] = [
  { id: "projects", label: "案件管理", description: "CRMと案件状態", icon: Briefcase, managerOnly: true },
  { id: "assistant", label: "AI支援", description: "詳細な営業支援", icon: Sparkles, managerOnly: true },
  { id: "editor", label: "詳細編集", description: "構成とデザイン", icon: PenTool, managerOnly: true },
  { id: "templates", label: "出力設定", description: "PPTテンプレート", icon: Wrench, managerOnly: true },
  { id: "analytics", label: "管理分析", description: "利用状況とKPI", icon: BarChart3, managerOnly: true }
];

const adminNavItems: NavItem[] = [
  { id: "admin", label: "管理コンソール", description: "ユーザー・監査・運用", icon: ShieldCheck, adminOnly: true }
];

function buildVisibleItems(role?: string | null) {
  const items = [...userNavItems, ...managerNavItems, ...adminNavItems];
  return items.filter((item) => {
    if (item.adminOnly) return isAdminRole(role ?? undefined);
    if (item.managerOnly) return isManagerCompatibleRole(role ?? undefined);
    return true;
  });
}

export function ProposalExperienceNav({
  activeView,
  collapsed,
  mobileOpen,
  role,
  workspaceName,
  organizationName,
  onChangeView,
  onToggleCollapsed,
  onToggleMobile
}: ProposalExperienceNavProps) {
  const visibleItems = buildVisibleItems(role);

  function selectView(view: ProposalExperienceView) {
    onChangeView(view);
    if (mobileOpen) onToggleMobile();
  }

  return (
    <>
      <button className="v80-mobile-menu-button" type="button" onClick={onToggleMobile} aria-expanded={mobileOpen} aria-label="メニューを開く">
        <Menu size={19} aria-hidden="true" />
      </button>
      <aside className={`v80-sidebar ${collapsed ? "is-collapsed" : ""} ${mobileOpen ? "is-open" : ""}`} data-testid="v80-sidebar">
        <div className="v80-sidebar-brand">
          <span className="v80-brand-mark" aria-hidden="true">
            <Briefcase size={18} />
          </span>
          {!collapsed && (
            <div>
              <strong>AI営業秘書</strong>
              <small>提案書作成ツール</small>
            </div>
          )}
        </div>

        <div className="v80-sidebar-context">
          {!collapsed && (
            <>
              <span>{organizationName}</span>
              <strong>{workspaceName}</strong>
            </>
          )}
        </div>

        <nav className="v80-nav-list" aria-label="メインメニュー">
          {visibleItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                type="button"
                key={item.id}
                className={`v80-nav-item ${activeView === item.id ? "is-active" : ""}`}
                data-testid={`nav-${item.id}`}
                onClick={() => selectView(item.id)}
                aria-current={activeView === item.id ? "page" : undefined}
                title={collapsed ? `${item.label}: ${item.description}` : undefined}
              >
                <Icon size={18} aria-hidden="true" />
                {!collapsed && (
                  <span>
                    <strong>{item.label}</strong>
                    <small>{item.description}</small>
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        <button className="v80-collapse-button" type="button" onClick={onToggleCollapsed} aria-label={collapsed ? "サイドバーを広げる" : "サイドバーを折りたたむ"}>
          {collapsed ? <PanelLeftOpen size={17} aria-hidden="true" /> : <PanelLeftClose size={17} aria-hidden="true" />}
          {!collapsed && <span>折りたたむ</span>}
        </button>
      </aside>
      {mobileOpen && <button className="v80-sidebar-backdrop" type="button" onClick={onToggleMobile} aria-label="メニューを閉じる" />}
      <div className="v80-view-switcher" aria-label="画面移動">
        <button type="button" onClick={() => selectView(previousView(activeView, visibleItems))} aria-label="前の画面">
          <ChevronLeft size={16} aria-hidden="true" />
        </button>
        <span>{visibleItems.find((item) => item.id === activeView)?.label ?? "ホーム"}</span>
        <button type="button" onClick={() => selectView(nextView(activeView, visibleItems))} aria-label="次の画面">
          <ChevronRight size={16} aria-hidden="true" />
        </button>
      </div>
    </>
  );
}

function previousView(current: ProposalExperienceView, items: NavItem[]): ProposalExperienceView {
  const index = Math.max(0, items.findIndex((item) => item.id === current));
  return items[index <= 0 ? items.length - 1 : index - 1]?.id ?? "home";
}

function nextView(current: ProposalExperienceView, items: NavItem[]): ProposalExperienceView {
  const index = Math.max(0, items.findIndex((item) => item.id === current));
  return items[index >= items.length - 1 ? 0 : index + 1]?.id ?? "home";
}
