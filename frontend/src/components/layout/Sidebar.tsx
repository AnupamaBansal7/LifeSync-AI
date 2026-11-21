import React from 'react';
import type { LucideIcon } from 'lucide-react';
import {
  Bot,
  Brain,
  Calendar,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Flame,
  Layers,
  LayoutDashboard,
  PieChart,
  Settings,
  Sparkles,
  Target,
  Workflow,
  Zap,
} from 'lucide-react';
import type { User } from '../../types';

export type NavTab =
  | 'overview'
  | 'workspace'
  | 'assistant'
  | 'agents'
  | 'tasks'
  | 'calendar'
  | 'goals'
  | 'habits'
  | 'automations'
  | 'memory'
  | 'analytics'
  | 'integrations'
  | 'settings';

interface SidebarProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
  user: User | null;
  activeRole: string;
  pendingApprovalsCount: number;
}

interface NavItemDef {
  id: NavTab;
  label: string;
  icon: LucideIcon;
  badge?: number | string;
  section?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  collapsed,
  onToggleCollapse,
  user,
  activeRole,
  pendingApprovalsCount,
}) => {
  const navItems: NavItemDef[] = [
    { id: 'overview', label: 'Command Center', icon: LayoutDashboard },
    { id: 'workspace', label: 'My Workspace', icon: Layers },
    { id: 'assistant', label: 'AI Assistant', icon: Sparkles },
    {
      id: 'agents',
      label: 'AI Agents',
      icon: Bot,
      badge: pendingApprovalsCount > 0 ? pendingApprovalsCount : undefined,
    },
    { id: 'tasks', label: 'Tasks', icon: CheckCircle2 },
    { id: 'calendar', label: 'Calendar & Plans', icon: Calendar },
    { id: 'goals', label: 'Goals & Milestones', icon: Target },
    { id: 'habits', label: 'Habits & Streaks', icon: Flame },
    { id: 'automations', label: 'Automations', icon: Workflow },
    { id: 'memory', label: 'Memory & RAG', icon: Brain },
    { id: 'analytics', label: 'Analytics', icon: PieChart },
    { id: 'integrations', label: 'Integrations', icon: Zap },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside
      className={`relative flex flex-col justify-between border-r border-slate-800/80 bg-slate-950/90 backdrop-blur-xl transition-all duration-300 z-30 select-none ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Top Branding */}
      <div>
        <div className="flex items-center justify-between p-4 border-b border-slate-800/60">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="relative p-2 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-white shadow-lg shadow-indigo-500/25 shrink-0">
              <Sparkles className="w-5 h-5 animate-pulse" />
            </div>
            {!collapsed && (
              <div className="leading-tight truncate">
                <div className="font-bold text-sm tracking-tight bg-gradient-to-r from-white via-indigo-100 to-slate-400 bg-clip-text text-transparent">
                  LifeSync AI
                </div>
                <div className="text-[10px] text-indigo-400 font-mono uppercase tracking-wider">
                  OS v2.0
                </div>
              </div>
            )}
          </div>
          <button
            onClick={onToggleCollapse}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 transition cursor-pointer"
            title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Active Role Pill */}
        {!collapsed && (
          <div className="px-4 py-3 border-b border-slate-800/40 bg-slate-900/30">
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1">
              Active Context
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs font-semibold capitalize text-indigo-300 truncate">
                {activeRole === 'all' ? 'Omni View (All Roles)' : activeRole}
              </span>
            </div>
          </div>
        )}

        {/* Navigation Items */}
        <nav className="p-2 space-y-1 overflow-y-auto max-h-[calc(100vh-220px)]">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                title={collapsed ? item.label : undefined}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all group cursor-pointer ${
                  isActive
                    ? 'bg-gradient-to-r from-indigo-600/25 to-violet-600/10 text-white border border-indigo-500/40 font-medium shadow-sm'
                    : 'text-slate-400 hover:bg-slate-900/60 hover:text-slate-200'
                } ${collapsed ? 'justify-center px-0' : ''}`}
              >
                <Icon
                  className={`w-4 h-4 shrink-0 transition-transform group-hover:scale-110 ${
                    isActive ? 'text-indigo-400' : 'text-slate-400'
                  }`}
                />
                {!collapsed && <span className="truncate">{item.label}</span>}
                {!collapsed && item.badge !== undefined && (
                  <span className="ml-auto text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40">
                    {item.badge}
                  </span>
                )}
                {collapsed && item.badge !== undefined && (
                  <span className="absolute top-1 right-2 w-2 h-2 rounded-full bg-amber-400" />
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer Profile */}
      <div className="p-3 border-t border-slate-800/60 bg-slate-950/60">
        <div
          onClick={() => onSelectTab('settings')}
          className={`flex items-center gap-3 p-2 rounded-xl hover:bg-slate-900/60 transition cursor-pointer ${
            collapsed ? 'justify-center' : ''
          }`}
          title="User Profile & Settings"
        >
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center text-xs font-bold text-white shadow shrink-0">
            {user?.full_name?.charAt(0) || 'U'}
          </div>
          {!collapsed && (
            <div className="truncate text-left">
              <div className="text-xs font-semibold text-slate-200 truncate">
                {user?.full_name || 'LifeSync User'}
              </div>
              <div className="text-[11px] text-slate-400 truncate">{user?.email}</div>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
};
