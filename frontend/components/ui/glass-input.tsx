import * as React from "react";
import { cn } from "@/lib/utils";

export interface GlassInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
}

export const GlassInput = React.forwardRef<HTMLInputElement, GlassInputProps>(
  ({ className, error, ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={cn(
          "glass-input w-full rounded-xl px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500",
          "focus:outline-none focus:border-[#1DB954]/60 focus:ring-2 focus:ring-[#1DB954]/20 transition-all duration-200",
          error && "border-rose-500/50 focus:border-rose-500 focus:ring-rose-500/20",
          className
        )}
        {...props}
      />
    );
  }
);
GlassInput.displayName = "GlassInput";
