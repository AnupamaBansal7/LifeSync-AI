import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  Check,
  CheckCircle2,
  GitBranch,
  HardDrive,
  Layers,
  Mail,
  Power,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Zap,
} from 'lucide-react';
import confetti from 'canvas-confetti';

import { api } from '../../lib/api';

interface IntegrationRecord {
  id?: string;
  service: string;
  name: string;
  category: string;
  description: string;
  status: 'connected' | 'disconnected' | 'error';
  account_email?: string;
  scopes: string[];
  last_synced_at?: string;
  details: string;
  auth_url?: string;
}

export const IntegrationsView: React.FC = () => {
  const [integrations, setIntegrations] = useState<IntegrationRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncingService, setSyncingService] = useState<string | null>(null);
  const [connectingService, setConnectingService] = useState<string | null>(null);
  const [notice, setNotice] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Connect Dialog State
  const [connectModalService, setConnectModalService] = useState<IntegrationRecord | null>(null);
  const [connectEmail, setConnectEmail] = useState('user@example.com');

  const fetchIntegrations = async () => {
    try {
      setLoading(true);
      const res = await api.get('/integrations');
      setIntegrations(res.data);
    } catch (err) {
      console.error('Failed to fetch integrations:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIntegrations();
  }, []);

  const handleSync = async (service: string) => {
    try {
      setSyncingService(service);
      const res = await api.post(`/integrations/${service}/sync`);
      await fetchIntegrations();
      showNotice(res.data.detail || `Synced ${service} successfully!`, 'success');
    } catch (err: any) {
      showNotice(err.response?.data?.detail || `Failed to sync ${service}`, 'error');
    } finally {
      setSyncingService(null);
    }
  };

  const handleDisconnect = async (service: string) => {
    try {
      await api.post(`/integrations/${service}/disconnect`);
      await fetchIntegrations();
      showNotice(`Disconnected ${service} integration.`, 'success');
    } catch (err: any) {
      showNotice(err.response?.data?.detail || `Failed to disconnect ${service}`, 'error');
    }
  };

  const handleConnect = async (service: string) => {
    const item = integrations.find((i) => i.service === service);
    if (!item) return;

    if (service === 'google') {
      try {
        setConnectingService(service);
        const res = await api.post('/integrations/google/auth-url');
        if (res.data.auth_url) {
          // Open OAuth consent window or simulation popup
          window.open(res.data.auth_url, '_blank', 'width=600,height=700');
          showNotice('OAuth authorization window opened. Complete sign-in and refresh.', 'success');
        }
      } catch (err: any) {
        // Fallback to dev connection modal
        setConnectModalService(item);
      } finally {
        setConnectingService(null);
      }
    } else {
      setConnectModalService(item);
    }
  };

  const handleExecuteConnect = async () => {
    if (!connectModalService) return;
    try {
      setConnectingService(connectModalService.service);
      await api.post('/integrations/mock-connect', {
        service: connectModalService.service,
        account_email: connectEmail.trim() || 'active.user@lifesync.ai',
      });
      confetti({ particleCount: 50, spread: 60, origin: { y: 0.6 } });
      showNotice(`Successfully connected ${connectModalService.name}!`, 'success');
      setConnectModalService(null);
      await fetchIntegrations();
    } catch (err: any) {
      showNotice(err.response?.data?.detail || 'Failed to connect service', 'error');
    } finally {
      setConnectingService(null);
    }
  };

  const showNotice = (text: string, type: 'success' | 'error') => {
    setNotice({ text, type });
    setTimeout(() => setNotice(null), 4000);
  };

  const getServiceIcon = (service: string) => {
    switch (service) {
      case 'google':
        return Mail;
      case 'ollama':
        return Sparkles;
      case 'openai_compatible':
        return Zap;
      case 'github':
        return GitBranch;
      case 'notion':
        return Layers;
      default:
        return HardDrive;
    }
  };

  const categories = ['all', 'Communication & Calendar', 'AI Engine', 'Developer Tools', 'Knowledge Base'];

  const filteredIntegrations = integrations.filter((item) => {
    const matchesCat = selectedCategory === 'all' || item.category === selectedCategory;
    const matchesSearch =
      item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.service.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCat && matchesSearch;
  });

  return (
    <div className="space-y-6 pb-12 select-none">
      {/* Header */}
      <div className="pb-4 border-b border-slate-800/80 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs uppercase tracking-wider mb-1">
            <Zap className="w-4 h-4" /> Real Ecosystem Connectors
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-white">Integrations & Data Pipes</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Connect external services to empower your multi-agent operating system with real email, calendar, and AI engines.
          </p>
        </div>

        <button
          onClick={fetchIntegrations}
          disabled={loading}
          className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs text-slate-300 font-medium transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Status
        </button>
      </div>

      {/* Notice Banner */}
      {notice && (
        <div
          className={`p-3 rounded-2xl text-xs flex items-center justify-between transition-all ${
            notice.type === 'success'
              ? 'bg-emerald-950/40 border border-emerald-500/40 text-emerald-300'
              : 'bg-rose-950/40 border border-rose-500/40 text-rose-300'
          }`}
        >
          <div className="flex items-center gap-2">
            {notice.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            )}
            <span>{notice.text}</span>
          </div>
          <button onClick={() => setNotice(null)} className="text-slate-400 hover:text-slate-200">
            ×
          </button>
        </div>
      )}

      {/* Search & Category Filter */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2 overflow-x-auto no-scrollbar pb-1 sm:pb-0">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition capitalize ${
                selectedCategory === cat
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              {cat === 'all' ? 'All Services' : cat}
            </button>
          ))}
        </div>

        <div className="relative min-w-[220px]">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search integrations..."
            className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 outline-none focus:border-indigo-500/50"
          />
        </div>
      </div>

      {/* Integrations Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-56 rounded-3xl bg-slate-900/40 border border-slate-800 animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredIntegrations.map((item) => {
            const Icon = getServiceIcon(item.service);
            const isConnected = item.status === 'connected';
            const isSyncing = syncingService === item.service;
            const isConnecting = connectingService === item.service;

            return (
              <div
                key={item.service}
                className="flex flex-col justify-between p-5 rounded-3xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700/80 transition-all backdrop-blur-xl group shadow-lg"
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="p-3 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 group-hover:scale-105 transition-transform">
                      <Icon className="w-6 h-6" />
                    </div>
                    <span
                      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-semibold uppercase tracking-wider ${
                        isConnected
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                          : 'bg-slate-800/80 text-slate-400 border border-slate-700/60'
                      }`}
                    >
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'
                        }`}
                      />
                      {item.status}
                    </span>
                  </div>

                  <h3 className="font-bold text-sm text-white group-hover:text-indigo-300 transition">
                    {item.name}
                  </h3>
                  <div className="text-[10px] text-indigo-400/80 font-medium mb-2">{item.category}</div>
                  <p className="text-xs text-slate-400 leading-relaxed line-clamp-2 mb-3">
                    {item.description}
                  </p>

                  {/* Connected Details */}
                  {isConnected && (
                    <div className="p-2.5 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-1 mb-3 text-[11px]">
                      {item.account_email && (
                        <div className="flex items-center justify-between text-slate-300">
                          <span className="text-slate-500 text-[10px]">Account:</span>
                          <span className="font-mono truncate max-w-[170px]">{item.account_email}</span>
                        </div>
                      )}
                      {item.last_synced_at && (
                        <div className="flex items-center justify-between text-slate-400 text-[10px]">
                          <span>Last Synced:</span>
                          <span className="font-mono">{new Date(item.last_synced_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        </div>
                      )}
                      {item.scopes && item.scopes.length > 0 && (
                        <div className="text-[10px] text-slate-500 truncate">
                          Scopes: {item.scopes.join(', ')}
                        </div>
                      )}
                    </div>
                  )}

                  {!isConnected && (
                    <p className="text-[11px] text-slate-500 italic mb-3">
                      {item.details}
                    </p>
                  )}
                </div>

                {/* Card Actions */}
                <div className="pt-3 border-t border-slate-800/60 flex items-center justify-between gap-2">
                  {isConnected ? (
                    <>
                      <button
                        onClick={() => handleSync(item.service)}
                        disabled={isSyncing}
                        className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700/80 text-xs font-semibold text-slate-200 transition disabled:opacity-50"
                      >
                        <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
                        {isSyncing ? 'Syncing...' : 'Sync Now'}
                      </button>
                      <button
                        onClick={() => handleDisconnect(item.service)}
                        className="px-3 py-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-xs font-semibold transition"
                        title="Disconnect Integration"
                      >
                        Disconnect
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => handleConnect(item.service)}
                      disabled={isConnecting}
                      className="w-full flex items-center justify-center gap-2 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-md shadow-indigo-600/30 transition disabled:opacity-50"
                    >
                      <Power className="w-3.5 h-3.5" />
                      {isConnecting ? 'Connecting...' : 'Connect Service'}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* One-Click Connect Modal */}
      {connectModalService && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-3xl bg-slate-900 border border-slate-800 p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2.5 rounded-xl bg-indigo-600/20 border border-indigo-500/30 text-indigo-400">
                  <Zap className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-sm text-white">Connect {connectModalService.name}</h3>
                  <span className="text-[10px] text-indigo-400 font-mono">{connectModalService.service}</span>
                </div>
              </div>
              <button
                onClick={() => setConnectModalService(null)}
                className="text-slate-400 hover:text-slate-200"
              >
                ×
              </button>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              {connectModalService.description}
            </p>

            <div className="space-y-1.5">
              <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Connected Account Email / Identifier
              </label>
              <input
                type="email"
                value={connectEmail}
                onChange={(e) => setConnectEmail(e.target.value)}
                placeholder="e.g. user@gmail.com"
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-100 placeholder-slate-600 outline-none focus:border-indigo-500"
              />
            </div>

            <div className="p-3 rounded-2xl bg-indigo-950/30 border border-indigo-500/20 text-[11px] text-indigo-300 flex items-start gap-2">
              <ShieldCheck className="w-4 h-4 flex-shrink-0 text-indigo-400 mt-0.5" />
              <span>
                Tokens and secrets are encrypted with AES-256 in your database. All high-risk outbound operations will prompt for your explicit approval.
              </span>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setConnectModalService(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleExecuteConnect}
                disabled={connectingService !== null}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-md shadow-indigo-600/30 transition disabled:opacity-50"
              >
                <Check className="w-4 h-4" />
                Confirm & Connect
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
