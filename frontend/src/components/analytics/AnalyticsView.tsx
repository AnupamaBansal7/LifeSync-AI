import React from 'react';
import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import {
  Activity,
  CheckCircle2,
  Flame,
  PieChart as PieIcon,
  Sparkles,
  Target,
} from 'lucide-react';

interface AnalyticsProps {
  overview: any;
  activeRole: string;
}

export const AnalyticsView: React.FC<AnalyticsProps> = ({ overview, activeRole }) => {
  if (!overview) {
    return (
      <div className="text-center py-16 text-xs text-slate-400">
        Loading analytics engine...
      </div>
    );
  }

  const roleDistributionData = Object.entries(overview.tasks?.by_role || {}).map(([role, count]) => ({
    name: role.toUpperCase(),
    value: Number(count),
  }));

  const COLORS = ['#6366f1', '#38bdf8', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'];

  const completionRate = overview.tasks?.completion_rate || 0;
  const avgGoalProgress = overview.goals?.average_progress || 0;

  return (
    <div className="space-y-6 pb-12 select-none">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs uppercase tracking-wider mb-1">
            <Activity className="w-4 h-4" /> Intelligence & Progress Analytics
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-white">Productivity & Role Distribution</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Calculated from real database records across your active responsibilities.
          </p>
        </div>
        <div className="px-3 py-1.5 rounded-xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold self-start sm:self-auto">
          Active Lens: <span className="uppercase font-mono">{activeRole}</span>
        </div>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-5 rounded-3xl bg-slate-900/70 border border-slate-800 backdrop-blur-xl">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span>Task Completion</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">{completionRate}%</div>
          <div className="text-[11px] text-slate-500 mt-1">
            {overview.tasks?.completed} of {overview.tasks?.total} finished
          </div>
        </div>

        <div className="p-5 rounded-3xl bg-slate-900/70 border border-slate-800 backdrop-blur-xl">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span>Goal Momentum</span>
            <Target className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">{avgGoalProgress}%</div>
          <div className="text-[11px] text-slate-500 mt-1">
            Across {overview.goals?.total} strategic goals
          </div>
        </div>

        <div className="p-5 rounded-3xl bg-slate-900/70 border border-slate-800 backdrop-blur-xl">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span>Top Streak</span>
            <Flame className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-amber-400">
            {overview.habits?.top_streak}d
          </div>
          <div className="text-[11px] text-slate-500 mt-1">
            {overview.habits?.active_count} active habits tracked
          </div>
        </div>

        <div className="p-5 rounded-3xl bg-slate-900/70 border border-slate-800 backdrop-blur-xl">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span>Vector Memories</span>
            <Sparkles className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-cyan-300">
            {overview.ai?.memories_stored}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">
            Indexed with pgvector
          </div>
        </div>
      </div>

      {/* Visual Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Workload Distribution By Role */}
        <div className="p-6 rounded-3xl bg-slate-900/70 border border-slate-800 backdrop-blur-xl space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <PieIcon className="w-4 h-4 text-indigo-400" />
              <span>Workload Distribution Across Roles</span>
            </h3>
            <span className="text-[11px] font-mono text-slate-400">By task count</span>
          </div>

          <div className="h-64 flex items-center justify-center">
            {roleDistributionData.length === 0 ? (
              <p className="text-xs text-slate-500">No role data available yet.</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={roleDistributionData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {roleDistributionData.map((_entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#1e293b',
                      borderRadius: '1rem',
                      fontSize: '12px',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Legend */}
          <div className="flex flex-wrap items-center justify-center gap-4 pt-2 border-t border-slate-800/60">
            {roleDistributionData.map((entry, index) => (
              <div key={entry.name} className="flex items-center gap-1.5 text-xs">
                <span
                  className="w-2.5 h-2.5 rounded-full"
                  style={{ backgroundColor: COLORS[index % COLORS.length] }}
                />
                <span className="text-slate-300 font-mono text-[11px]">
                  {entry.name}: {entry.value}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* AI Reflection & Progress Review */}
        <div className="p-6 rounded-3xl bg-slate-900/70 border border-slate-800 backdrop-blur-xl space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs uppercase tracking-wider mb-2">
              <Sparkles className="w-4 h-4" /> ReflectionCoachAgent Debrief
            </div>
            <h3 className="text-base font-bold text-white mb-2">Productivity Equilibrium Analysis</h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              Your task completion rate is currently at <strong>{completionRate}%</strong>.
              Habits show consistent momentum with a top streak of <strong>{overview.habits?.top_streak} days</strong>.
              AI orchestration has executed <strong>{overview.ai?.agent_runs} autonomous pipeline cycles</strong>, ensuring scheduling balance between your personal wellness and active responsibilities.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-indigo-950/20 border border-indigo-500/30 space-y-2">
            <span className="text-xs font-bold text-indigo-300">Actionable Architectural Suggestion:</span>
            <p className="text-[11px] text-slate-300 leading-relaxed">
              Maintain daily habit check-ins in the evening to sustain momentum. Consider setting a calendar block tomorrow morning for incomplete high-priority sprint tasks.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
