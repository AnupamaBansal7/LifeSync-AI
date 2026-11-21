import React, { useState } from 'react';
import {
  Calendar as CalendarIcon,
  Lock,
  Plus,
  Sparkles,
  X,
} from 'lucide-react';
import type { CalendarEvent, DailyPlan } from '../../types';

interface CalendarViewProps {
  events: CalendarEvent[];
  dailyPlans: DailyPlan[];
  activeRole: string;
  onCreateEvent: (event: any) => Promise<void>;
  onDeleteEvent: (id: string) => Promise<void>;
  onGeneratePlan: () => void;
}

export const CalendarView: React.FC<CalendarViewProps> = ({
  events,
  dailyPlans,
  activeRole,
  onCreateEvent,
  onDeleteEvent,
  onGeneratePlan,
}) => {
  const [viewMode, setViewMode] = useState<'day' | 'week' | 'month' | 'agenda'>('agenda');
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Form states
  const [title, setTitle] = useState('');
  const [eventType, setEventType] = useState<'meeting' | 'time_block' | 'exam' | 'deadline' | 'personal'>('time_block');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [roleContext, setRoleContext] = useState(activeRole === 'all' ? 'personal' : activeRole);
  const [isLocked, setIsLocked] = useState(false);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !startTime || !endTime) return;

    await onCreateEvent({
      title,
      event_type: eventType,
      start_time: new Date(startTime).toISOString(),
      end_time: new Date(endTime).toISOString(),
      role_context: roleContext,
      is_locked: isLocked,
    });

    setTitle('');
    setShowCreateModal(false);
  };

  const getEventTypeColor = (type: string) => {
    switch (type) {
      case 'exam':
        return 'bg-rose-500/15 border-rose-500/40 text-rose-300';
      case 'meeting':
        return 'bg-blue-500/15 border-blue-500/40 text-blue-300';
      case 'deadline':
        return 'bg-amber-500/15 border-amber-500/40 text-amber-300';
      case 'personal':
        return 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300';
      case 'time_block':
      default:
        return 'bg-indigo-500/15 border-indigo-500/40 text-indigo-300';
    }
  };

  return (
    <div className="space-y-6 pb-12 select-none">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-white">Smart Calendar & Time Blocks</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Conflict-aware scheduling balancing fixed meetings, study slots, and deep work blocks.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* View Mode Switcher */}
          <div className="flex items-center rounded-xl bg-slate-900 border border-slate-800 p-0.5">
            {(['agenda', 'day', 'week', 'month'] as const).map((mode) => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                className={`px-2.5 py-1 text-xs font-semibold rounded-lg capitalize transition cursor-pointer ${
                  viewMode === mode
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {mode}
              </button>
            ))}
          </div>

          {/* AI Plan Trigger */}
          <button
            onClick={onGeneratePlan}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-indigo-600/15 hover:bg-indigo-600/25 border border-indigo-500/30 text-indigo-300 text-xs font-semibold transition cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>AI Plan My Day</span>
          </button>

          {/* New Event Button */}
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Add Event</span>
          </button>
        </div>
      </div>

      {/* Main Agenda & Latest Daily Plan Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Scheduled Events Stream */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <CalendarIcon className="w-4 h-4 text-indigo-400" />
              <span>Upcoming Scheduled Commitments</span>
            </h3>
            <span className="text-xs font-mono text-slate-400">{events.length} events scheduled</span>
          </div>

          <div className="space-y-3">
            {events.length === 0 ? (
              <div className="text-center py-12 text-xs text-slate-400 bg-slate-900/40 rounded-3xl border border-slate-800 p-8">
                No calendar commitments scheduled. Click "Add Event" or let the AI orchestrator plan focus blocks.
              </div>
            ) : (
              events.map((ev) => (
                <div
                  key={ev.id}
                  className={`p-4 rounded-2xl border flex items-center justify-between gap-4 transition-all ${getEventTypeColor(
                    ev.event_type
                  )}`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-xs sm:text-sm text-white">{ev.title}</span>
                      {ev.is_locked && (
                        <span
                          className="p-0.5 rounded text-amber-400"
                          title="Locked Event: Auto-rescheduler will never move this"
                        >
                          <Lock className="w-3 h-3" />
                        </span>
                      )}
                    </div>

                    <div className="flex flex-wrap items-center gap-3 text-[11px] opacity-80 font-mono">
                      <span>{new Date(ev.start_time).toLocaleDateString()}</span>
                      <span>
                        {new Date(ev.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} -{' '}
                        {new Date(ev.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                      <span className="uppercase text-[9px] px-1.5 py-0.2 rounded bg-slate-950/50">
                        {ev.event_type}
                      </span>
                      <span className="capitalize text-slate-300">{ev.role_context}</span>
                    </div>
                  </div>

                  <button
                    onClick={() => onDeleteEvent(ev.id)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 transition cursor-pointer"
                    title="Remove event"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* AI Daily Plan Highlights */}
        <div className="rounded-3xl bg-slate-900/70 border border-slate-800 p-6 backdrop-blur-xl space-y-4">
          <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs uppercase tracking-wider">
            <Sparkles className="w-4 h-4" /> AI Synthesized Timetable
          </div>

          {dailyPlans.length > 0 ? (
            <div className="space-y-3">
              <p className="text-xs text-slate-300 italic bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                "{dailyPlans[0].summary}"
              </p>
              <div className="space-y-2">
                {dailyPlans[0].schedule_blocks.map((block, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 text-xs flex items-center justify-between"
                  >
                    <div>
                      <div className="font-semibold text-slate-200">{block.title}</div>
                      <div className="text-[10px] text-indigo-400 font-mono">{block.time}</div>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-slate-900 font-mono uppercase text-slate-400">
                      {block.role}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-400 py-6 text-center">
              No daily timetable generated yet. Click "AI Plan My Day" above to synthesize one.
            </p>
          )}
        </div>
      </div>

      {/* Add Event Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="w-full max-w-md rounded-3xl bg-slate-900 border border-slate-800 shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="font-bold text-sm text-white">Schedule Calendar Event</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Title</label>
                <input
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Distributed Systems Exam / Architecture Sprint"
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Event Type</label>
                  <select
                    value={eventType}
                    onChange={(e: any) => setEventType(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white capitalize"
                  >
                    <option value="time_block">Focus Time Block</option>
                    <option value="meeting">Meeting</option>
                    <option value="exam">Academic Exam</option>
                    <option value="deadline">Project Deadline</option>
                    <option value="personal">Personal Life</option>
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
                <label className="block text-xs text-slate-400 mb-1">Start Time</label>
                <input
                  type="datetime-local"
                  required
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
                />
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1">End Time</label>
                <input
                  type="datetime-local"
                  required
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="lockCheck"
                  checked={isLocked}
                  onChange={(e) => setIsLocked(e.target.checked)}
                  className="w-4 h-4 rounded text-indigo-600 bg-slate-950 border-slate-800"
                />
                <label htmlFor="lockCheck" className="text-xs text-slate-300">
                  Lock Event (Protects against auto-rescheduling)
                </label>
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
                  Confirm Event
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
