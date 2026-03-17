"""Chatbot agent service for AI Customer Support Copilot.

Orchestrates RAG retrieval, intent detection, and sentiment analysis
to produce grounded, context-aware responses for end-user conversations.
"""

from __future__ import annotations

import asyncio
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from services.conversation import conversation_service
from services.nlp.intent import intent_service
from services.nlp.sentiment import sentiment_service
from services.rag.pipeline import rag_pipeline

logger = structlog.get_logger(__name__)


class ChatbotService:
    """High-level chatbot that combines RAG, intent detection, and sentiment
    analysis to generate customer-facing responses."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_response(
        self,
        db: AsyncSession,
        tenant_id: str,
        conversation_id: str,
        user_message: str,
        history: list[dict] | None = None,
    ) -> dict[str, Any]:
        """Generate a chatbot response for *user_message*.

        Parameters
        ----------
        db:
            Async database session scoped to the current request.
        tenant_id:
            Tenant identifier for multi-tenant isolation.
        conversation_id:
            Conversation this message belongs to.
        user_message:
            The latest message from the end-user.
        history:
            Optional pre-loaded conversation history.  When ``None`` the
            history is fetched via :pyobj:`conversation_service`.

        Returns
        -------
        dict
            ``{"response": str, "citations": list, "intent": dict, "sentiment": dict}``
        """
        log = logger.bind(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
        )
        log.info("chatbot.get_response.start")

        try:
            # Load conversation history if the caller did not supply it.
            if history is None:
                history = await self._load_history(db, tenant_id, conversation_id, log)

            # Run NLP analysis (intent + sentiment) in parallel with RAG
            # retrieval so we minimise overall latency.
            (intent_result, sentiment_result), rag_result = await asyncio.gather(
                self._analyse_message(tenant_id, user_message, log),
                self._run_rag(db, tenant_id, user_message, history, log),
            )

            response_text: str = rag_result.get("answer", "")
            citations: list = rag_result.get("citations", [])

            log.info(
                "chatbot.get_response.complete",
                intent=intent_result.get("intent"),
                sentiment=sentiment_result.get("label"),
                citation_count=len(citations),
            )

            return {
                "response": response_text,
                "citations": citations,
                "intent": intent_result,
                "sentiment": sentiment_result,
            }

        except Exception:
            log.exception("chatbot.get_response.error")
            raise

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _load_history(
        self,
        db: AsyncSession,
        tenant_id: str,
        conversation_id: str,
        log: structlog.stdlib.BoundLogger,
    ) -> list[dict]:
        """Fetch conversation history via the conversation service."""
        try:
            conversation = await conversation_service.get_conversation(
                db,
                tenant_id=tenant_id,
                conversation_id=conversation_id,
            )
            return conversation.get("messages", []) if conversation else []
        except Exception:
            log.warning(
                "chatbot.load_history.failed",
                conversation_id=conversation_id,
            )
            return []

    async def _analyse_message(
        self,
        tenant_id: str,
        user_message: str,
        log: structlog.stdlib.BoundLogger,
    ) -> tuple[dict, dict]:
        """Run intent detection and sentiment analysis concurrently."""
        intent_result, sentiment_result = await asyncio.gather(
            self._detect_intent(tenant_id, user_message, log),
            self._detect_sentiment(tenant_id, user_message, log),
        )
        return intent_result, sentiment_result

    async def _detect_intent(
        self,
        tenant_id: str,
        user_message: str,
        log: structlog.stdlib.BoundLogger,
    ) -> dict:
        try:
            return await intent_service.detect(tenant_id=tenant_id, text=user_message)
        except Exception:
            log.warning("chatbot.intent_detection.failed")
            return {"intent": "unknown", "confidence": 0.0}

    async def _detect_sentiment(
        self,
        tenant_id: str,
        user_message: str,
        log: structlog.stdlib.BoundLogger,
    ) -> dict:
        try:
            return await sentiment_service.analyse(tenant_id=tenant_id, text=user_message)
        except Exception:
            log.warning("chatbot.sentiment_detection.failed")
            return {"label": "neutral", "score": 0.0}

    async def _run_rag(
        self,
        db: AsyncSession,
        tenant_id: str,
        user_message: str,
        history: list[dict],
        log: structlog.stdlib.BoundLogger,
    ) -> dict:
        """Execute the RAG pipeline to produce a grounded answer."""
        try:
            return await rag_pipeline.run(
                db=db,
                tenant_id=tenant_id,
                query=user_message,
                history=history,
            )
        except Exception:
            log.exception("chatbot.rag_pipeline.failed")
            return {"answer": "", "citations": []}


chatbot_service = ChatbotService()
