import React, { useState } from 'react';
import {
  Bot,
  Check,
  Compass,
  Mic,
  MicOff,
  Send,
  ShieldCheck,
  Sparkles,
  Volume2,
  VolumeX,
  X,
} from 'lucide-react';
import type { ActionApproval, AgentTraceItem, ClarificationCardData, ExecutionStep, TransactionPlan } from '../../types';
import { ShadowDiffCard } from '../executions/ShadowDiffCard';
import { ClarificationCard } from '../chat/ClarificationCard';
import { AgentCollaborationStrip } from '../chat/AgentCollaborationStrip';
import { useVoiceConversation } from '../../hooks/useVoiceConversation';

interface Message {
  sender: 'user' | 'assistant';
  content: string;
  intent?: string;
  latency?: number;
  steps?: ExecutionStep[];
  approvals?: ActionApproval[];
  plan?: TransactionPlan;
  card?: ClarificationCardData;
  agent_trace?: AgentTraceItem[];
  spoken_reply?: string;
}

interface AssistantProps {
  chatHistory: Message[];
  agentBusy: boolean;
  onSendMessage: (msg: string, role?: string, agentName?: string) => Promise<void>;
  pendingApprovals: ActionApproval[];
  onDecideApproval: (id: string, decision: 'approved' | 'rejected') => Promise<void>;
  activeRole: string;
  onSelectRole: (role: string) => void;
  availableRoles: string[];
}

export const AIAssistantWorkspace: React.FC<AssistantProps> = ({
  chatHistory,
  agentBusy,
  onSendMessage,
  pendingApprovals,
  onDecideApproval,
  activeRole,
  onSelectRole,
  availableRoles,
}) => {
  const [input, setInput] = useState('');

  // Voice & Speech Hook
  const {
    isListening,
    isSupported: isVoiceSupported,
    voiceReadbackEnabled,
    setVoiceReadbackEnabled,
    toggleListening,
    speak,
  } = useVoiceConversation({
    onTranscript: (text) => {
      setInput(text);
    },
  });

  const suggestedPromptsByRole: Record<string, string[]> = {
    personal: [
      'Plan my day based on my upcoming priorities and habits.',
      'Review my productivity and focus consistency this week.',
      'Remember that I prefer morning workouts between 07:00 and 08:00.',
    ],
    student: [
      'I have an examination next week. Create a spaced repetition study plan.',
      'Break down my machine learning capstone project into actionable tasks.',
      'Schedule a 2-hour deep work revision block for database systems tomorrow.',
    ],
    professional: [
      'Protect a 90-minute focus block for sprint deliverables tomorrow morning.',
      'Decompose our quarterly architectural migration into high-priority tasks.',
      'Review my upcoming deadlines and flag any overdue risks.',
    ],
    entrepreneur: [
      'Translate our 100-user beta objective into strategic milestones.',
      'Draft an execution schedule for our upcoming product launch sprint.',
      'Suggest reallocating unfinished operational tasks to available slots tomorrow.',
    ],
  };

  const currentPrompts =
    suggestedPromptsByRole[activeRole] || suggestedPromptsByRole.personal;

  const handleSend = async (textToSend?: string) => {
    const text = (textToSend ?? input).trim();
    if (!text || agentBusy) return;
    setInput('');
    await onSendMessage(text, activeRole);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[calc(100vh-140px)] select-none">
      {/* Left Col: Agents & Prompt Quick Library */}
      <div className="hidden lg:flex flex-col gap-4 col-span-1 rounded-3xl bg-slate-900/70 border border-slate-800 p-4 backdrop-blur-xl overflow-y-auto">
        <div>
          <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs uppercase tracking-wider mb-2">
            <Compass className="w-4 h-4" /> Active Context
          </div>
          <select
            value={activeRole}
            onChange={(e) => onSelectRole(e.target.value)}
            className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs font-semibold capitalize text-indigo-300 outline-none"
          >
            <option value="personal">Personal Life</option>
            {availableRoles.map((r) => (
              <option key={r} value={r} className="capitalize">
                {r}
              </option>
            ))}
          </select>
        </div>

        {/* Suggested Prompts */}
        <div className="pt-2 border-t border-slate-800/80">
          <div className="text-[11px] font-semibold text-slate-400 mb-2.5 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>Suggested Role Prompts</span>
          </div>
          <div className="space-y-2">
            {currentPrompts.map((prompt, idx) => (
              <button
                key={idx}
                disabled={agentBusy}
                onClick={() => handleSend(prompt)}
                className="w-full text-left p-2.5 rounded-xl bg-slate-950/70 hover:bg-indigo-950/30 border border-slate-800/80 hover:border-indigo-500/40 text-xs text-slate-300 transition-all cursor-pointer leading-relaxed"
              >
                "{prompt}"
              </button>
            ))}
          </div>
        </div>

        {/* Pending Action Approvals Sidebar widget */}
        {pendingApprovals.length > 0 && (
          <div className="pt-3 border-t border-slate-800/80">
            <div className="flex items-center gap-1.5 text-amber-400 text-xs font-bold mb-2">
              <ShieldCheck className="w-4 h-4" />
              <span>Pending Approvals ({pendingApprovals.length})</span>
            </div>
            <div className="space-y-2">
              {pendingApprovals.map((ap) => (
                <div
                  key={ap.id}
                  className="p-3 rounded-xl bg-amber-950/20 border border-amber-500/40 text-xs space-y-2"
                >
                  <p className="text-slate-200 font-medium leading-tight">{ap.action_summary}</p>
                  <div className="flex items-center gap-2 pt-1">
                    <button
                      onClick={() => onDecideApproval(ap.id, 'approved')}
                      className="px-2.5 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-[10px] font-bold transition cursor-pointer flex items-center gap-1"
                    >
                      <Check className="w-3 h-3" /> Approve
                    </button>
                    <button
                      onClick={() => onDecideApproval(ap.id, 'rejected')}
                      className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] font-medium transition cursor-pointer flex items-center gap-1"
                    >
                      <X className="w-3 h-3" /> Reject
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Main Chat Workspace */}
      <div className="col-span-1 lg:col-span-3 rounded-3xl bg-slate-900/70 border border-slate-800 flex flex-col justify-between backdrop-blur-xl overflow-hidden shadow-2xl">
        {/* Chat Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-white flex items-center gap-2">
                <span>LifeSync AI Orchestrator</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  {activeRole.toUpperCase()} CONTEXT
                </span>
              </div>
              <div className="text-[10px] text-slate-400">
                Direct access to real database operations, calendar time blocking & persistent memory
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setVoiceReadbackEnabled(!voiceReadbackEnabled)}
              className={`p-2 rounded-xl transition ${
                voiceReadbackEnabled
                  ? 'text-purple-300 bg-purple-900/40 border border-purple-500/40 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
              title={voiceReadbackEnabled ? 'Voice readback active (click to mute)' : 'Enable voice readback'}
            >
              {voiceReadbackEnabled ? <Volume2 className="w-4 h-4 text-purple-400" /> : <VolumeX className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
          {chatHistory.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center p-6 space-y-3">
              <div className="p-4 rounded-3xl bg-indigo-600/10 text-indigo-400 border border-indigo-500/20">
                <Bot className="w-8 h-8 animate-bounce" />
              </div>
              <h3 className="text-base font-bold text-white">How can LifeSync assist you today?</h3>
              <p className="text-xs text-slate-400 max-w-md">
                Ask me to schedule focus blocks, decompose broad goals into atomic tasks, review your weekly productivity, or remember your preferences.
              </p>
            </div>
          ) : (
            chatHistory.map((msg, idx) => {
              const isUser = msg.sender === 'user';
              return (
                <div
                  key={idx}
                  className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} space-y-1.5`}
                >
                  <div
                    className={`max-w-[85%] sm:max-w-[75%] p-4 rounded-2xl text-xs sm:text-sm leading-relaxed ${
                      isUser
                        ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white rounded-br-sm shadow-lg shadow-indigo-600/20'
                        : 'bg-slate-950/90 border border-slate-800 text-slate-200 rounded-bl-sm shadow-md'
                    }`}
                  >
                    {!isUser && msg.agent_trace && msg.agent_trace.length > 0 && (
                      <AgentCollaborationStrip trace={msg.agent_trace} />
                    )}
                    <div className="whitespace-pre-wrap">{msg.content}</div>

                    {!isUser && msg.latency && (
                      <div className="mt-2 pt-2 border-t border-slate-800/80 flex items-center gap-3 text-[10px] text-slate-500 font-mono">
                        <span>Intent: {msg.intent}</span>
                        <span>•</span>
                        <span>{msg.latency}ms</span>
                      </div>
                    )}

                    {!isUser && msg.plan && (
                      <div className="mt-3 w-full">
                        <ShadowDiffCard plan={msg.plan} />
                      </div>
                    )}

                    {!isUser && msg.card && (
                      <div className="mt-3 w-full">
                        <ClarificationCard
                          card={msg.card}
                          onRespond={(opts, custom, skip) => {
                            if (skip) {
                              handleSend('skip and generate blueprint plan');
                            } else {
                              handleSend(custom || opts.join(', '));
                            }
                          }}
                          onSpeakQuestion={(text) => speak(text, true)}
                        />
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}

          {agentBusy && (
            <div className="flex items-center gap-2.5 p-3 rounded-2xl bg-slate-950/80 border border-slate-800 max-w-xs text-xs text-indigo-300">
              <div className="w-3.5 h-3.5 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
              <span>Orchestrating agents & tools...</span>
            </div>
          )}
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/60">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center gap-2"
          >
            {isVoiceSupported && (
              <button
                type="button"
                onClick={() => toggleListening()}
                className={`p-3 rounded-xl border transition ${
                  isListening
                    ? 'bg-rose-500 text-white border-rose-400 animate-pulse'
                    : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white hover:border-slate-700'
                }`}
                title={isListening ? 'Stop listening' : 'Start voice input'}
              >
                {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              </button>
            )}
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={
                isListening
                  ? 'Listening to your speech...'
                  : `Ask LifeSync in ${activeRole} mode... (e.g. 'Plan my day', 'Break down project')`
              }
              disabled={agentBusy}
              className="flex-1 px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 outline-none"
            />
            <button
              type="submit"
              disabled={agentBusy || !input.trim()}
              className="px-5 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-semibold text-xs shadow-lg shadow-indigo-600/25 transition cursor-pointer disabled:opacity-40"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
