"""Agent-assist copilot service for AI Customer Support Copilot.

Provides support agents with suggested replies, conversation summaries,
knowledge-base retrieval, and structured troubleshooting steps.
"""

from __future__ import annotations

import asyncio
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from integrations.openai_client import openai_client
from repositories.message import MessageRepository
from repositories.ticket import TicketRepository
from services.rag.pipeline import rag_pipeline
from services.rag.retrieval import retrieval_service

logger = structlog.get_logger(__name__)


class CopilotService:
    """Agent-assist copilot that augments human support agents with
    AI-powered suggestions, summaries, and troubleshooting guidance."""

    # ------------------------------------------------------------------
    # Suggested Reply
    # ------------------------------------------------------------------

    async def suggest_reply(
        self,
        db: AsyncSession,
        tenant_id: str,
        ticket_or_conversation_id: str,
        context: str | None = None,
    ) -> dict[str, Any]:
        """Draft a suggested reply for a support agent.

        Parameters
        ----------
        db:
            Async database session.
        tenant_id:
            Tenant identifier for multi-tenant isolation.
        ticket_or_conversation_id:
            The ticket or conversation to reply to.
        context:
            Optional extra context supplied by the agent (e.g. internal notes).

        Returns
        -------
        dict
            ``{"suggested_reply": str, "confidence": float, "sources": list}``
        """
        log = logger.bind(
            tenant_id=tenant_id,
            ticket_or_conversation_id=ticket_or_conversation_id,
        )
        log.info("copilot.suggest_reply.start")

        try:
            # Gather conversation messages and relevant KB info in parallel.
            messages, rag_result = await asyncio.gather(
                self._fetch_messages(db, tenant_id, ticket_or_conversation_id, log),
                rag_pipeline.run(
                    db=db,
                    tenant_id=tenant_id,
                    query=context or self._extract_latest_query([], fallback=ticket_or_conversation_id),
                ),
            )

            # If we now have the actual messages, re-run RAG with the latest
            # customer message for better relevance (unless context was given).
            if messages and context is None:
                latest_query = self._extract_latest_query(messages)
                if latest_query:
                    rag_result = await rag_pipeline.run(
                        db=db,
                        tenant_id=tenant_id,
                        query=latest_query,
                    )

            kb_context = rag_result.get("answer", "")
            sources = rag_result.get("citations", [])

            prompt = self._build_reply_prompt(messages, kb_context, context)
            completion = await openai_client.chat_completion(
                messages=[{"role": "system", "content": prompt}],
                temperature=0.4,
            )

            suggested_reply = completion.get("content", "")
            confidence = self._estimate_confidence(rag_result, suggested_reply)

            log.info(
                "copilot.suggest_reply.complete",
                confidence=confidence,
                source_count=len(sources),
            )

            return {
                "suggested_reply": suggested_reply,
                "confidence": confidence,
                "sources": sources,
            }

        except Exception:
            log.exception("copilot.suggest_reply.error")
            raise

    # ------------------------------------------------------------------
    # Summarize
    # ------------------------------------------------------------------

    async def summarize(
        self,
        db: AsyncSession,
        tenant_id: str,
        ticket_or_conversation_id: str,
    ) -> dict[str, Any]:
        """Produce a structured summary of a ticket or conversation.

        Returns
        -------
        dict
            ``{"summary": str, "key_points": list[str], "action_items": list[str]}``
        """
        log = logger.bind(
            tenant_id=tenant_id,
            ticket_or_conversation_id=ticket_or_conversation_id,
        )
        log.info("copilot.summarize.start")

        try:
            messages = await self._fetch_messages(
                db, tenant_id, ticket_or_conversation_id, log,
            )

            if not messages:
                log.warning("copilot.summarize.no_messages")
                return {"summary": "", "key_points": [], "action_items": []}

            prompt = self._build_summarize_prompt(messages)
            completion = await openai_client.chat_completion(
                messages=[{"role": "system", "content": prompt}],
                temperature=0.3,
            )

            parsed = self._parse_summary_response(completion.get("content", ""))

            log.info(
                "copilot.summarize.complete",
                key_point_count=len(parsed.get("key_points", [])),
                action_item_count=len(parsed.get("action_items", [])),
            )

            return parsed

        except Exception:
            log.exception("copilot.summarize.error")
            raise

    # ------------------------------------------------------------------
    # Knowledge Base Retrieval
    # ------------------------------------------------------------------

    async def retrieve_kb(
        self,
        db: AsyncSession,
        tenant_id: str,
        query: str,
    ) -> list[dict[str, Any]]:
        """Search the knowledge base and return relevant articles.

        Returns
        -------
        list[dict]
            Each entry: ``{"content": str, "document_title": str, "relevance_score": float}``
        """
        log = logger.bind(tenant_id=tenant_id)
        log.info("copilot.retrieve_kb.start", query=query)

        try:
            results = await retrieval_service.retrieve(
                db=db,
                tenant_id=tenant_id,
                query=query,
            )

            documents = [
                {
                    "content": doc.get("content", ""),
                    "document_title": doc.get("title", doc.get("document_title", "")),
                    "relevance_score": float(doc.get("score", doc.get("relevance_score", 0.0))),
                }
                for doc in results
            ]

            log.info("copilot.retrieve_kb.complete", result_count=len(documents))
            return documents

        except Exception:
            log.exception("copilot.retrieve_kb.error")
            raise

    # ------------------------------------------------------------------
    # Troubleshooting Steps
    # ------------------------------------------------------------------

    async def troubleshooting_steps(
        self,
        db: AsyncSession,
        tenant_id: str,
        topic_or_ticket_id: str,
    ) -> dict[str, Any]:
        """Generate structured troubleshooting steps for a topic or ticket.

        Returns
        -------
        dict
            ``{"topic": str, "steps": list[dict], "related_articles": list}``
        """
        log = logger.bind(
            tenant_id=tenant_id,
            topic_or_ticket_id=topic_or_ticket_id,
        )
        log.info("copilot.troubleshooting_steps.start")

        try:
            # Use RAG to find relevant documentation.
            rag_result = await rag_pipeline.run(
                db=db,
                tenant_id=tenant_id,
                query=f"troubleshooting steps for {topic_or_ticket_id}",
            )

            kb_context = rag_result.get("answer", "")
            related_articles = rag_result.get("citations", [])

            prompt = self._build_troubleshooting_prompt(topic_or_ticket_id, kb_context)
            completion = await openai_client.chat_completion(
                messages=[{"role": "system", "content": prompt}],
                temperature=0.3,
            )

            parsed = self._parse_troubleshooting_response(
                completion.get("content", ""),
                topic_or_ticket_id,
            )

            log.info(
                "copilot.troubleshooting_steps.complete",
                step_count=len(parsed.get("steps", [])),
                related_article_count=len(related_articles),
            )

            return {
                "topic": parsed.get("topic", topic_or_ticket_id),
                "steps": parsed.get("steps", []),
                "related_articles": related_articles,
            }

        except Exception:
            log.exception("copilot.troubleshooting_steps.error")
            raise

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _fetch_messages(
        self,
        db: AsyncSession,
        tenant_id: str,
        ticket_or_conversation_id: str,
        log: structlog.stdlib.BoundLogger,
    ) -> list[dict]:
        """Try ticket messages first, then fall back to conversation messages."""
        try:
            ticket_repo = TicketRepository(db)
            messages = await ticket_repo.get_messages(
                tenant_id=tenant_id,
                ticket_id=ticket_or_conversation_id,
            )
            if messages:
                return messages
        except Exception:
            log.debug("copilot.fetch_messages.ticket_lookup_failed")

        try:
            message_repo = MessageRepository(db)
            messages = await message_repo.get_by_conversation(
                tenant_id=tenant_id,
                conversation_id=ticket_or_conversation_id,
            )
            return messages or []
        except Exception:
            log.warning("copilot.fetch_messages.failed")
            return []

    @staticmethod
    def _extract_latest_query(
        messages: list[dict],
        fallback: str = "",
    ) -> str:
        """Return the text of the most recent customer message."""
        for msg in reversed(messages):
            if msg.get("role") in ("user", "customer"):
                return msg.get("content", msg.get("text", ""))
        return fallback

    @staticmethod
    def _build_reply_prompt(
        messages: list[dict],
        kb_context: str,
        agent_context: str | None,
    ) -> str:
        conversation = "\n".join(
            f"{m.get('role', 'unknown')}: {m.get('content', m.get('text', ''))}"
            for m in messages
        )
        parts = [
            "You are an AI assistant helping a support agent draft a reply.",
            "Use the knowledge base context below to ground your answer.",
            "",
            "### Knowledge Base Context",
            kb_context or "(no relevant articles found)",
            "",
            "### Conversation",
            conversation or "(no messages available)",
        ]
        if agent_context:
            parts.extend(["", "### Agent Notes", agent_context])
        parts.extend([
            "",
            "Draft a professional, helpful reply for the support agent to send.",
            "Be concise and accurate. Cite sources when possible.",
        ])
        return "\n".join(parts)

    @staticmethod
    def _build_summarize_prompt(messages: list[dict]) -> str:
        conversation = "\n".join(
            f"{m.get('role', 'unknown')}: {m.get('content', m.get('text', ''))}"
            for m in messages
        )
        return (
            "Summarize the following support conversation.\n"
            "Return a JSON object with exactly these keys:\n"
            '- "summary": a concise paragraph\n'
            '- "key_points": a list of important points (strings)\n'
            '- "action_items": a list of follow-up actions (strings)\n\n'
            f"### Conversation\n{conversation}"
        )

    @staticmethod
    def _build_troubleshooting_prompt(topic: str, kb_context: str) -> str:
        return (
            "You are a support engineer. Generate structured troubleshooting "
            f"steps for the following topic: {topic}\n\n"
            "### Relevant Documentation\n"
            f"{kb_context or '(none available)'}\n\n"
            "Return a JSON object with:\n"
            '- "topic": the resolved topic name (string)\n'
            '- "steps": a list of objects, each with "step_number" (int), '
            '"title" (string), "description" (string), and "expected_outcome" (string)\n'
        )

    @staticmethod
    def _parse_summary_response(content: str) -> dict[str, Any]:
        """Best-effort parse of the LLM summary response."""
        import json

        try:
            return json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return {
                "summary": content,
                "key_points": [],
                "action_items": [],
            }

    @staticmethod
    def _parse_troubleshooting_response(
        content: str,
        fallback_topic: str,
    ) -> dict[str, Any]:
        """Best-effort parse of the LLM troubleshooting response."""
        import json

        try:
            return json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return {
                "topic": fallback_topic,
                "steps": [],
            }

    @staticmethod
    def _estimate_confidence(rag_result: dict, reply: str) -> float:
        """Heuristic confidence score based on RAG quality signals."""
        if not reply:
            return 0.0

        score = 0.5
        citations = rag_result.get("citations", [])
        if citations:
            score += min(len(citations) * 0.1, 0.3)

        relevance = rag_result.get("relevance_score", rag_result.get("score"))
        if relevance is not None:
            score = min(score + float(relevance) * 0.2, 1.0)

        return round(min(score, 1.0), 2)


copilot_service = CopilotService()
