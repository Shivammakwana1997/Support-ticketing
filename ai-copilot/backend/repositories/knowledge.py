from __future__ import annotations

from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.knowledge import KnowledgeChunk, KnowledgeDocument
from backend.repositories.base import BaseRepository


class KnowledgeDocumentRepository(BaseRepository[KnowledgeDocument]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(KnowledgeDocument, session)

    async def get_active(
        self, tenant_id: UUID, *, offset: int = 0, limit: int = 20
    ) -> Sequence[KnowledgeDocument]:
        stmt = (
            select(KnowledgeDocument)
            .where(KnowledgeDocument.tenant_id == tenant_id)
            .where(KnowledgeDocument.deleted_at.is_(None))
            .order_by(KnowledgeDocument.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class KnowledgeChunkRepository(BaseRepository[KnowledgeChunk]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(KnowledgeChunk, session)

    async def search_similar(
        self,
        embedding: list[float],
        tenant_id: UUID,
        *,
        top_k: int = 5,
        threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        """Search for similar chunks using pgvector cosine distance."""
        # Using cosine distance: 1 - cosine_similarity
        # Lower distance = more similar; threshold is cosine similarity
        distance_threshold = 1.0 - threshold

        query = text("""
            SELECT
                kc.id AS chunk_id,
                kc.document_id,
                kc.content,
                kc.chunk_index,
                kc.metadata AS chunk_metadata,
                kd.title AS document_title,
                1 - (kc.embedding <=> :embedding) AS similarity
            FROM knowledge_chunks kc
            JOIN knowledge_documents kd ON kd.id = kc.document_id
            WHERE kc.tenant_id = :tenant_id
              AND kd.deleted_at IS NULL
              AND (kc.embedding <=> :embedding) <= :distance_threshold
            ORDER BY kc.embedding <=> :embedding
            LIMIT :top_k
        """)

        result = await self.session.execute(
            query,
            {
                "embedding": str(embedding),
                "tenant_id": str(tenant_id),
                "distance_threshold": distance_threshold,
                "top_k": top_k,
            },
        )
        rows = result.fetchall()
        return [
            {
                "chunk_id": row.chunk_id,
                "document_id": row.document_id,
                "content": row.content,
                "chunk_index": row.chunk_index,
                "chunk_metadata": row.chunk_metadata,
                "document_title": row.document_title,
                "similarity": float(row.similarity),
            }
            for row in rows
        ]
