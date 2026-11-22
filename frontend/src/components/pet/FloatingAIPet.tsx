import React, { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import {
  Bot,
  Check,
  CheckCircle2,
  ChevronDown,
  Maximize2,
  Mic,
  MicOff,
  Minimize2,
  Monitor,
  MonitorOff,
  RefreshCw,
  Send,
  ShieldCheck,
  Sparkles,
  User as UserIcon,
  Volume2,
  VolumeX,
  X,
} from 'lucide-react';
import confetti from 'canvas-confetti';

import { api } from '../../lib/api';
import type { ActionApproval, AgentTraceItem, AICoreStatus, ClarificationCardData, DashboardSummary, ExecutionStep, TransactionPlan, User } from '../../types';
import type { NavTab } from '../layout/Sidebar';
import { ShadowDiffCard } from '../executions/ShadowDiffCard';
import { ClarificationCard } from '../chat/ClarificationCard';
import { AgentCollaborationStrip } from '../chat/AgentCollaborationStrip';
import { useSyncVoiceLoop } from '../../hooks/useSyncVoiceLoop';

interface PetMessage {
  id: string;
  sender: 'user' | 'assistant' | 'system';
  content: string;
  intent?: string;
  latency?: number;
  steps?: ExecutionStep[];
  approvals?: ActionApproval[];
  plan?: TransactionPlan;
  card?: ClarificationCardData;
  agent_trace?: AgentTraceItem[];
  spoken_reply?: string;
  quick_suggestions?: string[];
  timestamp: Date;
  hasScreen?: boolean;
}

interface FloatingAIPetProps {
  user: User | null;
  activeRole: string;
  activeTab: NavTab;
  onTabChange?: (tab: NavTab) => void;
  onRefreshData?: () => Promise<void>;
  approvals?: ActionApproval[];
  onDecideApproval?: (id: string, decision: 'approved' | 'rejected') => Promise<void>;
  aiCoreStatus?: AICoreStatus;
  onStatusChange?: (status: AICoreStatus) => void;
  summary?: DashboardSummary | null;
}

// Markdown Formatter for Assistant Outputs
const MarkdownContent: React.FC<{ content: string }> = ({ content }) => {
  const lines = content.split('\n');

  return (
    <div className="space-y-2 text-xs leading-relaxed text-slate-200">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        if (!trimmed) {
          return <div key={idx} className="h-1.5" />;
        }

        // Headers
        if (trimmed.startsWith('### ')) {
          return (
            <h4 key={idx} className="font-bold text-slate-100 text-xs mt-2 mb-1">
              {formatSpans(trimmed.slice(4))}
            </h4>
          );
        }
        if (trimmed.startsWith('## ') || trimmed.startsWith('# ')) {
          return (
            <h3 key={idx} className="font-bold text-sm text-indigo-300 mt-2 mb-1">
              {formatSpans(trimmed.replace(/^#+\s*/, ''))}
            </h3>
          );
        }

        // Bullet items
        if (trimmed.startsWith('• ') || trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
          return (
            <div key={idx} className="flex items-start gap-2 pl-2">
              <span className="text-indigo-400 mt-0.5">•</span>
              <span className="flex-1">{formatSpans(trimmed.replace(/^[•\-\*]\s*/, ''))}</span>
            </div>
          );
        }

        // Numbered list items
        const numMatch = trimmed.match(/^(\d+)\.\s+(.*)/);
        if (numMatch) {
          return (
            <div key={idx} className="flex items-start gap-2 pl-2">
              <span className="text-violet-400 font-semibold">{numMatch[1]}.</span>
              <span className="flex-1">{formatSpans(numMatch[2])}</span>
            </div>
          );
        }

        return <p key={idx}>{formatSpans(trimmed)}</p>;
      })}
    </div>
  );
};

// Helper to format inline bold, italics, backtick codes
function formatSpans(text: string) {
  const parts = text.split(/(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <code
          key={i}
          className="px-1.5 py-0.5 rounded bg-slate-800 text-indigo-300 font-mono text-[11px] border border-slate-700/60"
        >
          {part.slice(1, -1)}
        </code>
      );
    }
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={i} className="font-semibold text-slate-100">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith('*') && part.endsWith('*')) {
      return (
        <em key={i} className="text-slate-300 italic">
          {part.slice(1, -1)}
        </em>
      );
    }
    return part;
  });
}

export const FloatingAIPet: React.FC<FloatingAIPetProps> = ({
  user,
  activeRole,
  activeTab,
  onTabChange: _onTabChange,
  onRefreshData,
  approvals = [],
  onDecideApproval,
  aiCoreStatus: _aiCoreStatus = 'idle',
  onStatusChange,
  summary,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<PetMessage[]>([]);
  const [activeSpecialist, setActiveSpecialist] = useState<string>('LifeSync AI Orchestrator');

  const [voiceReadbackEnabled, setVoiceReadbackEnabled] = useState<boolean>(() => {
    try {
      return localStorage.getItem('lifesync_voice_readback') === 'true';
    } catch {
      return false;
    }
  });

  // Hands-free Voice Loop & Speech
  const {
    handsFreeEnabled,
    toggleHandsFree,
    isListening,
    isSupported: isVoiceSupported,
    startListening,
    stopListening,
    speakText,
    cancelSpeaking,
  } = useSyncVoiceLoop({
    onSendMessage: async (text) => {
      await handleSend(text);
    },
  });

  const [activeIntakeSessionId, setActiveIntakeSessionId] = useState<string | null>(null);

  // Screen Sharing
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const screenStreamRef = useRef<MediaStream | null>(null);
  const [screenPreviewUrl, setScreenPreviewUrl] = useState<string | null>(null);

  // Auto-scroll
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  // Proactive greeting on mount (once per session)
  useEffect(() => {
    const fetchGreeting = async () => {
      if (!user) return;
      const alreadyShown = sessionStorage.getItem('lifesync_greeting_shown');
      if (alreadyShown) return;

      try {
        const res = await api.get('/agents/greeting');
        sessionStorage.setItem('lifesync_greeting_shown', 'true');
        const greetingData = res.data;
        const greetingMsg: PetMessage = {
          id: `greeting-${Date.now()}`,
          sender: 'assistant',
          content: greetingData.greeting_text,
          quick_suggestions: greetingData.quick_suggestions || [],
          timestamp: new Date(),
        };
        setMessages((prev) => [greetingMsg, ...prev]);
        if (voiceReadbackEnabled || handsFreeEnabled) {
          speakText(greetingData.greeting_text);
        }
      } catch (err) {
        console.warn('Could not fetch proactive greeting:', err);
      }
    };

    fetchGreeting();
  }, [user, voiceReadbackEnabled, handsFreeEnabled, speakText]);

  // Fallback initial welcome message if no greeting fetched yet
  useEffect(() => {
    if (messages.length === 0 && user) {
      const firstName = user.full_name?.split(' ')[0] || 'there';
      setMessages([
        {
          id: 'welcome-msg',
          sender: 'assistant',
          content: `Hello ${firstName}! I am **Sync**, your floating AI companion.\n\nI operate across your entire workspace in **${activeRole.toUpperCase()}** mode. You can tell me to:\n• *"Plan my day"* or *"Schedule 2 hours for DSA tomorrow"*\n• *"Help me set a goal to master distributed systems"*\n• *"Create a to-do list for tomorrow: Project docs, DBMS study, and revision"*\n• *"Send an email to my professor regarding assignment extension"*\n• *"Analyze my shared screen"* by clicking the monitor icon below.`,
          timestamp: new Date(),
        },
      ]);
    }
  }, [user, activeRole, messages.length]);

  const toggleListening = () => {
    if (!isVoiceSupported) {
      alert('Speech recognition is not supported in this browser. Please try Google Chrome or Edge.');
      return;
    }
    if (isListening) {
      stopListening();
      onStatusChange?.('idle');
    } else {
      startListening();
      onStatusChange?.('listening');
    }
  };

  // Screen Capture Logic
  const startScreenShare = async () => {
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: true as any,
        audio: false,
      });

      screenStreamRef.current = stream;
      setIsScreenSharing(true);

      // Listen for user stopping screen share from browser banner
      stream.getVideoTracks()[0].onended = () => {
        stopScreenShare();
      };

      // Grab snapshot preview
      const video = document.createElement('video');
      video.srcObject = stream;
      video.play();

      video.onloadedmetadata = () => {
        const canvas = document.createElement('canvas');
        canvas.width = Math.min(video.videoWidth, 1280);
        canvas.height = Math.min(video.videoHeight, 720);
        const ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
          setScreenPreviewUrl(canvas.toDataURL('image/jpeg', 0.6));
        }
      };
    } catch (err) {
      console.error('Screen capture rejected or failed:', err);
      setIsScreenSharing(false);
    }
  };

  const stopScreenShare = () => {
    if (screenStreamRef.current) {
      screenStreamRef.current.getTracks().forEach((t) => t.stop());
      screenStreamRef.current = null;
    }
    setIsScreenSharing(false);
    setScreenPreviewUrl(null);
  };

  const captureActiveFrameBase64 = (): string | null => {
    if (!screenStreamRef.current) return null;
    const track = screenStreamRef.current.getVideoTracks()[0];
    if (!track || track.readyState !== 'live') return null;

    try {
      const video = document.createElement('video');
      video.srcObject = screenStreamRef.current;
      video.play();
      const canvas = document.createElement('canvas');
      canvas.width = 1280;
      canvas.height = 720;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(video, 0, 0, 1280, 720);
        const dataUrl = canvas.toDataURL('image/jpeg', 0.7);
        return dataUrl.split(',')[1] || null;
      }
    } catch {
      return null;
    }
    return null;
  };

  // Send Message through Central Multi-Agent Pipeline
  const handleSend = async (overrideText?: string) => {
    const textToSend = (overrideText ?? input).trim();
    if (!textToSend || busy) return;

    setInput('');
    setBusy(true);
    onStatusChange?.('thinking');

    let screenPayload: any = null;
    if (isScreenSharing) {
      const frameBase64 = captureActiveFrameBase64();
      if (frameBase64) {
        screenPayload = {
          image_data: frameBase64,
          format: 'jpeg',
          active_tab: activeTab,
        };
      }
    }

    const userMsg: PetMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      content: textToSend,
      timestamp: new Date(),
      hasScreen: !!screenPayload,
    };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const res = await api.post('/agents/chat', {
        message: textToSend,
        conversation_id: conversationId,
        active_role: activeRole,
        screen_context: screenPayload,
      });

      setConversationId(res.data.conversation_id);
      setActiveSpecialist(res.data.detected_intent?.replace(/_/g, ' ').toUpperCase() || 'SYNCHRONIZER');
      onStatusChange?.(res.data.pending_approvals?.length > 0 ? 'awaiting_approval' : 'completed');

      const assistantMsg: PetMessage = {
        id: `asst-${Date.now()}`,
        sender: 'assistant',
        content: res.data.reply,
        intent: res.data.detected_intent,
        latency: res.data.latency_ms,
        steps: res.data.steps,
        approvals: res.data.pending_approvals,
        plan: res.data.transaction_plan,
        card: res.data.clarification_card,
        agent_trace: res.data.agent_trace,
        spoken_reply: res.data.spoken_reply,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);

      if (res.data.clarification_card) {
        setActiveIntakeSessionId(res.data.clarification_card.session_id);
      }

      const textToSpeak = res.data.spoken_reply || res.data.reply;
      if ((voiceReadbackEnabled || handsFreeEnabled) && textToSpeak) {
        speakText(textToSpeak);
      }

      // Refresh parent app view data (tasks, habits, calendar, etc.)
      if (onRefreshData) {
        await onRefreshData();
      }
    } catch (err: any) {
      console.error('Agent chat error:', err);
      onStatusChange?.('error');
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: 'assistant',
          content: 'Sorry, I encountered an error connecting to the LifeSync agent orchestrator. Please verify your local backend connection.',
          timestamp: new Date(),
        },
      ]);
    } finally {
      setBusy(false);
    }
  };

  const handleClarificationResponse = async (
    selectedOptions: string[],
    customText?: string,
    skipAndGenerate: boolean = false
  ) => {
    if (activeIntakeSessionId) {
      setBusy(true);
      onStatusChange?.('thinking');
      try {
        const res = await api.post(`/intake/${activeIntakeSessionId}/respond`, {
          selected_options: selectedOptions,
          custom_text: customText,
          skip_and_generate: skipAndGenerate,
          role_context: activeRole,
        });

        if (res.data.clarification_card) {
          const cardMsg: PetMessage = {
            id: `card-${Date.now()}`,
            sender: 'assistant',
            content: res.data.reply || '',
            card: res.data.clarification_card,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, cardMsg]);
          if (voiceReadbackEnabled) {
            speakText(res.data.reply || res.data.clarification_card.question);
          }
        } else if (res.data.transaction_plan) {
          const planMsg: PetMessage = {
            id: `plan-${Date.now()}`,
            sender: 'assistant',
            content: res.data.reply || 'Blueprint plan compiled and simulated:',
            plan: res.data.transaction_plan,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, planMsg]);
          setActiveIntakeSessionId(null);
          if (voiceReadbackEnabled) {
            speakText('Your blueprint plan has been simulated. You can review the diff and apply or reject it.');
          }
        }
        if (onRefreshData) {
          await onRefreshData();
        }
      } catch (err: any) {
        console.error('Intake respond error:', err);
      } finally {
        setBusy(false);
        onStatusChange?.('idle');
      }
    } else {
      const text = customText || selectedOptions.join(', ');
      await handleSend(text);
    }
  };

  const handleApprovalDecision = async (approvalId: string, decision: 'approved' | 'rejected') => {
    try {
      await api.post(`/agents/approvals/${approvalId}/decide`, { decision });
      if (decision === 'approved') {
        confetti({ particleCount: 45, spread: 60, origin: { y: 0.7 } });
      }
      if (onDecideApproval) {
        await onDecideApproval(approvalId, decision);
      }
      if (onRefreshData) {
        await onRefreshData();
      }
      // Update local message approvals state
      setMessages((prev) =>
        prev.map((msg) => {
          if (!msg.approvals) return msg;
          return {
            ...msg,
            approvals: msg.approvals.map((ap) => (ap.id === approvalId ? { ...ap, status: decision } : ap)),
          };
        })
      );
    } catch (err) {
      console.error('Failed to decide approval:', err);
    }
  };

  // Quick Action Prompts
  const quickPrompts = [
    'Give me a brief summary of what I should do today',
    'Create a clear concise to-do list for tomorrow',
    'Plan my day with focus time blocks',
    'Analyze my screen and recommend next action',
  ];

  return (
    <>
      {/* 1. FLOATING COMPANION BUTTON / ORB (BOTTOM RIGHT) */}
      <div className="fixed bottom-6 right-6 z-50 flex items-center gap-3 select-none">
        {/* Subtle status tooltip when closed */}
        {!isOpen && (
          <motion.div
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/90 border border-slate-700/80 backdrop-blur-md shadow-xl text-xs text-slate-300 pointer-events-none"
          >
            <span
              className={`w-2 h-2 rounded-full ${
                busy ? 'bg-amber-400 animate-ping' : isScreenSharing ? 'bg-cyan-400 animate-pulse' : 'bg-emerald-400'
              }`}
            />
            <span className="font-medium text-slate-200">Sync AI</span>
            <span className="text-[10px] text-slate-400 capitalize">({activeRole})</span>
            {approvals.length > 0 && (
              <span className="px-1.5 py-0.2 rounded-full bg-amber-500 text-slate-950 font-bold text-[10px]">
                {approvals.length}
              </span>
            )}
          </motion.div>
        )}

        <motion.button
          onClick={() => setIsOpen(!isOpen)}
          whileHover={{ scale: 1.08 }}
          whileTap={{ scale: 0.94 }}
          className={`relative group w-14 h-14 rounded-2xl flex items-center justify-center shadow-2xl transition-all duration-300 ${
            isOpen
              ? 'bg-slate-800 text-slate-200 border border-slate-700'
              : 'bg-gradient-to-tr from-indigo-600 via-indigo-500 to-violet-500 text-white shadow-indigo-500/30'
          }`}
          aria-label="Toggle LifeSync AI Floating Companion"
        >
          {/* Animated 3D Glow Aura */}
          <div
            className={`absolute -inset-1 rounded-2xl filter blur-md opacity-60 transition duration-500 group-hover:opacity-100 ${
              busy
                ? 'bg-gradient-to-r from-amber-500 to-orange-500 animate-spin'
                : isScreenSharing
                ? 'bg-gradient-to-r from-cyan-400 to-blue-500 animate-pulse'
                : 'bg-gradient-to-r from-indigo-500 via-violet-500 to-cyan-400'
            }`}
          />

          <div className="relative z-10 flex items-center justify-center">
            {isOpen ? (
              <ChevronDown className="w-6 h-6 transition-transform group-hover:translate-y-0.5" />
            ) : (
              <div className="relative">
                <Bot className="w-7 h-7" />
                {busy && (
                  <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-amber-400 ring-2 ring-slate-900 animate-ping" />
                )}
                {approvals.length > 0 && !busy && (
                  <span className="absolute -top-1.5 -right-1.5 px-1 rounded-full bg-amber-400 text-slate-950 font-bold text-[9px] ring-2 ring-slate-900">
                    {approvals.length}
                  </span>
                )}
              </div>
            )}
          </div>
        </motion.button>
      </div>

      {/* 2. EXPANDABLE FLOATING CONVERSATIONAL DRAWER */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className={`fixed right-6 bottom-24 z-50 flex flex-col rounded-3xl bg-slate-900/95 border border-slate-700/80 shadow-2xl backdrop-blur-2xl overflow-hidden transition-all duration-300 ${
              isExpanded
                ? 'w-[calc(100vw-48px)] sm:w-[600px] h-[78vh] max-h-[850px]'
                : 'w-[calc(100vw-48px)] sm:w-[420px] h-[580px]'
            }`}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-950/60">
              <div className="flex items-center gap-2.5">
                <div className="relative flex items-center justify-center w-8 h-8 rounded-xl bg-indigo-600/20 border border-indigo-500/30 text-indigo-400">
                  <Sparkles className="w-4 h-4" />
                  <span
                    className={`absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full ${
                      busy ? 'bg-amber-400' : isScreenSharing ? 'bg-cyan-400 animate-pulse' : 'bg-emerald-400'
                    }`}
                  />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-xs text-slate-100">Sync Companion</span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 capitalize">
                      {activeRole}
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-400 font-mono truncate max-w-[190px]">
                    {busy ? 'Orchestrating agents...' : activeSpecialist}
                  </p>
                </div>
              </div>

              {/* Controls */}
              <div className="flex items-center gap-1">
                {isScreenSharing && (
                  <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 text-[10px]">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
                    Screen Shared
                  </span>
                )}
                {/* Hands-Free Voice Mode Toggle */}
                <button
                  type="button"
                  onClick={toggleHandsFree}
                  className={`px-2 py-0.5 rounded-lg text-[10px] font-semibold flex items-center gap-1 transition ${
                    handsFreeEnabled
                      ? 'bg-purple-600/30 text-purple-300 border border-purple-500/50 shadow-sm shadow-purple-500/20'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800 border border-slate-800'
                  }`}
                  title={handsFreeEnabled ? 'Hands-Free Voice Active (click to disable)' : 'Enable Hands-Free Voice Mode'}
                >
                  <Mic className={`w-3 h-3 ${handsFreeEnabled ? 'text-purple-400 animate-pulse' : ''}`} />
                  <span>Hands-Free</span>
                </button>
                <button
                  type="button"
                  onClick={() => setVoiceReadbackEnabled(!voiceReadbackEnabled)}
                  className={`p-1.5 rounded-lg transition ${
                    voiceReadbackEnabled
                      ? 'text-purple-300 bg-purple-900/40 border border-purple-500/40 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                  }`}
                  title={voiceReadbackEnabled ? 'Voice readback active (click to mute)' : 'Enable voice readback'}
                >
                  {voiceReadbackEnabled ? <Volume2 className="w-3.5 h-3.5 text-purple-400" /> : <VolumeX className="w-3.5 h-3.5" />}
                </button>
                <button
                  onClick={() => setIsExpanded(!isExpanded)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
                  title={isExpanded ? 'Restore size' : 'Expand panel'}
                >
                  {isExpanded ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition"
                  title="Minimize companion"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Screen Share Banner (Active Preview) */}
            {isScreenSharing && screenPreviewUrl && (
              <div className="relative px-4 py-2 bg-slate-950/80 border-b border-cyan-500/30 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Monitor className="w-4 h-4 text-cyan-400 animate-pulse" />
                  <span className="text-[11px] text-cyan-300 font-medium">Vision Stream Active</span>
                </div>
                <button
                  onClick={stopScreenShare}
                  className="px-2 py-0.5 rounded bg-rose-500/20 border border-rose-500/40 text-rose-300 text-[10px] font-semibold hover:bg-rose-500/30 transition"
                >
                  Stop Sharing
                </button>
              </div>
            )}

            {/* Proactive Suggestion Banner */}
            {summary && ((summary.metrics?.overdue_tasks ?? 0) > 0 || (summary.email_intelligence?.unread_count ?? 0) > 0) && (
              <div className="px-3.5 py-2 bg-gradient-to-r from-amber-950/40 via-indigo-950/40 to-slate-950/60 border-b border-amber-500/30 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2 truncate pr-2">
                  <Sparkles className="w-3.5 h-3.5 text-amber-400 shrink-0 animate-pulse" />
                  <span className="text-[11px] text-amber-200 truncate">
                    {(summary.metrics?.overdue_tasks ?? 0) > 0
                      ? `${summary.metrics.overdue_tasks} overdue tasks & ${summary.email_intelligence?.unread_count || 0} unread emails need review`
                      : `${summary.email_intelligence?.unread_count || 0} unread emails waiting in inbox`}
                  </span>
                </div>
                <button
                  onClick={() =>
                    handleSend(
                      'Sync, help me address my priority items: create an actionable schedule for my overdue tasks and unread messages.'
                    )
                  }
                  disabled={busy}
                  className="shrink-0 px-2 py-0.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 font-semibold text-[10px] border border-amber-500/40 transition cursor-pointer"
                >
                  Draft Plan
                </button>
              </div>
            )}

            {/* Conversation Stream */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {msg.sender === 'assistant' && (
                    <div className="flex-shrink-0 w-7 h-7 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 mt-1">
                      <Bot className="w-3.5 h-3.5" />
                    </div>
                  )}

                  <div
                    className={`max-w-[85%] rounded-2xl p-3 shadow-md ${
                      msg.sender === 'user'
                        ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white rounded-tr-none'
                        : 'bg-slate-950/80 border border-slate-800 text-slate-200 rounded-tl-none'
                    }`}
                  >
                    {msg.sender === 'user' ? (
                      <div>
                        {msg.hasScreen && (
                          <div className="flex items-center gap-1 text-[10px] text-cyan-200 font-semibold mb-1">
                            <Monitor className="w-3 h-3" /> Screen Frame Included
                          </div>
                        )}
                        <p className="text-xs whitespace-pre-wrap">{msg.content}</p>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {/* Agent Collaboration Trace Strip */}
                        {msg.agent_trace && msg.agent_trace.length > 0 && (
                          <AgentCollaborationStrip trace={msg.agent_trace} />
                        )}

                        <MarkdownContent content={msg.content} />

                        {/* Proactive Quick Suggestion Chips */}
                        {msg.quick_suggestions && msg.quick_suggestions.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 pt-1">
                            {msg.quick_suggestions.map((sug, sIdx) => (
                              <button
                                key={sIdx}
                                onClick={() => handleSend(sug)}
                                disabled={busy}
                                className="px-2.5 py-1 rounded-full bg-purple-900/40 hover:bg-purple-800/60 text-purple-200 border border-purple-500/30 text-[10px] font-medium transition cursor-pointer flex items-center gap-1 shadow-sm"
                              >
                                <Sparkles className="w-2.5 h-2.5 text-purple-400" />
                                {sug}
                              </button>
                            ))}
                          </div>
                        )}

                        {/* Transparent Step Logs */}
                        {msg.steps && msg.steps.length > 0 && (
                          <div className="pt-2 border-t border-slate-800/80">
                            <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1.5">
                              <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Multi-Agent Execution Steps ({msg.steps.length})
                            </div>
                            <div className="space-y-1">
                              {msg.steps.map((step, sIdx) => (
                                <div
                                  key={sIdx}
                                  className="flex items-center justify-between px-2 py-1 rounded bg-slate-900/60 border border-slate-800 text-[10px] text-slate-300"
                                >
                                  <span className="font-semibold text-indigo-300">{step.agent_name}</span>
                                  <span className="font-mono text-slate-400">{step.tool_name}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Interactive Action Approval Cards */}
                        {msg.approvals && msg.approvals.length > 0 && (
                          <div className="space-y-2 pt-2 border-t border-slate-800">
                            <div className="flex items-center gap-1.5 text-[10px] font-bold text-amber-400 uppercase tracking-wider">
                              <ShieldCheck className="w-3.5 h-3.5" /> High-Risk Action Requires Approval
                            </div>
                            {msg.approvals.map((ap) => (
                              <div
                                key={ap.id}
                                className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/30 space-y-2"
                              >
                                <div className="text-[11px] font-medium text-amber-200">
                                  {ap.action_summary}
                                </div>
                                <div className="flex items-center justify-between text-[10px] text-slate-400">
                                  <span>Agent: <strong className="text-slate-300">{ap.agent_name}</strong></span>
                                  <span>Tool: <code className="text-amber-300">{ap.tool_name}</code></span>
                                </div>
                                {ap.status === 'pending' ? (
                                  <div className="flex items-center gap-2 pt-1">
                                    <button
                                      onClick={() => handleApprovalDecision(ap.id, 'approved')}
                                      className="flex-1 flex items-center justify-center gap-1 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-[10px] transition"
                                    >
                                      <Check className="w-3 h-3" /> Approve & Execute
                                    </button>
                                    <button
                                      onClick={() => handleApprovalDecision(ap.id, 'rejected')}
                                      className="flex-1 flex items-center justify-center gap-1 py-1 rounded-lg bg-rose-600/30 hover:bg-rose-600/50 text-rose-300 font-semibold text-[10px] transition border border-rose-500/30"
                                    >
                                      <X className="w-3 h-3" /> Reject
                                    </button>
                                  </div>
                                ) : (
                                  <div className="text-[10px] font-semibold capitalize text-slate-400 pt-1">
                                    Status: <span className={ap.status === 'approved' ? 'text-emerald-400' : 'text-rose-400'}>{ap.status}</span>
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Shadow Execution Plan & Reversible Diff Card */}
                        {msg.plan && (
                          <div className="pt-2">
                            <ShadowDiffCard
                              plan={msg.plan}
                              onRefreshData={onRefreshData}
                              compact
                            />
                          </div>
                        )}

                        {/* Conversational Zero-Form Intake Card */}
                        {msg.card && (
                          <div className="pt-2">
                            <ClarificationCard
                              card={msg.card}
                              onRespond={(opts, custom, skip) => handleClarificationResponse(opts, custom, skip)}
                              onSpeakQuestion={(text) => speakText(text)}
                            />
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {msg.sender === 'user' && (
                    <div className="flex-shrink-0 w-7 h-7 rounded-xl bg-indigo-600 flex items-center justify-center text-white mt-1">
                      <UserIcon className="w-3.5 h-3.5" />
                    </div>
                  )}
                </div>
              ))}

              {busy && (
                <div className="flex items-center gap-3">
                  <div className="w-7 h-7 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 animate-spin">
                    <RefreshCw className="w-3.5 h-3.5" />
                  </div>
                  <div className="px-3 py-2 rounded-2xl bg-slate-950/80 border border-slate-800 text-xs text-indigo-300 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-indigo-400 animate-ping" />
                    Thinking and executing agent tasks...
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Quick Action Pills */}
            <div className="px-3 py-2 border-t border-slate-800/80 bg-slate-950/40 flex items-center gap-1.5 overflow-x-auto no-scrollbar">
              {quickPrompts.map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(p)}
                  disabled={busy}
                  className="flex-shrink-0 px-2.5 py-1 rounded-full bg-slate-800/80 hover:bg-slate-700/80 text-[10px] text-slate-300 border border-slate-700/50 hover:border-indigo-500/40 transition disabled:opacity-50"
                >
                  {p}
                </button>
              ))}
            </div>

            {/* Input Bar */}
            <div className="p-3 bg-slate-950/90 border-t border-slate-800">
              <div className="flex items-center gap-2 px-3 py-2 rounded-2xl bg-slate-900 border border-slate-800 focus-within:border-indigo-500/50 transition">
                {/* Screen Share Button */}
                <button
                  onClick={isScreenSharing ? stopScreenShare : startScreenShare}
                  className={`p-1.5 rounded-xl transition ${
                    isScreenSharing
                      ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm shadow-cyan-500/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                  }`}
                  title={isScreenSharing ? 'Stop sharing screen' : 'Share screen with AI companion'}
                >
                  {isScreenSharing ? <MonitorOff className="w-4 h-4" /> : <Monitor className="w-4 h-4" />}
                </button>

                {/* Voice Input Button */}
                <button
                  onClick={toggleListening}
                  className={`p-1.5 rounded-xl transition ${
                    isListening
                      ? 'bg-rose-500 text-white animate-pulse'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                  }`}
                  title={isListening ? 'Stop listening' : 'Start voice input'}
                >
                  {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                </button>

                {/* Text Input */}
                <input
                  type="text"
                  value={input}
                  onChange={(e) => {
                    cancelSpeaking();
                    setInput(e.target.value);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  placeholder={
                    handsFreeEnabled
                      ? 'Hands-Free active: Speak or type anytime...'
                      : isListening
                      ? 'Listening to your voice...'
                      : isScreenSharing
                      ? 'Ask about what is on your screen...'
                      : 'Tell Sync what you need done...'
                  }
                  disabled={busy}
                  className="flex-1 bg-transparent text-xs text-slate-100 placeholder-slate-500 outline-none"
                />

                {/* Send Button */}
                <button
                  onClick={() => handleSend()}
                  disabled={!input.trim() || busy}
                  className="p-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white transition disabled:opacity-40 disabled:hover:bg-indigo-600"
                  aria-label="Send message to AI companion"
                >
                  <Send className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};
