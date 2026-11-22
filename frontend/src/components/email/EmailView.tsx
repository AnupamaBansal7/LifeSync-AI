import React, { useEffect, useState } from 'react';
import {
  Archive,
  ArrowLeft,
  ArrowRight,
  Check,
  CheckCircle2,
  FileText,
  Forward,
  Inbox,
  Mail,
  Paperclip,
  Plus,
  RefreshCw,
  Reply,
  Search,
  Send,
  Sparkles,
  Star,
  X,
} from 'lucide-react';
import { api } from '../../lib/api';
import type { EmailMessage } from '../../types';
import type { NavTab } from '../layout/Sidebar';

interface EmailViewProps {
  onNavigateTab?: (tab: NavTab | string) => void;
  onRefreshData?: () => Promise<void>;
}

export const EmailView: React.FC<EmailViewProps> = ({ onNavigateTab: _onNavigateTab, onRefreshData }) => {
  const [folder, setFolder] = useState<string>('inbox');
  const [searchQuery, setSearchQuery] = useState('');
  const [emails, setEmails] = useState<EmailMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState<EmailMessage | null>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);

  // Provider Info
  const [providerInfo, setProviderInfo] = useState<{
    connected: boolean;
    provider: string;
    account_email?: string;
    unread_count: number;
    important_count: number;
  }>({
    connected: false,
    provider: 'simulation',
    unread_count: 0,
    important_count: 0,
  });

  // Compose Modal State
  const [showCompose, setShowCompose] = useState(false);
  const [composeTo, setComposeTo] = useState('');
  const [composeSubject, setComposeSubject] = useState('');
  const [composeBody, setComposeBody] = useState('');
  const [sending, setSending] = useState(false);
  const [sendSuccess, setSendSuccess] = useState(false);

  // Reply / Forward State
  const [replyMode, setReplyMode] = useState<'reply' | 'forward' | null>(null);
  const [replyText, setReplyText] = useState('');
  const [replying, setReplying] = useState(false);

  // AI Task Extraction State
  const [extractingTask, setExtractingTask] = useState(false);
  const [extractedTaskResult, setExtractedTaskResult] = useState<any>(null);

  // Pagination
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 15;

  const fetchEmails = async () => {
    setLoading(true);
    try {
      const res = await api.get('/email/messages', {
        params: {
          folder,
          q: searchQuery,
          page,
          page_size: pageSize,
        },
      });
      setEmails(res.data.messages || []);
      setTotalCount(res.data.total_count || 0);
      setProviderInfo({
        connected: res.data.connected,
        provider: res.data.provider,
        account_email: res.data.account_email,
        unread_count: res.data.unread_count || 0,
        important_count: res.data.important_count || 0,
      });

      // Auto-select first email if none selected
      if (!selectedEmail && res.data.messages?.length > 0) {
        handleSelectEmail(res.data.messages[0]);
      }
    } catch {
      // Fallback
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmails();
  }, [folder, page]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchEmails();
  };

  const handleSelectEmail = async (email: EmailMessage) => {
    setSelectedEmail(email);
    setLoadingDetails(true);
    setExtractedTaskResult(null);
    setReplyMode(null);
    try {
      const res = await api.get(`/email/messages/${email.id}`);
      if (res.data?.email) {
        setSelectedEmail(res.data.email);
      }
    } catch {
      // Keep existing email payload
    } finally {
      setLoadingDetails(false);
    }
  };

  const handleSendEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!composeTo.trim() || !composeSubject.trim()) return;

    setSending(true);
    try {
      await api.post('/email/send', {
        to: composeTo,
        subject: composeSubject,
        body: composeBody,
      });
      setSendSuccess(true);
      setTimeout(() => {
        setSendSuccess(false);
        setShowCompose(false);
        setComposeTo('');
        setComposeSubject('');
        setComposeBody('');
        fetchEmails();
      }, 1500);
    } catch {
      alert('Failed to send email. Check provider settings.');
    } finally {
      setSending(false);
    }
  };

  const handleSendReply = async () => {
    if (!selectedEmail || !replyText.trim()) return;
    setReplying(true);
    try {
      if (replyMode === 'forward') {
        await api.post('/email/forward', {
          message_id: selectedEmail.id,
          to: composeTo,
          comment: replyText,
        });
      } else {
        await api.post('/email/reply', {
          message_id: selectedEmail.id,
          body: replyText,
          reply_all: replyMode === 'reply',
        });
      }
      setReplyMode(null);
      setReplyText('');
      alert('Message sent successfully!');
      fetchEmails();
    } catch {
      alert('Failed to send message.');
    } finally {
      setReplying(false);
    }
  };

  const handleExtractTasks = async () => {
    if (!selectedEmail) return;
    setExtractingTask(true);
    try {
      const res = await api.post('/email/extract-tasks', {
        message_id: selectedEmail.id,
      });
      setExtractedTaskResult(res.data);
      if (onRefreshData) onRefreshData();
    } catch {
      alert('Could not extract tasks from this message.');
    } finally {
      setExtractingTask(false);
    }
  };

  const handleDraftAIReply = () => {
    if (!selectedEmail) return;
    const bodyLower = (selectedEmail.body || selectedEmail.snippet || '').toLowerCase();
    let draft = `Hi ${selectedEmail.sender_name || 'there'},\n\nThank you for reaching out.\n`;
    if (bodyLower.includes('meeting') || bodyLower.includes('sync')) {
      draft += 'I have checked my schedule and would be happy to sync tomorrow afternoon. Let me know if 3:00 PM works for you.\n\nBest regards,\nAlex';
    } else if (bodyLower.includes('deadline') || bodyLower.includes('submit')) {
      draft += 'I am currently finalizing the required deliverables and will ensure submission before the scheduled deadline.\n\nBest regards,\nAlex';
    } else {
      draft += 'I received your email and will follow up shortly with the requested information.\n\nBest regards,\nAlex';
    }
    setReplyMode('reply');
    setReplyText(draft);
  };

  const folders = [
    { id: 'inbox', label: 'Inbox', icon: Inbox, count: providerInfo.unread_count },
    { id: 'important', label: 'Important', icon: Star, count: providerInfo.important_count },
    { id: 'unread', label: 'Unread', icon: Mail },
    { id: 'sent', label: 'Sent Messages', icon: Send },
    { id: 'drafts', label: 'Drafts', icon: FileText },
    { id: 'archived', label: 'Archive', icon: Archive },
  ];

  return (
    <div className="space-y-6 pb-12 select-none">
      {/* 1. Header & Provider Connection Pill */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs uppercase tracking-wider mb-1">
            <Mail className="w-4 h-4" /> Communication Hub
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-white flex items-center gap-2">
            <span>Email Intelligence Workspace</span>
            <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-violet-950/80 border border-violet-800 text-violet-300 uppercase">
              {providerInfo.provider}
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Integrated Gmail & Outlook client with automated deadline extraction and AI-assisted reply drafting.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowCompose(true)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Compose Email</span>
          </button>
          <button
            onClick={fetchEmails}
            disabled={loading}
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 hover:text-white transition cursor-pointer"
            title="Refresh Inbox"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* 2. Main 3-Column Layout: Folders + List + Reading Pane */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 min-h-[640px]">
        {/* Left Column: Folders (3 Cols) */}
        <div className="md:col-span-3 space-y-4">
          <div className="p-4 rounded-3xl bg-slate-900/70 border border-slate-800 backdrop-blur-xl space-y-2">
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider px-2 mb-2">
              Mailboxes
            </div>
            {folders.map((f) => {
              const Icon = f.icon;
              const isActive = folder === f.id;
              return (
                <button
                  key={f.id}
                  onClick={() => {
                    setFolder(f.id);
                    setPage(1);
                  }}
                  className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-2xl text-xs font-medium transition cursor-pointer ${
                    isActive
                      ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-md shadow-indigo-600/20'
                      : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className="w-4 h-4" />
                    <span>{f.label}</span>
                  </div>
                  {f.count !== undefined && f.count > 0 && (
                    <span
                      className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full ${
                        isActive ? 'bg-white/20 text-white' : 'bg-slate-800 text-indigo-300'
                      }`}
                    >
                      {f.count}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Connected Account Card */}
          <div className="p-4 rounded-3xl bg-slate-900/60 border border-slate-800 text-xs space-y-2">
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              Connected Identity
            </div>
            <div className="p-2.5 rounded-2xl bg-slate-950/80 border border-slate-800/80 flex items-center gap-2">
              <div className="w-8 h-8 rounded-xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold">
                @
              </div>
              <div className="overflow-hidden">
                <div className="font-semibold text-white truncate text-[11px]">
                  {providerInfo.account_email || 'connected-user@gmail.com'}
                </div>
                <div className="text-[10px] text-emerald-400 font-mono">
                  ● {providerInfo.provider.toUpperCase()} ACTIVE
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Center Column: Email List (4 Cols) */}
        <div className="md:col-span-4 flex flex-col rounded-3xl bg-slate-900/70 border border-slate-800 backdrop-blur-xl overflow-hidden">
          {/* Search Bar */}
          <div className="p-3 border-b border-slate-800/80 bg-slate-950/40">
            <form onSubmit={handleSearchSubmit} className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-3 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search subject, sender, keywords..."
                className="w-full pl-8 pr-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:border-indigo-500 outline-none"
              />
            </form>
          </div>

          {/* Email Items List */}
          <div className="flex-1 overflow-y-auto divide-y divide-slate-800/60 max-h-[560px]">
            {loading ? (
              <div className="p-8 text-center text-xs text-slate-500 animate-pulse">
                Fetching emails from {providerInfo.provider}...
              </div>
            ) : emails.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500">
                No messages found in {folder}.
              </div>
            ) : (
              emails.map((msg) => {
                const isSelected = selectedEmail?.id === msg.id;
                return (
                  <div
                    key={msg.id}
                    onClick={() => handleSelectEmail(msg)}
                    className={`p-3.5 transition cursor-pointer flex flex-col gap-1 ${
                      isSelected
                        ? 'bg-indigo-950/40 border-l-4 border-l-indigo-500'
                        : msg.is_read
                        ? 'hover:bg-slate-850/50 text-slate-300'
                        : 'bg-slate-950/50 hover:bg-slate-800/60 font-medium text-white'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-white truncate max-w-[170px]">
                        {msg.sender_name || msg.sender}
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        {new Date(msg.date).toLocaleDateString([], { month: 'short', day: 'numeric' })}
                      </span>
                    </div>

                    <div className="text-xs font-medium text-slate-200 truncate">
                      {msg.subject}
                    </div>

                    <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                      {msg.snippet}
                    </p>

                    <div className="flex items-center gap-2 mt-1">
                      {msg.has_attachments && (
                        <span className="flex items-center gap-1 text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                          <Paperclip className="w-2.5 h-2.5" /> File
                        </span>
                      )}
                      {!msg.is_read && (
                        <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Pagination Controls */}
          <div className="p-2.5 border-t border-slate-800/80 bg-slate-950/50 flex items-center justify-between text-xs text-slate-400">
            <span>
              Total: {totalCount} message{totalCount !== 1 ? 's' : ''}
            </span>
            <div className="flex items-center gap-1">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="p-1 rounded bg-slate-850 border border-slate-800 hover:text-white disabled:opacity-30 cursor-pointer"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
              </button>
              <span className="font-mono text-[11px] px-1">{page}</span>
              <button
                disabled={emails.length < pageSize}
                onClick={() => setPage((p) => p + 1)}
                className="p-1 rounded bg-slate-850 border border-slate-800 hover:text-white disabled:opacity-30 cursor-pointer"
              >
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Reading & AI Action Pane (5 Cols) */}
        <div className="md:col-span-5 rounded-3xl bg-slate-900/70 border border-slate-800 backdrop-blur-xl p-6 flex flex-col justify-between">
          {!selectedEmail ? (
            <div className="flex flex-col items-center justify-center h-full text-slate-500 text-xs py-16">
              <Mail className="w-10 h-10 mb-2 opacity-40" />
              <span>Select an email message to view details</span>
            </div>
          ) : loadingDetails ? (
            <div className="flex flex-col items-center justify-center h-full text-slate-500 text-xs py-16 animate-pulse">
              Loading message contents...
            </div>
          ) : (
            <div className="space-y-4">
              {/* Message Header */}
              <div className="pb-4 border-b border-slate-800/80 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-950 text-indigo-300 font-bold uppercase">
                    {selectedEmail.folder.toUpperCase()}
                  </span>
                  <span className="text-xs text-slate-400 font-mono">
                    {new Date(selectedEmail.date).toLocaleString()}
                  </span>
                </div>

                <h3 className="font-bold text-base text-white leading-snug">
                  {selectedEmail.subject}
                </h3>

                <div className="flex items-center gap-2 pt-1 text-xs">
                  <div className="w-7 h-7 rounded-full bg-indigo-600/30 text-indigo-300 flex items-center justify-center font-bold text-xs">
                    {(selectedEmail.sender_name || selectedEmail.sender).charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <div className="font-semibold text-white text-xs">
                      {selectedEmail.sender_name || selectedEmail.sender}
                    </div>
                    <div className="text-[11px] text-slate-400 font-mono">
                      &lt;{selectedEmail.sender}&gt;
                    </div>
                  </div>
                </div>
              </div>

              {/* AI Action Header Pill */}
              <div className="p-3 rounded-2xl bg-gradient-to-r from-violet-950/60 via-indigo-950/40 to-slate-900 border border-indigo-500/30 flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-indigo-400" />
                  <span className="text-xs font-semibold text-indigo-200">
                    AI Email-to-Task Agent
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <button
                    disabled={extractingTask}
                    onClick={handleExtractTasks}
                    className="px-2.5 py-1 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-[10px] font-bold shadow transition cursor-pointer disabled:opacity-50 flex items-center gap-1"
                  >
                    <CheckCircle2 className="w-3 h-3" />
                    <span>{extractingTask ? 'Extracting...' : 'Extract Tasks'}</span>
                  </button>
                  <button
                    onClick={handleDraftAIReply}
                    className="px-2.5 py-1 rounded-xl bg-slate-950 hover:bg-slate-800 text-indigo-300 text-[10px] font-bold border border-slate-800 transition cursor-pointer"
                  >
                    Draft Reply
                  </button>
                </div>
              </div>

              {/* Extracted Tasks Feedback Banner */}
              {extractedTaskResult && (
                <div className="p-3 rounded-2xl bg-emerald-950/50 border border-emerald-500/40 text-xs text-emerald-300 space-y-1">
                  <div className="font-bold flex items-center gap-1.5">
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Tasks Created Successfully</span>
                  </div>
                  <ul className="list-disc list-inside text-[11px] space-y-0.5">
                    {extractedTaskResult.tasks?.map((t: any) => (
                      <li key={t.id}>{t.title}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Message Body Content */}
              <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800/80 text-xs text-slate-200 leading-relaxed max-h-[240px] overflow-y-auto whitespace-pre-wrap">
                {selectedEmail.body || selectedEmail.snippet}
              </div>

              {/* Attachments Section */}
              {selectedEmail.attachments && selectedEmail.attachments.length > 0 && (
                <div className="space-y-1.5">
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    Attachments ({selectedEmail.attachments.length})
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {selectedEmail.attachments.map((att, i) => (
                      <div
                        key={i}
                        className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 flex items-center gap-2 text-xs text-slate-300 hover:text-white transition cursor-pointer"
                      >
                        <FileText className="w-3.5 h-3.5 text-indigo-400" />
                        <span>{att.name}</span>
                        <span className="text-[10px] text-slate-500">({att.size})</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Inline Reply / Forward Box */}
              {replyMode && (
                <div className="p-4 rounded-2xl bg-slate-950 border border-indigo-500/50 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-indigo-300 uppercase">
                      {replyMode === 'reply' ? 'Drafting Reply' : 'Forwarding Message'}
                    </span>
                    <button
                      onClick={() => setReplyMode(null)}
                      className="text-slate-400 hover:text-white"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  {replyMode === 'forward' && (
                    <input
                      type="email"
                      value={composeTo}
                      onChange={(e) => setComposeTo(e.target.value)}
                      placeholder="Forward to: recipient@example.com"
                      className="w-full px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white outline-none"
                    />
                  )}
                  <textarea
                    rows={4}
                    value={replyText}
                    onChange={(e) => setReplyText(e.target.value)}
                    placeholder="Type your response..."
                    className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white outline-none resize-none"
                  />
                  <div className="flex justify-end gap-2">
                    <button
                      onClick={() => setReplyMode(null)}
                      className="px-3 py-1.5 rounded-xl text-xs text-slate-400 hover:text-white"
                    >
                      Cancel
                    </button>
                    <button
                      disabled={replying}
                      onClick={handleSendReply}
                      className="px-4 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                    >
                      <Send className="w-3 h-3" />
                      <span>{replying ? 'Sending...' : 'Send Message'}</span>
                    </button>
                  </div>
                </div>
              )}

              {/* Action Buttons Toolbar */}
              {!replyMode && (
                <div className="pt-2 border-t border-slate-800/80 flex items-center gap-2">
                  <button
                    onClick={() => {
                      setReplyMode('reply');
                      setReplyText('');
                    }}
                    className="flex-1 py-2 px-3 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 text-xs text-slate-200 hover:text-white font-medium flex items-center justify-center gap-1.5 transition cursor-pointer"
                  >
                    <Reply className="w-3.5 h-3.5 text-indigo-400" />
                    <span>Reply</span>
                  </button>
                  <button
                    onClick={() => {
                      setReplyMode('forward');
                      setReplyText('');
                    }}
                    className="flex-1 py-2 px-3 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 text-xs text-slate-200 hover:text-white font-medium flex items-center justify-center gap-1.5 transition cursor-pointer"
                  >
                    <Forward className="w-3.5 h-3.5 text-violet-400" />
                    <span>Forward</span>
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 3. Compose Email Modal */}
      {showCompose && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-lg p-6 rounded-3xl bg-slate-900 border border-slate-800 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="font-bold text-white text-base flex items-center gap-2">
                <Mail className="w-4 h-4 text-indigo-400" /> New Outbound Message
              </h3>
              <button
                onClick={() => setShowCompose(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {sendSuccess ? (
              <div className="p-8 text-center text-emerald-400 text-sm font-semibold flex flex-col items-center gap-2">
                <CheckCircle2 className="w-8 h-8" />
                <span>Message dispatched successfully via {providerInfo.provider.toUpperCase()}!</span>
              </div>
            ) : (
              <form onSubmit={handleSendEmail} className="space-y-3">
                <div>
                  <label className="text-xs font-semibold text-slate-300">Recipient Email</label>
                  <input
                    type="email"
                    required
                    value={composeTo}
                    onChange={(e) => setComposeTo(e.target.value)}
                    placeholder="colleague@company.com"
                    className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:border-indigo-500 outline-none"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-300">Subject</label>
                  <input
                    type="text"
                    required
                    value={composeSubject}
                    onChange={(e) => setComposeSubject(e.target.value)}
                    placeholder="Project Deliverable / Meeting Follow-up"
                    className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:border-indigo-500 outline-none"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-300">Message Body</label>
                  <textarea
                    rows={6}
                    required
                    value={composeBody}
                    onChange={(e) => setComposeBody(e.target.value)}
                    placeholder="Write your email message..."
                    className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:border-indigo-500 outline-none resize-none"
                  />
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowCompose(false)}
                    className="px-4 py-2 rounded-xl text-xs text-slate-400 hover:text-white"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={sending}
                    className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>{sending ? 'Sending...' : 'Send Message'}</span>
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
