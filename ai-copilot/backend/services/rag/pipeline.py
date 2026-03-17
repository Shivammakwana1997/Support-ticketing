"""RAG pipeline - orchestrates retrieval, context assembly, and LLM generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import structlog

from integrations.openai_client import openai_client
from services.rag.retrieval import retrieval_service, RetrievalResult

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SYSTEM_PROMPT = """You are a helpful customer support AI assistant. Answer the user's question based on the provided context from the knowledge base.

Rules:
1. Only answer based on the provided context. If the context doesn't contain relevant information, say so clearly.
2. Cite your sources by referencing the document titles when possible.
3. Be concise and direct in your responses.
4. If the question is ambiguous, ask for clarification.
5. Maintain a professional and friendly tone.

Context from knowledge base:
{context}"""


@dataclass
class Citation:
    """A citation referencing a source document."""

    document_id: str
    document_title: str
    chunk_id: str
    content_snippet: str
    relevance_score: float

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "document_title": self.document_title,
            "chunk_id": self.chunk_id,
            "content_snippet": self.content_snippet,
            "relevance_score": self.relevance_score,
        }


@dataclass
class RAGResponse:
    """Response from the RAG pipeline."""

    answer: str
    citations: list[Citation] = field(default_factory=list)
    confidence: float = 0.0
    retrieval_results: list[RetrievalResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "answer": self.answer,
            "citations": [c.to_dict() for c in self.citations],
            "confidence": self.confidence,
        }


class RAGPipeline:
    """Orchestrates retrieval-augmented generation for customer support queries."""

    def __init__(self, model: str = "gpt-4o") -> None:
        self.model = model

    async def answer(
        self,
        db: AsyncSession,
        tenant_id: str,
        query: str,
        conversation_history: list[dict[str, str]] | None = None,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> RAGResponse:
        """Generate an answer using retrieval-augmented generation.

        Args:
            db: Database session.
            tenant_id: Tenant identifier.
            query: User's question.
            conversation_history: Optional list of {"role": str, "content": str}.
            top_k: Number of chunks to retrieve.
            filters: Optional retrieval filters.

        Returns:
            RAGResponse with answer, citations, and confidence.
        """
        try:
            # Step 1: Retrieve relevant chunks
            if conversation_history:
                results = await retrieval_service.search_with_context(
                    db,
                    tenant_id=tenant_id,
                    query=query,
                    conversation_history=conversation_history,
                    top_k=top_k,
                    filters=filters,
                )
            else:
                results = await retrieval_service.search(
                    db,
                    tenant_id=tenant_id,
                    query=query,
                    top_k=top_k,
                    filters=filters,
                )

            # Step 2: Assemble context from retrieved chunks
            context = self._assemble_context(results)

            # Step 3: Build messages for LLM
            messages = self._build_messages(
                query=query,
                context=context,
                conversation_history=conversation_history,
            )

            # Step 4: Generate response via OpenAI
            response = await openai_client.chat_completion(
                messages=messages,
                model=self.model,
                temperature=0.3,
                max_tokens=1024,
            )

            answer_text = response.choices[0].message.content or ""

            # Step 5: Build citations
            citations = self._build_citations(results)

            # Step 6: Calculate confidence based on retrieval scores
            confidence = self._calculate_confidence(results)

            rag_response = RAGResponse(
                answer=answer_text,
                citations=citations,
                confidence=confidence,
                retrieval_results=results,
            )

            logger.info(
                "rag_answer_generated",
                tenant_id=tenant_id,
                query_length=len(query),
                num_results=len(results),
                confidence=confidence,
            )
            return rag_response

        except Exception as e:
            logger.error(
                "rag_pipeline_failed",
                tenant_id=tenant_id,
                error=str(e),
            )
            # Return a graceful fallback
            return RAGResponse(
                answer="I'm sorry, I encountered an error while searching the knowledge base. Please try again or contact support.",
                citations=[],
                confidence=0.0,
            )

    def _assemble_context(self, results: list[RetrievalResult]) -> str:
        """Assemble context string from retrieval results."""
        if not results:
            return "No relevant information found in the knowledge base."

        context_parts: list[str] = []
        for i, result in enumerate(results, 1):
            source_label = result.document_title or f"Document {result.document_id[:8]}"
            context_parts.append(
                f"[Source {i}: {source_label}]\n{result.content}"
            )

        return "\n\n---\n\n".join(context_parts)

    def _build_messages(
        self,
        query: str,
        context: str,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> list[dict[str, str]]:
        """Build the message list for the LLM call."""
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT.format(context=context),
            }
        ]

        # Add conversation history if provided
        if conversation_history:
            for msg in conversation_history[-10:]:  # Last 10 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role in ("user", "assistant") and content:
                    messages.append({"role": role, "content": content})

        # Add the current query
        messages.append({"role": "user", "content": query})

        return messages

    def _build_citations(self, results: list[RetrievalResult]) -> list[Citation]:
        """Build citation objects from retrieval results."""
        citations: list[Citation] = []
        seen_docs: set[str] = set()

        for result in results:
            if result.document_id in seen_docs:
                continue
            seen_docs.add(result.document_id)

            snippet = result.content[:200] + "..." if len(result.content) > 200 else result.content

            citations.append(
                Citation(
                    document_id=result.document_id,
                    document_title=result.document_title,
                    chunk_id=result.chunk_id,
                    content_snippet=snippet,
                    relevance_score=result.score,
                )
            )

        return citations

    def _calculate_confidence(self, results: list[RetrievalResult]) -> float:
        """Calculate confidence score based on retrieval quality."""
        if not results:
            return 0.0

        # Use the top result's score as the base, weighted by number of results
        top_score = results[0].score
        avg_score = sum(r.score for r in results) / len(results)

        # Blend top and average scores
        confidence = (top_score * 0.6 + avg_score * 0.4)

        # Clamp to [0, 1]
        return max(0.0, min(1.0, confidence))

    async def answer_streaming(
        self,
        db: AsyncSession,
        tenant_id: str,
        query: str,
        conversation_history: list[dict[str, str]] | None = None,
        top_k: int = 5,
    ):
        """Stream an answer token by token.

        Yields:
            Partial answer strings as they are generated.
        """
        results = await retrieval_service.search(
            db,
            tenant_id=tenant_id,
            query=query,
            top_k=top_k,
        )

        context = self._assemble_context(results)
        messages = self._build_messages(query, context, conversation_history)

        try:
            stream = await openai_client.chat_completion_stream(
                messages=messages,
                model=self.model,
                temperature=0.3,
                max_tokens=1024,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error("rag_streaming_failed", error=str(e))
            yield "I'm sorry, I encountered an error. Please try again."


rag_pipeline = RAGPipeline()
