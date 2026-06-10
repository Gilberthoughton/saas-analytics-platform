/** Shared types mirroring the backend API contracts. */

export type Role = "owner" | "admin" | "member";

export interface User {
  id: string;
  email: string;
  full_name: string;
  created_at: string;
}

export interface Me {
  user: User;
  organization_id: string;
  organization_name: string;
  role: Role;
}

export interface MetricsSummary {
  total_events: number;
  events_today: number;
  unique_users: number;
  active_api_keys: number;
}

export interface TimeseriesPoint {
  date: string;
  count: number;
}

export interface TopEvent {
  name: string;
  count: number;
}

export interface AnalyticsOverview {
  summary: MetricsSummary;
  events_per_day: TimeseriesPoint[];
  top_events: TopEvent[];
  cached: boolean;
}

export interface EventRecord {
  id: string;
  name: string;
  distinct_id: string;
  properties: Record<string, unknown>;
  timestamp: string;
}

export interface EventPage {
  items: EventRecord[];
  total: number;
  limit: number;
  offset: number;
}

export interface ApiKey {
  id: string;
  name: string;
  prefix: string;
  is_active: boolean;
  last_used_at: string | null;
  created_at: string;
}

export interface ApiKeyCreated extends ApiKey {
  key: string;
}

export interface AuditLog {
  id: string;
  actor_user_id: string | null;
  action: string;
  meta: Record<string, unknown>;
  created_at: string;
}
