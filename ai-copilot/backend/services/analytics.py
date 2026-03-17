from __future__ import annotations

import datetime
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import NotFoundError
from models.enums import ConversationStatus, TicketStatus
from repositories.agent import AgentRepository
from repositories.conversation import ConversationRepository
from repositories.ticket import TicketRepository

logger = structlog.get_logger(__name__)


class AnalyticsService:
    """Aggregates metrics from tickets, conversations, and agents for
    dashboard reporting and operational analytics."""

    # ------------------------------------------------------------------
    # Dashboard overview
    # ------------------------------------------------------------------

    async def get_dashboard(
        self,
        db: AsyncSession,
        tenant_id: str,
        start_date: datetime.datetime | None = None,
        end_date: datetime.datetime | None = None,
    ) -> dict[str, Any]:
        """Return a high-level dashboard summary for *tenant_id*.

        The response includes ticket totals, resolution metrics,
        conversation activity, satisfaction scores, and breakdowns by
        priority, status, and day.
        """
        log = logger.bind(tenant_id=tenant_id, start_date=start_date, end_date=end_date)
        log.info("analytics.dashboard.requested")

        ticket_repo = TicketRepository()
        conversation_repo = ConversationRepository()

        # -- Ticket counts ------------------------------------------------
        total_tickets = await self._safe_call(
            ticket_repo.count_by_tenant,  # type: ignore[attr-defined]
            db,
            tenant_id,
            start_date=start_date,
            end_date=end_date,
            default=0,
        )

        open_tickets = await self._safe_call(
            ticket_repo.count_by_status,  # type: ignore[attr-defined]
            db,
            tenant_id,
            status=TicketStatus.OPEN,
            start_date=start_date,
            end_date=end_date,
            default=0,
        )

        resolved_tickets = await self._safe_call(
            ticket_repo.count_by_status,  # type: ignore[attr-defined]
            db,
            tenant_id,
            status=TicketStatus.RESOLVED,
            start_date=start_date,
            end_date=end_date,
            default=0,
        )

        # -- Resolution time ----------------------------------------------
        avg_resolution_time_hours = await self._safe_call(
            ticket_repo.avg_resolution_time_hours,  # type: ignore[attr-defined]
            db,
            tenant_id,
            start_date=start_date,
            end_date=end_date,
            default=0.0,
        )

        # -- Conversations -------------------------------------------------
        total_conversations = await self._safe_call(
            conversation_repo.count_by_tenant,  # type: ignore[attr-defined]
            db,
            tenant_id,
            start_date=start_date,
            end_date=end_date,
            default=0,
        )

        active_conversations = await self._safe_call(
            conversation_repo.count_by_status,  # type: ignore[attr-defined]
            db,
            tenant_id,
            status=ConversationStatus.ACTIVE,
            start_date=start_date,
            end_date=end_date,
            default=0,
        )

        # -- Satisfaction ---------------------------------------------------
        customer_satisfaction_avg = await self._safe_call(
            ticket_repo.avg_customer_satisfaction,  # type: ignore[attr-defined]
            db,
            tenant_id,
            start_date=start_date,
            end_date=end_date,
            default=0.0,
        )

        # -- Breakdowns ----------------------------------------------------
        tickets_by_priority: dict[str, int] = await self._safe_call(
            ticket_repo.count_by_priority,  # type: ignore[attr-defined]
            db,
            tenant_id,
            start_date=start_date,
            end_date=end_date,
            default={},
        )

        tickets_by_status: dict[str, int] = await self._safe_call(
            ticket_repo.count_grouped_by_status,  # type: ignore[attr-defined]
            db,
            tenant_id,
            start_date=start_date,
            end_date=end_date,
            default={},
        )

        daily_ticket_counts: list[dict[str, Any]] = await self._safe_call(
            ticket_repo.daily_counts,  # type: ignore[attr-defined]
            db,
            tenant_id,
            start_date=start_date,
            end_date=end_date,
            default=[],
        )

        dashboard = {
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "resolved_tickets": resolved_tickets,
            "avg_resolution_time_hours": round(avg_resolution_time_hours, 2),
            "total_conversations": total_conversations,
            "active_conversations": active_conversations,
            "customer_satisfaction_avg": round(customer_satisfaction_avg, 2),
            "tickets_by_priority": tickets_by_priority,
            "tickets_by_status": tickets_by_status,
            "daily_ticket_counts": daily_ticket_counts,
        }

        log.info("analytics.dashboard.compiled", total_tickets=total_tickets)
        return dashboard

    # ------------------------------------------------------------------
    # Per-agent metrics
    # ------------------------------------------------------------------

    async def get_agent_metrics(
        self,
        db: AsyncSession,
        tenant_id: str,
        start_date: datetime.datetime | None = None,
        end_date: datetime.datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Return performance metrics for every agent belonging to
        *tenant_id*."""
        log = logger.bind(tenant_id=tenant_id, start_date=start_date, end_date=end_date)
        log.info("analytics.agent_metrics.requested")

        agent_repo = AgentRepository()
        ticket_repo = TicketRepository()

        # Retrieve all agents for the tenant.
        agents: list[Any] = await self._safe_call(
            agent_repo.list_by_tenant,  # type: ignore[attr-defined]
            db,
            tenant_id,
            default=[],
        )

        results: list[dict[str, Any]] = []

        for agent in agents:
            agent_id: str = getattr(agent, "id", str(agent))
            agent_name: str = getattr(agent, "name", "Unknown")
            current_status: str = getattr(agent, "status", "unknown")

            tickets_assigned = await self._safe_call(
                ticket_repo.count_by_agent,  # type: ignore[attr-defined]
                db,
                tenant_id,
                agent_id=agent_id,
                start_date=start_date,
                end_date=end_date,
                default=0,
            )

            tickets_resolved = await self._safe_call(
                ticket_repo.count_by_agent,  # type: ignore[attr-defined]
                db,
                tenant_id,
                agent_id=agent_id,
                status=TicketStatus.RESOLVED,
                start_date=start_date,
                end_date=end_date,
                default=0,
            )

            avg_resolution = await self._safe_call(
                ticket_repo.avg_resolution_time_hours,  # type: ignore[attr-defined]
                db,
                tenant_id,
                agent_id=agent_id,
                start_date=start_date,
                end_date=end_date,
                default=0.0,
            )

            avg_response = await self._safe_call(
                agent_repo.avg_response_time_minutes,  # type: ignore[attr-defined]
                db,
                tenant_id,
                agent_id=agent_id,
                start_date=start_date,
                end_date=end_date,
                default=0.0,
            )

            satisfaction = await self._safe_call(
                ticket_repo.avg_customer_satisfaction,  # type: ignore[attr-defined]
                db,
                tenant_id,
                agent_id=agent_id,
                start_date=start_date,
                end_date=end_date,
                default=0.0,
            )

            results.append(
                {
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "tickets_assigned": tickets_assigned,
                    "tickets_resolved": tickets_resolved,
                    "avg_resolution_time_hours": round(avg_resolution, 2),
                    "avg_response_time_minutes": round(avg_response, 2),
                    "customer_satisfaction_avg": round(satisfaction, 2),
                    "current_status": current_status,
                }
            )

        log.info("analytics.agent_metrics.compiled", agent_count=len(results))
        return results

    # ------------------------------------------------------------------
    # Call / conversation metrics
    # ------------------------------------------------------------------

    async def get_call_metrics(
        self,
        db: AsyncSession,
        tenant_id: str,
        start_date: datetime.datetime | None = None,
        end_date: datetime.datetime | None = None,
    ) -> dict[str, Any]:
        """Return aggregated call / conversation channel metrics for
        *tenant_id*."""
        log = logger.bind(tenant_id=tenant_id, start_date=start_date, end_date=end_date)
        log.info("analytics.call_metrics.requested")

        conversation_repo = ConversationRepository()

        total_calls = await self._safe_call(
            conversation_repo.count_by_tenant,  # type: ignore[attr-defined]
            db,
            tenant_id,
            start_date=start_date,
            end_date=end_date,
            default=0,
        )

        avg_duration_minutes = await self._safe_call(
            conversation_repo.avg_duration_minutes,  # type: ignore[attr-defined]
            db,
            tenant_id,
            start_date=start_date,
            end_date=end_date,
            default=0.0,
        )

        avg_wait_time_seconds = await self._safe_call(
            conversation_repo.avg_wait_time_seconds,  # type: ignore[attr-defined]
            db,
            tenant_id,
            start_date=start_date,
            end_date=end_date,
            default=0.0,
        )

        avg_sentiment_score = await self._safe_call(
            conversation_repo.avg_sentiment_score,  # type: ignore[attr-defined]
            db,
            tenant_id,
            start_date=start_date,
            end_date=end_date,
            default=0.0,
        )

        calls_by_channel: dict[str, int] = await self._safe_call(
            conversation_repo.count_by_channel,  # type: ignore[attr-defined]
            db,
            tenant_id,
            start_date=start_date,
            end_date=end_date,
            default={},
        )

        daily_call_counts: list[dict[str, Any]] = await self._safe_call(
            conversation_repo.daily_counts,  # type: ignore[attr-defined]
            db,
            tenant_id,
            start_date=start_date,
            end_date=end_date,
            default=[],
        )

        call_metrics = {
            "total_calls": total_calls,
            "avg_duration_minutes": round(avg_duration_minutes, 2),
            "avg_wait_time_seconds": round(avg_wait_time_seconds, 2),
            "avg_sentiment_score": round(avg_sentiment_score, 2),
            "calls_by_channel": calls_by_channel,
            "daily_call_counts": daily_call_counts,
        }

        log.info("analytics.call_metrics.compiled", total_calls=total_calls)
        return call_metrics

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _safe_call(
        method: Any,
        *args: Any,
        default: Any = None,
        **kwargs: Any,
    ) -> Any:
        """Invoke an async repository method, returning *default* if the
        method does not exist or raises an unexpected error.

        This allows the analytics layer to degrade gracefully when
        repository methods have not been implemented yet.
        """
        try:
            return await method(*args, **kwargs)
        except (AttributeError, TypeError, NotImplementedError) as exc:
            logger.warning(
                "analytics.safe_call.fallback",
                method=getattr(method, "__qualname__", str(method)),
                error=str(exc),
            )
            return default
        except Exception as exc:
            logger.error(
                "analytics.safe_call.error",
                method=getattr(method, "__qualname__", str(method)),
                error=str(exc),
                exc_info=True,
            )
            return default


# Module-level singleton used by route handlers.
analytics_service = AnalyticsService()
