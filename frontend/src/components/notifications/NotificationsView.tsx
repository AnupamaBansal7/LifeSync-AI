import React, { useState } from 'react';
import {
  Bell,
  Check,
  CheckCheck,
  CheckCircle2,
  Clock,
  Filter,
  Info,
  ShieldAlert,
  Sparkles,
  Trash2,
} from 'lucide-react';
import type { Notification } from '../../types';
import type { NavTab } from '../layout/Sidebar';

interface NotificationsViewProps {
  notifications: Notification[];
  onMarkRead: (id: string) => void;
  onMarkAllRead?: () => void;
  onClearAll?: () => void;
  onNavigateTab?: (tab: NavTab | string) => void;
}

export const NotificationsView: React.FC<NotificationsViewProps> = ({
  notifications,
  onMarkRead,
  onMarkAllRead,
  onClearAll,
  onNavigateTab,
}) => {
  const [filter, setFilter] = useState<'all' | 'unread' | 'deadline' | 'agent_approval' | 'reminder'>('all');

  const filteredNotifications = notifications.filter((n) => {
    if (filter === 'unread') return !n.is_read;
    if (filter === 'deadline') return n.category === 'deadline';
    if (filter === 'agent_approval') return n.category === 'agent_approval';
    if (filter === 'reminder') return n.category === 'reminder';
    return true;
  });

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'deadline':
        return <Clock className="w-4 h-4 text-rose-400" />;
      case 'agent_approval':
        return <ShieldAlert className="w-4 h-4 text-amber-400" />;
      case 'reminder':
        return <CheckCircle2 className="w-4 h-4 text-cyan-400" />;
      case 'insight':
        return <Sparkles className="w-4 h-4 text-indigo-400" />;
      default:
        return <Info className="w-4 h-4 text-slate-400" />;
    }
  };

  const getCategoryBadge = (category: string) => {
    switch (category) {
      case 'deadline':
        return 'bg-rose-500/10 text-rose-300 border-rose-500/30';
      case 'agent_approval':
        return 'bg-amber-500/10 text-amber-300 border-amber-500/30';
      case 'reminder':
        return 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30';
      case 'insight':
        return 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30';
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12 select-none">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-6 rounded-3xl bg-slate-900/80 border border-slate-800 backdrop-blur-xl">
        <div className="flex items-center gap-3.5">
          <div className="p-3 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 text-indigo-400">
            <Bell className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-white">Notifications & Alerts</h1>
              {unreadCount > 0 && (
                <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  {unreadCount} unread
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              System alerts, autonomous agent actions, and proactive schedule reminders
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {onMarkAllRead && unreadCount > 0 && (
            <button
              onClick={onMarkAllRead}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 border border-slate-700 transition cursor-pointer"
            >
              <CheckCheck className="w-3.5 h-3.5 text-indigo-400" />
              <span>Mark all read</span>
            </button>
          )}
          {onClearAll && notifications.length > 0 && (
            <button
              onClick={onClearAll}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-950/30 hover:bg-rose-900/40 text-xs text-rose-300 border border-rose-800/40 transition cursor-pointer"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear</span>
            </button>
          )}
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
        <div className="flex items-center gap-1.5 text-xs text-slate-400 mr-2">
          <Filter className="w-3.5 h-3.5" />
          <span>Filter:</span>
        </div>
        {[
          { id: 'all', label: 'All Notifications' },
          { id: 'unread', label: `Unread (${unreadCount})` },
          { id: 'deadline', label: 'Deadlines' },
          { id: 'agent_approval', label: 'Agent Approvals' },
          { id: 'reminder', label: 'Reminders' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setFilter(tab.id as any)}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition cursor-pointer ${
              filter === tab.id
                ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                : 'bg-slate-900/70 border border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Notifications List */}
      <div className="space-y-3">
        {filteredNotifications.length === 0 ? (
          <div className="text-center py-16 rounded-3xl bg-slate-900/40 border border-slate-800/60 p-8">
            <Bell className="w-10 h-10 text-slate-600 mx-auto mb-3" />
            <h3 className="text-sm font-semibold text-slate-300">No notifications in this view</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              You are all caught up! New alerts from agents, integrations, and scheduled tasks will appear here.
            </p>
          </div>
        ) : (
          filteredNotifications.map((notif) => (
            <div
              key={notif.id}
              className={`p-4 rounded-2xl border transition-all flex items-start justify-between gap-4 ${
                notif.is_read
                  ? 'bg-slate-950/40 border-slate-800/60 text-slate-400'
                  : 'bg-slate-900/80 border-slate-700/80 text-slate-200 shadow-md'
              }`}
            >
              <div className="flex items-start gap-3.5">
                <div className="p-2.5 rounded-xl bg-slate-800/80 border border-slate-700/60 mt-0.5 shrink-0">
                  {getCategoryIcon(notif.category)}
                </div>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-white">{notif.title}</span>
                    <span
                      className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded-full border ${getCategoryBadge(
                        notif.category
                      )}`}
                    >
                      {notif.category.replace('_', ' ')}
                    </span>
                    {!notif.is_read && (
                      <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse" />
                    )}
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">{notif.message}</p>
                  <div className="text-[10px] font-mono text-slate-500 pt-0.5">
                    {new Date(notif.created_at).toLocaleString([], {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                {notif.action_url && onNavigateTab && (
                  <button
                    onClick={() => {
                      if (!notif.is_read) onMarkRead(notif.id);
                      if (notif.action_url) onNavigateTab(notif.action_url);
                    }}
                    className="px-3 py-1.5 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-medium transition cursor-pointer"
                  >
                    View
                  </button>
                )}
                {!notif.is_read && (
                  <button
                    onClick={() => onMarkRead(notif.id)}
                    className="p-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-emerald-400 transition cursor-pointer"
                    title="Mark as read"
                  >
                    <Check className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
