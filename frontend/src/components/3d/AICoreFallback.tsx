import React from 'react';
import type { AICoreStatus } from '../../types';

interface FallbackProps {
  status: AICoreStatus;
  size?: number;
}

export const AICoreFallback: React.FC<FallbackProps> = ({ status, size = 180 }) => {
  const getColors = () => {
    switch (status) {
      case 'thinking':
        return { ring: 'border-violet-500', glow: 'from-violet-600/40 via-purple-600/30 to-indigo-900/10', core: 'bg-violet-400' };
      case 'processing':
        return { ring: 'border-cyan-400', glow: 'from-cyan-500/40 via-blue-600/30 to-slate-900/10', core: 'bg-cyan-300' };
      case 'executing':
        return { ring: 'border-amber-400', glow: 'from-amber-500/40 via-orange-600/30 to-slate-900/10', core: 'bg-amber-300' };
      case 'awaiting_approval':
        return { ring: 'border-amber-300', glow: 'from-amber-400/50 via-yellow-500/30 to-slate-900/10', core: 'bg-yellow-300' };
      case 'completed':
        return { ring: 'border-emerald-400', glow: 'from-emerald-500/40 via-teal-600/30 to-slate-900/10', core: 'bg-emerald-300' };
      case 'error':
        return { ring: 'border-rose-500', glow: 'from-rose-600/40 via-red-600/30 to-slate-900/10', core: 'bg-rose-400' };
      case 'idle':
      default:
        return { ring: 'border-indigo-500/60', glow: 'from-indigo-600/30 via-cyan-600/20 to-slate-900/10', core: 'bg-indigo-400' };
    }
  };

  const colors = getColors();

  return (
    <div
      className="relative flex items-center justify-center select-none"
      style={{ width: size, height: size }}
    >
      {/* Outer Glow Halo */}
      <div
        className={`absolute inset-0 rounded-full bg-gradient-to-tr ${colors.glow} blur-xl animate-pulse`}
      />

      {/* Outer Orbital Ring */}
      <div
        className={`absolute inset-2 rounded-full border border-dashed ${colors.ring} opacity-60 animate-spin`}
        style={{ animationDuration: '14s' }}
      />

      {/* Middle Orbital Ring */}
      <div
        className={`absolute inset-6 rounded-full border border-dotted ${colors.ring} opacity-80 animate-spin`}
        style={{ animationDuration: '8s', animationDirection: 'reverse' }}
      />

      {/* Central Core */}
      <div className="relative flex items-center justify-center w-14 h-14 rounded-full bg-slate-950 border border-indigo-400/50 shadow-inner">
        <div className={`w-6 h-6 rounded-full ${colors.core} blur-[2px] animate-ping`} />
        <div className={`absolute w-4 h-4 rounded-full ${colors.core} shadow-lg`} />
      </div>

      {/* Status Badge */}
      <div className="absolute -bottom-2 px-2.5 py-0.5 rounded-full bg-slate-900/90 border border-slate-700 text-[10px] font-mono uppercase tracking-wider text-slate-300 shadow">
        {status.replace('_', ' ')}
      </div>
    </div>
  );
};
