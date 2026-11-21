import React from 'react';
import {
  CheckCircle2,
  ChevronRight,
  Clock,
  Compass,
  Flame,
  Sparkles,
  Target,
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
  aiCoreStatus,
}) => {
  if (!summary) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-xs text-slate-400 font-mono">Synchronizing LifeSync Dashboard...</p>
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

  return (
    <div className="space-y-6 pb-12 select-none">
      {/* 1. Hero 3D AI Operating Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-900/90 via-indigo-950/40 to-slate-900/90 border border-slate-800/80 p-6 sm:p-8 backdrop-blur-xl shadow-2xl">
        <div className="absolute top-0 right-0 -mt-12 -mr-12 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative flex flex-col md:flex-row items-center justify-between gap-6">
          {/* Greeting & Productivity Score */}
          <div className="space-y-3 max-w-xl text-center md:text-left">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/15 border border-indigo-500/30 text-indigo-300 text-xs font-semibold">
              <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
              <span>LifeSync Operating Engine Active</span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
              {summary.greeting}
            </h1>

            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              {summary.role_highlights?.focus_recommendation ||
                'Your multi-agent ecosystem is actively balancing tasks, habits, and focus schedules across roles.'}
            </p>

            {/* Quick Metrics Bar */}
            <div className="flex flex-wrap items-center justify-center md:justify-start gap-4 pt-2">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-950/60 border border-slate-800">
                <span className="text-[11px] text-slate-400">Productivity Score:</span>
                <span className={`text-sm font-bold font-mono ${scoreColor}`}>
                  {summary.productivity_score}%
                </span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-950/60 border border-slate-800">
                <span className="text-[11px] text-slate-400">Pending Tasks:</span>
                <span className="text-sm font-bold font-mono text-slate-200">
                  {summary.metrics.pending_tasks}
                </span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-950/60 border border-slate-800">
                <span className="text-[11px] text-slate-400">Habits Logged Today:</span>
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
              size={200}
              onClick={() => onNavigateTab('assistant')}
            />
          </div>
        </div>
      </div>

      {/* 2. Role Switcher Tabs */}
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

      {/* 3. Main Grid: Priority Tasks + Calendar Timeline + Role Specialization */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Priorities & Today's Plan */}
        <div className="lg:col-span-2 space-y-6">
          {/* Priority Tasks Card */}
          <div className="rounded-3xl bg-slate-900/70 border border-slate-800 p-6 backdrop-blur-xl">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400">
                  <CheckCircle2 className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">Today's High Priorities</h3>
                  <p className="text-[11px] text-slate-400">Calculated from deadlines and active role</p>
                </div>
              </div>
              <button
                onClick={() => onNavigateTab('tasks')}
                className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1 cursor-pointer"
              >
                View all tasks <ChevronRight className="w-3.5 h-3.5" />
              </button>
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

          {/* AI Daily Plan Timeline */}
          <div className="rounded-3xl bg-slate-900/70 border border-slate-800 p-6 backdrop-blur-xl">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-violet-500/10 text-violet-400">
                  <Clock className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">Daily Focus Schedule</h3>
                  <p className="text-[11px] text-slate-400">Optimized time-blocking by ScheduleOptimizerAgent</p>
                </div>
              </div>
              <button
                onClick={() => onNavigateTab('calendar')}
                className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1 cursor-pointer"
              >
                Calendar <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <p className="text-xs text-slate-300 mb-4 italic bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
              "{summary.daily_plan.summary}"
            </p>

            <div className="space-y-2">
              {summary.daily_plan.blocks.length === 0 ? (
                <div className="text-xs text-slate-500 text-center py-4">
                  No schedule blocks generated yet. Open the AI Assistant and type "Plan my day".
                </div>
              ) : (
                summary.daily_plan.blocks.map((block, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-3 rounded-xl bg-slate-950/70 border border-slate-800 text-xs"
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-indigo-400 text-[11px]">{block.time}</span>
                      <span className="font-medium text-slate-200">{block.title}</span>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-slate-900 text-slate-400 capitalize">
                      {block.role}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right Col: Role Specialization & Habits & Approvals */}
        <div className="space-y-6">
          {/* Role Specialization Highlight Card */}
          <div className="rounded-3xl bg-gradient-to-br from-indigo-950/40 via-slate-900/80 to-slate-900/80 border border-indigo-500/30 p-6 backdrop-blur-xl">
            <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs uppercase tracking-wider mb-2">
              <Compass className="w-4 h-4" />
              <span>{summary.role_highlights?.title || 'Role Intelligence'}</span>
            </div>
            <p className="text-xs text-slate-300 mb-4">
              {summary.role_highlights?.focus_recommendation}
            </p>
            {summary.role_highlights?.exam_alerts && summary.role_highlights.exam_alerts.length > 0 && (
              <div className="p-3 rounded-xl bg-rose-950/30 border border-rose-500/40 text-xs text-rose-200 mb-3">
                <span className="font-bold">Urgent Exam Alert:</span>{' '}
                {summary.role_highlights.exam_alerts.join(', ')}
              </div>
            )}
          </div>

          {/* Daily Habits & Streaks */}
          <div className="rounded-3xl bg-slate-900/70 border border-slate-800 p-6 backdrop-blur-xl">
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

          {/* Goal Momentum Progress */}
          <div className="rounded-3xl bg-slate-900/70 border border-slate-800 p-6 backdrop-blur-xl">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4 text-emerald-400" />
                <h3 className="text-sm font-bold text-white">Active Goals</h3>
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
