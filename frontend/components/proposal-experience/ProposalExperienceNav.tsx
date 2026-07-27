"use client";

import {
  BarChart3,
  BookOpen,
  Briefcase,
  ChevronLeft,
  ChevronRight,
  FileClock,
  Home,
  LayoutTemplate,
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
  PenTool,
  Settings,
  ShieldCheck,
  Sparkles,
  Wand2
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

const navItems: NavItem[] = [
  { id: "home", label: "ホーム", description: "今日の提案状況", icon: Home },
  { id: "new-proposal", label: "新規提案", description: "Prompt Builder", icon: Wand2 },
  { id: "editor", label: "提案エディター", description: "Storyとスライド編集", icon: PenTool },
  { id: "history", label: "提案履歴", description: "作成履歴とCSV", icon: FileClock },
  { id: "projects", label: "案件一覧", description: "CRMと進行状況", icon: Briefcase },
  { id: "assistant", label: "AI営業秘書", description: "Copilotと提案支援", icon: Sparkles },
  { id: "templates", label: "テンプレート", description: "PPTデザイン選択", icon: LayoutTemplate },
  { id: "analytics", label: "分析", description: "営業KPI", icon: BarChart3, managerOnly: true },
  { id: "improvement", label: "業務改善", description: "短縮率と提出資料", icon: BookOpen },
  { id: "admin", label: "管理", description: "ユーザーと監査", icon: ShieldCheck, adminOnly: true },
  { id: "settings", label: "設定", description: "Workspaceと診断", icon: Settings, managerOnly: true }
];

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
  const visibleItems = navItems.filter((item) => {
    if (item.adminOnly) return isAdminRole(role ?? undefined);
    if (item.managerOnly) return isManagerCompatibleRole(role ?? undefined);
    return true;
  });

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
              <strong>ProposalPilot</strong>
              <small>Proposal Experience</small>
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

        <button className="v80-collapse-button" type="button" onClick={onToggleCollapsed} aria-label={collapsed ? "サイドバーを展開" : "サイドバーを折りたたむ"}>
          {collapsed ? <PanelLeftOpen size={17} aria-hidden="true" /> : <PanelLeftClose size={17} aria-hidden="true" />}
          {!collapsed && <span>折りたたむ</span>}
        </button>
      </aside>
      {mobileOpen && <button className="v80-sidebar-backdrop" type="button" onClick={onToggleMobile} aria-label="メニューを閉じる" />}
      <div className="v80-view-switcher" aria-label="ページ移動">
        <button type="button" onClick={() => selectView(previousView(activeView, visibleItems))} aria-label="前のページ">
          <ChevronLeft size={16} aria-hidden="true" />
        </button>
        <span>{visibleItems.find((item) => item.id === activeView)?.label ?? "ホーム"}</span>
        <button type="button" onClick={() => selectView(nextView(activeView, visibleItems))} aria-label="次のページ">
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
