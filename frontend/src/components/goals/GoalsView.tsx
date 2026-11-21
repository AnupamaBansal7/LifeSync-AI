import React, { useState } from 'react';
import {
  CheckCircle2,
  Circle,
  Plus,
  Sparkles,
  X,
} from 'lucide-react';
import type { Goal } from '../../types';

interface GoalsViewProps {
  goals: Goal[];
  activeRole: string;
  onCreateGoal: (goal: any) => Promise<void>;
  onToggleMilestone: (goalId: string, milestoneId: string, current: boolean) => Promise<void>;
  onAIDecomposeGoal: (goalTitle: string) => void;
}

export const GoalsView: React.FC<GoalsViewProps> = ({
  goals,
  activeRole,
  onCreateGoal,
  onToggleMilestone,
  onAIDecomposeGoal,
}) => {
  const [horizonFilter, setHorizonFilter] = useState<'all' | 'short_term' | 'long_term'>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Form states
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [horizon, setHorizon] = useState<'short_term' | 'long_term'>('short_term');
  const [roleContext, setRoleContext] = useState(activeRole === 'all' ? 'personal' : activeRole);
  const [milestonesInput, setMilestonesInput] = useState('Phase 1: Architecture, Phase 2: Implementation, Phase 3: Verification');

  const filteredGoals = goals.filter((g) => {
    if (horizonFilter !== 'all' && g.horizon !== horizonFilter) return false;
    return true;
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    const milestones = milestonesInput
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean)
      .map((m, idx) => ({ title: m, order_index: idx }));

    await onCreateGoal({
      title,
      description,
      horizon,
      role_context: roleContext,
      milestones,
    });

    setTitle('');
    setDescription('');
    setShowCreateModal(false);
  };

  return (
    <div className="space-y-6 pb-12 select-none">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-white">Goals & Milestones Roadmap</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Hierarchical OKRs broken down into atomic, measurable execution milestones.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Horizon Filter */}
          <div className="flex items-center p-1 rounded-xl bg-slate-900 border border-slate-800">
            <button
              onClick={() => setHorizonFilter('all')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
                horizonFilter === 'all' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              All Horizons
            </button>
            <button
              onClick={() => setHorizonFilter('short_term')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
                horizonFilter === 'short_term' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Short-Term
            </button>
            <button
              onClick={() => setHorizonFilter('long_term')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
                horizonFilter === 'long_term' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Long-Term
            </button>
          </div>

          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>New Goal</span>
          </button>
        </div>
      </div>

      {/* Goals Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filteredGoals.length === 0 ? (
          <div className="col-span-2 text-center py-16 text-xs text-slate-400 bg-slate-900/40 rounded-3xl border border-slate-800 p-8">
            No goals found for this horizon. Click "New Goal" to establish your next milestone.
          </div>
        ) : (
          filteredGoals.map((goal) => (
            <div
              key={goal.id}
              className="rounded-3xl bg-slate-900/70 border border-slate-800 p-6 backdrop-blur-xl space-y-4 shadow-md hover:border-slate-700 transition"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-500/15 text-indigo-300 capitalize font-bold">
                      {goal.horizon.replace('_', ' ')}
                    </span>
                    <span className="text-[10px] text-slate-400 capitalize">
                      {goal.role_context}
                    </span>
                  </div>
                  <h3 className="font-bold text-sm sm:text-base text-white">{goal.title}</h3>
                  {goal.description && (
                    <p className="text-xs text-slate-400 leading-relaxed">{goal.description}</p>
                  )}
                </div>

                <button
                  onClick={() => onAIDecomposeGoal(goal.title)}
                  className="px-2.5 py-1 rounded-lg bg-indigo-600/15 hover:bg-indigo-600/25 border border-indigo-500/30 text-indigo-300 text-[11px] font-semibold flex items-center gap-1 cursor-pointer shrink-0 transition"
                  title="Generate milestones and tasks"
                >
                  <Sparkles className="w-3 h-3 text-indigo-400" /> AI Breakdown
                </button>
              </div>

              {/* Progress Bar */}
              <div className="space-y-1.5 pt-2">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400 font-medium">Completion Progress</span>
                  <span className="font-mono text-emerald-400 font-bold">
                    {goal.progress_percent}%
                  </span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-950 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-indigo-500 via-violet-500 to-emerald-400 rounded-full transition-all duration-500"
                    style={{ width: `${goal.progress_percent}%` }}
                  />
                </div>
              </div>

              {/* Milestones Checklist */}
              <div className="space-y-2 pt-2 border-t border-slate-800/80">
                <div className="text-[11px] font-semibold text-slate-400 flex items-center justify-between">
                  <span>Key Milestones ({goal.milestones?.length || 0})</span>
                  <span>
                    {goal.milestones?.filter((m) => m.is_completed).length || 0} completed
                  </span>
                </div>

                <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                  {goal.milestones?.map((m) => (
                    <div
                      key={m.id}
                      onClick={() => onToggleMilestone(goal.id, m.id, m.is_completed)}
                      className={`p-2.5 rounded-xl border flex items-center gap-2.5 text-xs transition cursor-pointer ${
                        m.is_completed
                          ? 'bg-slate-950/40 border-slate-800 text-slate-500 line-through'
                          : 'bg-slate-950/80 border-slate-800 text-slate-200 hover:border-slate-700'
                      }`}
                    >
                      <button className="shrink-0 text-indigo-400">
                        {m.is_completed ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                        ) : (
                          <Circle className="w-4 h-4 text-slate-600" />
                        )}
                      </button>
                      <span className="truncate">{m.title}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Create Goal Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="w-full max-w-lg rounded-3xl bg-slate-900 border border-slate-800 shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="font-bold text-sm text-white">Create New Strategic Goal</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Goal Title</label>
                <input
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Master Distributed Systems Architecture"
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
                />
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1">Description / Motivation</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Why this goal matters and what success looks like..."
                  rows={2}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Horizon</label>
                  <select
                    value={horizon}
                    onChange={(e: any) => setHorizon(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white capitalize"
                  >
                    <option value="short_term">Short-Term (1-3 months)</option>
                    <option value="long_term">Long-Term (6-12 months)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Role Context</label>
                  <select
                    value={roleContext}
                    onChange={(e) => setRoleContext(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white capitalize"
                  >
                    <option value="personal">Personal</option>
                    <option value="student">Student</option>
                    <option value="professional">Professional</option>
                    <option value="entrepreneur">Entrepreneur</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1">Initial Milestones (comma-separated)</label>
                <input
                  value={milestonesInput}
                  onChange={(e) => setMilestonesInput(e.target.value)}
                  placeholder="Phase 1, Phase 2, Phase 3"
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-xl text-xs text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
                >
                  Create Goal
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
