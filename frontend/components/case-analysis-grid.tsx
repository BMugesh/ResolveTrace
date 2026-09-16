"use client";

import React, { useState } from "react";
import { 
  Bot, 
  ChevronDown, 
  ChevronUp, 
  Cpu, 
  Database, 
  FileText, 
  HelpCircle, 
  History, 
  MessageSquare, 
  ShieldAlert, 
  ShieldCheck, 
  Sliders, 
  Sparkles, 
  User, 
  Zap 
} from "lucide-react";
import { GlassCard, GlassCardContent, GlassCardHeader, GlassCardTitle, GlassCardDescription } from "@/components/ui/glass-card";
import { GlassBadge, DecisionBadge } from "@/components/ui/glass-badge";
import { cn } from "@/lib/utils";

export interface DecisionResult {
  intent: string;
  intent_confidence: number;
  state: {
    info_provided: boolean;
    troubleshoot_attempted: boolean;
    issue_recurring: boolean;
    billing_related: boolean;
    device_type: string;
    sentiment_frustrated?: boolean;
    evidence?: Record<string, string>;
  };
  decision: "AUTO-HANDLE" | "ESCALATE" | "UNKNOWN";
  recommended_action: string;
  reason: string;
  automation_score: number;
  matched_pathway_id?: string;
  matched_pathway?: {
    pathway_id: string;
    intent: string;
    conditions: Record<string, any>;
    action: string;
    evidence_count: number;
    pathway_confidence: number;
    status: string;
    outcome_distribution?: Record<string, number>;
    historical_examples?: Array<{
      thread_id: string;
      customer_message: string;
      agent_reply: string;
      outcome: string;
    }>;
  };
  draft_reply: string;
}

interface CaseAnalysisGridProps {
  customerMessage: string;
  result: DecisionResult | null;
  loading: boolean;
}

export function CaseAnalysisGrid({
  customerMessage,
  result,
  loading,
}: CaseAnalysisGridProps) {
  const [showHistory, setShowHistory] = useState(false);

  if (loading) {
    return (
      <GlassCard variant="featured" className="p-8 text-center space-y-4">
        <div className="flex flex-col items-center justify-center py-12 space-y-3">
          <div className="w-10 h-10 rounded-full border-2 border-[#1DB954] border-t-transparent animate-spin" />
          <div className="font-mono text-sm text-slate-300">
            Traversing 1,545 Mined Pathways & Safety Gates...
          </div>
          <p className="text-xs text-slate-500 max-w-sm">
            Extracting dialog state, evaluating Bayesian Laplace confidence, and checking conflict margin (δ=0.08).
          </p>
        </div>
      </GlassCard>
    );
  }

  if (!result) {
    return (
      <GlassCard variant="subtle" className="p-8 text-center text-slate-500">
        <p className="text-sm font-mono">No case dispatched yet. Select a preset or type a message above.</p>
      </GlassCard>
    );
  }

  const {
    intent,
    intent_confidence,
    state,
    decision,
    recommended_action,
    reason,
    automation_score,
    matched_pathway_id,
    matched_pathway,
    draft_reply,
  } = result;

  const examples = matched_pathway?.historical_examples || [];

  return (
    <div className="space-y-6">
      {/* ─────────────────────────────────────────────────────────────
          1. LARGE FEATURED POST: CONVERSATIONS & DECISION VERDICT
         ───────────────────────────────────────────────────────────── */}
      <GlassCard
        variant="featured"
        glow={
          decision === "AUTO-HANDLE"
            ? "emerald"
            : decision === "ESCALATE"
            ? "amber"
            : "rose"
        }
        className="p-6 sm:p-8 space-y-6"
      >
        {/* Top Header: Decision Verdict & Meta */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/[0.08]">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <DecisionBadge decision={decision} confidence={automation_score} />
              <GlassBadge variant="cyan" size="sm">
                ID: {matched_pathway_id || "UNMAPPED"}
              </GlassBadge>
              <GlassBadge variant="neutral" size="sm">
                Action: {recommended_action}
              </GlassBadge>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white mt-2">
              Customer Conversation & Support Decision
            </h2>
          </div>

          <div className="flex items-center gap-4 text-xs font-mono text-slate-400">
            <div className="text-right">
              <span className="text-slate-500 block text-[10px]">INTENT ACCURACY</span>
              <span className="text-white font-bold">{Math.round(intent_confidence * 100)}%</span>
            </div>
            <div className="h-7 w-[1px] bg-white/[0.1]" />
            <div className="text-right">
              <span className="text-slate-500 block text-[10px]">AUTO SCORE</span>
              <span className="text-[#1DB954] font-bold">{(automation_score * 100).toFixed(1)}%</span>
            </div>
          </div>
        </div>

        {/* Conversation Flow (Customer Message -> Grounded Agent Response) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 relative">
          {/* Customer Message Box */}
          <div className="rounded-xl p-4 bg-slate-950/70 border border-white/[0.08] space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-400 pb-1.5 border-b border-white/[0.04]">
              <span className="flex items-center gap-1.5 font-semibold text-slate-200">
                <User className="w-3.5 h-3.5 text-sky-400" />
                Customer Inquiry (@SpotifyCares)
              </span>
              <span className="font-mono text-[10px] text-slate-500">TURN 1 (INBOUND)</span>
            </div>
            <p className="text-sm text-slate-100 leading-relaxed font-sans select-text">
              &ldquo;{customerMessage}&rdquo;
            </p>
          </div>

          {/* Draft Reply Box */}
          <div className="rounded-xl p-4 bg-slate-950/70 border border-white/[0.08] space-y-2 relative">
            <div className="flex items-center justify-between text-xs text-slate-400 pb-1.5 border-b border-white/[0.04]">
              <span className="flex items-center gap-1.5 font-semibold text-slate-200">
                <Bot className="w-3.5 h-3.5 text-[#1DB954]" />
                Grounded Support Response
              </span>
              <span className="font-mono text-[10px] text-[#1DB954] flex items-center gap-1">
                <Sparkles className="w-3 h-3" />
                POLICY GROUNDED
              </span>
            </div>
            <p className="text-sm text-slate-100 leading-relaxed font-sans select-text italic">
              {draft_reply}
            </p>
            {matched_pathway_id && (
              <div className="pt-2 text-[11px] font-mono text-slate-400 flex items-center gap-1">
                <span>grounded in pathway →</span>
                <span className="text-[#1DB954] font-semibold">{matched_pathway_id}</span>
              </div>
            )}
          </div>
        </div>

        {/* Technical Decision Rationale Box */}
        <div className="rounded-xl p-4 bg-white/[0.02] border border-white/[0.08] flex items-start gap-3">
          <div className="mt-0.5 text-slate-400">
            {decision === "AUTO-HANDLE" ? (
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
            ) : decision === "ESCALATE" ? (
              <ShieldAlert className="w-5 h-5 text-amber-400" />
            ) : (
              <HelpCircle className="w-5 h-5 text-rose-400" />
            )}
          </div>
          <div className="space-y-1">
            <div className="text-xs font-mono uppercase tracking-wider text-slate-400">
              Why did ResolveTrace decide this?
            </div>
            <p className="text-sm text-slate-200 font-medium">
              {reason}
            </p>
          </div>
        </div>
      </GlassCard>

      {/* ─────────────────────────────────────────────────────────────
          2. MAGAZINE-STYLE GRID: CASE'S ANALYTICS (4 SMALLER CARDS)
         ───────────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* CARD 1: Extracted State */}
        <GlassCard variant="subtle" className="p-5 flex flex-col justify-between space-y-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase text-slate-400 flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                1. Extracted State
              </span>
              <span className="text-[10px] font-mono text-slate-500">Regex/Heuristics</span>
            </div>

            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between py-1 border-b border-white/[0.04]">
                <span className="text-slate-400">Intent:</span>
                <span className="font-mono text-slate-200 font-semibold">{intent}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/[0.04]">
                <span className="text-slate-400">Device Detected:</span>
                <span className="font-mono text-slate-200">{state.device_type}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/[0.04]">
                <span className="text-slate-400">Troubleshoot Attempted:</span>
                <span className={cn("font-mono font-semibold", state.troubleshoot_attempted ? "text-emerald-400" : "text-slate-500")}>
                  {state.troubleshoot_attempted ? "TRUE" : "FALSE"}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/[0.04]">
                <span className="text-slate-400">Issue Recurring:</span>
                <span className={cn("font-mono font-semibold", state.issue_recurring ? "text-amber-400" : "text-slate-500")}>
                  {state.issue_recurring ? "TRUE" : "FALSE"}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/[0.04]">
                <span className="text-slate-400">Billing/Refund Related:</span>
                <span className={cn("font-mono font-semibold", state.billing_related ? "text-rose-400" : "text-slate-500")}>
                  {state.billing_related ? "TRUE" : "FALSE"}
                </span>
              </div>
            </div>
          </div>

          {state.evidence && Object.keys(state.evidence).length > 0 && (
            <div className="pt-2 border-t border-white/[0.06] text-[11px] font-mono text-slate-400">
              <span className="text-slate-500 block text-[10px]">EVIDENCE TOKENS:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {Object.entries(state.evidence).map(([key, val]) => (
                  <span key={key} className="px-1.5 py-0.5 rounded bg-white/[0.06] text-slate-300">
                    {key}: &quot;{val}&quot;
                  </span>
                ))}
              </div>
            </div>
          )}
        </GlassCard>

        {/* CARD 2: Matched Support Pathway */}
        <GlassCard variant="subtle" className="p-5 flex flex-col justify-between space-y-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase text-slate-400 flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-[#1DB954]" />
                2. Matched Pathway
              </span>
              <span className="text-[10px] font-mono text-emerald-400">
                {matched_pathway?.status || "ACTIVE"}
              </span>
            </div>

            <div className="space-y-2">
              <div className="p-2.5 rounded-lg bg-slate-950/60 border border-white/[0.06]">
                <span className="text-[10px] font-mono text-slate-500 block">PATHWAY ID</span>
                <span className="font-mono text-sm text-white font-bold">
                  {matched_pathway_id || "NONE"}
                </span>
              </div>

              <div className="space-y-1 text-xs">
                <div className="flex justify-between py-1 border-b border-white/[0.04]">
                  <span className="text-slate-400">Laplace Confidence (Cp):</span>
                  <span className="font-mono text-[#1DB954] font-bold">
                    {matched_pathway?.pathway_confidence ? (matched_pathway.pathway_confidence * 100).toFixed(1) + "%" : "N/A"}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-white/[0.04]">
                  <span className="text-slate-400">Historical Evidence Count:</span>
                  <span className="font-mono text-slate-200">
                    {matched_pathway?.evidence_count ?? 0} threads
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-white/[0.04]">
                  <span className="text-slate-400">Recommended Action:</span>
                  <span className="font-mono text-slate-200 font-semibold">{recommended_action}</span>
                </div>
              </div>
            </div>
          </div>

          {examples.length > 0 && (
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="w-full py-1.5 px-2 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-[11px] font-mono text-slate-300 flex items-center justify-between transition-colors"
            >
              <span className="flex items-center gap-1">
                <History className="w-3 h-3 text-[#1DB954]" />
                View {examples.length} Historical Threads
              </span>
              {showHistory ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>
          )}
        </GlassCard>

        {/* CARD 3: 3-Way Safety Gating Matrix */}
        <GlassCard variant="subtle" className="p-5 flex flex-col justify-between space-y-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase text-slate-400 flex items-center gap-1.5">
                <Sliders className="w-3.5 h-3.5 text-amber-400" />
                3. Safety Gating Matrix
              </span>
              <span className="text-[10px] font-mono text-slate-500">Calibrated</span>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-white/[0.04]">
                <span className="text-slate-400">Conflict Margin (δ):</span>
                <span className="font-mono text-slate-200">0.08 (calibrated)</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/[0.04]">
                <span className="text-slate-400">Unknown Threshold (τ):</span>
                <span className="font-mono text-slate-200">0.50</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/[0.04]">
                <span className="text-slate-400">Auto Threshold:</span>
                <span className="font-mono text-slate-200">&gt;= 0.55</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/[0.04]">
                <span className="text-slate-400">Risk Assessment:</span>
                <span className={cn(
                  "font-mono font-semibold",
                  state.billing_related ? "text-rose-400" : "text-emerald-400"
                )}>
                  {state.billing_related ? "FINANCIAL RISK" : "STANDARD OPERATIONAL"}
                </span>
              </div>
            </div>
          </div>

          <div className="p-2.5 rounded-lg bg-slate-950/60 border border-white/[0.06] text-[11px] font-mono text-slate-400">
            <span className="text-slate-500 block text-[10px]">AUTOMATION SAFETY:</span>
            <span>
              {decision === "AUTO-HANDLE"
                ? "✓ Passed safety gates with zero conflict"
                : decision === "ESCALATE"
                ? "⚠ Gated to prevent false auto-handling"
                : "? Below confidence cutoff — fallback"}
            </span>
          </div>
        </GlassCard>

        {/* CARD 4: Outcome & Resolution Distribution */}
        <GlassCard variant="subtle" className="p-5 flex flex-col justify-between space-y-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase text-slate-400 flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5 text-violet-400" />
                4. Outcome Distribution
              </span>
              <span className="text-[10px] font-mono text-slate-500">Historical Mined</span>
            </div>

            <div className="space-y-2 text-xs">
              {matched_pathway?.outcome_distribution ? (
                Object.entries(matched_pathway.outcome_distribution).map(([outcomeKey, count]) => (
                  <div key={outcomeKey} className="space-y-1">
                    <div className="flex justify-between text-[11px] font-mono">
                      <span className="text-slate-400">{outcomeKey}:</span>
                      <span className="text-slate-200 font-semibold">{count}</span>
                    </div>
                    <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                      <div
                        className={cn(
                          "h-full rounded-full",
                          outcomeKey === "RESOLVED"
                            ? "bg-[#1DB954]"
                            : outcomeKey === "ESCALATED"
                            ? "bg-amber-400"
                            : outcomeKey === "LIKELY_RESOLVED"
                            ? "bg-sky-400"
                            : "bg-slate-500"
                        )}
                        style={{
                          width: `${Math.min(100, Math.max(10, (count / (matched_pathway.evidence_count || 1)) * 100))}%`,
                        }}
                      />
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-slate-500 font-mono text-xs py-4 text-center">
                  Sparse distribution data for unmapped query
                </div>
              )}
            </div>
          </div>

          <div className="text-[11px] font-mono text-slate-400">
            <span>Template Slots: </span>
            <span className="text-slate-300 font-semibold">{`{device}, {action}, {link}`}</span>
          </div>
        </GlassCard>

      </div>

      {/* Expandable Real Historical Example Conversations */}
      {showHistory && examples.length > 0 && (
        <GlassCard variant="default" className="p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
            <h4 className="text-sm font-bold text-white flex items-center gap-2 font-mono">
              <History className="w-4 h-4 text-[#1DB954]" />
              Historical Support Conversations from Twitter TWCS Dataset
            </h4>
            <span className="text-xs font-mono text-slate-400">
              Pathway {matched_pathway_id} Evidence
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {examples.slice(0, 4).map((ex, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl bg-slate-950/60 border border-white/[0.06] space-y-2 text-xs"
              >
                <div className="flex items-center justify-between text-slate-400 font-mono text-[11px]">
                  <span className="text-[#1DB954]">{ex.thread_id}</span>
                  <span className="px-1.5 py-0.5 rounded bg-white/[0.05]">Outcome: {ex.outcome}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block font-mono">CUSTOMER:</span>
                  <p className="text-slate-200">{ex.customer_message}</p>
                </div>
                <div className="pt-1 border-t border-white/[0.04]">
                  <span className="text-[10px] text-[#1DB954] block font-mono">SPOTIFYCARES AGENT:</span>
                  <p className="text-slate-300 italic">{ex.agent_reply}</p>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      )}
    </div>
  );
}
