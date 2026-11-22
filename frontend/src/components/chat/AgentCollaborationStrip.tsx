import React, { useState } from 'react';
import { ArrowRight, CheckCircle2, ChevronDown, ChevronRight, Cpu, Layers } from 'lucide-react';
import type { AgentTraceItem } from '../../types';

interface AgentCollaborationStripProps {
  trace: AgentTraceItem[];
}

export const AgentCollaborationStrip: React.FC<AgentCollaborationStripProps> = ({ trace }) => {
  const [expanded, setExpanded] = useState(false);

  if (!trace || trace.length === 0) return null;

  return (
    <div className="mb-2 rounded-lg border border-purple-500/25 bg-purple-950/30 backdrop-blur-sm text-xs overflow-hidden">
      <div
        className="flex items-center justify-between px-2.5 py-1.5 cursor-pointer hover:bg-purple-900/30 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-1.5 flex-wrap">
          <Layers className="w-3.5 h-3.5 text-purple-400 shrink-0" />
          <span className="text-purple-300 font-medium text-[11px]">Multi-Agent Pipeline:</span>
          <div className="flex items-center gap-1 flex-wrap">
            {trace.map((item, index) => (
              <React.Fragment key={index}>
                {index > 0 && <ArrowRight className="w-2.5 h-2.5 text-purple-500/60 shrink-0" />}
                <span className="inline-flex items-center gap-1 text-[11px] font-mono px-1.5 py-0.5 rounded bg-purple-900/50 text-purple-200 border border-purple-500/30">
                  <Cpu className="w-2.5 h-2.5 text-purple-400" />
                  {item.agent}
                  <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400" />
                </span>
              </React.Fragment>
            ))}
          </div>
        </div>
        <button
          type="button"
          className="text-purple-400 hover:text-purple-200 p-0.5 ml-1"
          aria-label={expanded ? "Collapse details" : "Expand details"}
        >
          {expanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
        </button>
      </div>

      {expanded && (
        <div className="px-2.5 py-2 border-t border-purple-500/10 bg-black/30 space-y-1.5 text-[11px]">
          {trace.map((item, index) => (
            <div key={index} className="flex items-start gap-2">
              <span className="text-purple-400 font-semibold">{item.agent}:</span>
              <span className="text-slate-300 flex-1">{item.detail || item.status}</span>
              <span className="text-emerald-400 text-[10px] uppercase font-mono px-1 py-0.2 rounded bg-emerald-950/40 border border-emerald-500/30">
                {item.status}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
