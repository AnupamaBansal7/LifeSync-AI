import React, { useEffect, useState } from 'react';
import confetti from 'canvas-confetti';
import { Sparkles } from 'lucide-react';

import { api } from './lib/api';
import type {
  ActionApproval,
  AgentRun,
  AICoreStatus,
  AutomationRule,
  CalendarEvent,
  DailyPlan,
  DashboardSummary,
  Goal,
  Habit,
  KnowledgeDocument,
  Memory,
  Notification,
  Role,
  Task,
  User,
} from './types';

// Layout & Workspaces
import { AgentsCatalog } from './components/agents/AgentsCatalog';
import { AnalyticsView } from './components/analytics/AnalyticsView';
import { AIAssistantWorkspace } from './components/assistant/AIAssistantWorkspace';
import { AutomationsView } from './components/automations/AutomationsView';
import { CalendarView } from './components/calendar/CalendarView';
import { PersonalizedDashboard } from './components/dashboard/PersonalizedDashboard';
import { EmailView } from './components/email/EmailView';
import { GoalsView } from './components/goals/GoalsView';
import { HabitsView } from './components/habits/HabitsView';
import { IntegrationsView } from './components/integrations/IntegrationsView';
import { CommandPalette } from './components/layout/CommandPalette';
import { Navbar } from './components/layout/Navbar';
import type { NavTab } from './components/layout/Sidebar';
import { Sidebar } from './components/layout/Sidebar';
import { MemoryView } from './components/memory/MemoryView';
import { NotificationsView } from './components/notifications/NotificationsView';
import { OnboardingWizard } from './components/onboarding/OnboardingWizard';
import { FloatingAIPet } from './components/pet/FloatingAIPet';
import { SettingsView } from './components/settings/SettingsView';
import { TasksView } from './components/tasks/TasksView';
import { MyWorkspaceView } from './components/workspace/MyWorkspaceView';

export default function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('lifesync_access_token'));
  const [user, setUser] = useState<User | null>(null);
  const [rolesCatalog, setRolesCatalog] = useState<Role[]>([]);
  const [activeRole, setActiveRole] = useState<string>('personal');
  const [activeTab, setActiveTab] = useState<NavTab>('overview');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [aiCoreStatus, setAiCoreStatus] = useState<AICoreStatus>('idle');
  const [loading, setLoading] = useState(false);

  // Auth Form State
  const [isRegister, setIsRegister] = useState(false);
  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authFullName, setAuthFullName] = useState('');
  const [authError, setAuthError] = useState('');

  // Domain States
  const [dashboardSummary, setDashboardSummary] = useState<DashboardSummary | null>(null);
  const [overviewAnalytics, setOverviewAnalytics] = useState<any>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [habits, setHabits] = useState<Habit[]>([]);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [dailyPlans, setDailyPlans] = useState<DailyPlan[]>([]);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [knowledgeDocs, setKnowledgeDocs] = useState<KnowledgeDocument[]>([]);
  const [automations, setAutomations] = useState<AutomationRule[]>([]);
  const [automationTemplates, setAutomationTemplates] = useState<any[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [approvals, setApprovals] = useState<ActionApproval[]>([]);
  const [agentCatalog, setAgentCatalog] = useState<any[]>([]);
  const [agentRuns, setAgentRuns] = useState<AgentRun[]>([]);

  // AI Assistant Chat State
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [chatHistory, setChatHistory] = useState<any[]>([]);
  const [agentBusy, setAgentBusy] = useState(false);

  // --- INITIAL DATA LOADING ---
  const loadUserData = async () => {
    try {
      const [meRes, catRes] = await Promise.all([
        api.get('/auth/me'),
        api.get('/users/roles/catalog'),
      ]);
      setUser(meRes.data);
      setRolesCatalog(catRes.data);

      if (meRes.data.is_onboarded) {
        const primary = meRes.data.roles?.find((r: any) => r.is_primary)?.role?.slug || 'personal';
        setActiveRole(primary);
        await refreshAllData(primary);
      }
    } catch {
      handleLogout();
    }
  };

  const refreshAllData = async (roleFilter: string) => {
    const q = roleFilter !== 'all' ? `?role_context=${roleFilter}` : '';
    try {
      const [
        dashRes,
        ovRes,
        tRes,
        gRes,
        hRes,
        evRes,
        dpRes,
        memRes,
        kRes,
        autoRes,
        autoTmplRes,
        notifRes,
        appRes,
        agentsRes,
        runsRes,
      ] = await Promise.all([
        api.get(`/dashboard/summary${q}`),
        api.get('/analytics/overview'),
        api.get(`/tasks${q}`),
        api.get(`/goals${q}`),
        api.get(`/habits${q}`),
        api.get(`/calendar/events${q}`),
        api.get('/calendar/daily-plans'),
        api.get('/memory'),
        api.get('/knowledge'),
        api.get('/automations'),
        api.get('/automations/templates'),
        api.get('/analytics/notifications'),
        api.get('/agents/approvals?status_filter=pending'),
        api.get('/agents/catalog'),
        api.get('/agents/runs?limit=15'),
      ]);

      setDashboardSummary(dashRes.data);
      setOverviewAnalytics(ovRes.data);
      setTasks(tRes.data);
      setGoals(gRes.data);
      setHabits(hRes.data);
      setEvents(evRes.data);
      setDailyPlans(dpRes.data);
      setMemories(memRes.data);
      setKnowledgeDocs(kRes.data);
      setAutomations(autoRes.data);
      setAutomationTemplates(autoTmplRes.data);
      setNotifications(notifRes.data);
      setApprovals(appRes.data);
      setAgentCatalog(agentsRes.data);
      setAgentRuns(runsRes.data);
    } catch {
      // Keep existing state on transient failures
    }
  };

  useEffect(() => {
    if (token) loadUserData();
  }, [token]);

  useEffect(() => {
    if (user?.is_onboarded) {
      refreshAllData(activeRole);
    }
  }, [activeRole]);

  useEffect(() => {
    if (agentBusy) {
      setAiCoreStatus('processing');
    } else if (approvals.length > 0) {
      setAiCoreStatus('awaiting_approval');
    } else {
      setAiCoreStatus('idle');
    }
  }, [agentBusy, approvals.length]);

  // --- AUTH ACTIONS ---
  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError('');
    setLoading(true);
    try {
      const endpoint = isRegister ? '/auth/register' : '/auth/login';
      const body = isRegister
        ? { email: authEmail, password: authPassword, full_name: authFullName }
        : { email: authEmail, password: authPassword };
      const res = await api.post(endpoint, body);
      const accToken = res.data.tokens.access_token;
      localStorage.setItem('lifesync_access_token', accToken);
      setToken(accToken);
    } catch (err: any) {
      setAuthError(err.response?.data?.detail || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('lifesync_access_token');
    setToken(null);
    setUser(null);
    setDashboardSummary(null);
    setChatHistory([]);
  };

  // --- ONBOARDING COMPLETION ---
  const handleCompleteOnboarding = async (onboardingData: any) => {
    setLoading(true);
    try {
      await api.post('/users/onboarding', onboardingData);
      confetti({ particleCount: 80, spread: 70, origin: { y: 0.6 } });
      await loadUserData();
      setActiveTab('overview');
    } finally {
      setLoading(false);
    }
  };

  // --- AI ASSISTANT CHAT ---
  const handleSendMessage = async (msg: string, role?: string) => {
    const text = msg.trim();
    if (!text || agentBusy) return;

    setAgentBusy(true);
    setAiCoreStatus('thinking');
    setChatHistory((prev) => [...prev, { sender: 'user', content: text }]);

    try {
      const res = await api.post('/agents/chat', {
        message: text,
        conversation_id: conversationId,
        active_role: role || activeRole,
      });

      setConversationId(res.data.conversation_id);
      setAiCoreStatus('completed');
      setChatHistory((prev) => [
        ...prev,
        {
          sender: 'assistant',
          content: res.data.reply,
          intent: res.data.detected_intent,
          latency: res.data.latency_ms,
          steps: res.data.steps,
          approvals: res.data.pending_approvals,
          plan: res.data.transaction_plan,
        },
      ]);
      await refreshAllData(activeRole);
    } catch {
      setAiCoreStatus('error');
    } finally {
      setAgentBusy(false);
    }
  };

  // --- DOMAIN MUTATIONS ---
  const handleToggleTask = async (taskId: string, currentStatus: string) => {
    const nextStatus = currentStatus === 'completed' ? 'todo' : 'completed';
    await api.patch(`/tasks/${taskId}`, { status: nextStatus });
    if (nextStatus === 'completed') {
      confetti({ particleCount: 35, spread: 50, origin: { y: 0.7 } });
    }
    await refreshAllData(activeRole);
  };

  const handleCreateTask = async (taskPayload: any) => {
    await api.post('/tasks', taskPayload);
    await refreshAllData(activeRole);
  };

  const handleUpdateTask = async (id: string, updates: any) => {
    await api.patch(`/tasks/${id}`, updates);
    await refreshAllData(activeRole);
  };

  const handleDeleteTask = async (id: string) => {
    await api.delete(`/tasks/${id}`);
    await refreshAllData(activeRole);
  };

  const handleCreateGoal = async (goalPayload: any) => {
    await api.post('/goals', goalPayload);
    await refreshAllData(activeRole);
  };

  const handleToggleMilestone = async (_goalId: string, milestoneId: string, current: boolean) => {
    await api.patch(`/milestones/${milestoneId}`, { is_completed: !current });
    if (!current) {
      confetti({ particleCount: 40, spread: 60, origin: { y: 0.6 } });
    }
    await refreshAllData(activeRole);
  };

  const handleCreateHabit = async (habitPayload: any) => {
    await api.post('/habits', habitPayload);
    await refreshAllData(activeRole);
  };

  const handleLogHabit = async (habitId: string) => {
    await api.post(`/habits/${habitId}/log`, {});
    confetti({ particleCount: 50, spread: 60, origin: { y: 0.8 } });
    await refreshAllData(activeRole);
  };

  const handleCreateEvent = async (eventPayload: any) => {
    await api.post('/calendar/events', eventPayload);
    await refreshAllData(activeRole);
  };

  const handleDeleteEvent = async (id: string) => {
    await api.delete(`/calendar/events/${id}`);
    await refreshAllData(activeRole);
  };

  const handleGeneratePlan = async () => {
    setActiveTab('assistant');
    await handleSendMessage('Plan my day and schedule time blocks aligned with my deadlines.');
  };

  const handleCreateRule = async (rulePayload: any) => {
    await api.post('/automations', rulePayload);
    await refreshAllData(activeRole);
  };

  const handleToggleRule = async (id: string, active: boolean) => {
    await api.patch(`/automations/${id}`, { is_active: active });
    await refreshAllData(activeRole);
  };

  const handleDeleteRule = async (id: string) => {
    await api.delete(`/automations/${id}`);
    await refreshAllData(activeRole);
  };

  const handleTriggerRule = async (id: string) => {
    const res = await api.post(`/automations/${id}/trigger`);
    await refreshAllData(activeRole);
    return res.data;
  };

  const handleAddMemory = async (memPayload: any) => {
    await api.post('/memory', memPayload);
    await refreshAllData(activeRole);
  };

  const handleSearchMemories = async (q: string): Promise<Memory[]> => {
    const res = await api.get(`/memory/search?q=${encodeURIComponent(q)}`);
    return res.data;
  };

  const handleIngestKnowledge = async (docPayload: any) => {
    await api.post('/knowledge/ingest', docPayload);
    await refreshAllData(activeRole);
  };

  const handleApproveAction = async (approvalId: string, decision: 'approved' | 'rejected') => {
    await api.post(`/agents/approvals/${approvalId}/decide`, { decision });
    confetti({ particleCount: 45, spread: 60, origin: { y: 0.5 } });
    await refreshAllData(activeRole);
  };

  const handleMarkNotificationRead = async (id: string) => {
    await api.patch(`/analytics/notifications/${id}/read`);
    await refreshAllData(activeRole);
  };

  const handleUpdateProfile = async (profilePayload: any) => {
    await api.patch('/users/profile', profilePayload);
    await loadUserData();
  };

  const handleUpdatePreferences = async (prefPayload: any) => {
    await api.patch('/users/preferences', prefPayload);
    await loadUserData();
  };

  const availableRoleSlugs = user?.roles?.map((r) => r.role?.slug || r.role_id) || ['personal'];

  // --- RENDER SCREEN: AUTHENTICATION ---
  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-slate-950 via-indigo-950/40 to-slate-950 select-none">
        <div className="w-full max-w-md rounded-3xl bg-slate-900/90 border border-slate-800 p-8 shadow-2xl backdrop-blur-xl">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-white shadow-lg shadow-indigo-500/30">
              <Sparkles className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white">LifeSync AI</h1>
              <p className="text-xs text-indigo-400 font-mono">Personal Life Management OS</p>
            </div>
          </div>

          <form onSubmit={handleAuth} className="space-y-4">
            {isRegister && (
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Full Name</label>
                <div className="relative">
                  <input
                    required
                    value={authFullName}
                    onChange={(e) => setAuthFullName(e.target.value)}
                    placeholder="e.g. Anupama Bansal"
                    className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:border-indigo-500 outline-none"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Email</label>
              <input
                type="email"
                required
                value={authEmail}
                onChange={(e) => setAuthEmail(e.target.value)}
                placeholder="you@domain.com"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:border-indigo-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Password</label>
              <input
                type="password"
                required
                minLength={8}
                value={authPassword}
                onChange={(e) => setAuthPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:border-indigo-500 outline-none"
              />
            </div>

            {authError && (
              <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs">
                {authError}
              </div>
            )}

            <button
              disabled={loading}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 font-semibold text-xs text-white shadow-lg shadow-indigo-600/30 transition cursor-pointer disabled:opacity-50"
            >
              {loading
                ? 'Authenticating...'
                : isRegister
                ? 'Create LifeSync OS Account'
                : 'Sign In to LifeSync'}
            </button>
          </form>

          <button
            onClick={() => {
              setIsRegister(!isRegister);
              setAuthError('');
            }}
            className="w-full mt-4 text-xs text-slate-400 hover:text-indigo-400 transition cursor-pointer text-center"
          >
            {isRegister ? 'Already registered? Sign in' : "Don't have an account? Set up your OS"}
          </button>
        </div>
      </div>
    );
  }

  // --- RENDER SCREEN: ONBOARDING WIZARD ---
  if (user && !user.is_onboarded) {
    return (
      <OnboardingWizard
        user={user}
        rolesCatalog={rolesCatalog}
        onComplete={handleCompleteOnboarding}
        loading={loading}
      />
    );
  }

  // --- RENDER SCREEN: MAIN LIFE MANAGEMENT OS SHELL ---
  return (
    <div
      className={`min-h-screen flex ${
        theme === 'dark' ? 'bg-slate-950 text-slate-100' : 'bg-slate-50 text-slate-900'
      }`}
    >
      {/* 1. Collapsible Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        user={user}
        activeRole={activeRole}
        pendingApprovalsCount={approvals.length}
        emailUnreadCount={dashboardSummary?.email_intelligence?.unread_count || 0}
        unreadNotificationsCount={notifications.filter((n) => !n.is_read).length}
      />

      {/* 2. Main Workstation Shell */}
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar
          user={user}
          rolesCatalog={rolesCatalog}
          activeRole={activeRole}
          onSelectRole={setActiveRole}
          onOpenCommandPalette={() => setCommandPaletteOpen(true)}
          onOpenAssistant={() => setActiveTab('assistant')}
          onLogout={handleLogout}
          notifications={notifications}
          onMarkNotificationRead={handleMarkNotificationRead}
          theme={theme}
          onToggleTheme={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
        />

        <main className="flex-1 p-4 sm:p-8 max-w-7xl w-full mx-auto overflow-y-auto">
          {activeTab === 'overview' && (
            <PersonalizedDashboard
              summary={dashboardSummary}
              activeRole={activeRole}
              onSelectRole={setActiveRole}
              availableRoles={availableRoleSlugs}
              onToggleTask={handleToggleTask}
              onLogHabit={handleLogHabit}
              onApproveAction={handleApproveAction}
              onNavigateTab={setActiveTab}
              onReprioritize={() => {
                setActiveTab('assistant');
                handleSendMessage(
                  'Analyze my deadlines, upcoming events, and active roles, and reprioritize my tasks for optimal focus today.'
                );
              }}
              aiCoreStatus={aiCoreStatus}
            />
          )}

          {activeTab === 'workspace' && (
            <MyWorkspaceView
              user={user}
              rolesCatalog={rolesCatalog}
              activeRole={activeRole}
              onSelectRole={setActiveRole}
              onNavigateTab={setActiveTab}
            />
          )}

          {activeTab === 'assistant' && (
            <AIAssistantWorkspace
              chatHistory={chatHistory}
              agentBusy={agentBusy}
              onSendMessage={handleSendMessage}
              pendingApprovals={approvals}
              onDecideApproval={handleApproveAction}
              activeRole={activeRole}
              onSelectRole={setActiveRole}
              availableRoles={availableRoleSlugs}
            />
          )}

          {activeTab === 'agents' && (
            <AgentsCatalog
              catalog={agentCatalog}
              runs={agentRuns}
              activeRole={activeRole}
              onRunTestPrompt={(prompt) => {
                setActiveTab('assistant');
                handleSendMessage(prompt);
              }}
            />
          )}

          {activeTab === 'tasks' && (
            <TasksView
              tasks={tasks}
              activeRole={activeRole}
              onCreateTask={handleCreateTask}
              onUpdateTask={handleUpdateTask}
              onDeleteTask={handleDeleteTask}
              onAIBreakDown={(taskTitle) => {
                setActiveTab('assistant');
                handleSendMessage(`Break down this project into atomic subtasks: "${taskTitle}"`);
              }}
            />
          )}

          {activeTab === 'calendar' && (
            <CalendarView
              events={events}
              dailyPlans={dailyPlans}
              activeRole={activeRole}
              onCreateEvent={handleCreateEvent}
              onDeleteEvent={handleDeleteEvent}
              onGeneratePlan={handleGeneratePlan}
            />
          )}

          {activeTab === 'goals' && (
            <GoalsView
              goals={goals}
              activeRole={activeRole}
              onCreateGoal={handleCreateGoal}
              onToggleMilestone={handleToggleMilestone}
              onAIDecomposeGoal={(goalTitle) => {
                setActiveTab('assistant');
                handleSendMessage(`Decompose this strategic goal into actionable milestones and tasks: "${goalTitle}"`);
              }}
            />
          )}

          {activeTab === 'habits' && (
            <HabitsView
              habits={habits}
              activeRole={activeRole}
              onCreateHabit={handleCreateHabit}
              onLogHabit={handleLogHabit}
            />
          )}

          {activeTab === 'automations' && (
            <AutomationsView
              rules={automations}
              templates={automationTemplates}
              onCreateRule={handleCreateRule}
              onToggleRule={handleToggleRule}
              onDeleteRule={handleDeleteRule}
              onTriggerRule={handleTriggerRule}
            />
          )}

          {activeTab === 'memory' && (
            <MemoryView
              memories={memories}
              knowledgeDocs={knowledgeDocs}
              activeRole={activeRole}
              onAddMemory={handleAddMemory}
              onSearchMemories={handleSearchMemories}
              onIngestKnowledge={handleIngestKnowledge}
            />
          )}

          {activeTab === 'analytics' && (
            <AnalyticsView overview={overviewAnalytics} activeRole={activeRole} />
          )}

          {activeTab === 'email' && (
            <EmailView onNavigateTab={(tab) => setActiveTab(tab as NavTab)} />
          )}

          {activeTab === 'notifications' && (
            <NotificationsView
              notifications={notifications}
              onMarkRead={handleMarkNotificationRead}
              onNavigateTab={(tab) => setActiveTab(tab as NavTab)}
            />
          )}

          {activeTab === 'integrations' && <IntegrationsView />}

          {activeTab === 'settings' && (
            <SettingsView
              user={user}
              rolesCatalog={rolesCatalog}
              onUpdateProfile={handleUpdateProfile}
              onUpdatePreferences={handleUpdatePreferences}
              theme={theme}
              onToggleTheme={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            />
          )}
        </main>
      </div>

      {/* Global Command Palette (Ctrl+K / Cmd+K) */}
      <CommandPalette
        isOpen={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
        onSelectTab={setActiveTab}
        onSelectRole={setActiveRole}
        availableRoles={availableRoleSlugs}
      />

      {/* Floating AI Companion (Persistent on all workspaces) */}
      <FloatingAIPet
        user={user}
        activeRole={activeRole}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onRefreshData={() => refreshAllData(activeRole)}
        approvals={approvals}
        onDecideApproval={handleApproveAction}
        aiCoreStatus={aiCoreStatus}
        onStatusChange={setAiCoreStatus}
        summary={dashboardSummary}
      />
    </div>
  );
}
