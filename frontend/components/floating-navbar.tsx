"use client";

import React, { useState, useEffect } from "react";
import { 
  Activity, 
  BookOpen, 
  Layers, 
  PlayCircle, 
  TrendingUp, 
  ExternalLink 
} from "lucide-react";
import { cn } from "@/lib/utils";

interface FloatingNavbarProps {
  activeTab: "agent" | "benchmark" | "playbook";
  onSelectTab: (tab: "agent" | "benchmark" | "playbook") => void;
  backendConnected: boolean | null;
}

export function FloatingNavbar({
  activeTab,
  onSelectTab,
  backendConnected,
}: FloatingNavbarProps) {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 24);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const navItems: Array<{
    id: "agent" | "benchmark" | "playbook";
    label: string;
    icon: React.ElementType;
  }> = [
    { id: "agent", label: "Live Ticket Feed & Inspector", icon: PlayCircle },
    { id: "benchmark", label: "Evaluation & Trust", icon: TrendingUp },
    { id: "playbook", label: "Playbook Explorer", icon: BookOpen },
  ];

  return (
    <nav
      className={cn(
        "fixed top-4 sm:top-6 left-1/2 -translate-x-1/2 z-50",
        "w-[94%] max-w-5xl transition-all duration-300 ease-out",
        "rounded-full px-3 py-2 sm:px-4 sm:py-2.5 flex items-center justify-between",
        isScrolled
          ? "glass-pill-scrolled"
          : "glass-pill"
      )}
    >
      {/* Brand Identity */}
      <div className="flex items-center gap-2.5 sm:gap-3 pl-1">
        <div className="w-8 h-8 rounded-full bg-[#1DB954] flex items-center justify-center font-bold text-black text-base shadow-[0_0_15px_rgba(29,185,84,0.4)]">
          ♫
        </div>
        <div className="flex items-center gap-2">
          <span className="font-bold text-sm sm:text-base text-white tracking-tight">
            ResolveTrace
          </span>
          <span className="hidden md:inline-flex px-2 py-0.5 text-[10px] font-semibold rounded-full bg-[#1DB954]/15 text-[#1DB954] border border-[#1DB954]/30">
            SpotifyCares
          </span>
        </div>
      </div>

      {/* Navigation Pills */}
      <div className="flex items-center gap-1 sm:gap-1.5 p-1 rounded-full bg-slate-900/60 border border-white/[0.06]">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 sm:px-3.5 sm:py-1.5 rounded-full text-xs font-medium transition-all duration-200 select-none",
                isActive
                  ? "bg-[#1DB954] text-black font-semibold shadow-[0_2px_12px_rgba(29,185,84,0.35)] scale-[1.02]"
                  : "text-slate-300 hover:text-white hover:bg-white/[0.06]"
              )}
            >
              <Icon className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">{item.label}</span>
              <span className="sm:hidden">
                {item.id === "agent" ? "Feed" : item.id === "benchmark" ? "Trust" : "Playbook"}
              </span>
            </button>
          );
        })}
      </div>

      {/* Backend Health Status & Links */}
      <div className="flex items-center gap-2 pr-1">
        {backendConnected === true ? (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="hidden lg:inline">FastAPI</span> :8000
          </div>
        ) : backendConnected === false ? (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono text-amber-400 bg-amber-500/10 border border-amber-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            <span className="hidden lg:inline">Offline</span> Mock
          </div>
        ) : (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono text-slate-400 bg-slate-800/40 border border-white/[0.06]">
            <Activity className="w-3 h-3 animate-spin text-slate-400" />
            <span className="hidden lg:inline">Connecting...</span>
          </div>
        )}

        <a
          href="https://github.com/BMugesh/ResolveTrace"
          target="_blank"
          rel="noreferrer"
          className="hidden sm:flex items-center justify-center w-8 h-8 rounded-full text-slate-400 hover:text-white hover:bg-white/[0.08] transition-colors"
          title="View GitHub Repository"
        >
          <ExternalLink className="w-3.5 h-3.5" />
        </a>
      </div>
    </nav>
  );
}
