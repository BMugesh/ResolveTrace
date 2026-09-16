import * as React from "react";
import { cn } from "@/lib/utils";

export interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "featured" | "subtle" | "interactive";
  glow?: "none" | "emerald" | "amber" | "rose" | "cyan";
}

export const GlassCard = React.forwardRef<HTMLDivElement, GlassCardProps>(
  ({ className, variant = "default", glow = "none", children, ...props }, ref) => {
    const variantClasses = {
      default: "glass-panel rounded-2xl",
      featured:
        "glass-panel rounded-2xl border-white/[0.14] shadow-[0_24px_50px_-12px_rgba(0,0,0,0.7),inset_0_1px_1px_0_rgba(255,255,255,0.12)]",
      subtle: "glass-panel-subtle rounded-xl",
      interactive:
        "glass-panel rounded-xl hover:border-white/[0.18] hover:bg-white/[0.05] hover:shadow-[0_20px_40px_-15px_rgba(0,0,0,0.6),inset_0_1px_1px_0_rgba(255,255,255,0.14)] transition-all duration-200 cursor-pointer",
    };

    const glowClasses = {
      none: "",
      emerald: "shadow-[0_0_40px_-10px_rgba(29,185,84,0.25)] border-[#1DB954]/30",
      amber: "shadow-[0_0_40px_-10px_rgba(245,158,11,0.25)] border-amber-500/30",
      rose: "shadow-[0_0_40px_-10px_rgba(244,63,94,0.25)] border-rose-500/30",
      cyan: "shadow-[0_0_40px_-10px_rgba(6,182,212,0.25)] border-cyan-500/30",
    };

    return (
      <div
        ref={ref}
        className={cn(
          "relative overflow-hidden transition-all",
          variantClasses[variant],
          glowClasses[glow],
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);
GlassCard.displayName = "GlassCard";

export function GlassCardHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("p-6 pb-3 space-y-1.5", className)} {...props} />;
}

export function GlassCardTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn("text-base font-semibold text-white tracking-tight flex items-center gap-2", className)}
      {...props}
    />
  );
}

export function GlassCardDescription({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn("text-xs text-slate-400 leading-relaxed", className)} {...props} />;
}

export function GlassCardContent({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("p-6 pt-3", className)} {...props} />;
}

export function GlassCardFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("p-6 pt-0 flex items-center justify-between", className)} {...props} />;
}
