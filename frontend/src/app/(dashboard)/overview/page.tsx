"use client";

import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/feedback";
import { MetricCard, MetricCardSkeleton } from "@/components/MetricCard";
import { EventsTrendChart } from "@/components/charts/EventsTrendChart";
import { TopEventsChart } from "@/components/charts/TopEventsChart";
import { api } from "@/lib/api";
import { useAsync } from "@/lib/useAsync";
import { useSession } from "@/store/session";

export default function OverviewPage() {
  const token = useSession((s) => s.token);
  const orgId = useSession((s) => s.me?.organization_id);

  const { data, loading, error, reload } = useAsync(
    () => api.analyticsOverview(token!, orgId!),
    [token, orgId],
  );

  return (
    <div className="space-y-6">
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {loading || !data
          ? Array.from({ length: 4 }).map((_, i) => <MetricCardSkeleton key={i} />)
          : [
              { label: "Total Events", value: data.summary.total_events },
              { label: "Events Today", value: data.summary.events_today },
              { label: "Unique Users", value: data.summary.unique_users },
              { label: "Active API Keys", value: data.summary.active_api_keys },
            ].map((m) => <MetricCard key={m.label} label={m.label} value={m.value} />)}
      </section>

      {error ? (
        <Card>
          <ErrorState message={error} onRetry={reload} />
        </Card>
      ) : (
        <section className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          <Card>
            <CardHeader
              title="Events Over Time"
              description="Daily event volume"
              action={
                data ? (
                  <Badge tone={data.cached ? "info" : "neutral"}>
                    {data.cached ? "cached" : "live"}
                  </Badge>
                ) : null
              }
            />
            <CardBody>
              {loading || !data ? (
                <Skeleton className="h-64 w-full" />
              ) : (
                <EventsTrendChart data={data.events_per_day} />
              )}
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="Top Events" description="Most frequent event names" />
            <CardBody>
              {loading || !data ? (
                <Skeleton className="h-64 w-full" />
              ) : data.top_events.length === 0 ? (
                <EmptyState
                  title="No events yet"
                  description="Send events with your API key to see analytics."
                />
              ) : (
                <TopEventsChart data={data.top_events} />
              )}
            </CardBody>
          </Card>
        </section>
      )}
    </div>
  );
}
