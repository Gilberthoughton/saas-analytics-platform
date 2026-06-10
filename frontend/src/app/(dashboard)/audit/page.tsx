"use client";

import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader } from "@/components/ui/Card";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/feedback";
import { api } from "@/lib/api";
import { useAsync } from "@/lib/useAsync";
import { formatDateTime, titleCase } from "@/lib/utils";
import { useSession } from "@/store/session";

export default function AuditPage() {
  const token = useSession((s) => s.token);
  const orgId = useSession((s) => s.me?.organization_id);

  const { data, loading, error, reload } = useAsync(
    () => api.auditLogs(token!, orgId!),
    [token, orgId],
  );

  return (
    <Card>
      <CardHeader title="Audit Log" description="Security-relevant actions in your organization" />
      {error ? (
        <ErrorState message={error} onRetry={reload}>
          <p className="text-xs text-slate-500">Audit access requires an admin or owner role.</p>
        </ErrorState>
      ) : loading || !data ? (
        <div className="space-y-2 p-5">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-9 w-full" />
          ))}
        </div>
      ) : data.length === 0 ? (
        <EmptyState title="No activity yet" />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-border text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-5 py-2 font-medium">Action</th>
                <th className="px-5 py-2 font-medium">Details</th>
                <th className="px-5 py-2 text-right font-medium">When</th>
              </tr>
            </thead>
            <tbody>
              {data.map((log) => (
                <tr key={log.id} className="border-b border-surface-border/60 last:border-0">
                  <td className="px-5 py-3">
                    <Badge tone="brand">{titleCase(log.action)}</Badge>
                  </td>
                  <td className="px-5 py-3 font-mono text-xs text-slate-500">
                    {Object.keys(log.meta).length ? JSON.stringify(log.meta) : "—"}
                  </td>
                  <td className="px-5 py-3 text-right text-slate-400">
                    {formatDateTime(log.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
