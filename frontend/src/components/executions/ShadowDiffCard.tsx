import React, { useState } from 'react';
import {
  AlertCircle,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Layers,
  RotateCcw,
  Shield,
  Undo2,
} from 'lucide-react';
import confetti from 'canvas-confetti';
import { api } from '../../lib/api';
import type { TransactionPlan } from '../../types';

interface ShadowDiffCardProps {
  plan: TransactionPlan;
  onPlanUpdated?: (updatedPlan: TransactionPlan) => void;
  onRefreshData?: () => Promise<void>;
  compact?: boolean;
}

export const ShadowDiffCard: React.FC<ShadowDiffCardProps> = ({
  plan: initialPlan,
  onPlanUpdated,
  onRefreshData,
  compact = false,
}) => {
  const [plan, setPlan] = useState<TransactionPlan>(initialPlan);
  const [selectedStepIds, setSelectedStepIds] = useState<Set<string>>(
    new Set(initialPlan.steps.map((s) => s.id))
  );
  const [expandedStepIds, setExpandedStepIds] = useState<Set<string>>(
    new Set(initialPlan.steps.map((s) => s.id))
  );
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const toggleSelectStep = (stepId: string) => {
    setSelectedStepIds((prev) => {
      const next = new Set(prev);
      if (next.has(stepId)) {
        next.delete(stepId);
      } else {
        next.add(stepId);
      }
      return next;
    });
  };

  const toggleExpandStep = (stepId: string) => {
    setExpandedStepIds((prev) => {
      const next = new Set(prev);
      if (next.has(stepId)) {
        next.delete(stepId);
      } else {
        next.add(stepId);
      }
      return next;
    });
  };

  const handleApprove = async () => {
    setLoadingAction('approve');
    setActionError(null);
    try {
      const res = await api.post(`/executions/plans/${plan.id}/approve`, {
        approved_step_ids: Array.from(selectedStepIds),
      });
      if (res.data?.plan) {
        setPlan(res.data.plan);
        onPlanUpdated?.(res.data.plan);
      }
      if (res.data?.success) {
        confetti({ particleCount: 35, spread: 55, origin: { y: 0.7 } });
      }
      if (onRefreshData) {
        await onRefreshData();
      }
    } catch (err: any) {
      setActionError(err.response?.data?.detail || 'Failed to approve execution plan');
    } finally {
      setLoadingAction(null);
    }
  };

  const handleRollback = async () => {
    setLoadingAction('rollback');
    setActionError(null);
    try {
      const res = await api.post(`/executions/plans/${plan.id}/rollback`);
      if (res.data?.plan) {
        setPlan(res.data.plan);
        onPlanUpdated?.(res.data.plan);
      }
      if (res.data?.success) {
        confetti({ particleCount: 45, spread: 60, origin: { y: 0.7 } });
      }
      if (onRefreshData) {
        await onRefreshData();
      }
    } catch (err: any) {
      setActionError(err.response?.data?.detail || 'Failed to rollback transaction plan');
    } finally {
      setLoadingAction(null);
    }
  };

  const handleReject = async () => {
    setLoadingAction('reject');
    setActionError(null);
    try {
      const res = await api.post(`/executions/plans/${plan.id}/reject`);
      if (res.data?.plan) {
        setPlan(res.data.plan);
        onPlanUpdated?.(res.data.plan);
      }
      if (onRefreshData) {
        await onRefreshData();
      }
    } catch (err: any) {
      setActionError(err.response?.data?.detail || 'Failed to reject transaction plan');
    } finally {
      setLoadingAction(null);
    }
  };

  const getStatusBadge = () => {
    switch (plan.status) {
      case 'SIMULATED':
      case 'AWAITING_APPROVAL':
        return (
          <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-amber-500/15 border border-amber-500/30 text-amber-300 font-mono text-[10px] font-bold">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
            Dry-Run Simulated
          </span>
        );
      case 'EXECUTING':
        return (
          <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-indigo-500/15 border border-indigo-500/30 text-indigo-300 font-mono text-[10px] font-bold">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-ping" />
            Executing Mutations
          </span>
        );
      case 'VERIFIED':
        return (
          <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 font-mono text-[10px] font-bold">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            Verified & Committed
          </span>
        );
      case 'PARTIALLY_FAILED':
        return (
          <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-rose-500/15 border border-rose-500/30 text-rose-300 font-mono text-[10px] font-bold">
            <AlertCircle className="w-3 h-3 text-rose-400" />
            Partially Failed
          </span>
        );
      case 'ROLLED_BACK':
        return (
          <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-blue-500/15 border border-blue-500/30 text-blue-300 font-mono text-[10px] font-bold">
            <RotateCcw className="w-3 h-3 text-blue-400" />
            Rolled Back (Reverted)
          </span>
        );
      case 'CANCELLED':
        return (
          <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-400 font-mono text-[10px] font-bold">
            Cancelled
          </span>
        );
      default:
        return null;
    }
  };

  const getRiskBadge = () => {
    switch (plan.overall_risk) {
      case 'HIGH':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-rose-950/40 border border-rose-500/40 text-rose-300">
            High Risk
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-amber-950/40 border border-amber-500/40 text-amber-300">
            Medium Risk
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-cyan-950/40 border border-cyan-500/40 text-cyan-300">
            Low Risk
          </span>
        );
    }
  };

  const isPendingApproval = plan.status === 'SIMULATED' || plan.status === 'AWAITING_APPROVAL';
  const canRollback =
    (plan.status === 'VERIFIED' || plan.status === 'PARTIALLY_FAILED') &&
    plan.steps.some((s) => s.status === 'verified' && s.reversibility === 'REVERSIBLE');

  return (
    <div
      className={`rounded-2xl border transition-all duration-300 overflow-hidden ${
        plan.status === 'ROLLED_BACK'
          ? 'bg-slate-950/60 border-slate-800'
          : plan.status === 'VERIFIED'
          ? 'bg-gradient-to-br from-slate-900/90 via-slate-950/80 to-emerald-950/10 border-emerald-500/30 shadow-lg shadow-emerald-950/20'
          : 'bg-gradient-to-br from-slate-900/95 via-indigo-950/30 to-slate-950/90 border-indigo-500/30 shadow-xl'
      } ${compact ? 'p-3' : 'p-4 sm:p-5'}`}
    >
      {/* 1. Header with Intent & Risk Badges */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2.5 pb-3 border-b border-slate-800/80">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-indigo-600/20 border border-indigo-500/30 text-indigo-400">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono uppercase tracking-wider text-indigo-300 font-bold">
                Shadow Execution Diff
              </span>
              {getRiskBadge()}
            </div>
            <h4 className="text-xs sm:text-sm font-bold text-white leading-tight mt-0.5">
              {plan.intent_summary}
            </h4>
          </div>
        </div>

        <div className="flex items-center gap-2 self-end sm:self-auto">
          {getStatusBadge()}
        </div>
      </div>

      {actionError && (
        <div className="my-2 p-2 rounded-xl bg-rose-950/40 border border-rose-500/40 text-[11px] text-rose-300 flex items-center gap-2">
          <AlertCircle className="w-3.5 h-3.5 shrink-0" />
          <span>{actionError}</span>
        </div>
      )}

      {/* 2. Proposed Steps Diff List */}
      <div className="mt-3 space-y-2.5">
        <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 px-1">
          <span>
            {isPendingApproval
              ? 'Select steps to approve & execute:'
              : `Executed steps (${plan.steps.length}):`}
          </span>
          <span className="text-slate-500">
            {plan.is_fully_reversible ? '100% Reversible Plan' : 'Contains Irreversible Operations'}
          </span>
        </div>

        {plan.steps.map((step, idx) => {
          const isSelected = selectedStepIds.has(step.id);
          const isExpanded = expandedStepIds.has(step.id);
          const hasDiff =
            (step.before_state && Object.keys(step.before_state).length > 0) ||
            (step.after_state && Object.keys(step.after_state).length > 0);

          return (
            <div
              key={step.id || idx}
              className={`rounded-xl border transition-all ${
                step.status === 'rolled_back'
                  ? 'bg-slate-950/40 border-slate-800/80 opacity-70'
                  : step.status === 'verified'
                  ? 'bg-slate-950/70 border-emerald-500/20'
                  : step.status === 'failed'
                  ? 'bg-rose-950/20 border-rose-500/30'
                  : isSelected
                  ? 'bg-slate-950/80 border-indigo-500/40'
                  : 'bg-slate-950/40 border-slate-800'
              }`}
            >
              {/* Step Header */}
              <div className="p-2.5 flex items-center justify-between gap-2.5">
                <div className="flex items-center gap-2.5 flex-1 min-w-0">
                  {isPendingApproval && (
                    <button
                      type="button"
                      onClick={() => toggleSelectStep(step.id)}
                      className={`w-4 h-4 rounded border flex items-center justify-center transition cursor-pointer shrink-0 ${
                        isSelected
                          ? 'bg-indigo-600 border-indigo-500 text-white'
                          : 'border-slate-700 hover:border-slate-500 text-transparent'
                      }`}
                    >
                      <Check className="w-3 h-3" />
                    </button>
                  )}

                  <span className="w-4 text-[10px] font-mono font-bold text-slate-500 shrink-0">
                    #{step.step_order}
                  </span>

                  <div className="truncate flex-1">
                    <div className="flex items-center gap-2 truncate">
                      <span className="text-xs font-semibold text-slate-200 truncate">
                        {step.tool_name}
                      </span>
                      <span
                        className={`text-[9px] font-mono px-1.5 py-0.2 rounded border font-semibold ${
                          step.reversibility === 'REVERSIBLE'
                            ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                            : step.reversibility === 'DELAYED_UNDO'
                            ? 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30'
                            : 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                        }`}
                      >
                        {step.reversibility === 'REVERSIBLE'
                          ? 'Reversible'
                          : step.reversibility === 'DELAYED_UNDO'
                          ? 'Delayed Undo'
                          : 'Irreversible'}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {step.status === 'verified' && (
                    <span className="text-[10px] font-mono text-emerald-400 flex items-center gap-1 font-semibold">
                      <CheckCircle2 className="w-3 h-3" />
                      Verified
                    </span>
                  )}
                  {step.status === 'rolled_back' && (
                    <span className="text-[10px] font-mono text-blue-400 flex items-center gap-1">
                      <RotateCcw className="w-3 h-3" />
                      Reverted
                    </span>
                  )}
                  {step.status === 'failed' && (
                    <span className="text-[10px] font-mono text-rose-400 flex items-center gap-1">
                      <AlertCircle className="w-3 h-3" />
                      Failed
                    </span>
                  )}
                  {step.status === 'skipped' && (
                    <span className="text-[10px] font-mono text-slate-500">Skipped</span>
                  )}

                  {hasDiff && (
                    <button
                      type="button"
                      onClick={() => toggleExpandStep(step.id)}
                      className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
                      title={isExpanded ? 'Collapse diff' : 'Expand diff'}
                    >
                      {isExpanded ? (
                        <ChevronDown className="w-3.5 h-3.5" />
                      ) : (
                        <ChevronRight className="w-3.5 h-3.5" />
                      )}
                    </button>
                  )}
                </div>
              </div>

              {/* 3. Before → After Diff Details */}
              {isExpanded && hasDiff && (
                <div className="px-3 pb-3 pt-1 border-t border-slate-800/80 bg-slate-950/80 space-y-2">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] font-mono">
                    {/* Before State */}
                    <div className="p-2.5 rounded-xl bg-rose-950/15 border border-rose-500/20">
                      <div className="text-[10px] font-bold text-rose-300 uppercase tracking-wider mb-1 flex items-center gap-1">
                        <span>[-] State Before</span>
                      </div>
                      {Object.keys(step.before_state || {}).length === 0 ? (
                        <span className="text-slate-500 italic text-[10px]">
                          (No existing entity / new creation)
                        </span>
                      ) : (
                        <div className="space-y-0.5 text-slate-300 overflow-x-auto">
                          {Object.entries(step.before_state).map(([k, v]) => (
                            <div key={k} className="flex gap-1">
                              <span className="text-slate-400">{k}:</span>
                              <span className="text-rose-200 truncate">{JSON.stringify(v)}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* After State */}
                    <div className="p-2.5 rounded-xl bg-emerald-950/15 border border-emerald-500/20">
                      <div className="text-[10px] font-bold text-emerald-300 uppercase tracking-wider mb-1 flex items-center gap-1">
                        <span>[+] State After</span>
                      </div>
                      {Object.keys(step.after_state || {}).length === 0 ? (
                        <span className="text-slate-500 italic text-[10px]">(No changes)</span>
                      ) : (
                        <div className="space-y-0.5 text-slate-300 overflow-x-auto">
                          {Object.entries(step.after_state).map(([k, v]) => (
                            <div key={k} className="flex gap-1">
                              <span className="text-slate-400">{k}:</span>
                              <span className="text-emerald-200 truncate">{JSON.stringify(v)}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {step.error_message && (
                    <div className="p-2 rounded-lg bg-rose-950/40 border border-rose-500/30 text-[11px] text-rose-300 font-mono">
                      Error: {step.error_message}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* 4. Action Controls */}
      <div className="mt-4 pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-400">
          <Shield className="w-3.5 h-3.5 text-indigo-400" />
          <span>LifeSync Shadow Safety Contract Active</span>
        </div>

        <div className="flex items-center gap-2">
          {/* Awaiting Approval Actions */}
          {isPendingApproval && (
            <>
              <button
                type="button"
                onClick={handleReject}
                disabled={loadingAction !== null}
                className="px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition cursor-pointer disabled:opacity-40"
              >
                Reject
              </button>
              <button
                type="button"
                onClick={handleApprove}
                disabled={loadingAction !== null || selectedStepIds.size === 0}
                className="flex items-center gap-1.5 px-4 py-1.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-bold shadow-md shadow-indigo-600/30 transition cursor-pointer disabled:opacity-40"
              >
                {loadingAction === 'approve' ? (
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Check className="w-3.5 h-3.5" />
                )}
                <span>Approve Selected ({selectedStepIds.size})</span>
              </button>
            </>
          )}

          {/* Rollback Action (When verified and reversible) */}
          {canRollback && (
            <button
              type="button"
              onClick={handleRollback}
              disabled={loadingAction !== null}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-blue-600/30 to-indigo-600/30 hover:from-blue-600/40 hover:to-indigo-600/40 text-blue-300 border border-blue-500/40 text-xs font-bold transition cursor-pointer shadow-md disabled:opacity-40"
              title="Reverse all committed mutations back to pre-execution state"
            >
              {loadingAction === 'rollback' ? (
                <div className="w-3.5 h-3.5 border-2 border-blue-300 border-t-transparent rounded-full animate-spin" />
              ) : (
                <Undo2 className="w-3.5 h-3.5" />
              )}
              <span>Undo / Rollback Mutations</span>
            </button>
          )}

          {plan.status === 'ROLLED_BACK' && (
            <span className="text-xs font-mono font-semibold text-blue-400 flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" />
              State successfully reverted
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
