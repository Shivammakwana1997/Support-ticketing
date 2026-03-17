"""Automated ticket actions service.

Provides AI-powered categorisation, stale-ticket housekeeping, and
escalation detection for the customer-support copilot.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from integrations.openai_client import openai_client
from models.enums import Priority, TicketStatus
from repositories.ticket import TicketRepository

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_VALID_CATEGORIES: list[str] = [
    "billing",
    "technical",
    "account",
    "product",
    "shipping",
    "general",
]

_VALID_PRIORITIES: list[str] = [
    Priority.urgent.value if hasattr(Priority, "urgent") else "urgent",
    Priority.high.value if hasattr(Priority, "high") else "high",
    Priority.medium.value if hasattr(Priority, "medium") else "medium",
    Priority.low.value if hasattr(Priority, "low") else "low",
]


class AutomationService:
    """High-level automation actions for tickets."""

    # ------------------------------------------------------------------
    # Auto-categorise
    # ------------------------------------------------------------------

    async def auto_categorize(self, ticket: object) -> dict:
        """Use AI to classify *ticket* into a category, priority, and tags.

        Returns ``{"category": str, "priority": str, "tags": list[str]}``.
        Falls back to safe defaults when the LLM call fails.
        """
        subject: str = getattr(ticket, "subject", "") or ""
        description: str = getattr(ticket, "description", "") or ""

        prompt = (
            "You are a support-ticket classifier. Analyse the ticket below "
            "and return a JSON object with exactly three keys:\n"
            '  "category" — one of: billing, technical, account, product, '
            "shipping, general\n"
            '  "priority" — one of: urgent, high, medium, low\n'
            '  "tags"     — a list of up to 5 short keyword tags\n\n'
            f"Subject: {subject}\n"
            f"Description: {description}\n\n"
            "Respond with valid JSON only."
        )

        try:
            raw = await openai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=256,
                temperature=0.0,
            )
            result = self._parse_categorization(raw)
            logger.info(
                "auto_actions.categorized",
                ticket_id=getattr(ticket, "id", None),
                category=result["category"],
                priority=result["priority"],
            )
            return result
        except Exception:
            logger.exception(
                "auto_actions.categorize_failed",
                ticket_id=getattr(ticket, "id", None),
            )
            return {
                "category": "general",
                "priority": "medium",
                "tags": [],
            }

    # ------------------------------------------------------------------
    # Auto-close stale tickets
    # ------------------------------------------------------------------

    async def auto_close_stale(
        self,
        db: AsyncSession,
        tenant_id: str,
        days: int = 7,
    ) -> int:
        """Close tickets that have been *pending* with no updates for *days*.

        Returns the number of tickets closed.
        """
        log = logger.bind(tenant_id=tenant_id, stale_days=days)
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        try:
            tickets = await TicketRepository.list_by_tenant(db, tenant_id)
        except Exception:
            log.exception("auto_actions.stale_fetch_failed")
            return 0

        closed = 0
        for ticket in tickets:
            status_val: str = (
                ticket.status.value
                if hasattr(ticket.status, "value")
                else str(ticket.status)
            ).lower()

            if status_val != (
                TicketStatus.pending.value
                if hasattr(TicketStatus, "pending")
                else "pending"
            ):
                continue

            updated_at: datetime | None = getattr(ticket, "updated_at", None)
            if updated_at is None:
                continue

            if updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=timezone.utc)

            if updated_at >= cutoff:
                continue

            try:
                await TicketRepository.update_status(
                    db,
                    ticket_id=ticket.id,
                    status=TicketStatus.closed
                    if hasattr(TicketStatus, "closed")
                    else "closed",
                    system_message=(
                        "Automatically closed after "
                        f"{days} days of inactivity."
                    ),
                )
                closed += 1
            except Exception:
                log.exception(
                    "auto_actions.stale_close_failed",
                    ticket_id=ticket.id,
                )

        log.info("auto_actions.stale_closed", count=closed)
        return closed

    # ------------------------------------------------------------------
    # Escalation detection
    # ------------------------------------------------------------------

    async def should_escalate(
        self,
        ticket: object,
        messages: list,
    ) -> dict:
        """Decide whether *ticket* should be escalated to a senior agent.

        Returns ``{"should_escalate": bool, "reason": str, "urgency": str}``.
        """
        subject: str = getattr(ticket, "subject", "") or ""
        description: str = getattr(ticket, "description", "") or ""
        priority: str = (
            ticket.priority.value
            if hasattr(getattr(ticket, "priority", None), "value")
            else str(getattr(ticket, "priority", "medium"))
        )
        is_vip: bool = getattr(ticket, "is_vip", False) or False

        # Build a compact conversation summary for the LLM.
        conversation_lines: list[str] = []
        for msg in messages[-15:]:  # cap to last 15 messages
            role = getattr(msg, "role", "unknown")
            body = getattr(msg, "body", "") or getattr(msg, "content", "") or ""
            conversation_lines.append(f"[{role}]: {body[:300]}")
        conversation_text = "\n".join(conversation_lines)

        prompt = (
            "You are a support-escalation evaluator. Decide if this ticket "
            "should be escalated.\n\n"
            "Consider these factors:\n"
            "- Negative sentiment or frustration from the customer\n"
            "- Long wait times without resolution\n"
            "- VIP or high-priority customers\n"
            "- Repeated contacts about the same issue\n\n"
            f"Ticket subject: {subject}\n"
            f"Ticket description: {description}\n"
            f"Priority: {priority}\n"
            f"VIP customer: {is_vip}\n"
            f"Message count: {len(messages)}\n\n"
            f"Recent conversation:\n{conversation_text}\n\n"
            "Respond with valid JSON containing exactly:\n"
            '  "should_escalate": true/false\n'
            '  "reason": brief explanation\n'
            '  "urgency": one of "critical", "high", "medium", "low"\n'
        )

        try:
            raw = await openai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=256,
                temperature=0.0,
            )
            result = self._parse_escalation(raw)
            logger.info(
                "auto_actions.escalation_evaluated",
                ticket_id=getattr(ticket, "id", None),
                should_escalate=result["should_escalate"],
                urgency=result["urgency"],
            )
            return result
        except Exception:
            logger.exception(
                "auto_actions.escalation_check_failed",
                ticket_id=getattr(ticket, "id", None),
            )
            # Fail-safe: surface the ticket for human review.
            return {
                "should_escalate": True,
                "reason": "Automated analysis failed; escalating as a precaution.",
                "urgency": "medium",
            }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_categorization(raw: str) -> dict:
        """Parse and validate the LLM's categorisation response."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Try to extract JSON from surrounding text.
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start != -1 and end > start:
                data = json.loads(raw[start:end])
            else:
                raise

        category = str(data.get("category", "general")).lower()
        if category not in _VALID_CATEGORIES:
            category = "general"

        priority = str(data.get("priority", "medium")).lower()
        if priority not in _VALID_PRIORITIES:
            priority = "medium"

        tags_raw = data.get("tags", [])
        tags: list[str] = (
            [str(t) for t in tags_raw[:5]] if isinstance(tags_raw, list) else []
        )

        return {"category": category, "priority": priority, "tags": tags}

    @staticmethod
    def _parse_escalation(raw: str) -> dict:
        """Parse and validate the LLM's escalation response."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start != -1 and end > start:
                data = json.loads(raw[start:end])
            else:
                raise

        valid_urgencies = {"critical", "high", "medium", "low"}
        urgency = str(data.get("urgency", "medium")).lower()
        if urgency not in valid_urgencies:
            urgency = "medium"

        return {
            "should_escalate": bool(data.get("should_escalate", False)),
            "reason": str(data.get("reason", "")),
            "urgency": urgency,
        }


automation_service = AutomationService()
