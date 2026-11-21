import React, { useEffect, useState } from 'react';
import {
  Bot,
  Brain,
  Calendar,
  CheckCircle2,
  Compass,
  Flame,
  LayoutDashboard,
  PieChart,
  Search,
  Settings,
  Sparkles,
  Target,
  Workflow,
  X,
} from 'lucide-react';
import type { NavTab } from './Sidebar';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectTab: (tab: NavTab) => void;
  onSelectRole: (role: string) => void;
  availableRoles: string[];
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  onSelectTab,
  onSelectRole,
  availableRoles,
}) => {
  const [query, setQuery] = useState('');

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
        else onClose(); // parent toggles
      } else if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const actions = [
    { label: 'Go to Command Center', icon: LayoutDashboard, action: () => onSelectTab('overview') },
    { label: 'Chat with AI Assistant', icon: Sparkles, action: () => onSelectTab('assistant') },
    { label: 'View AI Agents Ecosystem', icon: Bot, action: () => onSelectTab('agents') },
    { label: 'View Tasks & Kanban Board', icon: CheckCircle2, action: () => onSelectTab('tasks') },
    { label: 'View Calendar & Time Blocks', icon: Calendar, action: () => onSelectTab('calendar') },
    { label: 'View Goals & Roadmaps', icon: Target, action: () => onSelectTab('goals') },
    { label: 'Check Habits & Streaks', icon: Flame, action: () => onSelectTab('habits') },
    { label: 'Manage Automations & Workflows', icon: Workflow, action: () => onSelectTab('automations') },
    { label: 'Search Semantic Memory & RAG', icon: Brain, action: () => onSelectTab('memory') },
    { label: 'View Productivity Analytics', icon: PieChart, action: () => onSelectTab('analytics') },
    { label: 'System Settings & AI Providers', icon: Settings, action: () => onSelectTab('settings') },
  ];

  const roleActions = availableRoles.map((r) => ({
    label: `Switch to ${r.toUpperCase()} mode`,
    icon: Compass,
    action: () => onSelectRole(r),
  }));

  const allItems = [...actions, ...roleActions];
  const filtered = allItems.filter((item) =>
    item.label.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-150">
      <div className="w-full max-w-xl rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl overflow-hidden flex flex-col">
        {/* Search Input Bar */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-800">
          <Search className="w-5 h-5 text-indigo-400 shrink-0" />
          <input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or jump to workspace..."
            className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-400 outline-none"
          />
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Results List */}
        <div className="max-h-80 overflow-y-auto p-2 space-y-1">
          {filtered.length === 0 ? (
            <p className="text-xs text-slate-400 text-center py-6">No matching actions found.</p>
          ) : (
            filtered.map((item, idx) => {
              const Icon = item.icon;
              return (
                <button
                  key={idx}
                  onClick={() => {
                    item.action();
                    onClose();
                  }}
                  className="w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs text-slate-300 hover:bg-indigo-600/20 hover:text-white transition text-left cursor-pointer group"
                >
                  <Icon className="w-4 h-4 text-slate-400 group-hover:text-indigo-400 shrink-0" />
                  <span className="truncate">{item.label}</span>
                </button>
              );
            })
          )}
        </div>

        {/* Footer shortcuts */}
        <div className="px-4 py-2 border-t border-slate-800/60 bg-slate-950/50 flex items-center justify-between text-[11px] text-slate-400">
          <span>Navigation Quick Jumper</span>
          <span>Press ESC to close</span>
        </div>
      </div>
    </div>
  );
};
