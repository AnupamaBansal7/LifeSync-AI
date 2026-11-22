import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Sparkles,
  Check,
  FastForward,
  CornerDownLeft,
  ChevronRight,
  Volume2,
} from 'lucide-react';
import type { ClarificationCardData } from '../../types';

interface ClarificationCardProps {
  card: ClarificationCardData;
  onRespond: (selectedOptions: string[], customText?: string, skipAndGenerate?: boolean) => void;
  disabled?: boolean;
  onSpeakQuestion?: (text: string) => void;
}

export const ClarificationCard: React.FC<ClarificationCardProps> = ({
  card,
  onRespond,
  disabled = false,
  onSpeakQuestion,
}) => {
  const [selectedValues, setSelectedValues] = useState<string[]>([]);
  const [customInput, setCustomInput] = useState('');
  const [isAnswered, setIsAnswered] = useState(false);
  const [answeredSummary, setAnsweredSummary] = useState<string | null>(null);

  const isMulti = card.selection_mode === 'multi';

  const handleOptionClick = (val: string, label: string) => {
    if (disabled || isAnswered) return;

    if (isMulti) {
      setSelectedValues((prev) =>
        prev.includes(val) ? prev.filter((v) => v !== val) : [...prev, val]
      );
    } else {
      setSelectedValues([val]);
      setIsAnswered(true);
      setAnsweredSummary(label);
      onRespond([val], undefined, false);
    }
  };

  const handleMultiSubmit = () => {
    if (disabled || isAnswered || selectedValues.length === 0) return;
    setIsAnswered(true);
    const summary = card.options
      .filter((o) => selectedValues.includes(o.value))
      .map((o) => o.label)
      .join(', ');
    setAnsweredSummary(summary);
    onRespond(selectedValues, customInput.trim() || undefined, false);
  };

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (disabled || isAnswered || !customInput.trim()) return;
    setIsAnswered(true);
    setAnsweredSummary(customInput.trim());
    onRespond(selectedValues, customInput.trim(), false);
  };

  const handleSkip = () => {
    if (disabled || isAnswered) return;
    setIsAnswered(true);
    setAnsweredSummary('Skipped & Built Plan');
    onRespond([], undefined, true);
  };

  // Collapsed View if already answered
  if (isAnswered && answeredSummary) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        className="my-2 flex items-center justify-between rounded-lg border border-purple-500/20 bg-purple-950/20 px-3 py-1.5 text-xs text-purple-300 backdrop-blur-sm"
      >
        <div className="flex items-center gap-2">
          <span className="flex h-4 w-4 items-center justify-center rounded-full bg-purple-500/20 text-[10px] text-purple-300">
            ✓
          </span>
          <span className="font-medium text-slate-300">Step {card.step}:</span>
          <span className="text-purple-200">{answeredSummary}</span>
        </div>
        <span className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold">
          Saved
        </span>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -10 }}
      className="my-3 overflow-hidden rounded-xl border border-purple-500/30 bg-gradient-to-b from-purple-950/40 via-slate-900/80 to-slate-950/90 p-4 shadow-xl shadow-purple-950/20 backdrop-blur-md"
    >
      {/* Header & Step Pill */}
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1 rounded-full bg-purple-500/20 px-2.5 py-0.5 text-[10px] font-semibold text-purple-300 border border-purple-500/30">
            <Sparkles className="h-3 w-3 text-purple-400" />
            Step {card.step} of {card.estimated_total_steps}
          </span>
          <span className="rounded-full bg-slate-800/80 px-2 py-0.5 text-[10px] font-medium text-slate-400">
            {card.domain.replace(/_/g, ' ')}
          </span>
        </div>

        {onSpeakQuestion && (
          <button
            type="button"
            onClick={() => onSpeakQuestion(card.question)}
            title="Read question aloud"
            className="rounded p-1 text-slate-400 hover:text-purple-300 hover:bg-purple-900/30 transition-colors"
          >
            <Volume2 className="h-3.5 w-3.5" />
          </button>
        )}
      </div>

      {/* Conversational Question */}
      <h4 className="mb-3 text-sm font-semibold text-slate-100 leading-snug">
        {card.question}
      </h4>

      {/* Options Grid */}
      <div className="space-y-2">
        {card.options.map((option) => {
          const isSelected = selectedValues.includes(option.value);
          return (
            <button
              key={option.id}
              type="button"
              disabled={disabled}
              onClick={() => handleOptionClick(option.value, option.label)}
              className={`group flex w-full items-start justify-between rounded-lg border p-2.5 text-left transition-all ${
                isSelected
                  ? 'border-purple-500 bg-purple-900/30 text-white shadow-md shadow-purple-950/40'
                  : 'border-slate-800/80 bg-slate-900/50 text-slate-300 hover:border-purple-500/50 hover:bg-purple-950/20 hover:text-slate-100'
              }`}
            >
              <div className="flex-1 pr-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold">{option.label}</span>
                </div>
                {option.description && (
                  <p className="mt-0.5 text-[11px] text-slate-400 group-hover:text-slate-300">
                    {option.description}
                  </p>
                )}
              </div>
              <div
                className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded ${
                  isMulti ? 'border' : 'rounded-full border'
                } ${
                  isSelected
                    ? 'border-purple-400 bg-purple-500 text-white'
                    : 'border-slate-600 bg-slate-800/40'
                }`}
              >
                {isSelected && <Check className="h-3 w-3 stroke-[3]" />}
              </div>
            </button>
          );
        })}
      </div>

      {/* Multi-Select Continue Button */}
      {isMulti && (
        <div className="mt-3 flex justify-end">
          <button
            type="button"
            disabled={disabled || selectedValues.length === 0}
            onClick={handleMultiSubmit}
            className="flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 px-3.5 py-1.5 text-xs font-medium text-white shadow-md shadow-purple-900/30 transition-all hover:brightness-110 disabled:opacity-50"
          >
            Continue <ChevronRight className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      {/* Custom Answer Input Bar */}
      {card.allow_custom_input && (
        <form onSubmit={handleCustomSubmit} className="mt-3 flex items-center gap-2">
          <input
            type="text"
            value={customInput}
            onChange={(e) => setCustomInput(e.target.value)}
            disabled={disabled}
            placeholder="Or type your custom answer..."
            className="flex-1 rounded-lg border border-slate-800 bg-slate-900/80 px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500/50"
          />
          {customInput.trim() && (
            <button
              type="submit"
              disabled={disabled}
              className="flex items-center justify-center rounded-lg bg-purple-600 px-2.5 py-1.5 text-xs text-white hover:bg-purple-500 transition-colors"
            >
              <CornerDownLeft className="h-3.5 w-3.5" />
            </button>
          )}
        </form>
      )}

      {/* Skip & Generate Blueprint Now */}
      {card.can_skip_and_generate && (
        <div className="mt-3 flex items-center justify-between border-t border-slate-800/60 pt-2 text-[11px] text-slate-400">
          <span>Have enough context?</span>
          <button
            type="button"
            disabled={disabled}
            onClick={handleSkip}
            className="flex items-center gap-1 font-medium text-purple-400 hover:text-purple-300 hover:underline transition-all"
          >
            <FastForward className="h-3 w-3" />
            Skip & Build Plan Now
          </button>
        </div>
      )}
    </motion.div>
  );
};
