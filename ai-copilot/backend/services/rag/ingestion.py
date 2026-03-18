"""Document ingestion service for the RAG pipeline."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import structlog

from core.config import settings
from core.exceptions import NotFoundError
from services.rag.chunking import chunking_service
from services.rag.embedding import embedding_service

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from repositories.knowledge import KnowledgeDocumentRepository, KnowledgeChunkRepository
from models.enums import DocumentStatusEnum

logger = structlog.get_logger(__name__)


class IngestionService:
    """Handles document ingestion: upload, chunking, embedding, and storage."""

    def __init__(self) -> None:
        pass

    async def ingest_document(
        self,
        db: AsyncSession,
        tenant_id: str,
        file_path_or_url: str,
        title: str,
        source_type: str = "file",
        collection_id: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """Create a document record and queue it for processing.

        Args:
            db: Database session.
            tenant_id: Tenant identifier.
            file_path_or_url: Local file path or URL to ingest.
            title: Human-readable title for the document.
            source_type: One of 'file', 'url', 'text'.
            collection_id: Optional knowledge collection ID.
            metadata: Optional extra metadata.

        Returns:
            The created document record as a dict.
        """
        doc_id = str(uuid.uuid4())

        document = await self.doc_repo.create(
            db,
            {
                "id": doc_id,
                "tenant_id": tenant_id,
                "title": title,
                "source_type": source_type,
                "source_url": file_path_or_url if source_type == "url" else None,
                "file_path": file_path_or_url if source_type == "file" else None,
                "collection_id": collection_id,
                "status": DocumentStatusEnum.PENDING,
                "metadata_": metadata or {},
                "created_at": datetime.now(timezone.utc),
            },
        )

        logger.info(
            "document_ingested",
            document_id=doc_id,
            tenant_id=tenant_id,
            source_type=source_type,
            title=title,
        )

        # Queue for async processing via Redis
        try:
            from integrations.redis_client import redis_client

            await redis_client.enqueue(
                "ingestion_queue",
                {"document_id": doc_id, "tenant_id": tenant_id},
            )
            logger.info("ingestion_job_queued", document_id=doc_id)
        except Exception as e:
            logger.warning(
                "ingestion_queue_failed",
                document_id=doc_id,
                error=str(e),
            )
            # Process inline as fallback
            try:
                await self.process_document(db, doc_id)
            except Exception as proc_err:
                logger.error(
                    "inline_processing_failed",
                    document_id=doc_id,
                    error=str(proc_err),
                )

        return document

    async def process_document(self, db: AsyncSession, document_id: str) -> int:
        """Process a document: extract text, chunk, embed, and store.

        Args:
            db: Database session.
            document_id: ID of the document to process.

        Returns:
            Number of chunks created.
        """
        document = await self.doc_repo.get_by_id(db, document_id)
        if not document:
            raise NotFoundError(f"Document {document_id} not found")

        # Update status to processing
        await self.doc_repo.update(
            db,
            document_id,
            {"status": DocumentStatusEnum.PROCESSING},
        )

        try:
            # Extract text based on source type
            source_type = getattr(document, "source_type", "file")
            text = ""

            if source_type == "url":
                text = await self._fetch_url_content(
                    getattr(document, "source_url", "")
                )
                chunks = chunking_service.chunk_html(text) if "<" in text else chunking_service.chunk_text(text)
            elif source_type == "file":
                file_path = getattr(document, "file_path", "")
                if file_path.endswith(".pdf"):
                    chunks = chunking_service.chunk_pdf(file_path)
                elif file_path.endswith((".html", ".htm")):
                    with open(file_path, "r", encoding="utf-8") as f:
                        html_content = f.read()
                    chunks = chunking_service.chunk_html(html_content)
                else:
                    with open(file_path, "r", encoding="utf-8") as f:
                        text = f.read()
                    chunks = chunking_service.chunk_text(text)
            else:
                # Raw text passed as source
                text = getattr(document, "content", "") or ""
                chunks = chunking_service.chunk_text(text)

            if not chunks:
                logger.warning("no_chunks_created", document_id=document_id)
                await self.doc_repo.update(
                    db,
                    document_id,
                    {"status": DocumentStatusEnum.READY, "chunk_count": 0},
                )
                return 0

            # Generate embeddings in batch
            chunk_texts = [c.text for c in chunks]
            embeddings = await embedding_service.embed_batch(chunk_texts)

            # Store chunks with embeddings
            chunk_records = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_id = str(uuid.uuid4())
                chunk_records.append(
                    {
                        "id": chunk_id,
                        "document_id": document_id,
                        "tenant_id": getattr(document, "tenant_id", ""),
                        "content": chunk.text,
                        "embedding": embedding,
                        "chunk_index": i,
                        "metadata_": {
                            **chunk.metadata,
                            "content_hash": chunk.content_hash,
                        },
                        "created_at": datetime.now(timezone.utc),
                    }
                )

            await self.chunk_repo.bulk_create(db, chunk_records)

            # Update document status
            await self.doc_repo.update(
                db,
                document_id,
                {
                    "status": DocumentStatusEnum.READY,
                    "chunk_count": len(chunk_records),
                    "processed_at": datetime.now(timezone.utc),
                },
            )

            logger.info(
                "document_processed",
                document_id=document_id,
                num_chunks=len(chunk_records),
            )
            return len(chunk_records)

        except Exception as e:
            logger.error(
                "document_processing_failed",
                document_id=document_id,
                error=str(e),
            )
            await self.doc_repo.update(
                db,
                document_id,
                {
                    "status": DocumentStatusEnum.FAILED,
                    "error_message": str(e),
                },
            )
            raise

    async def _fetch_url_content(self, url: str) -> str:
        """Fetch content from a URL.

        Args:
            url: The URL to fetch.

        Returns:
            The response text content.
        """
        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text


ingestion_service = IngestionService()
