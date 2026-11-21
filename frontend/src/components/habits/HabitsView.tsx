import React, { useState } from 'react';
import {
  Check,
  Clock,
  Flame,
  Plus,
  X,
} from 'lucide-react';
import type { Habit } from '../../types';

interface HabitsViewProps {
  habits: Habit[];
  activeRole: string;
  onCreateHabit: (habit: any) => Promise<void>;
  onLogHabit: (id: string) => Promise<void>;
}

export const HabitsView: React.FC<HabitsViewProps> = ({
  habits,
  activeRole,
  onCreateHabit,
  onLogHabit,
}) => {
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Form states
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [frequency, setFrequency] = useState<'daily' | 'weekly' | 'custom'>('daily');
  const [targetDays, setTargetDays] = useState(7);
  const [reminderTime, setReminderTime] = useState('08:00');
  const [roleContext, setRoleContext] = useState(activeRole === 'all' ? 'personal' : activeRole);

  const daysOfWeek = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    await onCreateHabit({
      title,
      description,
      frequency,
      target_days_per_week: targetDays,
      reminder_time: reminderTime,
      role_context: roleContext,
    });

    setTitle('');
    setShowCreateModal(false);
  };

  return (
    <div className="space-y-6 pb-12 select-none">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-white">Habit & Routine Consistency</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Positive habit formation powered by progressive streak momentum and zero punishment.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>New Habit</span>
        </button>
      </div>

      {/* Motivational Reinforcement Banner */}
      <div className="p-4 rounded-3xl bg-gradient-to-r from-indigo-950/40 via-amber-950/20 to-slate-900 border border-amber-500/30 flex items-center gap-3">
        <div className="p-2.5 rounded-2xl bg-amber-500/20 text-amber-400 shrink-0">
          <Flame className="w-5 h-5 fill-amber-400" />
        </div>
        <div>
          <h4 className="text-xs font-bold text-amber-200">Consistency Over Perfection</h4>
          <p className="text-[11px] text-slate-300 mt-0.5">
            Missing one day does not erase your identity. Check off today's habits to reinforce neural pathways and sustain momentum.
          </p>
        </div>
      </div>

      {/* Habits List & 7-Day Consistency Grid */}
      <div className="space-y-3">
        {habits.length === 0 ? (
          <div className="text-center py-16 text-xs text-slate-400 bg-slate-900/40 rounded-3xl border border-slate-800 p-8">
            No habits tracked yet. Click "New Habit" to start building your daily wellness and focus routines.
          </div>
        ) : (
          habits.map((habit) => (
            <div
              key={habit.id}
              className="p-5 rounded-3xl bg-slate-900/70 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4 backdrop-blur-xl hover:border-slate-700 transition shadow-sm"
            >
              <div className="flex items-center gap-4">
                <button
                  onClick={() => onLogHabit(habit.id)}
                  className={`w-8 h-8 rounded-2xl border flex items-center justify-center transition-all cursor-pointer shrink-0 ${
                    habit.completed_today
                      ? 'bg-amber-500 text-slate-950 border-amber-400 shadow-md shadow-amber-500/30 scale-105'
                      : 'border-slate-700 hover:border-amber-400 text-transparent'
                  }`}
                  title={habit.completed_today ? 'Completed today!' : 'Click to complete for today'}
                >
                  <Check className="w-5 h-5 stroke-[3]" />
                </button>

                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-white">{habit.title}</span>
                    <span className="text-[10px] font-mono px-2 py-0.2 rounded bg-slate-950 text-indigo-300 capitalize">
                      {habit.role_context}
                    </span>
                  </div>
                  {habit.description && (
                    <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">{habit.description}</p>
                  )}
                  <div className="flex items-center gap-3 mt-1 text-[11px] text-slate-400">
                    <span>{habit.frequency} ({habit.target_days_per_week}x/week)</span>
                    {habit.reminder_time && (
                      <span className="flex items-center gap-1 font-mono text-slate-400">
                        <Clock className="w-3 h-3 text-indigo-400" /> {habit.reminder_time}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Streaks & Consistency */}
              <div className="flex items-center gap-6 self-end sm:self-center">
                {/* Visual 7-day indicators */}
                <div className="hidden sm:flex items-center gap-1.5">
                  {daysOfWeek.map((day, idx) => {
                    const isToday = idx === 6; // visual mockup
                    return (
                      <div key={day} className="flex flex-col items-center gap-1">
                        <span className="text-[9px] text-slate-500 font-mono">{day}</span>
                        <div
                          className={`w-3.5 h-3.5 rounded-md border ${
                            isToday && habit.completed_today
                              ? 'bg-amber-400 border-amber-300 shadow-sm'
                              : 'bg-slate-950 border-slate-800'
                          }`}
                        />
                      </div>
                    );
                  })}
                </div>

                <div className="flex items-center gap-4 text-right">
                  <div>
                    <div className="flex items-center gap-1 text-amber-400 font-bold font-mono text-base">
                      <Flame className="w-4 h-4 fill-amber-400" />
                      <span>{habit.current_streak}d</span>
                    </div>
                    <span className="text-[10px] text-slate-500 font-mono">Current Streak</span>
                  </div>
                  <div>
                    <div className="text-slate-300 font-bold font-mono text-base">
                      {habit.longest_streak}d
                    </div>
                    <span className="text-[10px] text-slate-500 font-mono">Best Streak</span>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Create Habit Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="w-full max-w-md rounded-3xl bg-slate-900 border border-slate-800 shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="font-bold text-sm text-white">Create Daily / Weekly Habit</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Habit Title</label>
                <input
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Read 20 pages of research paper / 30m cardio"
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
                />
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1">Description / Cue</label>
                <input
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="After morning coffee, before opening laptop..."
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Frequency</label>
                  <select
                    value={frequency}
                    onChange={(e: any) => setFrequency(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white capitalize"
                  >
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="custom">Custom</option>
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

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Target Days / Week</label>
                  <input
                    type="number"
                    min={1}
                    max={7}
                    value={targetDays}
                    onChange={(e) => setTargetDays(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Reminder Time</label>
                  <input
                    type="time"
                    value={reminderTime}
                    onChange={(e) => setReminderTime(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
                  />
                </div>
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
                  Create Habit
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
