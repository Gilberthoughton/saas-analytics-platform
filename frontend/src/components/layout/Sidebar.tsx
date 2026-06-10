"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/overview", label: "Overview" },
  { href: "/events", label: "Event Explorer" },
  { href: "/api-keys", label: "API Keys" },
  { href: "/audit", label: "Audit Log" },
] as const;

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden w-56 shrink-0 flex-col border-r border-surface-border bg-surface-raised lg:flex">
      <div className="flex h-16 items-center gap-2 border-b border-surface-border px-5">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-brand text-sm font-bold text-white">
          A
        </div>
        <span className="text-sm font-semibold text-slate-100">Analytics</span>
      </div>
      <nav className="flex-1 space-y-1 p-3" aria-label="Primary">
        {NAV.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "block rounded-md px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-surface-overlay font-medium text-slate-100"
                  : "text-slate-400 hover:bg-surface-overlay/60 hover:text-slate-200",
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-surface-border p-4 text-xs text-slate-500">v1.0.0</div>
    </aside>
  );
}
