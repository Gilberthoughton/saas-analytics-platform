import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export type Tone = "success" | "warning" | "danger" | "info" | "neutral" | "brand";

const TONES: Record<Tone, string> = {
  success: "bg-status-success/15 text-status-success ring-status-success/30",
  warning: "bg-status-warning/15 text-status-warning ring-status-warning/30",
  danger: "bg-status-danger/15 text-status-danger ring-status-danger/30",
  info: "bg-status-info/15 text-status-info ring-status-info/30",
  neutral: "bg-status-neutral/15 text-status-neutral ring-status-neutral/30",
  brand: "bg-brand/15 text-brand ring-brand/30",
};

export function Badge({
  tone = "neutral",
  children,
  className,
}: {
  tone?: Tone;
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset",
        TONES[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}
