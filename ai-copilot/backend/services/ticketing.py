from __future__ import annotations

import uuid
import datetime
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import NotFoundError, ForbiddenError
from integrations.openai_client import openai_client
from models.enums import AgentStatus, Priority, TicketStatus
from models.ticket import Ticket
from repositories.agent import AgentRepository
from repositories.conversation import ConversationRepository
from repositories.message import MessageRepository
from repositories.ticket import TicketRepository
from schemas.common import PaginatedResponse
from schemas.ticket import TicketCreate, TicketUpdate

logger = structlog.get_logger(__name__)


def _generate_ticket_number() -> str:
    """Generate a human-readable ticket number with a short UUID suffix."""
    short_id = uuid.uuid4().hex[:8].upper()
    return f"TKT-{short_id}"


class TicketingService:
    """Service layer for ticket lifecycle management, AI-powered routing,
    summarisation, and duplicate detection."""

    def __init__(self) -> None:
        self.ticket_repo = TicketRepository()
        self.conversation_repo = ConversationRepository()
        self.agent_repo = AgentRepository()
        self.message_repo = MessageRepository()

    # ------------------------------------------------------------------
    # 1. Create
    # ------------------------------------------------------------------

    async def create_ticket(
        self,
        db: AsyncSession,
        tenant_id: str,
        customer_id: str,
        subject: str,
        description: str = "",
        conversation_id: str | None = None,
        priority: Priority = Priority.MEDIUM,
        metadata: dict | None = None,
    ) -> Ticket:
        """Create a new support ticket with an auto-generated ticket number."""
        log = logger.bind(
            tenant_id=tenant_id,
            customer_id=customer_id,
            subject=subject,
        )
        log.info("ticketing.create_ticket.start")

        ticket_number = _generate_ticket_number()

        ticket_data = TicketCreate(
            tenant_id=tenant_id,
            customer_id=customer_id,
            subject=subject,
            description=description,
            ticket_number=ticket_number,
            conversation_id=conversation_id,
            priority=priority,
            status=TicketStatus.OPEN,
            metadata=metadata or {},
        )

        ticket = await self.ticket_repo.create(db, ticket_data)

        log.info(
            "ticketing.create_ticket.success",
            ticket_id=str(ticket.id),
            ticket_number=ticket_number,
        )
        return ticket

    # ------------------------------------------------------------------
    # 2. Get single ticket (with messages)
    # ------------------------------------------------------------------

    async def get_ticket(
        self,
        db: AsyncSession,
        tenant_id: str,
        ticket_id: str,
    ) -> dict[str, Any]:
        """Return a ticket together with its associated messages.

        Raises ``NotFoundError`` if the ticket does not exist and
        ``ForbiddenError`` if the caller's tenant does not own it.
        """
        log = logger.bind(tenant_id=tenant_id, ticket_id=ticket_id)
        log.info("ticketing.get_ticket.start")

        ticket = await self.ticket_repo.get(db, ticket_id)
        if ticket is None:
            log.warning("ticketing.get_ticket.not_found")
            raise NotFoundError(f"Ticket {ticket_id} not found")

        if str(ticket.tenant_id) != tenant_id:
            log.warning("ticketing.get_ticket.forbidden")
            raise ForbiddenError("Access denied to this ticket")

        messages = await self.message_repo.list_by_ticket(db, ticket_id)

        log.info(
            "ticketing.get_ticket.success",
            message_count=len(messages),
        )
        return {
            "ticket": ticket,
            "messages": messages,
        }

    # ------------------------------------------------------------------
    # 3. List tickets (filtered + paginated)
    # ------------------------------------------------------------------

    async def list_tickets(
        self,
        db: AsyncSession,
        tenant_id: str,
        status: TicketStatus | None = None,
        priority: Priority | None = None,
        assigned_to: str | None = None,
        customer_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """Return a paginated, optionally filtered list of tickets for a tenant."""
        log = logger.bind(
            tenant_id=tenant_id,
            status=status,
            priority=priority,
            assigned_to=assigned_to,
            customer_id=customer_id,
            page=page,
            page_size=page_size,
        )
        log.info("ticketing.list_tickets.start")

        filters: dict[str, Any] = {"tenant_id": tenant_id}
        if status is not None:
            filters["status"] = status
        if priority is not None:
            filters["priority"] = priority
        if assigned_to is not None:
            filters["assigned_to"] = assigned_to
        if customer_id is not None:
            filters["customer_id"] = customer_id

        offset = (page - 1) * page_size

        tickets, total = await self.ticket_repo.list(
            db,
            filters=filters,
            offset=offset,
            limit=page_size,
        )

        total_pages = (total + page_size - 1) // page_size if total else 0

        log.info("ticketing.list_tickets.success", total=total)
        return PaginatedResponse(
            items=tickets,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    # ------------------------------------------------------------------
    # 4. Update ticket
    # ------------------------------------------------------------------

    async def update_ticket(
        self,
        db: AsyncSession,
        tenant_id: str,
        ticket_id: str,
        data: dict[str, Any],
    ) -> Ticket:
        """Update editable fields of an existing ticket.

        Raises ``NotFoundError`` / ``ForbiddenError`` as appropriate.
        """
        log = logger.bind(tenant_id=tenant_id, ticket_id=ticket_id, data=data)
        log.info("ticketing.update_ticket.start")

        ticket = await self.ticket_repo.get(db, ticket_id)
        if ticket is None:
            log.warning("ticketing.update_ticket.not_found")
            raise NotFoundError(f"Ticket {ticket_id} not found")

        if str(ticket.tenant_id) != tenant_id:
            log.warning("ticketing.update_ticket.forbidden")
            raise ForbiddenError("Access denied to this ticket")

        update_payload = TicketUpdate(**data)
        updated_ticket = await self.ticket_repo.update(db, ticket_id, update_payload)

        log.info("ticketing.update_ticket.success")
        return updated_ticket

    # ------------------------------------------------------------------
    # 5. AI-powered ticket summary
    # ------------------------------------------------------------------

    async def get_ticket_summary(
        self,
        db: AsyncSession,
        tenant_id: str,
        ticket_id: str,
    ) -> dict[str, Any]:
        """Use an LLM to produce a structured summary of the ticket and its
        conversation history.

        Returns a dict with ``summary``, ``key_issues``, and
        ``suggested_actions``.
        """
        log = logger.bind(tenant_id=tenant_id, ticket_id=ticket_id)
        log.info("ticketing.get_ticket_summary.start")

        ticket_data = await self.get_ticket(db, tenant_id, ticket_id)
        ticket: Ticket = ticket_data["ticket"]
        messages: list = ticket_data["messages"]

        conversation_text = "\n".join(
            f"[{msg.role}] {msg.content}" for msg in messages
        )

        system_prompt = (
            "You are an expert support analyst. Analyse the following support ticket "
            "and its conversation history. Respond with valid JSON containing exactly "
            "three keys:\n"
            '  "summary": a concise paragraph summarising the ticket,\n'
            '  "key_issues": a JSON array of strings listing the main issues raised,\n'
            '  "suggested_actions": a JSON array of strings with recommended next steps.\n'
            "Do NOT include any text outside the JSON object."
        )

        user_prompt = (
            f"Subject: {ticket.subject}\n"
            f"Description: {ticket.description}\n"
            f"Status: {ticket.status}\n"
            f"Priority: {ticket.priority}\n\n"
            f"Conversation:\n{conversation_text or '(no messages yet)'}"
        )

        log.info("ticketing.get_ticket_summary.calling_llm")

        response = await openai_client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )

        import json

        try:
            result = json.loads(response)
        except (json.JSONDecodeError, TypeError):
            log.error("ticketing.get_ticket_summary.parse_error", raw=response)
            result = {
                "summary": response if isinstance(response, str) else str(response),
                "key_issues": [],
                "suggested_actions": [],
            }

        # Ensure the expected keys exist even if the model omitted one.
        result.setdefault("summary", "")
        result.setdefault("key_issues", [])
        result.setdefault("suggested_actions", [])

        log.info("ticketing.get_ticket_summary.success")
        return result

    # ------------------------------------------------------------------
    # 6. Intelligent ticket routing
    # ------------------------------------------------------------------

    async def route_ticket(
        self,
        db: AsyncSession,
        tenant_id: str,
        ticket_id: str,
    ) -> dict[str, Any]:
        """Analyse ticket content with an LLM, find available agents, and
        assign the best-matching agent based on skill overlap.

        Returns a dict with ``agent_id``, ``agent_name``, and ``reason``.
        """
        log = logger.bind(tenant_id=tenant_id, ticket_id=ticket_id)
        log.info("ticketing.route_ticket.start")

        ticket_data = await self.get_ticket(db, tenant_id, ticket_id)
        ticket: Ticket = ticket_data["ticket"]

        # --- Step 1: Ask the LLM what category / skills are needed -----------

        import json

        analysis_prompt = (
            "You are a support-ticket classifier. Given the ticket below, respond "
            "with valid JSON containing exactly two keys:\n"
            '  "category": a short category label (e.g. "billing", "technical", "account"),\n'
            '  "required_skills": a JSON array of short skill tags the handling agent needs.\n'
            "Do NOT include any text outside the JSON object.\n\n"
            f"Subject: {ticket.subject}\n"
            f"Description: {ticket.description}\n"
            f"Priority: {ticket.priority}"
        )

        analysis_raw = await openai_client.chat_completion(
            messages=[
                {"role": "system", "content": "You are a support-ticket classifier."},
                {"role": "user", "content": analysis_prompt},
            ],
            response_format={"type": "json_object"},
        )

        try:
            analysis = json.loads(analysis_raw)
        except (json.JSONDecodeError, TypeError):
            log.error("ticketing.route_ticket.analysis_parse_error", raw=analysis_raw)
            analysis = {"category": "general", "required_skills": []}

        required_skills: list[str] = [
            s.lower().strip() for s in analysis.get("required_skills", [])
        ]
        category: str = analysis.get("category", "general")

        log.info(
            "ticketing.route_ticket.analysis_done",
            category=category,
            required_skills=required_skills,
        )

        # --- Step 2: Find available agents -----------------------------------

        available_agents = await self.agent_repo.list_available(db, tenant_id)

        if not available_agents:
            log.warning("ticketing.route_ticket.no_agents_available")
            raise NotFoundError("No available agents for routing")

        # --- Step 3: Score agents by skill overlap ---------------------------

        best_agent = None
        best_score: int = -1
        best_reason: str = ""

        for agent in available_agents:
            agent_skills: list[str] = [
                s.lower().strip()
                for s in (getattr(agent, "skills", None) or [])
            ]

            overlap = set(required_skills) & set(agent_skills)
            score = len(overlap)

            if score > best_score:
                best_score = score
                best_agent = agent
                if overlap:
                    best_reason = (
                        f"Agent matched on skills: {', '.join(sorted(overlap))} "
                        f"for category '{category}'"
                    )
                else:
                    best_reason = (
                        f"Agent selected as best available for category '{category}'"
                    )

        # Fallback: if no agent matched any skill, pick the first available.
        if best_agent is None:
            best_agent = available_agents[0]
            best_reason = "Assigned to first available agent (no skill match)"

        # --- Step 4: Assign the agent to the ticket --------------------------

        await self.ticket_repo.update(
            db,
            ticket_id,
            TicketUpdate(
                assigned_to=str(best_agent.id),
                status=TicketStatus.IN_PROGRESS,
            ),
        )

        agent_name = getattr(best_agent, "name", None) or str(best_agent.id)

        log.info(
            "ticketing.route_ticket.success",
            agent_id=str(best_agent.id),
            agent_name=agent_name,
            score=best_score,
        )

        return {
            "agent_id": str(best_agent.id),
            "agent_name": agent_name,
            "reason": best_reason,
        }

    # ------------------------------------------------------------------
    # 7. Duplicate detection
    # ------------------------------------------------------------------

    async def detect_duplicates(
        self,
        db: AsyncSession,
        tenant_id: str,
        ticket_id: str,
    ) -> list[dict[str, Any]]:
        """Compare a ticket against recent tickets in the same tenant and
        return potential duplicates ranked by similarity.

        Uses an LLM to evaluate subject/description similarity and returns a
        list of dicts with ``ticket_id``, ``subject``, and
        ``similarity_score`` (0.0 -- 1.0).
        """
        log = logger.bind(tenant_id=tenant_id, ticket_id=ticket_id)
        log.info("ticketing.detect_duplicates.start")

        ticket_data = await self.get_ticket(db, tenant_id, ticket_id)
        ticket: Ticket = ticket_data["ticket"]

        # Fetch recent tickets for the same tenant (last 100).
        recent_tickets, _ = await self.ticket_repo.list(
            db,
            filters={"tenant_id": tenant_id},
            offset=0,
            limit=100,
        )

        # Exclude the target ticket itself.
        candidates = [
            t for t in recent_tickets if str(t.id) != ticket_id
        ]

        if not candidates:
            log.info("ticketing.detect_duplicates.no_candidates")
            return []

        # Build a compact representation for the LLM.
        candidate_lines = "\n".join(
            f"- ID: {t.id} | Subject: {t.subject} | Description: {t.description or ''}"
            for t in candidates
        )

        import json

        system_prompt = (
            "You are a duplicate-ticket detector. You will be given a reference ticket "
            "and a list of candidate tickets. For each candidate, evaluate how similar "
            "it is to the reference ticket on a scale from 0.0 (completely different) "
            "to 1.0 (identical issue). Only return candidates with a similarity score "
            "of 0.5 or above.\n\n"
            "Respond with valid JSON: an array of objects, each with keys "
            '"ticket_id" (string), "subject" (string), "similarity_score" (float). '
            "Sort by similarity_score descending. If no duplicates found, return an "
            "empty array []."
        )

        user_prompt = (
            f"Reference ticket:\n"
            f"  Subject: {ticket.subject}\n"
            f"  Description: {ticket.description or '(none)'}\n\n"
            f"Candidates:\n{candidate_lines}"
        )

        log.info(
            "ticketing.detect_duplicates.calling_llm",
            candidate_count=len(candidates),
        )

        response = await openai_client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )

        try:
            parsed = json.loads(response)
            # The model may wrap the list in a key; handle both shapes.
            if isinstance(parsed, list):
                duplicates = parsed
            elif isinstance(parsed, dict):
                # Try common wrapper keys.
                duplicates = (
                    parsed.get("duplicates")
                    or parsed.get("results")
                    or parsed.get("candidates")
                    or next(
                        (v for v in parsed.values() if isinstance(v, list)),
                        [],
                    )
                )
            else:
                duplicates = []
        except (json.JSONDecodeError, TypeError):
            log.error("ticketing.detect_duplicates.parse_error", raw=response)
            duplicates = []

        # Normalise and validate each entry.
        results: list[dict[str, Any]] = []
        for entry in duplicates:
            if not isinstance(entry, dict):
                continue
            try:
                score = float(entry.get("similarity_score", 0))
            except (ValueError, TypeError):
                continue
            results.append(
                {
                    "ticket_id": str(entry.get("ticket_id", "")),
                    "subject": str(entry.get("subject", "")),
                    "similarity_score": round(max(0.0, min(1.0, score)), 2),
                }
            )

        # Ensure descending order by score.
        results.sort(key=lambda d: d["similarity_score"], reverse=True)

        log.info(
            "ticketing.detect_duplicates.success",
            duplicate_count=len(results),
        )
        return results


# Module-level singleton
ticketing_service = TicketingService()
