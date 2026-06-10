/**
 * Typed API client.
 *
 * A thin wrapper over `fetch` that injects the bearer token, sets the active
 * organization header, and surfaces a consistent {@link ApiError}. All network
 * access goes through this module.
 */

import type {
  AnalyticsOverview,
  ApiKey,
  ApiKeyCreated,
  AuditLog,
  EventPage,
  Me,
} from "@/types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  token?: string | null;
  orgId?: string | null;
  /** Send as application/x-www-form-urlencoded (used by the login endpoint). */
  form?: Record<string, string>;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, token, orgId, form } = options;
  const headers: Record<string, string> = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (orgId) headers["X-Org-Id"] = orgId;

  let payload: BodyInit | undefined;
  if (form) {
    headers["Content-Type"] = "application/x-www-form-urlencoded";
    payload = new URLSearchParams(form).toString();
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  let resp: Response;
  try {
    resp = await fetch(`${BASE_URL}${path}`, { method, headers, body: payload });
  } catch {
    throw new ApiError("Unable to reach the API. Is the backend running?", 0);
  }

  if (!resp.ok) {
    let detail = `Request failed (${resp.status})`;
    try {
      const data = await resp.json();
      if (typeof data.detail === "string") detail = data.detail;
    } catch {
      /* keep default */
    }
    throw new ApiError(detail, resp.status);
  }

  if (resp.status === 204) return undefined as T;
  return (await resp.json()) as T;
}

export const api = {
  async login(email: string, password: string): Promise<string> {
    const data = await request<{ access_token: string }>("/auth/login", {
      method: "POST",
      form: { username: email, password },
    });
    return data.access_token;
  },

  register(input: {
    email: string;
    password: string;
    full_name: string;
    organization_name: string;
  }): Promise<unknown> {
    return request("/auth/register", { method: "POST", body: input });
  },

  me(token: string): Promise<Me> {
    return request<Me>("/auth/me", { token });
  },

  analyticsOverview(token: string, orgId: string, days = 14): Promise<AnalyticsOverview> {
    return request<AnalyticsOverview>(`/analytics/overview?days=${days}`, {
      token,
      orgId,
    });
  },

  events(
    token: string,
    orgId: string,
    params: { name?: string; distinct_id?: string; limit?: number; offset?: number },
  ): Promise<EventPage> {
    const q = new URLSearchParams();
    if (params.name) q.set("name", params.name);
    if (params.distinct_id) q.set("distinct_id", params.distinct_id);
    q.set("limit", String(params.limit ?? 50));
    q.set("offset", String(params.offset ?? 0));
    return request<EventPage>(`/events?${q.toString()}`, { token, orgId });
  },

  listApiKeys(token: string, orgId: string): Promise<ApiKey[]> {
    return request<ApiKey[]>("/api-keys", { token, orgId });
  },

  createApiKey(token: string, orgId: string, name: string): Promise<ApiKeyCreated> {
    return request<ApiKeyCreated>("/api-keys", {
      method: "POST",
      body: { name },
      token,
      orgId,
    });
  },

  revokeApiKey(token: string, orgId: string, id: string): Promise<ApiKey> {
    return request<ApiKey>(`/api-keys/${id}`, { method: "DELETE", token, orgId });
  },

  auditLogs(token: string, orgId: string): Promise<AuditLog[]> {
    return request<AuditLog[]>("/audit-logs", { token, orgId });
  },
};
