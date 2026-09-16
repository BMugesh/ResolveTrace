import * as React from "react";
import { cn } from "@/lib/utils";

export interface GlassButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "destructive" | "outline";
  size?: "sm" | "md" | "lg";
}

export const GlassButton = React.forwardRef<HTMLButtonElement, GlassButtonProps>(
  ({ className, variant = "secondary", size = "md", children, disabled, ...props }, ref) => {
    const base =
      "inline-flex items-center justify-center font-medium rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-950 disabled:opacity-50 disabled:pointer-events-none select-none active:scale-[0.98]";

    const sizes = {
      sm: "text-xs px-3 py-1.5 h-8 gap-1.5",
      md: "text-sm px-4 py-2 h-10 gap-2",
      lg: "text-sm sm:text-base px-5 py-2.5 h-12 gap-2.5 font-semibold",
    };

    const variants = {
      primary:
        "glass-button-primary text-black font-semibold hover:brightness-110 focus:ring-[#1DB954]",
      secondary:
        "glass-panel text-slate-100 hover:bg-white/[0.08] hover:border-white/[0.18] focus:ring-slate-400 shadow-sm",
      ghost:
        "text-slate-300 hover:text-white hover:bg-white/[0.06] focus:ring-slate-500",
      destructive:
        "bg-rose-500/15 text-rose-300 border border-rose-500/30 hover:bg-rose-500/25 focus:ring-rose-500 shadow-[0_0_20px_-5px_rgba(244,63,94,0.3)]",
      outline:
        "border border-white/[0.12] bg-transparent text-slate-200 hover:bg-white/[0.05] hover:border-white/[0.2] focus:ring-slate-400",
    };

    return (
      <button
        ref={ref}
        disabled={disabled}
        className={cn(base, sizes[size], variants[variant], className)}
        {...props}
      >
        {children}
      </button>
    );
  }
);
GlassButton.displayName = "GlassButton";
