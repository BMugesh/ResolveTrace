"use client";

import React, { useState, useEffect } from "react";
import { BookOpen, Database, Filter, Search } from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { GlassBadge } from "@/components/ui/glass-badge";
import { GlassInput } from "@/components/ui/glass-input";
import { cn } from "@/lib/utils";

export function PlaybookExplorer() {
  const [filterIntent, setFilterIntent] = useState<string>("ALL");
  const [filterStatus, setFilterStatus] = useState<string>("ACTIVE");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [pathways, setPathways] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const INTENTS = [
    "ALL",
    "PLAYBACK_STREAMING_AUDIO",
    "OFFLINE_SYNC_DOWNLOADS",
    "APP_CRASH_BUG",
    "SUBSCRIPTION_BILLING_PREMIUM",
    "ACCOUNT_ACCESS_AUTH",
    "DEVICE_INTEGRATION_CONNECT",
    "FAMILY_PLAN_SETUP",
    "STUDENT_DISCOUNT_HULU",
    "AMBIGUOUS_INQUIRY",
  ];

  useEffect(() => {
    const fetchPathways = async () => {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      try {
        const queryParams = new URLSearchParams();
        if (filterIntent !== "ALL") queryParams.set("intent", filterIntent);
        if (filterStatus !== "ALL") queryParams.set("status", filterStatus);

        const res = await fetch(`${apiUrl}/playbook/pathways?${queryParams.toString()}`);
        if (res.ok) {
          const data = await res.json();
          setPathways(data.pathways || []);
        } else {
          throw new Error("Failed to fetch");
        }
      } catch {
        // Fallback sample pathways for offline demo
        setPathways([
          {
            pathway_id: "PW_PLAY_0012",
            intent: "PLAYBACK_STREAMING_AUDIO",
            action: "PROVIDE_INSTRUCTIONS",
            status: "ACTIVE",
            evidence_count: 842,
            pathway_confidence: 0.74,
            conditions: { device_type: "android", troubleshoot_attempted: false },
          },
          {
            pathway_id: "PW_OFFL_0403",
            intent: "OFFLINE_SYNC_DOWNLOADS",
            action: "REQUEST_INFORMATION",
            status: "ACTIVE",
            evidence_count: 29,
            pathway_confidence: 0.55,
            conditions: { device_type: "phone", troubleshoot_attempted: true, issue_recurring: true },
          },
          {
            pathway_id: "PW_SUBS_0043",
            intent: "SUBSCRIPTION_BILLING_PREMIUM",
            action: "REQUEST_INFO_AND_REDIRECT_DM",
            status: "ACTIVE",
            evidence_count: 741,
            pathway_confidence: 0.70,
            conditions: { billing_related: true },
          },
          {
            pathway_id: "PW_CRAS_0088",
            intent: "APP_CRASH_BUG",
            action: "TROUBLESHOOT_RESTART",
            status: "ACTIVE",
            evidence_count: 312,
            pathway_confidence: 0.68,
            conditions: { troubleshoot_attempted: false },
          },
          {
            pathway_id: "PW_DEVI_0155",
            intent: "DEVICE_INTEGRATION_CONNECT",
            action: "PROVIDE_INSTRUCTIONS",
            status: "PROBATION",
            evidence_count: 7,
            pathway_confidence: 0.44,
            conditions: { device_type: "smart_speaker" },
          },
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchPathways();
  }, [filterIntent, filterStatus]);

  const filtered = pathways.filter((p) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      p.pathway_id?.toLowerCase().includes(q) ||
      p.intent?.toLowerCase().includes(q) ||
      p.action?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-[#1DB954]" />
            Mined Playbook Explorer
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Browse 1,545 Mined Historical Decision Pathways with Bayesian Laplace-shrunk confidence
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            297 Active
          </span>
          <span className="px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
            323 Probation
          </span>
          <span className="px-2.5 py-1 rounded-full bg-slate-800/60 text-slate-400 border border-white/[0.06]">
            925 Sparse
          </span>
        </div>
      </div>

      {/* Filter Bar */}
      <GlassCard variant="subtle" className="p-4">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label className="text-[11px] font-mono text-slate-400 block mb-1">SEARCH PATHWAY</label>
            <div className="relative">
              <GlassInput
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search ID, intent, action..."
                className="h-9 pl-8 text-xs font-mono"
              />
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
            </div>
          </div>

          <div>
            <label className="text-[11px] font-mono text-slate-400 block mb-1">STATUS TIER</label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="glass-input w-full h-9 rounded-xl px-3 text-xs text-slate-200 bg-slate-950 focus:outline-none"
            >
              <option value="ALL">ALL STATUSES</option>
              <option value="ACTIVE">ACTIVE (Cp &gt;= 0.50, N &gt;= 10)</option>
              <option value="PROBATION">PROBATION (N: 3-9)</option>
              <option value="SPARSE">SPARSE (N: 1-2)</option>
            </select>
          </div>

          <div>
            <label className="text-[11px] font-mono text-slate-400 block mb-1">INTENT FILTER</label>
            <select
              value={filterIntent}
              onChange={(e) => setFilterIntent(e.target.value)}
              className="glass-input w-full h-9 rounded-xl px-3 text-xs text-slate-200 bg-slate-950 focus:outline-none"
            >
              {INTENTS.map((it) => (
                <option key={it} value={it}>
                  {it}
                </option>
              ))}
            </select>
          </div>
        </div>
      </GlassCard>

      {/* Pathways Table */}
      <GlassCard variant="default" className="p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono border-collapse">
            <thead>
              <tr className="border-b border-white/[0.08] text-slate-400 bg-white/[0.02]">
                <th className="py-3 px-4">Pathway ID</th>
                <th className="py-3 px-4">Intent</th>
                <th className="py-3 px-4">Policy Action</th>
                <th className="py-3 px-4 text-center">Status</th>
                <th className="py-3 px-4 text-right">Evidence (N)</th>
                <th className="py-3 px-4 text-right">Laplace Conf (Cp)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500 font-mono">
                    Loading pathways...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500 font-mono">
                    No matching pathways found for this filter.
                  </td>
                </tr>
              ) : (
                filtered.map((pw) => (
                  <tr key={pw.pathway_id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3 px-4 font-bold text-white flex items-center gap-2">
                      <Database className="w-3.5 h-3.5 text-[#1DB954]" />
                      <span>{pw.pathway_id}</span>
                    </td>
                    <td className="py-3 px-4 text-slate-300 font-sans text-xs">
                      {pw.intent}
                    </td>
                    <td className="py-3 px-4 text-slate-300">
                      <span className="px-2 py-0.5 rounded bg-white/[0.05] text-slate-200">
                        {pw.action}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className={cn(
                          "px-2 py-0.5 rounded text-[10px] font-semibold",
                          pw.status === "ACTIVE"
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                            : pw.status === "PROBATION"
                            ? "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                            : "bg-slate-800 text-slate-400"
                        )}
                      >
                        {pw.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right text-slate-200 font-semibold">
                      {pw.evidence_count}
                    </td>
                    <td className="py-3 px-4 text-right text-[#1DB954] font-bold">
                      {(pw.pathway_confidence * 100).toFixed(1)}%
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </GlassCard>
    </div>
  );
}
