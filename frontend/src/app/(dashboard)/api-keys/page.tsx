"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/feedback";
import { api, ApiError } from "@/lib/api";
import { useAsync } from "@/lib/useAsync";
import { formatDateTime } from "@/lib/utils";
import { useSession } from "@/store/session";

export default function ApiKeysPage() {
  const token = useSession((s) => s.token);
  const orgId = useSession((s) => s.me?.organization_id);
  const role = useSession((s) => s.me?.role);
  const canManage = role === "owner" || role === "admin";

  const { data, loading, error, reload } = useAsync(
    () => api.listApiKeys(token!, orgId!),
    [token, orgId],
  );

  const [name, setName] = useState("");
  const [creating, setCreating] = useState(false);
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const onCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setFormError(null);
    try {
      const created = await api.createApiKey(token!, orgId!, name);
      setCreatedKey(created.key);
      setName("");
      reload();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Failed to create key");
    } finally {
      setCreating(false);
    }
  };

  const onRevoke = async (id: string) => {
    await api.revokeApiKey(token!, orgId!, id);
    reload();
  };

  return (
    <div className="space-y-6">
      {canManage ? (
        <Card>
          <CardHeader title="Create API key" description="Use keys to ingest events" />
          <CardBody className="space-y-4">
            <form onSubmit={onCreate} className="flex flex-wrap items-end gap-3">
              <Input
                id="key-name"
                label="Key name"
                placeholder="e.g. production"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
              <Button type="submit" disabled={creating || !name}>
                Create key
              </Button>
            </form>
            {formError ? <p className="text-xs text-status-danger">{formError}</p> : null}
            {createdKey ? (
              <div className="rounded-md border border-status-warning/40 bg-status-warning/10 p-3">
                <p className="text-xs text-status-warning">
                  Copy this key now — it won&apos;t be shown again.
                </p>
                <code className="mt-1 block break-all font-mono text-sm text-slate-100">
                  {createdKey}
                </code>
              </div>
            ) : null}
          </CardBody>
        </Card>
      ) : null}

      <Card>
        <CardHeader title="API keys" description="Active and revoked keys" />
        {error ? (
          <ErrorState message={error} onRetry={reload} />
        ) : loading || !data ? (
          <CardBody className="space-y-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </CardBody>
        ) : data.length === 0 ? (
          <EmptyState title="No API keys" description="Create a key to start ingesting events." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-border text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-5 py-2 font-medium">Name</th>
                  <th className="px-5 py-2 font-medium">Prefix</th>
                  <th className="px-5 py-2 font-medium">Status</th>
                  <th className="px-5 py-2 font-medium">Created</th>
                  <th className="px-5 py-2" />
                </tr>
              </thead>
              <tbody>
                {data.map((key) => (
                  <tr
                    key={key.id}
                    className="border-b border-surface-border/60 last:border-0"
                  >
                    <td className="px-5 py-3 font-medium text-slate-200">{key.name}</td>
                    <td className="px-5 py-3 font-mono text-xs text-slate-400">
                      {key.prefix}…
                    </td>
                    <td className="px-5 py-3">
                      <Badge tone={key.is_active ? "success" : "neutral"}>
                        {key.is_active ? "active" : "revoked"}
                      </Badge>
                    </td>
                    <td className="px-5 py-3 text-slate-400">{formatDateTime(key.created_at)}</td>
                    <td className="px-5 py-3 text-right">
                      {canManage && key.is_active ? (
                        <Button variant="danger" onClick={() => onRevoke(key.id)}>
                          Revoke
                        </Button>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
