"""SLA management service.

Calculates SLA deadlines based on ticket priority, detects breaches, and
dispatches notifications for overdue tickets.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from models.enums import Priority, TicketStatus
from repositories.ticket import TicketRepository

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Priority -> response-window mapping (hours)
# ---------------------------------------------------------------------------
_PRIORITY_HOURS: dict[str, int] = {
    Priority.urgent.value if hasattr(Priority, "urgent") else "urgent": 1,
    Priority.high.value if hasattr(Priority, "high") else "high": 4,
    Priority.medium.value if hasattr(Priority, "medium") else "medium": 8,
    Priority.low.value if hasattr(Priority, "low") else "low": 24,
}

# Statuses that are considered *resolved* and therefore exempt from SLA
# breach checks.
_RESOLVED_STATUSES: set[str] = {
    TicketStatus.resolved.value if hasattr(TicketStatus, "resolved") else "resolved",
    TicketStatus.closed.value if hasattr(TicketStatus, "closed") else "closed",
}


class SLAService:
    """Calculate SLA deadlines, detect breaches, and send notifications."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def calculate_sla(self, priority: str) -> datetime:
        """Return the SLA due-by timestamp for a given *priority*.

        Falls back to the ``medium`` window (8 h) when the priority string
        is not recognised.
        """
        hours = _PRIORITY_HOURS.get(priority.lower(), 8)
        due_at = datetime.now(timezone.utc) + timedelta(hours=hours)
        logger.debug(
            "sla.calculated",
            priority=priority,
            hours=hours,
            due_at=due_at.isoformat(),
        )
        return due_at

    async def check_breaches(
        self,
        db: AsyncSession,
        tenant_id: str,
    ) -> list[dict]:
        """Return a list of tickets that have breached their SLA.

        Each item contains ``ticket_id``, ``subject``, ``priority``,
        ``sla_due_at``, and ``breach_minutes``.
        """
        log = logger.bind(tenant_id=tenant_id)
        now = datetime.now(timezone.utc)

        try:
            tickets = await TicketRepository.list_by_tenant(db, tenant_id)
        except Exception:
            log.exception("sla.ticket_fetch_failed")
            return []

        breaches: list[dict] = []
        for ticket in tickets:
            status_val: str = (
                ticket.status.value
                if hasattr(ticket.status, "value")
                else str(ticket.status)
            ).lower()

            if status_val in _RESOLVED_STATUSES:
                continue

            sla_due_at: datetime | None = getattr(ticket, "sla_due_at", None)
            if sla_due_at is None:
                continue

            # Ensure timezone-aware comparison.
            if sla_due_at.tzinfo is None:
                sla_due_at = sla_due_at.replace(tzinfo=timezone.utc)

            if sla_due_at >= now:
                continue

            breach_delta = now - sla_due_at
            breach_minutes = int(breach_delta.total_seconds() / 60)

            breaches.append(
                {
                    "ticket_id": str(ticket.id),
                    "subject": getattr(ticket, "subject", ""),
                    "priority": (
                        ticket.priority.value
                        if hasattr(ticket.priority, "value")
                        else str(ticket.priority)
                    ),
                    "sla_due_at": sla_due_at.isoformat(),
                    "breach_minutes": breach_minutes,
                }
            )

        log.info("sla.breach_check_complete", breaches_found=len(breaches))
        return breaches

    async def send_breach_notifications(
        self,
        db: AsyncSession,
        tenant_id: str,
        breaches: list[dict],
    ) -> int:
        """Queue notifications for each SLA breach.

        Returns the number of notifications successfully queued.
        """
        log = logger.bind(tenant_id=tenant_id)

        if not breaches:
            return 0

        sent = 0
        for breach in breaches:
            try:
                await self._queue_notification(db, tenant_id, breach)
                sent += 1
            except Exception:
                log.exception(
                    "sla.notification_failed",
                    ticket_id=breach.get("ticket_id"),
                )

        log.info("sla.notifications_sent", count=sent, total=len(breaches))
        return sent

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _queue_notification(
        db: AsyncSession,
        tenant_id: str,
        breach: dict,
    ) -> None:
        """Persist / dispatch a single breach notification.

        This is a placeholder for the real notification transport (e.g.
        email, Slack webhook, in-app notification queue).  Extend with
        your preferred channel.
        """
        logger.info(
            "sla.notification_queued",
            tenant_id=tenant_id,
            ticket_id=breach.get("ticket_id"),
            breach_minutes=breach.get("breach_minutes"),
        )
        # TODO: integrate with the notification subsystem (email / Slack /
        # in-app) once it is available.


sla_service = SLAService()
