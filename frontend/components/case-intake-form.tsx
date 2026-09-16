"use client";

import React, { useState } from "react";
import { Sparkles, ArrowRight, CornerDownLeft, Terminal } from "lucide-react";
import { GlassCard, GlassCardContent } from "@/components/ui/glass-card";
import { GlassButton } from "@/components/ui/glass-button";
import { GlassInput } from "@/components/ui/glass-input";

export interface CaseIntakeFormProps {
  onAnalyze: (message: string) => void;
  loading: boolean;
  initialMessage?: string;
}

export const PRESET_CASES = [
  {
    id: "offline-crash",
    tag: "Offline Playback",
    title: "Offline Crash with Prior Reinstall",
    text: "My Spotify keeps crashing whenever I try to use offline playback. I already reinstalled the app twice and restarted my phone.",
  },
  {
    id: "billing-charge",
    tag: "Billing Risk",
    title: "Card Double Charge & Refund Request",
    text: "I cancelled my Premium subscription last week, but I was still charged $10.99 on my credit card this morning. I want an immediate refund.",
  },
  {
    id: "account-hack",
    tag: "High Risk Security",
    title: "Compromised Account & Changed Email",
    text: "Someone hacked my Spotify account! The email was changed to an unknown address and someone in France is streaming right now.",
  },
  {
    id: "ambiguous-query",
    tag: "Edge Case",
    title: "Ambiguous / Low-Information Prompt",
    text: "nothing works spotify is completely broken fix it now",
  },
];

export function CaseIntakeForm({
  onAnalyze,
  loading,
  initialMessage = "",
}: CaseIntakeFormProps) {
  const [inputText, setInputText] = useState(initialMessage || PRESET_CASES[0].text);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || loading) return;
    onAnalyze(inputText.trim());
  };

  return (
    <GlassCard variant="featured" className="p-1 sm:p-2">
      <GlassCardContent className="p-5 sm:p-7 space-y-4">
        {/* Header with technical badge */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-1 border-b border-white/[0.06]">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-[#1DB954]/10 border border-[#1DB954]/30 flex items-center justify-center text-[#1DB954]">
              <Sparkles className="w-3.5 h-3.5" />
            </div>
            <h2 className="text-sm font-semibold tracking-tight text-white uppercase font-mono">
              Live Decision Intake • Magic Link Dispatch
            </h2>
          </div>
          <span className="text-[11px] font-mono text-slate-400">
            Engine: Laplace Bayes + 3-Way Safety Gating
          </span>
        </div>

        {/* Magic-Link Flow: Single Clean Input + Primary CTA Button */}
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="relative flex flex-col sm:flex-row items-stretch gap-2.5">
            <div className="relative flex-1">
              <GlassInput
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Paste customer support tweet or message to evaluate decision pathway..."
                className="h-12 pl-4 pr-10 text-sm font-sans"
                disabled={loading}
              />
              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] font-mono text-slate-500 hidden sm:inline-block pointer-events-none">
                TXT
              </span>
            </div>

            <GlassButton
              type="submit"
              variant="primary"
              size="lg"
              disabled={loading || !inputText.trim()}
              className="h-12 px-6 flex items-center justify-center gap-2 whitespace-nowrap"
            >
              <span>{loading ? "Analyzing..." : "Dispatch to Case Analysis"}</span>
              <ArrowRight className="w-4 h-4" />
            </GlassButton>
          </div>

          {/* Helper Text */}
          <div className="flex items-center justify-between text-xs text-slate-400 px-1">
            <p className="flex items-center gap-1.5 text-slate-400">
              <CornerDownLeft className="w-3 h-3 text-[#1DB954]" />
              <span>
                A structured reasoning trace and decision log will be dispatched directly to your Case Analysis below.
              </span>
            </p>
            <span className="hidden md:inline font-mono text-[11px] text-slate-500">
              Press Enter ↵
            </span>
          </div>
        </form>

        {/* Quick-Pick Example Buttons */}
        <div className="pt-2 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400">
              Quick-pick benchmarks for reviewers:
            </span>
            <span className="text-[11px] text-slate-500 italic hidden sm:inline">
              1-click test load
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
            {PRESET_CASES.map((preset) => (
              <button
                key={preset.id}
                type="button"
                onClick={() => {
                  setInputText(preset.text);
                  onAnalyze(preset.text);
                }}
                className="text-left p-2.5 rounded-xl glass-panel-subtle hover:bg-white/[0.06] hover:border-white/[0.16] transition-all group"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-mono uppercase tracking-wider px-1.5 py-0.5 rounded bg-white/[0.05] text-slate-300 group-hover:text-[#1DB954]">
                    {preset.tag}
                  </span>
                  <Terminal className="w-3 h-3 text-slate-600 group-hover:text-slate-400" />
                </div>
                <div className="text-xs font-semibold text-slate-200 group-hover:text-white line-clamp-1">
                  {preset.title}
                </div>
                <div className="text-[11px] text-slate-500 line-clamp-1 mt-0.5">
                  {preset.text}
                </div>
              </button>
            ))}
          </div>

          {/* Quiet copy as requested in spec */}
          <div className="pt-2 text-center text-xs text-slate-400 border-t border-white/[0.04]">
            <span className="inline-flex items-center gap-1.5 text-slate-400">
              <span className="w-1.5 h-1.5 rounded-full bg-[#1DB954]" />
              This system is designed to say <span className="font-semibold text-slate-200">&apos;I don&apos;t know&apos;</span> rather than guess — try an unusual message and see what happens.
            </span>
          </div>
        </div>
      </GlassCardContent>
    </GlassCard>
  );
}
