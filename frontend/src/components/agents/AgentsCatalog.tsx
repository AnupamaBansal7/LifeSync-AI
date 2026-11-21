import React, { useState } from 'react';
import { Activity, Bot } from 'lucide-react';
import type { AgentRun } from '../../types';

interface AgentInfo {
  name: string;
  display_name: string;
  description: string;
  category: 'common' | 'role_specific';
  supported_roles: string[];
  allowed_tools: string[];
  is_active: boolean;
}

interface AgentsCatalogProps {
  catalog: AgentInfo[];
  runs: AgentRun[];
  activeRole: string;
  onRunTestPrompt: (prompt: string) => void;
}

export const AgentsCatalog: React.FC<AgentsCatalogProps> = ({
  catalog,
  runs,
  activeRole: _activeRole,
  onRunTestPrompt,
}) => {
  const [filterCategory, setFilterCategory] = useState<'all' | 'common' | 'role_specific'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredAgents = catalog.filter((agent) => {
    if (filterCategory !== 'all' && agent.category !== filterCategory) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        agent.display_name.toLowerCase().includes(q) ||
        agent.description.toLowerCase().includes(q) ||
        agent.name.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="space-y-6 pb-12 select-none">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs uppercase tracking-wider mb-1">
            <Bot className="w-4 h-4" /> Multi-Agent Ecosystem
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-white">Active Autonomous Agents</h2>
          <p className="text-xs text-slate-400 mt-1">
            LifeSync coordinates specialized agents with scoped permissions and verifiable tool calling.
          </p>
        </div>

        {/* Filter Pills & Search */}
        <div className="flex flex-wrap items-center gap-2">
          <input
            type="text"
            placeholder="Search agents or tools..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="px-3 py-1.5 rounded-xl text-xs bg-slate-900 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
          <button
            onClick={() => setFilterCategory('all')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer ${
              filterCategory === 'all'
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            All ({catalog.length})
          </button>
          <button
            onClick={() => setFilterCategory('common')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer ${
              filterCategory === 'common'
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            Common (9)
          </button>
          <button
            onClick={() => setFilterCategory('role_specific')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer ${
              filterCategory === 'role_specific'
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            Role-Specific
          </button>
        </div>
      </div>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredAgents.map((agent) => (
          <div
            key={agent.name}
            className="rounded-3xl bg-slate-900/70 border border-slate-800 p-5 flex flex-col justify-between backdrop-blur-xl hover:border-indigo-500/40 transition-all shadow-md group"
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="p-2.5 rounded-2xl bg-indigo-600/15 text-indigo-400 border border-indigo-500/20 group-hover:scale-105 transition-transform">
                  <Bot className="w-5 h-5" />
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-[10px] font-mono text-emerald-400 font-bold uppercase">
                    ONLINE
                  </span>
                </div>
              </div>

              <h3 className="font-bold text-sm text-white mb-1">{agent.display_name}</h3>
              <p className="text-xs text-slate-300 line-clamp-3 leading-relaxed mb-4">
                {agent.description}
              </p>
            </div>

            <div className="space-y-3 pt-3 border-t border-slate-800/80">
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="text-[10px] text-slate-400 font-mono">Tools:</span>
                {agent.allowed_tools.map((tool, idx) => (
                  <span
                    key={idx}
                    className="text-[10px] px-2 py-0.5 rounded-md bg-slate-950 border border-slate-800 font-mono text-indigo-300"
                  >
                    {tool}
                  </span>
                ))}
              </div>

              <div className="flex items-center justify-between text-[11px] text-slate-400">
                <span className="capitalize text-slate-400">
                  {agent.category === 'common'
                    ? 'All Roles'
                    : `Roles: ${agent.supported_roles.join(', ')}`}
                </span>
                <button
                  onClick={() => onRunTestPrompt(`Ask ${agent.display_name} to optimize today's priorities.`)}
                  className="text-indigo-400 hover:text-indigo-300 font-medium cursor-pointer"
                >
                  Interact &rarr;
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Execution Runs History */}
      <div className="mt-8 rounded-3xl bg-slate-900/70 border border-slate-800 p-6 backdrop-blur-xl">
        <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs uppercase tracking-wider mb-4">
          <Activity className="w-4 h-4" /> Agent Execution Audit Log
        </div>

        <div className="space-y-3">
          {runs.length === 0 ? (
            <div className="text-center py-6 text-xs text-slate-400">
              No recent agent execution runs recorded yet.
            </div>
          ) : (
            runs.slice(0, 8).map((run) => (
              <div
                key={run.id}
                className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
              >
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold text-white">"{run.user_query}"</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-bold uppercase">
                      {run.detected_intent}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400">
                    Steps: {run.steps.length} • Approvals: {run.approvals.length} • Status: {run.status}
                  </div>
                </div>

                <div className="flex items-center gap-3 text-[11px] text-slate-400 font-mono shrink-0">
                  <span>{run.latency_ms || 120}ms</span>
                  <span>{new Date(run.created_at).toLocaleTimeString()}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
