import React from 'react';
import {
  Bot,
  Calendar,
  CheckCircle2,
  ChevronRight,
  Clock,
  Compass,
  ExternalLink,
  Flame,
  Globe,
  Mail,
  Plus,
  RefreshCw,
  Sparkles,
  Target,
  Zap,
} from 'lucide-react';
import type { AICoreStatus, DashboardSummary } from '../../types';
import { AICore3D } from '../3d/AICore3D';

interface DashboardProps {
  summary: DashboardSummary | null;
  activeRole: string;
  onSelectRole: (role: string) => void;
  availableRoles: string[];
  onToggleTask: (taskId: string, currentStatus: string) => void;
  onLogHabit: (habitId: string) => void;
  onApproveAction: (approvalId: string, decision: 'approved' | 'rejected') => void;
  onNavigateTab: (tab: any) => void;
  onReprioritize?: () => void;
  aiCoreStatus: AICoreStatus;
}

export const PersonalizedDashboard: React.FC<DashboardProps> = ({
  summary,
  activeRole,
  onSelectRole,
  availableRoles,
  onToggleTask,
  onLogHabit,
  onApproveAction: _onApproveAction,
  onNavigateTab,
  onReprioritize,
  aiCoreStatus,
}) => {
  if (!summary) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-xs text-slate-400 font-mono">Synchronizing LifeSync Command Center...</p>
        </div>
      </div>
    );
  }

  const scoreColor =
    summary.productivity_score >= 80
      ? 'text-emerald-400'
      : summary.productivity_score >= 50
      ? 'text-indigo-400'
      : 'text-amber-400';

  const scoreBg =
    summary.productivity_score >= 80
      ? 'from-emerald-500 to-teal-400'
      : summary.productivity_score >= 50
      ? 'from-indigo-500 to-violet-400'
      : 'from-amber-500 to-orange-400';

  return (
    <div className="space-y-8 pb-16 select-none">
      {/* ========================================================= */}
      {/* SECTION A: PERSONAL OVERVIEW HERO WITH 3D AI SPHERE       */}
      {/* ========================================================= */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-900/95 via-indigo-950/40 to-slate-900/95 border border-slate-800/80 p-6 sm:p-8 backdrop-blur-xl shadow-2xl">
        <div className="absolute top-0 right-0 -mt-12 -mr-12 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative flex flex-col md:flex-row items-center justify-between gap-6">
          {/* Greeting, Timezone & Productivity Score */}
          <div className="space-y-4 max-w-xl text-center md:text-left">
            <div className="flex flex-wrap items-center justify-center md:justify-start gap-2">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/15 border border-indigo-500/30 text-indigo-300 text-xs font-semibold">
                <Sparkles className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
                <span>LifeSync OS v2.0 Active</span>
              </div>
              {summary.user_timezone && (
                <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-950/60 border border-slate-800 text-[11px] font-mono text-slate-400">
                  <Globe className="w-3 h-3 text-slate-500" />
                  <span>{summary.user_timezone}</span>
                </div>
              )}
            </div>

            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
              {summary.greeting}
            </h1>

            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              {summary.role_highlights?.focus_recommendation ||
                'Your autonomous multi-agent ecosystem is balancing tasks, calendars, and inbox communication across all roles.'}
            </p>

            {/* Quick Metrics & Productivity Ring Bar */}
            <div className="flex flex-wrap items-center justify-center md:justify-start gap-3 pt-2">
              <div className="flex items-center gap-3 px-3.5 py-2 rounded-2xl bg-slate-950/70 border border-slate-800 shadow-inner">
                <div className="relative w-9 h-9 flex items-center justify-center">
                  <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                    <path
                      className="text-slate-800"
                      strokeWidth="3.5"
                      stroke="currentColor"
                      fill="none"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                    <path
                      className={`text-transparent stroke-current bg-gradient-to-r ${scoreBg}`}
                      strokeDasharray={`${summary.productivity_score}, 100`}
                      strokeWidth="3.5"
                      strokeLinecap="round"
                      stroke="currentColor"
                      fill="none"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                  </svg>
                  <span className={`absolute text-[10px] font-bold font-mono ${scoreColor}`}>
                    {summary.productivity_score}
                  </span>
                </div>
                <div>
                  <div className="text-[10px] uppercase font-mono tracking-wider text-slate-400">
                    Productivity
                  </div>
                  <div className="text-xs font-semibold text-slate-200">
                    {summary.productivity_score >= 80
                      ? 'Optimal Flow'
                      : summary.productivity_score >= 50
                      ? 'Steady Pace'
                      : 'Needs Attention'}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2.5 px-3 py-2 rounded-2xl bg-slate-950/70 border border-slate-800">
                <span className="text-[11px] text-slate-400">Pending Tasks:</span>
                <span className="text-sm font-bold font-mono text-slate-100">
                  {summary.metrics.pending_tasks}
                </span>
              </div>

              <div className="flex items-center gap-2.5 px-3 py-2 rounded-2xl bg-slate-950/70 border border-slate-800">
                <span className="text-[11px] text-slate-400">Habits Today:</span>
                <span className="text-sm font-bold font-mono text-emerald-400">
                  {summary.metrics.completed_habits_today}/{summary.metrics.active_habits}
                </span>
              </div>
            </div>
          </div>

          {/* 3D AI Core Centerpiece */}
          <div className="flex flex-col items-center">
            <AICore3D
              status={aiCoreStatus}
              size={210}
              onClick={() => onNavigateTab('assistant')}
            />
          </div>
        </div>
      </div>

      {/* Role Context Bar */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
        <button
          onClick={() => onSelectRole('all')}
          className={`flex items-center gap-2 px-4 py-2 rounded-2xl text-xs font-semibold whitespace-nowrap transition cursor-pointer ${
            activeRole === 'all'
              ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-md shadow-indigo-600/30'
              : 'bg-slate-900/60 border border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
          }`}
        >
          <Compass className="w-3.5 h-3.5" />
          <span>Omni View (All Roles)</span>
        </button>

        {availableRoles.map((role) => {
          const isActive = activeRole === role;
          return (
            <button
              key={role}
              onClick={() => onSelectRole(role)}
              className={`flex items-center gap-2 px-4 py-2 rounded-2xl text-xs font-semibold whitespace-nowrap capitalize transition cursor-pointer ${
                isActive
                  ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-md shadow-indigo-600/30'
                  : 'bg-slate-900/60 border border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <span>{role}</span>
            </button>
          );
        })}
      </div>

      {/* ========================================================= */}
      {/* SECTION G: GROUNDED PROACTIVE INSIGHTS (CARDS)             */}
      {/* ========================================================= */}
      {summary.proactive_insights && summary.proactive_insights.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 px-1 text-xs font-bold uppercase tracking-wider text-slate-400 font-mono">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            <span>Autonomous Proactive Intelligence</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {summary.proactive_insights.map((ins, idx) => {
              const borderTheme =
                ins.urgency === 'urgent'
                  ? 'border-rose-500/40 bg-rose-950/20 text-rose-300'
                  : ins.urgency === 'high'
                  ? 'border-amber-500/40 bg-amber-950/20 text-amber-300'
                  : 'border-indigo-500/30 bg-indigo-950/20 text-indigo-300';

              return (
                <div
                  key={idx}
                  className={`p-4 rounded-2xl border backdrop-blur-md flex flex-col justify-between transition-all hover:scale-[1.01] ${borderTheme}`}
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono uppercase font-bold tracking-wider opacity-80">
                        {ins.type}
                      </span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded font-mono font-bold uppercase bg-slate-950/60">
                        {ins.urgency}
                      </span>
                    </div>
                    <div className="text-xs font-semibold text-white leading-tight">{ins.title}</div>
                    <p className="text-[11px] text-slate-300 leading-relaxed">{ins.description}</p>
                  </div>

                  {ins.action_text && (
                    <button
                      onClick={() => onNavigateTab(ins.tab || 'tasks')}
                      className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-white hover:underline cursor-pointer"
                    >
                      <span>{ins.action_text}</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* 2-COLUMN MAIN WORKSTATION GRID                            */}
      {/* ========================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* LEFT 2 COLUMNS: Priorities, Schedule, and Email Hub */}
        <div className="lg:col-span-2 space-y-6">
          {/* ========================================================= */}
          {/* SECTION B: TODAY'S PRIORITIES (WITH REPRIORITIZE)         */}
          {/* ========================================================= */}
          <div className="rounded-3xl bg-slate-900/80 border border-slate-800 p-6 backdrop-blur-xl shadow-lg">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4">
              <div className="flex items-center gap-2.5">
                <div className="p-2.5 rounded-xl bg-indigo-500/15 text-indigo-400">
                  <CheckCircle2 className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">Today's Highest Priorities</h3>
                  <p className="text-[11px] text-slate-400">
                    Dynamically ranked by deadline urgency and active role
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    if (onReprioritize) onReprioritize();
                    else onNavigateTab('assistant');
                  }}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-medium transition cursor-pointer"
                  title="Invoke TaskManagementAgent to re-evaluate priorities"
                >
                  <RefreshCw className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Ask Sync to Reprioritize</span>
                </button>
                <button
                  onClick={() => onNavigateTab('tasks')}
                  className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1 cursor-pointer pl-1"
                >
                  Tasks <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            <div className="space-y-2.5">
              {summary.today_priorities.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-xs">
                  No priority tasks remaining for today. Great job!
                </div>
              ) : (
                summary.today_priorities.map((task) => {
                  const isDone = task.status === 'completed';
                  return (
                    <div
                      key={task.id}
                      className={`p-3.5 rounded-2xl border flex items-center justify-between transition-all ${
                        isDone
                          ? 'bg-slate-950/40 border-slate-800/50 text-slate-500 line-through'
                          : 'bg-slate-950/80 border-slate-800 text-slate-200 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => onToggleTask(task.id, task.status)}
                          className={`w-5 h-5 rounded-lg border flex items-center justify-center transition cursor-pointer ${
                            isDone
                              ? 'bg-emerald-500/20 border-emerald-500 text-emerald-400'
                              : 'border-slate-700 hover:border-indigo-400 text-transparent'
                          }`}
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                        </button>
                        <div>
                          <div className="text-xs font-semibold">{task.title}</div>
                          <div className="flex items-center gap-2 mt-0.5 text-[10px] text-slate-400">
                            <span className="capitalize text-indigo-300 font-mono">
                              {task.role_context}
                            </span>
                            <span>•</span>
                            <span>{task.estimated_minutes}m est.</span>
                            {task.due_date && (
                              <>
                                <span>•</span>
                                <span className="font-mono text-slate-400">
                                  Due {new Date(task.due_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>

                      <span
                        className={`text-[10px] font-mono px-2 py-0.5 rounded-full uppercase font-semibold ${
                          task.priority === 'urgent'
                            ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                            : task.priority === 'high'
                            ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                            : 'bg-slate-800 text-slate-300'
                        }`}
                      >
                        {task.priority}
                      </span>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* ========================================================= */}
          {/* SECTION D: TODAY'S SCHEDULE & FOCUS BLOCKS               */}
          {/* ========================================================= */}
          <div className="rounded-3xl bg-slate-900/80 border border-slate-800 p-6 backdrop-blur-xl shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2.5">
                <div className="p-2.5 rounded-xl bg-violet-500/15 text-violet-400">
                  <Calendar className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">Today's Schedule & Focus Blocks</h3>
                  <p className="text-[11px] text-slate-400">
                    Synchronized from Calendar & optimized by CalendarAgent
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => onNavigateTab('calendar')}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Schedule block</span>
                </button>
                <button
                  onClick={() => onNavigateTab('calendar')}
                  className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1 cursor-pointer pl-1"
                >
                  Calendar <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {summary.daily_plan.summary && (
              <p className="text-xs text-slate-300 mb-4 italic bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                "{summary.daily_plan.summary}"
              </p>
            )}

            <div className="space-y-2">
              {summary.daily_plan.blocks.length === 0 ? (
                <div className="text-xs text-slate-500 text-center py-4">
                  No focus schedule generated yet. Ask Sync to "Plan my day with focus blocks".
                </div>
              ) : (
                summary.daily_plan.blocks.map((block, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-3 rounded-xl bg-slate-950/70 border border-slate-800 text-xs hover:border-slate-700 transition"
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-indigo-400 text-[11px]">{block.time}</span>
                      <span className="font-medium text-slate-200">{block.title}</span>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-slate-900 text-slate-400 capitalize font-mono">
                      {block.role}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* ========================================================= */}
          {/* SECTION E: EMAIL INTELLIGENCE WIDGET                      */}
          {/* ========================================================= */}
          <div className="rounded-3xl bg-slate-900/80 border border-slate-800 p-6 backdrop-blur-xl shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2.5">
                <div className="p-2.5 rounded-xl bg-cyan-500/15 text-cyan-400">
                  <Mail className="w-4 h-4" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-bold text-white">Email Intelligence</h3>
                    {summary.email_intelligence?.unread_count ? (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                        {summary.email_intelligence.unread_count} unread
                      </span>
                    ) : null}
                  </div>
                  <p className="text-[11px] text-slate-400">
                    Important messages, extracted deadlines, and pending replies
                  </p>
                </div>
              </div>

              <button
                onClick={() => onNavigateTab('email')}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-indigo-600/30 to-violet-600/30 hover:from-indigo-600/40 hover:to-violet-600/40 text-indigo-300 border border-indigo-500/40 text-xs font-semibold transition cursor-pointer"
              >
                <span>Open Email Hub</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Extracted Deadlines from Emails */}
            {summary.email_intelligence?.extracted_deadlines &&
            summary.email_intelligence.extracted_deadlines.length > 0 ? (
              <div className="mb-4 space-y-2">
                <div className="text-[10px] uppercase font-mono tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Clock className="w-3 h-3 text-cyan-400" />
                  <span>Deadlines Extracted by Email Agent</span>
                </div>
                {summary.email_intelligence.extracted_deadlines.map((dl, dIdx) => (
                  <div
                    key={dIdx}
                    className="p-3 rounded-xl bg-cyan-950/20 border border-cyan-500/30 flex items-center justify-between text-xs"
                  >
                    <div>
                      <div className="font-semibold text-slate-200">{dl.subject}</div>
                      <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                        Deadline: <span className="text-cyan-300">{dl.deadline}</span> • From: {dl.sender}
                      </div>
                    </div>
                    <button
                      onClick={() => onNavigateTab('tasks')}
                      className="px-2.5 py-1 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 font-semibold text-[10px] border border-cyan-500/30 transition cursor-pointer"
                    >
                      + Add to Tasks
                    </button>
                  </div>
                ))}
              </div>
            ) : null}

            {/* Important Emails Needing Reply */}
            <div className="space-y-2">
              {summary.email_intelligence?.unread_important_messages &&
              summary.email_intelligence.unread_important_messages.length > 0 ? (
                summary.email_intelligence.unread_important_messages.map((msg) => (
                  <div
                    key={msg.id}
                    onClick={() => onNavigateTab('email')}
                    className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-indigo-500/40 transition cursor-pointer flex items-center justify-between"
                  >
                    <div className="space-y-0.5 max-w-[85%]">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-xs text-white">
                          {msg.sender_name || msg.sender}
                        </span>
                        <span className="text-[10px] px-1.5 rounded bg-indigo-500/20 text-indigo-300 font-mono">
                          Important
                        </span>
                      </div>
                      <div className="text-xs text-slate-300 font-medium truncate">{msg.subject}</div>
                      <div className="text-[10px] text-slate-400 truncate">{msg.snippet}</div>
                    </div>
                    <ChevronRight className="w-4 h-4 text-slate-500 shrink-0" />
                  </div>
                ))
              ) : (
                <div className="text-center py-4 text-xs text-slate-500">
                  No pending important emails in your inbox.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: AI Agent Live Activity, Habits & Goals */}
        <div className="space-y-6">
          {/* ========================================================= */}
          {/* SECTION C: AI AGENT LIVE ACTIVITY PANEL                   */}
          {/* ========================================================= */}
          <div className="rounded-3xl bg-slate-900/80 border border-slate-800 p-6 backdrop-blur-xl shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Bot className="w-4 h-4 text-indigo-400" />
                <h3 className="text-sm font-bold text-white">AI Agent Live Activity</h3>
              </div>
              <button
                onClick={() => onNavigateTab('agents')}
                className="text-xs text-indigo-400 hover:text-indigo-300 font-medium cursor-pointer"
              >
                View all
              </button>
            </div>

            <div className="space-y-2.5">
              {summary.agent_activity && summary.agent_activity.length > 0 ? (
                summary.agent_activity.slice(0, 4).map((agent) => {
                  const isWorking = agent.status.toLowerCase() === 'working';
                  const isWaiting = agent.status.toLowerCase().includes('approval');
                  return (
                    <div
                      key={agent.id}
                      className="p-3 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-1.5"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-slate-200">
                          {agent.agent_name}
                        </span>
                        <span
                          className={`text-[9px] font-mono uppercase px-2 py-0.5 rounded-full font-bold ${
                            isWorking
                              ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 animate-pulse'
                              : isWaiting
                              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                              : 'bg-slate-800 text-slate-400'
                          }`}
                        >
                          {agent.status}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 leading-tight truncate">
                        {agent.assignment}
                      </p>
                      <div className="text-[10px] text-slate-500 font-mono">
                        Result: <span className="text-slate-300">{agent.result_summary}</span>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="text-xs text-slate-500 text-center py-4">
                  Agents standing by.
                </div>
              )}
            </div>
          </div>

          {/* ========================================================= */}
          {/* SECTION F: HABITS & STREAKS                               */}
          {/* ========================================================= */}
          <div className="rounded-3xl bg-slate-900/80 border border-slate-800 p-6 backdrop-blur-xl shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Flame className="w-4 h-4 text-amber-400" />
                <h3 className="text-sm font-bold text-white">Habits & Streaks</h3>
              </div>
              <button
                onClick={() => onNavigateTab('habits')}
                className="text-xs text-indigo-400 hover:text-indigo-300 font-medium cursor-pointer"
              >
                View all
              </button>
            </div>

            <div className="space-y-2.5">
              {summary.habits.length === 0 ? (
                <div className="text-xs text-slate-500 text-center py-4">No active habits.</div>
              ) : (
                summary.habits.slice(0, 5).map((habit) => (
                  <div
                    key={habit.id}
                    className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs"
                  >
                    <div className="flex items-center gap-2.5">
                      <button
                        onClick={() => onLogHabit(habit.id)}
                        className={`w-5 h-5 rounded-lg border flex items-center justify-center transition cursor-pointer ${
                          habit.completed_today
                            ? 'bg-amber-500/20 border-amber-500 text-amber-400'
                            : 'border-slate-700 hover:border-amber-400 text-transparent'
                        }`}
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                      </button>
                      <span className="text-slate-200 font-medium truncate max-w-[140px]">
                        {habit.title}
                      </span>
                    </div>

                    <div className="flex items-center gap-1 text-amber-400 font-mono text-[11px] font-bold">
                      <Flame className="w-3 h-3 fill-amber-400" />
                      <span>{habit.current_streak}d</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* ========================================================= */}
          {/* SECTION F (CONT): STRATEGIC GOALS & MILESTONES             */}
          {/* ========================================================= */}
          <div className="rounded-3xl bg-slate-900/80 border border-slate-800 p-6 backdrop-blur-xl shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4 text-emerald-400" />
                <h3 className="text-sm font-bold text-white">Strategic Goals</h3>
              </div>
              <button
                onClick={() => onNavigateTab('goals')}
                className="text-xs text-indigo-400 hover:text-indigo-300 font-medium cursor-pointer"
              >
                View all
              </button>
            </div>

            <div className="space-y-3">
              {summary.goals.length === 0 ? (
                <div className="text-xs text-slate-500 text-center py-4">No active goals yet.</div>
              ) : (
                summary.goals.slice(0, 3).map((goal) => (
                  <div key={goal.id} className="space-y-1.5">
                    <div className="flex justify-between text-xs">
                      <span className="font-medium text-slate-200 truncate">{goal.title}</span>
                      <span className="font-mono text-emerald-400 font-bold">
                        {goal.progress_percent}%
                      </span>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-slate-950 overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-indigo-500 to-emerald-400 rounded-full transition-all duration-500"
                        style={{ width: `${goal.progress_percent}%` }}
                      />
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
