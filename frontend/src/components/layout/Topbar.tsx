"use client";

import { useRouter } from "next/navigation";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useSession } from "@/store/session";

export function Topbar() {
  const me = useSession((s) => s.me);
  const logout = useSession((s) => s.logout);
  const router = useRouter();

  const onLogout = () => {
    logout();
    router.replace("/login");
  };

  return (
    <header className="flex h-16 items-center justify-between border-b border-surface-border bg-surface-raised px-5">
      <div>
        <h1 className="text-base font-semibold text-slate-100">
          {me?.organization_name ?? "Dashboard"}
        </h1>
        <p className="text-xs text-slate-500">{me?.user.email}</p>
      </div>
      <div className="flex items-center gap-3">
        {me ? <Badge tone="brand">{me.role}</Badge> : null}
        <Button variant="secondary" onClick={onLogout}>
          Sign out
        </Button>
      </div>
    </header>
  );
}
