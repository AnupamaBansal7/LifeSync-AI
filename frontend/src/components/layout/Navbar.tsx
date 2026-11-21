import React, { useState } from 'react';
import {
  Bell,
  Command,
  Compass,
  LogOut,
  Moon,
  Search,
  Sparkles,
  Sun,
} from 'lucide-react';
import type { Notification, Role, User } from '../../types';

interface NavbarProps {
  user: User | null;
  rolesCatalog: Role[];
  activeRole: string;
  onSelectRole: (role: string) => void;
  onOpenCommandPalette: () => void;
  onOpenAssistant: () => void;
  onLogout: () => void;
  notifications: Notification[];
  onMarkNotificationRead: (id: string) => void;
  theme: 'dark' | 'light';
  onToggleTheme: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  user,
  rolesCatalog,
  activeRole,
  onSelectRole,
  onOpenCommandPalette,
  onOpenAssistant,
  onLogout,
  notifications,
  onMarkNotificationRead,
  theme,
  onToggleTheme,
}) => {
  const [showRoleMenu, setShowRoleMenu] = useState(false);
  const [showNotifMenu, setShowNotifMenu] = useState(false);

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const userRoleSlugs = user?.roles?.map((r) => r.role?.slug || r.role_id) || [];
  const availableRoles = rolesCatalog.filter(
    (rc) => userRoleSlugs.includes(rc.slug) || rc.slug === 'personal'
  );

  return (
    <header className="h-16 border-b border-slate-800/80 bg-slate-950/70 backdrop-blur-xl px-6 flex items-center justify-between sticky top-0 z-20 select-none">
      {/* Left: Command Search Trigger */}
      <div className="flex items-center gap-4">
        <button
          onClick={onOpenCommandPalette}
          className="flex items-center gap-2.5 px-3.5 py-1.5 rounded-xl bg-slate-900/80 hover:bg-slate-800/80 border border-slate-800 text-xs text-slate-400 hover:text-slate-200 transition cursor-pointer shadow-inner"
        >
          <Search className="w-3.5 h-3.5 text-indigo-400" />
          <span>Search or command...</span>
          <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-mono rounded bg-slate-950 border border-slate-800 text-slate-400">
            <Command className="w-2.5 h-2.5" /> K
          </kbd>
        </button>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3">
        {/* Role Switcher Dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowRoleMenu(!showRoleMenu)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-indigo-600/10 hover:bg-indigo-600/20 border border-indigo-500/30 text-xs font-medium text-indigo-300 transition cursor-pointer"
          >
            <Compass className="w-3.5 h-3.5 text-indigo-400" />
            <span className="capitalize">
              {activeRole === 'all' ? 'All Roles' : activeRole}
            </span>
          </button>

          {showRoleMenu && (
            <div className="absolute right-0 mt-2 w-52 rounded-2xl bg-slate-900/95 border border-slate-800 shadow-2xl p-2 z-50 backdrop-blur-xl">
              <div className="px-2 py-1 text-[10px] font-mono uppercase tracking-wider text-slate-400 border-b border-slate-800/60 mb-1">
                Switch Role Context
              </div>
              <button
                onClick={() => {
                  onSelectRole('all');
                  setShowRoleMenu(false);
                }}
                className={`w-full text-left px-3 py-2 rounded-xl text-xs transition cursor-pointer flex items-center justify-between ${
                  activeRole === 'all'
                    ? 'bg-indigo-600/20 text-indigo-300 font-semibold'
                    : 'text-slate-300 hover:bg-slate-800/60'
                }`}
              >
                <span>Omni View (All Roles)</span>
                {activeRole === 'all' && <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />}
              </button>
              {availableRoles.map((r) => {
                const isActive = activeRole === r.slug;
                return (
                  <button
                    key={r.slug}
                    onClick={() => {
                      onSelectRole(r.slug);
                      setShowRoleMenu(false);
                    }}
                    className={`w-full text-left px-3 py-2 rounded-xl text-xs transition cursor-pointer flex items-center justify-between ${
                      isActive
                        ? 'bg-indigo-600/20 text-indigo-300 font-semibold'
                        : 'text-slate-300 hover:bg-slate-800/60'
                    }`}
                  >
                    <span className="capitalize">{r.name}</span>
                    {isActive && <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Quick Ask AI Button */}
        <button
          onClick={onOpenAssistant}
          className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-medium shadow-md shadow-indigo-600/25 transition cursor-pointer"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>Ask AI</span>
        </button>

        {/* Notification Bell */}
        <div className="relative">
          <button
            onClick={() => setShowNotifMenu(!showNotifMenu)}
            className="relative p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-900 border border-transparent hover:border-slate-800 transition cursor-pointer"
            title="Notifications"
          >
            <Bell className="w-4 h-4" />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
            )}
          </button>

          {showNotifMenu && (
            <div className="absolute right-0 mt-2 w-80 rounded-2xl bg-slate-900/95 border border-slate-800 shadow-2xl p-3 z-50 backdrop-blur-xl">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800/60 mb-2">
                <span className="text-xs font-semibold text-slate-200">Notifications</span>
                <span className="text-[10px] text-slate-400">{unreadCount} unread</span>
              </div>
              <div className="max-h-72 overflow-y-auto space-y-2">
                {notifications.length === 0 ? (
                  <p className="text-xs text-slate-400 text-center py-4">No notifications yet.</p>
                ) : (
                  notifications.map((n) => (
                    <div
                      key={n.id}
                      onClick={() => onMarkNotificationRead(n.id)}
                      className={`p-2.5 rounded-xl border text-left text-xs transition cursor-pointer ${
                        n.is_read
                          ? 'bg-slate-950/40 border-slate-800/50 text-slate-400'
                          : 'bg-indigo-950/20 border-indigo-500/30 text-slate-200'
                      }`}
                    >
                      <div className="font-semibold text-xs text-indigo-300">{n.title}</div>
                      <div className="text-[11px] opacity-80 mt-0.5 line-clamp-2">{n.message}</div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Theme Toggle */}
        <button
          onClick={onToggleTheme}
          className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-900 border border-transparent hover:border-slate-800 transition cursor-pointer"
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} mode`}
        >
          {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>

        {/* Logout */}
        <button
          onClick={onLogout}
          className="p-2 rounded-xl text-slate-400 hover:text-rose-400 hover:bg-rose-950/20 transition cursor-pointer"
          title="Sign Out"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
