"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/feedback";
import { api } from "@/lib/api";
import { useAsync } from "@/lib/useAsync";
import { formatDateTime } from "@/lib/utils";
import { useSession } from "@/store/session";

const PAGE_SIZE = 25;

export default function EventsPage() {
  const token = useSession((s) => s.token);
  const orgId = useSession((s) => s.me?.organization_id);

  const [name, setName] = useState("");
  const [distinctId, setDistinctId] = useState("");
  const [applied, setApplied] = useState({ name: "", distinctId: "" });
  const [offset, setOffset] = useState(0);

  const { data, loading, error, reload } = useAsync(
    () =>
      api.events(token!, orgId!, {
        name: applied.name || undefined,
        distinct_id: applied.distinctId || undefined,
        limit: PAGE_SIZE,
        offset,
      }),
    [token, orgId, applied, offset],
  );

  const applyFilters = (e: React.FormEvent) => {
    e.preventDefault();
    setOffset(0);
    setApplied({ name, distinctId });
  };

  const total = data?.total ?? 0;
  const hasNext = offset + PAGE_SIZE < total;

  return (
    <Card>
      <CardHeader
        title="Event Explorer"
        description="Search and page through ingested events"
        action={<Badge tone="neutral">{total} total</Badge>}
      />
      <CardBody className="space-y-4">
        <form onSubmit={applyFilters} className="flex flex-wrap items-end gap-3">
          <Input
            id="filter-name"
            label="Event name"
            placeholder="e.g. signup"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <Input
            id="filter-distinct"
            label="Distinct ID"
            placeholder="e.g. user-1"
            value={distinctId}
            onChange={(e) => setDistinctId(e.target.value)}
          />
          <Button type="submit">Search</Button>
        </form>

        {error ? (
          <ErrorState message={error} onRetry={reload} />
        ) : loading || !data ? (
          <div className="space-y-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-9 w-full" />
            ))}
          </div>
        ) : data.items.length === 0 ? (
          <EmptyState title="No events found" description="Adjust your filters or ingest events." />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-surface-border text-left text-xs uppercase tracking-wide text-slate-500">
                    <th className="px-3 py-2 font-medium">Event</th>
                    <th className="px-3 py-2 font-medium">Distinct ID</th>
                    <th className="px-3 py-2 font-medium">Properties</th>
                    <th className="px-3 py-2 text-right font-medium">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((evt) => (
                    <tr
                      key={evt.id}
                      className="border-b border-surface-border/60 last:border-0 hover:bg-surface-overlay/50"
                    >
                      <td className="px-3 py-2.5">
                        <span className="font-medium text-slate-200">{evt.name}</span>
                      </td>
                      <td className="px-3 py-2.5 font-mono text-xs text-slate-400">
                        {evt.distinct_id}
                      </td>
                      <td className="px-3 py-2.5 font-mono text-xs text-slate-500">
                        {Object.keys(evt.properties).length
                          ? JSON.stringify(evt.properties)
                          : "—"}
                      </td>
                      <td className="px-3 py-2.5 text-right text-slate-400">
                        {formatDateTime(evt.timestamp)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex items-center justify-between text-xs text-slate-500">
              <span>
                Showing {offset + 1}–{Math.min(offset + PAGE_SIZE, total)} of {total}
              </span>
              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  disabled={offset === 0}
                  onClick={() => setOffset((o) => Math.max(0, o - PAGE_SIZE))}
                >
                  Previous
                </Button>
                <Button
                  variant="secondary"
                  disabled={!hasNext}
                  onClick={() => setOffset((o) => o + PAGE_SIZE)}
                >
                  Next
                </Button>
              </div>
            </div>
          </>
        )}
      </CardBody>
    </Card>
  );
}
