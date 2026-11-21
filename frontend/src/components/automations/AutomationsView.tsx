import React, { useState, useEffect } from 'react';
import {
  Activity,
  Bot,
  CheckCircle2,
  Clock,
  Layers,
  Play,
  Plus,
  Power,
  RefreshCw,
  ShieldAlert,
  Sparkles,
  Trash2,
  Workflow,
  X,
  Zap,
} from 'lucide-react';
import { api } from '../../lib/api';
import type { AutomationRule } from '../../types';

interface AutomationsViewProps {
  rules: AutomationRule[];
  templates: any[];
  onCreateRule: (rule: any) => Promise<void>;
  onToggleRule: (id: string, active: boolean) => Promise<void>;
  onDeleteRule: (id: string) => Promise<void>;
  onTriggerRule: (id: string) => Promise<any>;
}

interface WorkflowNode {
  id: string;
  type: 'trigger' | 'condition' | 'ai_agent' | 'approval' | 'notification';
  title: string;
  description: string;
  tool_name?: string;
  config: Record<string, any>;
}

export const AutomationsView: React.FC<AutomationsViewProps> = ({
  rules,
  templates,
  onCreateRule,
  onToggleRule,
  onDeleteRule,
  onTriggerRule,
}) => {
  const [activeTab, setActiveTab] = useState<'rules' | 'visual_builder' | 'system_health'>('rules');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [triggeringId, setTriggeringId] = useState<string | null>(null);
  const [triggerFeedback, setTriggerFeedback] = useState<string | null>(null);

  // Natural Language AI Automation Generator State
  const [nlPrompt, setNlPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [triggerLogs, setTriggerLogs] = useState<any[]>([]);

  // System Health State
  const [systemHealth, setSystemHealth] = useState<any>(null);
  const [loadingHealth, setLoadingHealth] = useState(false);

  // Form states
  const [name, setName] = useState('');
  const [triggerType, setTriggerType] = useState<'schedule' | 'task_overdue' | 'habit_missed' | 'deadline_approaching'>('schedule');
  const [actionType, setActionType] = useState<'notify' | 'generate_plan' | 'reschedule_suggest' | 'daily_review'>('notify');
  const [requiresApproval, setRequiresApproval] = useState(false);

  // Visual Workflow Studio Nodes State
  const [workflowNodes, setWorkflowNodes] = useState<WorkflowNode[]>([
    {
      id: 'node-1',
      type: 'trigger',
      title: 'Trigger: High-Priority Inbound Email',
      description: 'Listens for messages with keywords "deadline", "urgent", or "exam".',
      config: { service: 'gmail', filter: 'is:important' },
    },
    {
      id: 'node-2',
      type: 'ai_agent',
      title: 'AI Classification & Parameter Extraction',
      description: 'Sync extracts the due date, required milestone, and estimated hours.',
      tool_name: 'read_email_thread',
      config: { agent: 'EmailAgent' },
    },
    {
      id: 'node-3',
      type: 'condition',
      title: 'Condition: Requires Focus Block (> 60 mins)?',
      description: 'Evaluates calendar availability and schedules dedicated study session.',
      config: { threshold_minutes: 60 },
    },
    {
      id: 'node-4',
      type: 'approval',
      title: 'Human-in-the-Loop Confirmation Gate',
      description: 'Stops execution and awaits user approval card confirmation before outbound reply.',
      tool_name: 'send_email',
      config: { requires_approval: true },
    },
    {
      id: 'node-5',
      type: 'notification',
      title: 'Completion & Sync Alert',
      description: 'Dispatches in-app notification and syncs task with Google Workspace.',
      config: { channel: 'in_app' },
    },
  ]);
  const [executingWorkflow, setExecutingWorkflow] = useState(false);
  const [workflowRunResult, setWorkflowRunResult] = useState<any>(null);

  useEffect(() => {
    fetchLogs();
    fetchHealth();
  }, []);

  const fetchLogs = async () => {
    try {
      const res = await api.get('/automations/logs?limit=5');
      if (res.data) {
        setTriggerLogs(res.data);
      }
    } catch (e) {
      // Offline fallback
    }
  };

  const fetchHealth = async () => {
    setLoadingHealth(true);
    try {
      const res = await api.get('/system/health');
      if (res.data) {
        setSystemHealth(res.data);
      }
    } catch (e) {
      // Offline
    } finally {
      setLoadingHealth(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    await onCreateRule({
      name,
      trigger_type: triggerType,
      trigger_config: {},
      action_type: actionType,
      action_config: {},
      requires_approval: requiresApproval,
      is_active: true,
    });

    setName('');
    setShowCreateModal(false);
  };

  const handleCreateWithAI = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nlPrompt.trim() || isGenerating) return;

    setIsGenerating(true);
    setTriggerFeedback(null);
    try {
      const res = await api.post('/automations/parse-natural-language', {
        prompt: nlPrompt.trim(),
        auto_save: true,
      });

      if (res.data && res.data.rule) {
        setTriggerFeedback(`AI Automation Activated: ${res.data.explanation}`);
        setNlPrompt('');
        setTimeout(() => setTriggerFeedback(null), 6000);
        await onCreateRule(res.data.rule);
        fetchLogs();
      }
    } catch (err: any) {
      setTriggerFeedback('Could not parse natural language automation. Please try rephrasing.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleApplyTemplate = async (tmpl: any) => {
    await onCreateRule({
      name: tmpl.name,
      trigger_type: tmpl.trigger_type,
      trigger_config: tmpl.trigger_config,
      action_type: tmpl.action_type,
      action_config: tmpl.action_config,
      requires_approval: tmpl.requires_approval,
      is_active: true,
    });
  };

  const handleRunTest = async (ruleId: string) => {
    setTriggeringId(ruleId);
    setTriggerFeedback(null);
    try {
      const res = await onTriggerRule(ruleId);
      setTriggerFeedback(`Automation executed successfully! Action: ${res.action_type}`);
      fetchLogs();
      setTimeout(() => setTriggerFeedback(null), 4000);
    } finally {
      setTriggeringId(null);
    }
  };

  const handleExecuteWorkflowDAG = async () => {
    setExecutingWorkflow(true);
    setWorkflowRunResult(null);

    try {
      const res = await api.post('/workflows', {
        name: 'Visual DAG: Email Deadline to Calendar Sync',
        auto_start: true,
        steps: [
          {
            step_id: 'step_1',
            name: 'Search Inbound Urgent Emails',
            agent_name: 'EmailAgent',
            tool_name: 'search_emails',
            input_payload: { query: 'urgent deadline', max_results: 3 },
            depends_on: [],
          },
          {
            step_id: 'step_2',
            name: 'Check Calendar Availability',
            agent_name: 'CalendarAgent',
            tool_name: 'list_calendar_events',
            input_payload: { start_date: new Date().toISOString().slice(0, 10) },
            depends_on: ['step_1'],
          },
          {
            step_id: 'step_3',
            name: 'Create Focus Session Block',
            agent_name: 'CalendarAgent',
            tool_name: 'create_calendar_block',
            input_payload: { title: 'Focus Sprint: Email Deliverable', duration_minutes: 60, role_context: 'personal' },
            depends_on: ['step_2'],
          },
        ],
      });

      setWorkflowRunResult(res.data);
      setTriggerFeedback(`Workflow DAG Completed! Status: ${res.data.status}. Steps executed: ${res.data.steps?.length || 3}`);
      fetchLogs();
      fetchHealth();
    } catch (err: any) {
      setTriggerFeedback(`Workflow Execution Error: ${err.message || 'Check backend logs'}`);
    } finally {
      setExecutingWorkflow(false);
    }
  };

  return (
    <div className="space-y-6 pb-12 select-none">
      {/* Header & Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-white flex items-center gap-2">
            <Workflow className="w-6 h-6 text-indigo-400" />
            <span>Autonomous Automation & Workflow Engine</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Design DAG task graphs, trigger background routines, and monitor multi-agent execution checkpoints.
          </p>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex items-center gap-1.5 p-1 rounded-2xl bg-slate-900 border border-slate-800">
          <button
            onClick={() => setActiveTab('rules')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'rules' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Zap className="w-3.5 h-3.5" />
            <span>Active Rules</span>
          </button>
          <button
            onClick={() => setActiveTab('visual_builder')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'visual_builder' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Visual DAG Studio</span>
          </button>
          <button
            onClick={() => {
              setActiveTab('system_health');
              fetchHealth();
            }}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'system_health' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>System Diagnostics</span>
          </button>
        </div>
      </div>

      {triggerFeedback && (
        <div className="p-3.5 rounded-2xl bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 text-xs flex items-center gap-2 animate-in fade-in duration-200">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          <span>{triggerFeedback}</span>
        </div>
      )}

      {/* TAB 1: RULES & NATURAL LANGUAGE GENERATOR */}
      {activeTab === 'rules' && (
        <>
          {/* Natural Language Automation Builder Bar */}
          <div className="p-4 rounded-3xl bg-gradient-to-r from-indigo-950/40 via-purple-950/20 to-slate-900 border border-indigo-500/30 backdrop-blur-xl shadow-xl shadow-indigo-950/20">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              <span className="text-xs font-bold text-white uppercase tracking-wider">
                Natural-Language Automation Creator
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-mono">
                AI 4.0
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mb-3">
              Describe any automated workflow in plain English. Sync will synthesize the schedule, triggers, and actions.
            </p>
            <form onSubmit={handleCreateWithAI} className="flex gap-2">
              <input
                type="text"
                value={nlPrompt}
                onChange={(e) => setNlPrompt(e.target.value)}
                placeholder="e.g. 'Every morning at 8:00 AM synthesize my daily plan' or 'Alert me 24h before any deadline'..."
                className="flex-1 px-4 py-2.5 rounded-2xl bg-slate-950/80 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
              />
              <button
                type="submit"
                disabled={isGenerating || !nlPrompt.trim()}
                className="px-5 py-2.5 rounded-2xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-bold transition shadow-lg shadow-indigo-600/30 disabled:opacity-50 flex items-center gap-2 cursor-pointer"
              >
                {isGenerating ? (
                  <span>Synthesizing...</span>
                ) : (
                  <>
                    <Bot className="w-4 h-4" />
                    <span>Create with AI</span>
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Preset Workflow Templates */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-2">
              <Zap className="w-4 h-4" /> Recommended Automation Presets
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {templates.map((tmpl, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-3xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between hover:border-slate-700 transition"
                >
                  <div>
                    <div className="font-bold text-xs text-white mb-1">{tmpl.name}</div>
                    <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed mb-3">
                      {tmpl.description}
                    </p>
                  </div>
                  <button
                    onClick={() => handleApplyTemplate(tmpl)}
                    className="w-full py-2 rounded-xl bg-indigo-600/15 hover:bg-indigo-600/25 border border-indigo-500/30 text-indigo-300 text-xs font-semibold transition cursor-pointer flex items-center justify-center gap-1"
                  >
                    <Plus className="w-3.5 h-3.5" /> Enable Preset
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Active Rules List */}
          <div className="space-y-3 pt-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                <Workflow className="w-4 h-4 text-indigo-400" /> Active Configured Rules ({rules.length})
              </h3>
              <button
                onClick={() => setShowCreateModal(true)}
                className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold cursor-pointer"
              >
                + Custom Rule
              </button>
            </div>

            <div className="space-y-3">
              {rules.length === 0 ? (
                <div className="text-center py-12 text-xs text-slate-400 bg-slate-900/40 rounded-3xl border border-slate-800 p-8">
                  No automation rules configured. Use the AI bar above, enable a preset, or create a custom workflow.
                </div>
              ) : (
                rules.map((rule) => (
                  <div
                    key={rule.id}
                    className="p-4 rounded-3xl bg-slate-900/70 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4 backdrop-blur-xl"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-white">{rule.name}</span>
                        <span
                          className={`text-[9px] font-mono px-2 py-0.5 rounded uppercase font-bold ${
                            rule.is_active
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                              : 'bg-slate-800 text-slate-500'
                          }`}
                        >
                          {rule.is_active ? 'ACTIVE' : 'PAUSED'}
                        </span>
                        {rule.requires_approval && (
                          <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                            APPROVAL GATED
                          </span>
                        )}
                      </div>

                      <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-400 font-mono">
                        <span>Trigger: {rule.trigger_type}</span>
                        <span>•</span>
                        <span>Action: {rule.action_type}</span>
                        {rule.last_triggered_at && (
                          <>
                            <span>•</span>
                            <span>Last run: {new Date(rule.last_triggered_at).toLocaleTimeString()}</span>
                          </>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-3 self-end sm:self-center">
                      <button
                        disabled={triggeringId === rule.id}
                        onClick={() => handleRunTest(rule.id)}
                        className="px-3 py-1.5 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 text-xs text-slate-300 hover:text-white transition cursor-pointer flex items-center gap-1.5"
                        title="Execute rule immediately"
                      >
                        <Play className="w-3 h-3 text-indigo-400" />
                        <span>{triggeringId === rule.id ? 'Running...' : 'Run Test'}</span>
                      </button>

                      <button
                        onClick={() => onToggleRule(rule.id, !rule.is_active)}
                        className={`p-2 rounded-xl border transition cursor-pointer ${
                          rule.is_active
                            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                            : 'bg-slate-950 border-slate-800 text-slate-500'
                        }`}
                        title={rule.is_active ? 'Pause Rule' : 'Activate Rule'}
                      >
                        <Power className="w-4 h-4" />
                      </button>

                      <button
                        onClick={() => onDeleteRule(rule.id)}
                        className="p-2 rounded-xl text-slate-400 hover:text-rose-400 hover:bg-rose-950/20 transition cursor-pointer"
                        title="Delete Rule"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Execution History Logs */}
          {triggerLogs.length > 0 && (
            <div className="space-y-3 pt-4 border-t border-slate-800/80">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                <Activity className="w-4 h-4 text-emerald-400" /> Recent Execution Logs
              </h3>
              <div className="rounded-3xl bg-slate-900/50 border border-slate-800 overflow-hidden divide-y divide-slate-800/60">
                {triggerLogs.map((log) => (
                  <div key={log.id} className="p-3 text-xs flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="w-2 h-2 rounded-full bg-emerald-400" />
                      <span className="font-mono text-slate-300">Trigger: {log.trigger_event}</span>
                      <span className="text-[10px] text-slate-500">
                        Status: <span className="text-emerald-400 font-bold">{log.status}</span>
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-400 text-[10px] font-mono">
                      <Clock className="w-3 h-3 text-slate-500" />
                      <span>{new Date(log.executed_at).toLocaleString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* TAB 2: VISUAL WORKFLOW STUDIO (DAG EDITOR) */}
      {activeTab === 'visual_builder' && (
        <div className="space-y-6">
          <div className="p-4 rounded-3xl bg-slate-900/60 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-400" />
                <span>Visual Workflow DAG Editor</span>
              </h3>
              <p className="text-xs text-slate-400">
                Connected graph execution pipeline with dependency verification and approval gates.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  const newNode: WorkflowNode = {
                    id: `node-${workflowNodes.length + 1}`,
                    type: 'ai_agent',
                    title: `Step ${workflowNodes.length + 1}: Custom Agent Task`,
                    description: 'Custom autonomous tool execution step in the DAG pipeline.',
                    config: {},
                  };
                  setWorkflowNodes([...workflowNodes, newNode]);
                }}
                className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold transition flex items-center gap-1.5 cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Step</span>
              </button>
              <button
                disabled={executingWorkflow}
                onClick={handleExecuteWorkflowDAG}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold transition shadow-lg shadow-emerald-600/30 flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
              >
                <Play className="w-3.5 h-3.5" />
                <span>{executingWorkflow ? 'Executing DAG...' : 'Run Workflow DAG'}</span>
              </button>
            </div>
          </div>

          {/* Node Pipeline Diagram */}
          <div className="space-y-4">
            {workflowNodes.map((node, idx) => (
              <div key={node.id} className="relative">
                <div className="p-5 rounded-3xl bg-slate-900/80 border border-slate-800 hover:border-indigo-500/50 transition backdrop-blur-xl shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="flex items-start gap-4">
                    <div
                      className={`w-9 h-9 rounded-2xl flex items-center justify-center font-bold text-xs flex-shrink-0 ${
                        node.type === 'trigger'
                          ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                          : node.type === 'ai_agent'
                          ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                          : node.type === 'condition'
                          ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                          : node.type === 'approval'
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      }`}
                    >
                      {idx + 1}
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-white">{node.title}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono uppercase">
                          {node.type.replace('_', ' ')}
                        </span>
                        {node.tool_name && (
                          <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-950/60 text-indigo-300 font-mono">
                            Tool: {node.tool_name}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-400">{node.description}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 text-xs text-slate-500 font-mono">
                    <span>Prereq: {idx === 0 ? 'None (Start)' : `Node ${idx}`}</span>
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  </div>
                </div>

                {/* Arrow connector */}
                {idx < workflowNodes.length - 1 && (
                  <div className="flex justify-center my-1.5">
                    <div className="w-0.5 h-4 bg-indigo-500/30" />
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Workflow Execution Result Card */}
          {workflowRunResult && (
            <div className="p-5 rounded-3xl bg-slate-900 border border-indigo-500/40 space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-bold text-sm text-white flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>Workflow Execution Verified</span>
                </span>
                <span className="text-xs font-mono text-emerald-400 font-bold uppercase">
                  {workflowRunResult.status}
                </span>
              </div>
              <div className="text-xs text-slate-400 font-mono">
                Workflow ID: {workflowRunResult.id}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
                {workflowRunResult.steps?.map((step: any, i: number) => (
                  <div key={i} className="p-3 rounded-2xl bg-slate-950 border border-slate-800 text-xs">
                    <div className="font-bold text-white mb-1">{step.name}</div>
                    <div className="text-slate-400 font-mono text-[10px]">Tool: {step.tool_name}</div>
                    <div className="text-emerald-400 font-mono text-[10px] mt-1">Status: {step.status}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: SYSTEM DIAGNOSTICS & VERIFIED HEALTH */}
      {activeTab === 'system_health' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-indigo-400" /> Real-Time Service Verification
            </h3>
            <button
              onClick={fetchHealth}
              disabled={loadingHealth}
              className="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-xs text-slate-300 flex items-center gap-1.5 cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingHealth ? 'animate-spin' : ''}`} />
              <span>Refresh Status</span>
            </button>
          </div>

          {systemHealth ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Database */}
              <div className="p-4 rounded-3xl bg-slate-900/70 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">PostgreSQL & PGVector</span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-bold">
                    CONNECTED
                  </span>
                </div>
                <div className="text-xs text-slate-400">
                  Latency: <span className="font-mono text-emerald-400">{systemHealth.components.database.latency_ms} ms</span>
                </div>
              </div>

              {/* LLM Engine */}
              <div className="p-4 rounded-3xl bg-slate-900/70 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">AI Reasoning Engine</span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-bold uppercase">
                    {systemHealth.components.llm_engine.status}
                  </span>
                </div>
                <div className="text-xs text-slate-400">
                  Model: <span className="font-mono text-slate-200">{systemHealth.components.llm_engine.model}</span>
                </div>
              </div>

              {/* Agent Mesh */}
              <div className="p-4 rounded-3xl bg-slate-900/70 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">Specialized Agents</span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-bold uppercase">
                    {systemHealth.components.agent_mesh.status}
                  </span>
                </div>
                <div className="text-xs text-slate-400">
                  Active Agents: <span className="font-mono text-slate-200">{systemHealth.components.agent_mesh.total_registered} registered</span>
                </div>
              </div>

              {/* Tool Registry */}
              <div className="p-4 rounded-3xl bg-slate-900/70 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">Atomic Tool Suite</span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-bold uppercase">
                    {systemHealth.components.tool_registry.status}
                  </span>
                </div>
                <div className="text-xs text-slate-400">
                  Tools: <span className="font-mono text-slate-200">{systemHealth.components.tool_registry.total_tools}</span> (Approval Gated: {systemHealth.components.tool_registry.approval_gated_tools})
                </div>
              </div>

              {/* Workflow Engine */}
              <div className="p-4 rounded-3xl bg-slate-900/70 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">DAG Workflow Engine</span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-bold uppercase">
                    ACTIVE
                  </span>
                </div>
                <div className="text-xs text-slate-400">
                  Running: <span className="font-mono text-emerald-400">{systemHealth.components.workflow_engine.active_running}</span>, Completed: <span className="font-mono text-slate-200">{systemHealth.components.workflow_engine.completed}</span>
                </div>
              </div>

              {/* Google Workspace */}
              <div className="p-4 rounded-3xl bg-slate-900/70 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">Google Workspace</span>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
                      systemHealth.components.google_workspace.connected
                        ? 'bg-emerald-500/20 text-emerald-300'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {systemHealth.components.google_workspace.connected ? 'CONNECTED' : 'STANDBY / MOCK'}
                  </span>
                </div>
                <div className="text-xs text-slate-400">
                  Email: <span className="font-mono text-slate-200">{systemHealth.components.google_workspace.account_email || 'Simulation Mode'}</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-10 text-xs text-slate-400">Loading live health telemetry...</div>
          )}
        </div>
      )}

      {/* Create Custom Rule Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="w-full max-w-md rounded-3xl bg-slate-900 border border-slate-800 shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="font-bold text-sm text-white">Create Custom Automation Rule</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Rule Name</label>
                <input
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Alert me when an urgent task becomes overdue"
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
                />
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1">Trigger Event</label>
                <select
                  value={triggerType}
                  onChange={(e: any) => setTriggerType(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
                >
                  <option value="schedule">Daily / Weekly Schedule</option>
                  <option value="task_overdue">When a Task Becomes Overdue</option>
                  <option value="deadline_approaching">When a Deadline is Within 24h</option>
                  <option value="habit_missed">When a Habit is Missed by Evening</option>
                </select>
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1">Action to Execute</label>
                <select
                  value={actionType}
                  onChange={(e: any) => setActionType(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
                >
                  <option value="notify">Send In-App Notification</option>
                  <option value="generate_plan">Synthesize Daily Focus Plan</option>
                  <option value="reschedule_suggest">Suggest Automatic Rescheduling</option>
                  <option value="daily_review">Generate Daily Review Summary</option>
                </select>
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="approvalCheck"
                  checked={requiresApproval}
                  onChange={(e) => setRequiresApproval(e.target.checked)}
                  className="w-4 h-4 rounded text-indigo-600 bg-slate-950 border-slate-800"
                />
                <label htmlFor="approvalCheck" className="text-xs text-slate-300">
                  Require user approval before committing automated modifications
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
                  Activate Rule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
