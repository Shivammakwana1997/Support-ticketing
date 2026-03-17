from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class MetricPoint(BaseModel):
    timestamp: datetime
    value: float


class DashboardResponse(BaseModel):
    total_tickets: int = 0
    open_tickets: int = 0
    resolved_tickets: int = 0
    avg_resolution_time_hours: float | None = None
    total_conversations: int = 0
    active_conversations: int = 0
    total_customers: int = 0
    csat_score: float | None = None
    ticket_trend: list[MetricPoint] = []
    conversation_trend: list[MetricPoint] = []


class AgentMetricsResponse(BaseModel):
    agent_id: str
    display_name: str
    tickets_resolved: int = 0
    avg_response_time_seconds: float | None = None
    avg_resolution_time_hours: float | None = None
    csat_score: float | None = None
    active_conversations: int = 0


class CallMetricsResponse(BaseModel):
    total_calls: int = 0
    avg_duration_seconds: float | None = None
    avg_sentiment: float | None = None
    calls_by_day: list[MetricPoint] = []
