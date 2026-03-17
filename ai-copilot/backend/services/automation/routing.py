"""Intelligent ticket routing service.

Scores available agents based on skill match, current workload, and
availability, then assigns the best-fit agent to the incoming ticket.
"""

from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from integrations.openai_client import openai_client
from models.enums import AgentStatus
from repositories.agent import AgentRepository
from repositories.ticket import TicketRepository

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Scoring weights – tweak to change routing behaviour
# ---------------------------------------------------------------------------
_SKILL_MATCH_WEIGHT: float = 0.50
_WORKLOAD_WEIGHT: float = 0.35
_AVAILABILITY_WEIGHT: float = 0.15

# Maximum open tickets an agent can hold before the workload score drops to 0
_MAX_WORKLOAD: int = 20


class RoutingService:
    """Route tickets to the most suitable available agent."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def route_ticket(
        self,
        db: AsyncSession,
        tenant_id: str,
        ticket: object,
    ) -> dict | None:
        """Score available agents and assign the best one to *ticket*.

        Returns a dict with ``agent_id``, ``agent_name``, ``reason`` and
        ``method`` on success, or ``None`` when no agents are available.
        """
        log = logger.bind(tenant_id=tenant_id, ticket_id=getattr(ticket, "id", None))

        try:
            agents = await AgentRepository.list_available(db, tenant_id)
        except Exception:
            log.exception("routing.agents_fetch_failed")
            return None

        if not agents:
            log.warning("routing.no_available_agents")
            return None

        # Determine the ticket category so we can match against agent skills.
        category = await self._resolve_category(ticket)

        scored: list[tuple[object, float, str]] = []
        for agent in agents:
            score, reason = self._score_agent(agent, category)
            scored.append((agent, score, reason))

        # Pick the highest-scoring agent.
        scored.sort(key=lambda t: t[1], reverse=True)
        best_agent, best_score, best_reason = scored[0]

        # Persist the assignment.
        try:
            await TicketRepository.assign_agent(
                db,
                ticket_id=getattr(ticket, "id", None),
                agent_id=best_agent.id,
            )
        except Exception:
            log.exception("routing.assignment_failed", agent_id=best_agent.id)
            return None

        log.info(
            "routing.ticket_assigned",
            agent_id=best_agent.id,
            score=round(best_score, 4),
            reason=best_reason,
        )

        return {
            "agent_id": str(best_agent.id),
            "agent_name": getattr(best_agent, "name", "Unknown"),
            "reason": best_reason,
            "method": "skill_workload_scoring",
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _resolve_category(self, ticket: object) -> str:
        """Return the ticket category, falling back to AI classification."""
        category: str | None = getattr(ticket, "category", None)
        if category:
            return category.lower()

        # Use the LLM to infer a category from subject + description.
        subject = getattr(ticket, "subject", "") or ""
        description = getattr(ticket, "description", "") or ""
        prompt = (
            "Classify this support ticket into exactly one category: "
            "billing, technical, account, product, shipping, general.\n\n"
            f"Subject: {subject}\nDescription: {description}\n\n"
            "Respond with the single category word only."
        )

        try:
            response = await openai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=16,
                temperature=0.0,
            )
            return response.strip().lower()
        except Exception:
            logger.warning("routing.category_inference_failed")
            return "general"

    @staticmethod
    def _score_agent(
        agent: object,
        category: str,
    ) -> tuple[float, str]:
        """Return ``(score, reason)`` for a single agent.

        Score components:
        * **Skill match** – 1.0 if *category* is in the agent's skill list,
          0.0 otherwise.
        * **Workload** – linearly decreasing from 1.0 (no open tickets) to
          0.0 (at or above ``_MAX_WORKLOAD``).
        * **Availability** – 1.0 for ``online``, 0.5 for ``away``, 0.0
          otherwise.
        """
        reasons: list[str] = []

        # --- Skill match ------------------------------------------------
        skills: list[str] = [
            s.lower() for s in (getattr(agent, "skills", None) or [])
        ]
        skill_score = 1.0 if category in skills else 0.0
        if skill_score:
            reasons.append(f"skill match ({category})")

        # --- Workload ----------------------------------------------------
        open_tickets: int = getattr(agent, "open_ticket_count", 0) or 0
        workload_score = max(0.0, 1.0 - open_tickets / _MAX_WORKLOAD)
        reasons.append(f"workload {open_tickets}/{_MAX_WORKLOAD}")

        # --- Availability ------------------------------------------------
        status: str = (
            getattr(agent, "status", AgentStatus.offline).value
            if hasattr(getattr(agent, "status", None), "value")
            else str(getattr(agent, "status", "offline"))
        ).lower()

        availability_map: dict[str, float] = {
            "online": 1.0,
            "away": 0.5,
        }
        availability_score = availability_map.get(status, 0.0)

        # --- Weighted total ---------------------------------------------
        total = (
            _SKILL_MATCH_WEIGHT * skill_score
            + _WORKLOAD_WEIGHT * workload_score
            + _AVAILABILITY_WEIGHT * availability_score
        )

        reason = "; ".join(reasons)
        return total, reason


routing_service = RoutingService()
