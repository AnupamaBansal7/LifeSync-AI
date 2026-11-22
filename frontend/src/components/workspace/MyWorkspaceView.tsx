import React, { useEffect, useState } from 'react';
import {
  Calendar,
  CheckCircle2,
  ChevronRight,
  Flame,
  FolderGit2,
  Layers,
  Lightbulb,
  Plus,
  Sparkles,
  StickyNote,
  Target,
  Workflow,
  X,
} from 'lucide-react';
import { api } from '../../lib/api';
import type { Project, Role, User } from '../../types';

interface MyWorkspaceViewProps {
  user: User | null;
  rolesCatalog: Role[];
  activeRole: string;
  onSelectRole: (role: string) => void;
  onNavigateTab: (tab: any) => void;
}

export const MyWorkspaceView: React.FC<MyWorkspaceViewProps> = ({
  user,
  rolesCatalog: _rolesCatalog,
  activeRole,
  onSelectRole,
  onNavigateTab,
}) => {
  const userRoles = user?.roles || [];

  // Project Workspaces & Brain State
  const [projects, setProjects] = useState<Project[]>([]);
  const [loadingProjects, setLoadingProjects] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');
  const [newProjectDate, setNewProjectDate] = useState('');
  const [activeProjectNoteModal, setActiveProjectNoteModal] = useState<string | null>(null);
  const [noteText, setNoteText] = useState('');
  const [activeProjectDecisionModal, setActiveProjectDecisionModal] = useState<string | null>(null);
  const [decisionText, setDecisionText] = useState('');
  const [decisionRationale, setDecisionRationale] = useState('');

  const fetchProjects = async () => {
    setLoadingProjects(true);
    try {
      const res = await api.get('/projects', {
        params: activeRole !== 'all' ? { role_context: activeRole } : undefined,
      });
      setProjects(res.data || []);
    } catch {
      // Offline fallback mock data
      setProjects([
        {
          id: 'proj-1',
          user_id: user?.id || 'demo-user',
          name: 'LifeSync AI 4.0 Architecture',
          description: 'Autonomous Multi-Agent Personal Life Management Operating System',
          role_context: activeRole,
          status: 'active',
          target_date: '2026-12-31',
          notes: [
            'DAG workflow execution engine with step-level checkpointing and approval isolation.',
            'Computer Use Agent integrated with Win32 window state inspection.',
          ],
          decisions: [
            {
              decision: 'Use Win32 ctypes for zero-latency active window inspection',
              date: '2026-11-21',
              rationale: 'Avoids heavy native extensions while remaining fully compatible with Windows.',
            },
          ],
        },
      ]);
    } finally {
      setLoadingProjects(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [activeRole]);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;

    try {
      const res = await api.post('/projects', {
        name: newProjectName,
        description: newProjectDesc,
        role_context: activeRole !== 'all' ? activeRole : 'personal',
        target_date: newProjectDate || null,
      });
      setProjects((prev) => [res.data, ...prev]);
      setShowCreateModal(false);
      setNewProjectName('');
      setNewProjectDesc('');
      setNewProjectDate('');
    } catch {
      const fallbackProj: Project = {
        id: `proj-${Date.now()}`,
        user_id: user?.id || 'demo-user',
        name: newProjectName,
        description: newProjectDesc,
        role_context: activeRole,
        status: 'active',
        target_date: newProjectDate || undefined,
        notes: [],
        decisions: [],
      };
      setProjects((prev) => [fallbackProj, ...prev]);
      setShowCreateModal(false);
      setNewProjectName('');
      setNewProjectDesc('');
      setNewProjectDate('');
    }
  };

  const handleAddNote = async (projectId: string) => {
    if (!noteText.trim()) return;
    try {
      await api.post(`/projects/${projectId}/notes`, { note: noteText });
      setProjects((prev) =>
        prev.map((p) => (p.id === projectId ? { ...p, notes: [...p.notes, noteText] } : p))
      );
    } catch {
      setProjects((prev) =>
        prev.map((p) => (p.id === projectId ? { ...p, notes: [...p.notes, noteText] } : p))
      );
    }
    setNoteText('');
    setActiveProjectNoteModal(null);
  };

  const handleAddDecision = async (projectId: string) => {
    if (!decisionText.trim()) return;
    const newDec = {
      decision: decisionText,
      rationale: decisionRationale,
      date: new Date().toISOString().split('T')[0],
    };
    try {
      await api.post(`/projects/${projectId}/decisions`, newDec);
      setProjects((prev) =>
        prev.map((p) => (p.id === projectId ? { ...p, decisions: [...p.decisions, newDec] } : p))
      );
    } catch {
      setProjects((prev) =>
        prev.map((p) => (p.id === projectId ? { ...p, decisions: [...p.decisions, newDec] } : p))
      );
    }
    setDecisionText('');
    setDecisionRationale('');
    setActiveProjectDecisionModal(null);
  };

  return (
    <div className="space-y-8 pb-12 select-none">
      {/* Header */}
      <div className="pb-4 border-b border-slate-800/80">
        <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs uppercase tracking-wider mb-1">
          <Layers className="w-4 h-4" /> Multi-Role Hub & Knowledge Workspaces
        </div>
        <h2 className="text-xl sm:text-2xl font-bold text-white">Workspaces & Knowledge Brain</h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Seamlessly balance multiple domains of your life, project roadmaps, and architectural decisions.
        </p>
      </div>

      {/* Role Cards Grid */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wide flex items-center gap-2">
            <Layers className="w-4 h-4 text-indigo-400" /> Active Identities & Roles
          </h3>
          <span className="text-xs text-slate-400 font-mono">
            {userRoles.length} Roles Configured
          </span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {userRoles.map((ur) => {
            const roleSlug = ur.role?.slug || ur.role_id;
            const roleName = ur.role?.name || roleSlug;
            const isSelected = activeRole === roleSlug;

            return (
              <div
                key={ur.id}
                className={`p-6 rounded-3xl border transition-all flex flex-col justify-between space-y-4 backdrop-blur-xl ${
                  isSelected
                    ? 'bg-gradient-to-br from-indigo-950/60 via-slate-900 to-slate-900 border-indigo-500 shadow-xl shadow-indigo-500/10'
                    : 'bg-slate-900/70 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-slate-950 text-indigo-300 font-bold uppercase">
                      {ur.is_primary ? 'PRIMARY ROLE' : 'ACTIVE ROLE'}
                    </span>
                    {isSelected && (
                      <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    )}
                  </div>

                  <h3 className="font-bold text-base text-white capitalize">{roleName}</h3>
                  <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                    {ur.role?.description || 'Custom role workspace managed by LifeSync.'}
                  </p>

                  {/* Metadata details if present */}
                  {ur.context_metadata && Object.keys(ur.context_metadata).length > 0 && (
                    <div className="mt-3 p-2.5 rounded-xl bg-slate-950/70 border border-slate-800/80 text-[11px] text-slate-300 space-y-1">
                      {Object.entries(ur.context_metadata).map(([k, v]) => (
                        <div key={k} className="flex justify-between">
                          <span className="text-slate-400 capitalize">{k.replace('_', ' ')}:</span>
                          <span className="font-medium text-slate-200 truncate max-w-[140px]">
                            {String(v)}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="pt-2 flex items-center justify-between">
                  <button
                    onClick={() => onSelectRole(roleSlug)}
                    className={`px-4 py-2 rounded-xl text-xs font-semibold transition cursor-pointer ${
                      isSelected
                        ? 'bg-indigo-600 text-white shadow-md'
                        : 'bg-slate-950 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800'
                    }`}
                  >
                    {isSelected ? 'Currently Viewing' : 'Switch to this Role'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Project Workspaces & Knowledge Brain */}
      <section className="space-y-4 pt-2">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wide flex items-center gap-2">
              <FolderGit2 className="w-4 h-4 text-violet-400" /> Project Workspaces & Knowledge Brain
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Dedicated work contexts for your initiatives, architectural decisions, and continuous notes.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => onNavigateTab('assistant')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-purple-950/60 hover:bg-purple-900/60 border border-purple-500/40 text-purple-200 text-xs font-semibold shadow-lg shadow-purple-950/40 transition cursor-pointer"
              title="Start conversational zero-form project intake session"
            >
              <Sparkles className="w-3.5 h-3.5 text-purple-400 animate-pulse" />
              <span>Plan with AI (No Forms)</span>
            </button>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 transition cursor-pointer"
            >
              <Plus className="w-4 h-4" /> New Project
            </button>
          </div>
        </div>

        {loadingProjects ? (
          <div className="p-8 text-center text-xs text-slate-400 bg-slate-900/50 rounded-2xl border border-slate-800 animate-pulse">
            Loading Knowledge Workspaces...
          </div>
        ) : projects.length === 0 ? (
          <div className="p-8 text-center bg-slate-900/40 rounded-3xl border border-slate-800/80">
            <FolderGit2 className="w-8 h-8 text-slate-500 mx-auto mb-2" />
            <div className="text-sm font-medium text-slate-300">No projects yet in this context</div>
            <div className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Create a project workspace to track milestones, decisions, tasks, and memory.
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-4 px-4 py-2 bg-indigo-600/80 hover:bg-indigo-600 text-white text-xs rounded-xl font-semibold transition cursor-pointer"
            >
              Create First Project
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {projects.map((proj) => (
              <div
                key={proj.id}
                className="p-5 rounded-3xl bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition flex flex-col justify-between space-y-4"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-violet-950/80 text-violet-300 border border-violet-800/50 font-bold uppercase">
                      {proj.status}
                    </span>
                    {proj.target_date && (
                      <span className="text-[11px] text-slate-400 font-mono">
                        Target: {proj.target_date}
                      </span>
                    )}
                  </div>
                  <h4 className="font-bold text-base text-white">{proj.name}</h4>
                  {proj.description && (
                    <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                      {proj.description}
                    </p>
                  )}

                  {/* Architectural Decisions */}
                  {proj.decisions && proj.decisions.length > 0 && (
                    <div className="mt-4 space-y-2">
                      <div className="flex items-center gap-1.5 text-[11px] font-bold text-amber-300 uppercase tracking-wider">
                        <Lightbulb className="w-3.5 h-3.5" /> Architectural Decisions
                      </div>
                      <div className="space-y-1.5">
                        {proj.decisions.map((dec, i) => (
                          <div
                            key={i}
                            className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800/80 text-xs text-slate-200"
                          >
                            <div className="font-medium text-white">{dec.decision}</div>
                            {dec.rationale && (
                              <div className="text-[11px] text-slate-400 mt-0.5">{dec.rationale}</div>
                            )}
                            {dec.date && (
                              <div className="text-[10px] text-slate-500 font-mono mt-1">
                                Recorded {dec.date}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Knowledge Notes */}
                  {proj.notes && proj.notes.length > 0 && (
                    <div className="mt-4 space-y-2">
                      <div className="flex items-center gap-1.5 text-[11px] font-bold text-indigo-300 uppercase tracking-wider">
                        <StickyNote className="w-3.5 h-3.5" /> Project Notes
                      </div>
                      <div className="space-y-1">
                        {proj.notes.map((note, idx) => (
                          <div
                            key={idx}
                            className="p-2 rounded-xl bg-slate-950/50 border border-slate-800/50 text-xs text-slate-300 flex items-start gap-2"
                          >
                            <ChevronRight className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                            <span>{note}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="pt-2 flex items-center gap-2 border-t border-slate-800/60">
                  <button
                    onClick={() => setActiveProjectNoteModal(proj.id)}
                    className="flex-1 py-1.5 px-3 rounded-xl bg-slate-950 hover:bg-slate-800 text-[11px] font-medium text-slate-300 hover:text-white border border-slate-800 transition cursor-pointer flex items-center justify-center gap-1"
                  >
                    <Plus className="w-3 h-3 text-indigo-400" /> Add Note
                  </button>
                  <button
                    onClick={() => setActiveProjectDecisionModal(proj.id)}
                    className="flex-1 py-1.5 px-3 rounded-xl bg-slate-950 hover:bg-slate-800 text-[11px] font-medium text-slate-300 hover:text-white border border-slate-800 transition cursor-pointer flex items-center justify-center gap-1"
                  >
                    <Lightbulb className="w-3 h-3 text-amber-400" /> Record Decision
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Quick Launchpad to Modules */}
      <section className="p-6 rounded-3xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl space-y-4">
        <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
          Workspace Quick Launchpad
        </h3>

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          <button
            onClick={() => onNavigateTab('tasks')}
            className="p-4 rounded-2xl bg-slate-950/70 hover:bg-indigo-950/30 border border-slate-800 hover:border-indigo-500/40 text-left transition cursor-pointer group"
          >
            <CheckCircle2 className="w-5 h-5 text-indigo-400 group-hover:scale-110 transition-transform mb-2" />
            <div className="font-bold text-xs text-white">Tasks & Kanban</div>
            <div className="text-[10px] text-slate-400 mt-0.5">Manage backlogs</div>
          </button>

          <button
            onClick={() => onNavigateTab('calendar')}
            className="p-4 rounded-2xl bg-slate-950/70 hover:bg-indigo-950/30 border border-slate-800 hover:border-indigo-500/40 text-left transition cursor-pointer group"
          >
            <Calendar className="w-5 h-5 text-indigo-400 group-hover:scale-110 transition-transform mb-2" />
            <div className="font-bold text-xs text-white">Calendar Blocks</div>
            <div className="text-[10px] text-slate-400 mt-0.5">Daily focus slots</div>
          </button>

          <button
            onClick={() => onNavigateTab('goals')}
            className="p-4 rounded-2xl bg-slate-950/70 hover:bg-indigo-950/30 border border-slate-800 hover:border-indigo-500/40 text-left transition cursor-pointer group"
          >
            <Target className="w-5 h-5 text-emerald-400 group-hover:scale-110 transition-transform mb-2" />
            <div className="font-bold text-xs text-white">Strategic Goals</div>
            <div className="text-[10px] text-slate-400 mt-0.5">Milestones & OKRs</div>
          </button>

          <button
            onClick={() => onNavigateTab('habits')}
            className="p-4 rounded-2xl bg-slate-950/70 hover:bg-indigo-950/30 border border-slate-800 hover:border-indigo-500/40 text-left transition cursor-pointer group"
          >
            <Flame className="w-5 h-5 text-amber-400 group-hover:scale-110 transition-transform mb-2" />
            <div className="font-bold text-xs text-white">Habit Streaks</div>
            <div className="text-[10px] text-slate-400 mt-0.5">Consistency matrix</div>
          </button>

          <button
            onClick={() => onNavigateTab('automations')}
            className="p-4 rounded-2xl bg-slate-950/70 hover:bg-indigo-950/30 border border-slate-800 hover:border-indigo-500/40 text-left transition cursor-pointer group"
          >
            <Workflow className="w-5 h-5 text-cyan-400 group-hover:scale-110 transition-transform mb-2" />
            <div className="font-bold text-xs text-white">Workflow Studio</div>
            <div className="text-[10px] text-slate-400 mt-0.5">DAG execution engine</div>
          </button>
        </div>
      </section>

      {/* Modal: Create Project */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-md p-6 rounded-3xl bg-slate-900 border border-slate-800 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="font-bold text-white text-base flex items-center gap-2">
                <FolderGit2 className="w-4 h-4 text-indigo-400" /> Create Project Workspace
              </h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <form onSubmit={handleCreateProject} className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-slate-300">Project Name</label>
                <input
                  type="text"
                  required
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  placeholder="e.g. LifeSync AI 4.0 Core Architecture"
                  className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:border-indigo-500 outline-none"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-300">Description</label>
                <textarea
                  rows={3}
                  value={newProjectDesc}
                  onChange={(e) => setNewProjectDesc(e.target.value)}
                  placeholder="Summary of goals, roadmap, and scope..."
                  className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:border-indigo-500 outline-none resize-none"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-300">Target Delivery Date</label>
                <input
                  type="date"
                  value={newProjectDate}
                  onChange={(e) => setNewProjectDate(e.target.value)}
                  className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:border-indigo-500 outline-none"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-xl text-xs text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20"
                >
                  Create Workspace
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Add Note */}
      {activeProjectNoteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-sm p-5 rounded-3xl bg-slate-900 border border-slate-800 shadow-2xl space-y-3">
            <h4 className="font-bold text-white text-sm flex items-center gap-2">
              <StickyNote className="w-4 h-4 text-indigo-400" /> Add Project Note
            </h4>
            <textarea
              rows={3}
              value={noteText}
              onChange={(e) => setNoteText(e.target.value)}
              placeholder="Record architectural observation, constraint, or insight..."
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:border-indigo-500 outline-none resize-none"
            />
            <div className="flex justify-end gap-2 pt-1">
              <button
                type="button"
                onClick={() => setActiveProjectNoteModal(null)}
                className="px-3 py-1.5 rounded-xl text-xs text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => handleAddNote(activeProjectNoteModal)}
                className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
              >
                Save Note
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Add Decision */}
      {activeProjectDecisionModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-sm p-5 rounded-3xl bg-slate-900 border border-slate-800 shadow-2xl space-y-3">
            <h4 className="font-bold text-white text-sm flex items-center gap-2">
              <Lightbulb className="w-4 h-4 text-amber-400" /> Record Architectural Decision
            </h4>
            <div>
              <label className="text-[11px] font-semibold text-slate-300">Decision</label>
              <input
                type="text"
                value={decisionText}
                onChange={(e) => setDecisionText(e.target.value)}
                placeholder="e.g. Adopt DAG-based execution engine"
                className="w-full mt-1 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:border-amber-500 outline-none"
              />
            </div>
            <div>
              <label className="text-[11px] font-semibold text-slate-300">Rationale</label>
              <textarea
                rows={2}
                value={decisionRationale}
                onChange={(e) => setDecisionRationale(e.target.value)}
                placeholder="Why was this chosen over alternatives..."
                className="w-full mt-1 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:border-amber-500 outline-none resize-none"
              />
            </div>
            <div className="flex justify-end gap-2 pt-1">
              <button
                type="button"
                onClick={() => setActiveProjectDecisionModal(null)}
                className="px-3 py-1.5 rounded-xl text-xs text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => handleAddDecision(activeProjectDecisionModal)}
                className="px-3 py-1.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold"
              >
                Save Decision
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};