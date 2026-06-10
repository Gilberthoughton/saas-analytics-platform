import type { InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export function Input({ label, id, className, ...props }: InputProps) {
  return (
    <div className="flex flex-col gap-1">
      {label ? (
        <label
          htmlFor={id}
          className="text-xs font-medium uppercase tracking-wide text-slate-500"
        >
          {label}
        </label>
      ) : null}
      <input
        id={id}
        className={cn(
          "rounded-md border border-surface-border bg-surface-overlay px-3 py-1.5 text-sm text-slate-200 placeholder:text-slate-500 transition-colors hover:border-slate-600 focus:border-brand focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/40",
          className,
        )}
        {...props}
      />
    </div>
  );
}
