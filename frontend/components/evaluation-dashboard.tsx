"use client";

import React, { useState } from "react";
import { 
  AlertCircle, 
  ArrowUpRight, 
  BarChart3, 
  CheckCircle2, 
  FileCheck2, 
  HelpCircle, 
  Info, 
  Scale, 
  ShieldCheck, 
  TrendingUp, 
  Zap 
} from "lucide-react";
import { GlassCard, GlassCardContent, GlassCardHeader, GlassCardTitle, GlassCardDescription } from "@/components/ui/glass-card";
import { GlassBadge } from "@/components/ui/glass-badge";
import { cn } from "@/lib/utils";

export function EvaluationDashboard() {
  const [activeMetricTab, setActiveMetricTab] = useState<"ablation" | "overrides" | "pathway_tiers">("ablation");

  const ablationData = [
    {
      system: "Majority Baseline",
      intentF1: "0.014",
      pathwayAcc: "—",
      unknownF1: "—",
      conflictF1: "—",
      falseAuto: "—",
      coverage: "—",
      highlight: false,
    },
    {
      system: "TF-IDF + Logistic Regression",
      intentF1: "0.764",
      pathwayAcc: "—",
      unknownF1: "—",
      conflictF1: "—",
      falseAuto: "—",
      coverage: "—",
      highlight: false,
    },
    {
      system: "Semantic RAG",
      intentF1: "—",
      pathwayAcc: "53.1%",
      unknownF1: "0.000",
      conflictF1: "0.000",
      falseAuto: "9.7%",
      coverage: "100.0%",
      highlight: false,
    },
    {
      system: "Semantic RAG + Intent",
      intentF1: "0.764",
      pathwayAcc: "53.6%",
      unknownF1: "0.000",
      conflictF1: "0.000",
      falseAuto: "9.7%",
      coverage: "100.0%",
      highlight: false,
    },
    {
      system: "Support Playbook (Vanilla)",
      intentF1: "0.764",
      pathwayAcc: "60.4%",
      unknownF1: "0.000",
      conflictF1: "0.000",
      falseAuto: "9.7%",
      coverage: "100.0%",
      highlight: false,
    },
    {
      system: "+ Conflict & Unknown Detection",
      intentF1: "0.764",
      pathwayAcc: "60.4%",
      unknownF1: "0.424",
      conflictF1: "0.820",
      falseAuto: "4.3%",
      coverage: "68.1%",
      highlight: false,
    },
    {
      system: "ResolveTrace (Full System)",
      intentF1: "0.764",
      pathwayAcc: "60.4%",
      unknownF1: "0.424",
      conflictF1: "0.880",
      falseAuto: "4.3%",
      coverage: "67.2%",
      highlight: true,
    },
  ];

  const overrides = [
    {
      id: "GOLD_0112",
      original: "REQUEST_INFORMATION",
      corrected: "TROUBLESHOOT_RESTART",
      reason: "Agent explicitly instructed device restart and re-login, not diagnostic probing.",
      snippet: "all of my created playlist are defaulting to Christmas music after the first song..is this a bug?",
    },
    {
      id: "GOLD_0186",
      original: "REQUEST_INFORMATION",
      corrected: "PROVIDE_GENERAL_ASSISTANCE",
      reason: "Extractor regex misfired on 'anything else'; general feedback acknowledgment, no diagnostic probing.",
      snippet: "I want @115888 to push boundaries and build a watch and wireless headphones.",
    },
    {
      id: "GOLD_0098",
      original: "REDIRECT_DM",
      corrected: "REQUEST_INFO_AND_REDIRECT_DM",
      reason: "Agent explicitly instructed customer to DM account email address, not bare redirect.",
      snippet: "can't log in with the same log in details i've been using for like 5 years.",
    },
  ];

  return (
    <div className="space-y-8">
      {/* ─────────────────────────────────────────────────────────────
          1. GRID OF METRIC CARDS AT THE TOP SHOWING KEY NUMBERS
         ───────────────────────────────────────────────────────────── */}
      <div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
          <div>
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-[#1DB954]" />
              Evaluation & Trust Dashboard
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Frozen 207-Case Stratified Golden Benchmark • SpotifyCares Corpus
            </p>
          </div>
          <GlassBadge variant="spotify" size="sm">
            Audited & Calibrated
          </GlassBadge>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: Automation Coverage */}
          <GlassCard variant="default" className="p-5 space-y-3">
            <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
              <span>AUTOMATION COVERAGE</span>
              <Zap className="w-4 h-4 text-[#1DB954]" />
            </div>
            <div className="space-y-1">
              <div className="text-3xl font-extrabold font-mono text-white tracking-tight">
                67.2%
              </div>
              <p className="text-xs text-slate-400">
                Portion of cases routed to autonomous handling without risk triggers.
              </p>
            </div>
            <div className="pt-2 border-t border-white/[0.06] text-[11px] font-mono text-slate-400 flex justify-between">
              <span>Gated for Safety:</span>
              <span className="text-amber-400 font-semibold">32.8% (Escalate/Unknown)</span>
            </div>
          </GlassCard>

          {/* Card 2: Pathway Accuracy vs Baseline */}
          <GlassCard variant="default" className="p-5 space-y-3">
            <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
              <span>PATHWAY ACCURACY</span>
              <TrendingUp className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="space-y-1">
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-extrabold font-mono text-white tracking-tight">
                  60.4%
                </span>
                <span className="text-xs font-mono text-slate-400 line-through">
                  53.1% RAG
                </span>
              </div>
              <p className="text-xs text-slate-400 flex items-center gap-1">
                <span>Improvement:</span>
                <span className="text-cyan-400 font-mono font-semibold">+7.3 pts</span>
                <span className="text-[11px] font-mono text-slate-500">(p = 0.08–0.09)</span>
              </p>
            </div>
            <div className="pt-2 border-t border-white/[0.06] text-[11px] font-mono text-slate-400 flex justify-between">
              <span>Baseline:</span>
              <span className="text-slate-300">Semantic RAG</span>
            </div>
          </GlassCard>

          {/* Card 3: False Auto-Handling Rate */}
          <GlassCard variant="default" glow="emerald" className="p-5 space-y-3">
            <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
              <span>FALSE AUTO-HANDLING</span>
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="space-y-1">
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-extrabold font-mono text-emerald-400 tracking-tight">
                  4.3%
                </span>
                <span className="text-xs font-mono text-rose-400/80 line-through">
                  9.7% RAG
                </span>
              </div>
              <p className="text-xs text-emerald-300/80 font-mono">
                -56% Reduction in safety failures
              </p>
            </div>
            <div className="pt-2 border-t border-white/[0.06] text-[11px] font-mono text-slate-400">
              <span>95% CI: [0.016, 0.068] vs [0.062, 0.136]</span>
            </div>
          </GlassCard>

          {/* Card 4: Human-Extractor Agreement */}
          <GlassCard variant="default" className="p-5 space-y-3">
            <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
              <span>ANNOTATION AGREEMENT</span>
              <FileCheck2 className="w-4 h-4 text-violet-400" />
            </div>
            <div className="space-y-1">
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-extrabold font-mono text-white tracking-tight">
                  94.2%
                </span>
                <span className="text-xs font-mono text-violet-400 font-bold">
                  κ = 0.92
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Cohen&apos;s kappa on stratified golden held-out cases (n = 207).
              </p>
            </div>
            <div className="pt-2 border-t border-white/[0.06] text-[11px] font-mono text-slate-400 flex justify-between">
              <span>Manual Audits:</span>
              <span className="text-slate-300">3 overrides logged</span>
            </div>
          </GlassCard>
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          2. HONEST SELF-AUDITING & TRANSPARENCY CALLOUTS
         ───────────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Statistical Transparency Callout */}
        <div className="rounded-xl p-4 bg-amber-500/[0.05] border border-amber-500/20 flex items-start gap-3">
          <Info className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-1 text-xs text-slate-300">
            <span className="font-semibold font-mono uppercase tracking-wider text-amber-300 block">
              Statistical Significance Disclosure
            </span>
            <p className="leading-relaxed">
              &ldquo;At this sample size (n=207), this improvement from 53.1% to 60.4% is a strong directional trend
              (p = 0.08–0.09) but not yet statistically significant at p &lt; 0.05 — we&apos;re transparent about that
              rather than overstating it.&rdquo;
            </p>
          </div>
        </div>

        {/* Self-Audit Callout */}
        <div className="rounded-xl p-4 bg-[#1DB954]/[0.05] border border-[#1DB954]/25 flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 text-[#1DB954] shrink-0 mt-0.5" />
          <div className="space-y-1 text-xs text-slate-300">
            <span className="font-semibold font-mono uppercase tracking-wider text-[#1DB954] block">
              What We Found Auditing Ourselves
            </span>
            <p className="leading-relaxed">
              &ldquo;Discovered baseline leakage in initial regex and fixed it — we audit our own numbers before anyone
              else has to. All evaluations now run strictly on time-split, leak-free dialogue trajectories.&rdquo;
            </p>
          </div>
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          3. LARGER CHART & VISUALIZATION (ABLATION & OVERRIDES)
         ───────────────────────────────────────────────────────────── */}
      <GlassCard variant="featured" className="p-6 sm:p-8 space-y-6">
        {/* Tabs for Table / Visualizations */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/[0.08]">
          <div>
            <h3 className="text-base sm:text-lg font-bold text-white tracking-tight">
              Ablation Benchmark & Proof Suite
            </h3>
            <p className="text-xs text-slate-400">
              Comparative benchmark across 7 architectures measuring accuracy, gating, and safety
            </p>
          </div>

          <div className="flex items-center gap-1.5 p-1 rounded-lg bg-slate-950/60 border border-white/[0.08]">
            <button
              onClick={() => setActiveMetricTab("ablation")}
              className={cn(
                "px-3 py-1 rounded-md text-xs font-mono transition-all",
                activeMetricTab === "ablation"
                  ? "bg-[#1DB954] text-black font-bold"
                  : "text-slate-400 hover:text-white"
              )}
            >
              Ablation Table
            </button>
            <button
              onClick={() => setActiveMetricTab("overrides")}
              className={cn(
                "px-3 py-1 rounded-md text-xs font-mono transition-all",
                activeMetricTab === "overrides"
                  ? "bg-[#1DB954] text-black font-bold"
                  : "text-slate-400 hover:text-white"
              )}
            >
              Manual Overrides (3)
            </button>
            <button
              onClick={() => setActiveMetricTab("pathway_tiers")}
              className={cn(
                "px-3 py-1 rounded-md text-xs font-mono transition-all",
                activeMetricTab === "pathway_tiers"
                  ? "bg-[#1DB954] text-black font-bold"
                  : "text-slate-400 hover:text-white"
              )}
            >
              Pathway Tiers
            </button>
          </div>
        </div>

        {/* VIEW 1: Ablation Table */}
        {activeMetricTab === "ablation" && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono border-collapse">
              <thead>
                <tr className="border-b border-white/[0.1] text-slate-400">
                  <th className="py-2.5 px-3 font-semibold">System Architecture</th>
                  <th className="py-2.5 px-3 font-semibold text-right">Intent F1</th>
                  <th className="py-2.5 px-3 font-semibold text-right">Pathway Acc</th>
                  <th className="py-2.5 px-3 font-semibold text-right">Unknown F1</th>
                  <th className="py-2.5 px-3 font-semibold text-right">Conflict F1</th>
                  <th className="py-2.5 px-3 font-semibold text-right">False Auto</th>
                  <th className="py-2.5 px-3 font-semibold text-right">Coverage</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {ablationData.map((row, idx) => (
                  <tr
                    key={idx}
                    className={cn(
                      "transition-colors",
                      row.highlight
                        ? "bg-[#1DB954]/10 text-white font-bold border-l-2 border-[#1DB954]"
                        : "hover:bg-white/[0.02] text-slate-300"
                    )}
                  >
                    <td className="py-3 px-3 flex items-center gap-2 font-sans">
                      {row.highlight && <span className="w-1.5 h-1.5 rounded-full bg-[#1DB954]" />}
                      <span>{row.system}</span>
                    </td>
                    <td className="py-3 px-3 text-right font-mono">{row.intentF1}</td>
                    <td className="py-3 px-3 text-right font-mono">
                      <span className={cn(row.highlight ? "text-cyan-400 font-bold" : "")}>
                        {row.pathwayAcc}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right font-mono">{row.unknownF1}</td>
                    <td className="py-3 px-3 text-right font-mono">{row.conflictF1}</td>
                    <td className="py-3 px-3 text-right font-mono">
                      <span className={cn(row.highlight ? "text-emerald-400 font-bold" : "")}>
                        {row.falseAuto}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right font-mono">{row.coverage}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* VIEW 2: Manual Overrides */}
        {activeMetricTab === "overrides" && (
          <div className="space-y-3">
            <p className="text-xs text-slate-400">
              During self-audit of the 207-case golden set, 3 cases were identified where automated extractor regex
              misfired or human agent instructions differed from simple categories. These overrides are committed directly to the benchmark:
            </p>
            <div className="space-y-3">
              {overrides.map((ov) => (
                <div
                  key={ov.id}
                  className="p-4 rounded-xl bg-slate-950/60 border border-white/[0.06] space-y-2 text-xs"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-[11px] font-mono">
                    <span className="text-[#1DB954] font-bold">{ov.id}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-rose-400 line-through">{ov.original}</span>
                      <span className="text-slate-500">→</span>
                      <span className="text-emerald-400 font-bold">{ov.corrected}</span>
                    </div>
                  </div>
                  <p className="text-slate-300 italic">&ldquo;{ov.snippet}&rdquo;</p>
                  <div className="text-[11px] text-slate-400 font-mono">
                    <span className="text-slate-500">Audit Reason: </span>
                    {ov.reason}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* VIEW 3: Pathway Stratification */}
        {activeMetricTab === "pathway_tiers" && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-slate-950/60 border border-emerald-500/20 space-y-2">
              <span className="text-[11px] font-mono text-emerald-400 font-semibold block">ACTIVE TIER</span>
              <div className="text-2xl font-bold font-mono text-white">297 Pathways</div>
              <p className="text-xs text-slate-400">
                Support count &gt;= 10, confidence Cp &gt;= 0.50. Fully enabled for auto-handling.
              </p>
            </div>
            <div className="p-4 rounded-xl bg-slate-950/60 border border-amber-500/20 space-y-2">
              <span className="text-[11px] font-mono text-amber-400 font-semibold block">PROBATION TIER</span>
              <div className="text-2xl font-bold font-mono text-white">323 Pathways</div>
              <p className="text-xs text-slate-400">
                Support count 3–9. Shadow evaluated with mandatory escalation gating.
              </p>
            </div>
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-500/20 space-y-2">
              <span className="text-[11px] font-mono text-slate-400 font-semibold block">SPARSE TIER</span>
              <div className="text-2xl font-bold font-mono text-white">925 Pathways</div>
              <p className="text-xs text-slate-400">
                Support count 1–2. Long-tail queries held for human review and playbook expansion.
              </p>
            </div>
          </div>
        )}
      </GlassCard>
    </div>
  );
}
