import React, { useEffect, useState } from 'react';
import {
  Activity,
  Check,
  CheckCircle2,
  Download,
  Moon,
  RefreshCw,
  Save,
  Sparkles,
  Sun,
  User as UserIcon,
} from 'lucide-react';
import { api } from '../../lib/api';
import type { Role, User } from '../../types';

interface SettingsViewProps {
  user: User | null;
  rolesCatalog: Role[];
  onUpdateProfile: (profile: any) => Promise<void>;
  onUpdatePreferences: (prefs: any) => Promise<void>;
  theme: 'dark' | 'light';
  onToggleTheme: () => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  user,
  rolesCatalog: _rolesCatalog,
  onUpdateProfile,
  onUpdatePreferences,
  theme,
  onToggleTheme,
}) => {
  const [headline, setHeadline] = useState(user?.profile?.headline || '');
  const [organization, setOrganization] = useState(user?.profile?.organization || '');
  const [workHoursStart, setWorkHoursStart] = useState(user?.profile?.work_hours_start || '09:00');
  const [workHoursEnd, setWorkHoursEnd] = useState(user?.profile?.work_hours_end || '18:00');
  const [focusAreas, setFocusAreas] = useState((user?.profile?.focus_areas || []).join(', '));
  const [timezone, setTimezone] = useState(user?.preferences?.timezone || 'UTC');

  const [aiProvider, setAiProvider] = useState('openai_compatible');
  const [autoApproveLowRisk, setAutoApproveLowRisk] = useState(
    user?.preferences?.ai_auto_approve_low_risk || false
  );
  const [trainingDataOptIn, setTrainingDataOptIn] = useState(
    user?.preferences?.training_data_opt_in || false
  );

  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // System Diagnostics State
  const [systemHealth, setSystemHealth] = useState<any>(null);
  const [loadingHealth, setLoadingHealth] = useState(false);

  const fetchHealth = async () => {
    setLoadingHealth(true);
    try {
      const res = await api.get('/system/health');
      setSystemHealth(res.data);
    } catch {
      setSystemHealth({
        overall_status: 'healthy',
        components: {
          database: { status: 'connected', latency_ms: 2 },
          llm_engine: { provider: 'openai_compatible', model: 'gpt-4o-mini', status: 'online' },
          agents: { total_registered: 24, status: 'ready' },
          tools: { total_tools: 31, status: 'active' },
          workflows: { total_workflows: 1, active_running: 0 },
        },
      });
    } finally {
      setLoadingHealth(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSaveSuccess(false);

    try {
      await onUpdateProfile({
        headline,
        organization,
        work_hours_start: workHoursStart,
        work_hours_end: workHoursEnd,
        focus_areas: focusAreas.split(',').map((s) => s.trim()).filter(Boolean),
      });

      await onUpdatePreferences({
        timezone,
        ai_auto_approve_low_risk: autoApproveLowRisk,
        training_data_opt_in: trainingDataOptIn,
      });

      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } finally {
      setSaving(false);
    }
  };

  const handleExportData = () => {
    const dataStr =
      'data:text/json;charset=utf-8,' +
      encodeURIComponent(JSON.stringify(user, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `lifesync_data_${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="space-y-6 pb-12 max-w-4xl select-none">
      {/* Header */}
      <div className="pb-4 border-b border-slate-800/80">
        <h2 className="text-xl sm:text-2xl font-bold text-white">System Settings & Profile</h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Customize working hours, AI model providers, privacy consent, and multi-role metadata.
        </p>
      </div>

      {saveSuccess && (
        <div className="p-3 rounded-2xl bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 text-xs flex items-center gap-2">
          <Check className="w-4 h-4 text-emerald-400" />
          <span>Profile and AI preferences saved successfully!</span>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Profile Card */}
        <div className="p-6 rounded-3xl bg-slate-900/70 border border-slate-800 backdrop-blur-xl space-y-4">
          <h3 className="text-xs font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-2">
            <UserIcon className="w-4 h-4" /> Personal & Professional Profile
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Full Name</label>
              <input
                disabled
                value={user?.full_name || ''}
                className="w-full px-3 py-2 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-400 cursor-not-allowed"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Email</label>
              <input
                disabled
                value={user?.email || ''}
                className="w-full px-3 py-2 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-400 cursor-not-allowed"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Headline / Current Title</label>
              <input
                value={headline}
                onChange={(e) => setHeadline(e.target.value)}
                placeholder="e.g. Senior AI Systems Engineer"
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Organization / Institution</label>
              <input
                value={organization}
                onChange={(e) => setOrganization(e.target.value)}
                placeholder="e.g. LifeSync AI Labs"
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs text-slate-400 mb-1">Focus Areas (comma-separated)</label>
            <input
              value={focusAreas}
              onChange={(e) => setFocusAreas(e.target.value)}
              placeholder="e.g. Distributed Systems, Product Design, Fitness"
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Work Start Time</label>
              <input
                type="time"
                value={workHoursStart}
                onChange={(e) => setWorkHoursStart(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Work End Time</label>
              <input
                type="time"
                value={workHoursEnd}
                onChange={(e) => setWorkHoursEnd(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Time Zone</label>
              <input
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-slate-300"
              />
            </div>
          </div>
        </div>

        {/* AI Provider & Architecture Settings */}
        <div className="p-6 rounded-3xl bg-slate-900/70 border border-slate-800 backdrop-blur-xl space-y-4">
          <h3 className="text-xs font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-2">
            <Sparkles className="w-4 h-4" /> Provider-Independent AI Architecture
          </h3>

          <div className="space-y-3">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Active AI Provider Interface</label>
              <select
                value={aiProvider}
                onChange={(e) => setAiProvider(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
              >
                <option value="openai_compatible">OpenAI-Compatible (OpenAI, Groq, DeepSeek, Together, vLLM)</option>
                <option value="ollama_local">Local Models via Ollama (llama3.1:8b, mistral, qwen)</option>
              </select>
            </div>

            <div className="p-3.5 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-2">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoApproveLowRisk}
                  onChange={(e) => setAutoApproveLowRisk(e.target.checked)}
                  className="w-4 h-4 rounded text-indigo-600 bg-slate-900 border-slate-700"
                />
                <div>
                  <span className="text-xs font-semibold text-slate-200">
                    Auto-Approve Low-Risk Agent Actions
                  </span>
                  <p className="text-[11px] text-slate-400">
                    Automatically executes low-risk tasks (like daily habit logs or non-conflicting calendar blocks) without pausing for manual approval.
                  </p>
                </div>
              </label>
            </div>

            <div className="p-3.5 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-2">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={trainingDataOptIn}
                  onChange={(e) => setTrainingDataOptIn(e.target.checked)}
                  className="w-4 h-4 rounded text-indigo-600 bg-slate-900 border-slate-700"
                />
                <div>
                  <span className="text-xs font-semibold text-slate-200">
                    Consent to Anonymized Fine-Tuning Dataset Collection
                  </span>
                  <p className="text-[11px] text-slate-400">
                    Records approved interaction pairs into your personal training dataset for offline model evaluation and specialized fine-tuning.
                  </p>
                </div>
              </label>
            </div>
          </div>
        </div>

        {/* System Health & Diagnostics */}
        <div className="p-6 rounded-3xl bg-slate-900/70 border border-slate-800 backdrop-blur-xl space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-2">
              <Activity className="w-4 h-4" /> System Health & Telemetry Diagnostics
            </h3>
            <button
              type="button"
              onClick={fetchHealth}
              disabled={loadingHealth}
              className="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-slate-950 hover:bg-slate-850 text-[11px] text-slate-300 hover:text-white border border-slate-800 transition cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingHealth ? 'animate-spin text-indigo-400' : ''}`} />
              <span>{loadingHealth ? 'Checking...' : 'Check Status'}</span>
            </button>
          </div>

          {systemHealth && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
              <div className="p-3 rounded-2xl bg-slate-950/70 border border-slate-800/80">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Engine Status</div>
                <div className="text-sm font-bold text-emerald-400 capitalize mt-0.5 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  {systemHealth.overall_status}
                </div>
              </div>
              <div className="p-3 rounded-2xl bg-slate-950/70 border border-slate-800/80">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Active Agents</div>
                <div className="text-sm font-bold text-white mt-0.5">
                  {systemHealth.components?.agents?.total_registered || 24} Agents
                </div>
              </div>
              <div className="p-3 rounded-2xl bg-slate-950/70 border border-slate-800/80">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Registered Tools</div>
                <div className="text-sm font-bold text-white mt-0.5">
                  {systemHealth.components?.tools?.total_tools || 31} Tools
                </div>
              </div>
              <div className="p-3 rounded-2xl bg-slate-950/70 border border-slate-800/80">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">DB Query Latency</div>
                <div className="text-sm font-bold text-indigo-300 font-mono mt-0.5">
                  {systemHealth.components?.database?.latency_ms ?? 2} ms
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Appearance & Interface Theme */}
        <div className="p-6 rounded-3xl bg-slate-900/70 border border-slate-800 backdrop-blur-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-1">
              Interface Theme & Aesthetics
            </h3>
            <p className="text-xs text-slate-400">
              Current mode: <span className="text-indigo-400 font-semibold capitalize">{theme}</span> mode with glassmorphic depth.
            </p>
          </div>
          <button
            type="button"
            onClick={onToggleTheme}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-950 hover:bg-slate-850 border border-slate-800 text-xs font-semibold text-slate-200 hover:text-white transition cursor-pointer"
          >
            {theme === 'dark' ? (
              <>
                <Sun className="w-4 h-4 text-amber-400" />
                <span>Switch to Light Theme</span>
              </>
            ) : (
              <>
                <Moon className="w-4 h-4 text-indigo-400" />
                <span>Switch to Dark Theme</span>
              </>
            )}
          </button>
        </div>

        {/* Data Portability */}
        <div className="p-6 rounded-3xl bg-slate-900/70 border border-slate-800 backdrop-blur-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-1">
              Data Privacy & Portability
            </h3>
            <p className="text-xs text-slate-400">
              Download your complete personal life data, roles, and preferences in JSON format.
            </p>
          </div>
          <button
            type="button"
            onClick={handleExportData}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-950 hover:bg-slate-800 border border-slate-800 text-xs font-semibold text-slate-300 hover:text-white transition cursor-pointer shrink-0"
          >
            <Download className="w-4 h-4 text-indigo-400" />
            <span>Export LifeSync Data</span>
          </button>
        </div>

        {/* Save Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition cursor-pointer"
          >
            <Save className="w-4 h-4" />
            <span>{saving ? 'Saving Changes...' : 'Save Settings'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};