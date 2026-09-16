import * as React from "react";
import { cn } from "@/lib/utils";

export interface GlassBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "autohandle" | "escalate" | "unknown" | "neutral" | "cyan" | "spotify";
  size?: "sm" | "md";
}

export function GlassBadge({
  className,
  variant = "neutral",
  size = "md",
  children,
  ...props
}: GlassBadgeProps) {
  const sizes = {
    sm: "text-[11px] px-2 py-0.5 gap-1",
    md: "text-xs px-2.5 py-1 gap-1.5",
  };

  const variants = {
    autohandle:
      "bg-emerald-500/10 text-emerald-400 border border-emerald-500/25 shadow-[0_0_12px_-3px_rgba(16,185,129,0.3)] font-semibold",
    escalate:
      "bg-amber-500/10 text-amber-400 border border-amber-500/25 shadow-[0_0_12px_-3px_rgba(245,158,11,0.3)] font-semibold",
    unknown:
      "bg-rose-500/10 text-rose-400 border border-rose-500/25 shadow-[0_0_12px_-3px_rgba(244,63,94,0.3)] font-semibold",
    spotify:
      "bg-[#1DB954]/10 text-[#1DB954] border border-[#1DB954]/30 shadow-[0_0_12px_-3px_rgba(29,185,84,0.3)] font-semibold",
    cyan:
      "bg-cyan-500/10 text-cyan-400 border border-cyan-500/25 shadow-[0_0_12px_-3px_rgba(6,182,212,0.3)] font-mono",
    neutral:
      "bg-slate-800/40 text-slate-300 border border-white/[0.08] backdrop-blur-sm",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full font-medium transition-all select-none",
        sizes[size],
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}

export function DecisionBadge({
  decision,
  confidence,
}: {
  decision: "AUTO-HANDLE" | "ESCALATE" | "UNKNOWN" | string;
  confidence?: number;
}) {
  const d = decision?.toUpperCase();

  if (d === "AUTO-HANDLE") {
    return (
      <GlassBadge variant="autohandle">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
        <span>AUTO-HANDLE</span>
        {confidence !== undefined && (
          <span className="font-mono text-[10px] text-emerald-300/80 border-l border-emerald-500/30 pl-1.5 ml-0.5">
            {Math.round(confidence * 100)}%
          </span>
        )}
      </GlassBadge>
    );
  }

  if (d === "ESCALATE") {
    return (
      <GlassBadge variant="escalate">
        <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
        <span>ESCALATE</span>
        {confidence !== undefined && (
          <span className="font-mono text-[10px] text-amber-300/80 border-l border-amber-500/30 pl-1.5 ml-0.5">
            {Math.round(confidence * 100)}%
          </span>
        )}
      </GlassBadge>
    );
  }

  return (
    <GlassBadge variant="unknown">
      <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
      <span>UNKNOWN</span>
      {confidence !== undefined && (
        <span className="font-mono text-[10px] text-rose-300/80 border-l border-rose-500/30 pl-1.5 ml-0.5">
          {Math.round(confidence * 100)}%
        </span>
      )}
    </GlassBadge>
  );
}
