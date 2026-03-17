"""Retrieval service for RAG pipeline - semantic search over knowledge chunks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import structlog

from services.rag.embedding import embedding_service
from repositories.knowledge import KnowledgeChunkRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


@dataclass
class RetrievalResult:
    """A single retrieval result with chunk content and metadata."""

    chunk_id: str
    content: str
    score: float
    document_id: str
    document_title: str
    metadata: dict

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "score": self.score,
            "document_id": self.document_id,
            "document_title": self.document_title,
            "metadata": self.metadata,
        }


class RetrievalService:
    """Handles semantic search over knowledge base chunks using pgvector."""

    def __init__(self) -> None:
        self.chunk_repo = KnowledgeChunkRepository()

    async def search(
        self,
        db: AsyncSession,
        tenant_id: str,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
        score_threshold: float = 0.0,
    ) -> list[RetrievalResult]:
        """Perform semantic search over knowledge chunks.

        Args:
            db: Database session.
            tenant_id: Tenant identifier.
            query: The search query text.
            top_k: Maximum number of results to return.
            filters: Optional filters (e.g., collection_id, document_id).
            score_threshold: Minimum similarity score to include.

        Returns:
            List of RetrievalResult objects sorted by relevance.
        """
        if not query or not query.strip():
            return []

        try:
            # Generate query embedding
            query_embedding = await embedding_service.embed_text(query)
            if not query_embedding:
                logger.warning("empty_query_embedding", query=query[:100])
                return []

            # Perform similarity search via repository
            raw_results = await self.chunk_repo.similarity_search(
                db,
                tenant_id=tenant_id,
                embedding=query_embedding,
                top_k=top_k,
                filters=filters,
            )

            results: list[RetrievalResult] = []
            for row in raw_results:
                score = getattr(row, "score", 0.0) if hasattr(row, "score") else row.get("score", 0.0) if isinstance(row, dict) else 0.0

                if score < score_threshold:
                    continue

                if isinstance(row, dict):
                    results.append(
                        RetrievalResult(
                            chunk_id=row.get("id", ""),
                            content=row.get("content", ""),
                            score=score,
                            document_id=row.get("document_id", ""),
                            document_title=row.get("document_title", ""),
                            metadata=row.get("metadata_", {}),
                        )
                    )
                else:
                    results.append(
                        RetrievalResult(
                            chunk_id=getattr(row, "id", ""),
                            content=getattr(row, "content", ""),
                            score=score,
                            document_id=getattr(row, "document_id", ""),
                            document_title=getattr(row, "document_title", row.__class__.__name__),
                            metadata=getattr(row, "metadata_", {}),
                        )
                    )

            logger.info(
                "retrieval_search",
                tenant_id=tenant_id,
                query_length=len(query),
                top_k=top_k,
                results_count=len(results),
            )
            return results

        except Exception as e:
            logger.error(
                "retrieval_search_failed",
                tenant_id=tenant_id,
                error=str(e),
            )
            raise

    async def search_with_context(
        self,
        db: AsyncSession,
        tenant_id: str,
        query: str,
        conversation_history: list[dict] | None = None,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        """Search with conversation context to improve relevance.

        Augments the query with recent conversation context to better
        capture user intent.

        Args:
            db: Database session.
            tenant_id: Tenant identifier.
            query: The search query text.
            conversation_history: List of recent messages with 'role' and 'content'.
            top_k: Maximum number of results.
            filters: Optional filters.

        Returns:
            List of RetrievalResult objects.
        """
        # Build an augmented query using conversation context
        augmented_query = query
        if conversation_history:
            # Take the last few messages to add context
            recent = conversation_history[-3:]
            context_parts = [
                msg.get("content", "")
                for msg in recent
                if msg.get("content")
            ]
            if context_parts:
                context_text = " ".join(context_parts[-2:])
                # Combine: weight the actual query more heavily
                augmented_query = f"{query} {context_text[:200]}"

        results = await self.search(
            db,
            tenant_id=tenant_id,
            query=augmented_query,
            top_k=top_k,
            filters=filters,
        )

        logger.debug(
            "retrieval_search_with_context",
            original_query=query[:100],
            augmented_length=len(augmented_query),
            results_count=len(results),
        )
        return results


retrieval_service = RetrievalService()
