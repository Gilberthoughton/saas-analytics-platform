"""Analytics schemas."""

from pydantic import BaseModel


class MetricsSummary(BaseModel):
    total_events: int
    events_today: int
    unique_users: int
    active_api_keys: int


class TimeseriesPoint(BaseModel):
    date: str  # YYYY-MM-DD
    count: int


class TopEvent(BaseModel):
    name: str
    count: int


class AnalyticsOverview(BaseModel):
    summary: MetricsSummary
    events_per_day: list[TimeseriesPoint]
    top_events: list[TopEvent]
    cached: bool
