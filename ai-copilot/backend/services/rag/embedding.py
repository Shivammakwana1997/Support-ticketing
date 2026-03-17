"""Embedding service using OpenAI API."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from integrations.openai_client import openai_client
from core.config import settings

if TYPE_CHECKING:
    pass

logger = structlog.get_logger(__name__)

DEFAULT_MODEL = "text-embedding-3-small"
MAX_BATCH_SIZE = 100


class EmbeddingService:
    """Service for generating text embeddings via OpenAI."""

    def __init__(self, model: str | None = None):
        self.model = model or getattr(settings, "EMBEDDING_MODEL", DEFAULT_MODEL)

    async def embed_text(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text.

        Args:
            text: The input text to embed.

        Returns:
            A list of floats representing the embedding vector.
        """
        if not text or not text.strip():
            logger.warning("embed_empty_text")
            return []

        try:
            response = await openai_client.create_embedding(
                input=text.strip(),
                model=self.model,
            )
            vector = response.data[0].embedding
            logger.debug(
                "embedded_text",
                text_length=len(text),
                vector_dim=len(vector),
            )
            return vector
        except Exception as e:
            logger.error("embedding_failed", error=str(e), text_length=len(text))
            raise

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts.

        Args:
            texts: List of input texts to embed.

        Returns:
            List of embedding vectors, one per input text.
        """
        if not texts:
            return []

        # Filter empty strings but track positions
        cleaned: list[tuple[int, str]] = [
            (i, t.strip()) for i, t in enumerate(texts) if t and t.strip()
        ]

        if not cleaned:
            return [[] for _ in texts]

        all_vectors: dict[int, list[float]] = {}

        # Process in batches
        for batch_start in range(0, len(cleaned), MAX_BATCH_SIZE):
            batch = cleaned[batch_start:batch_start + MAX_BATCH_SIZE]
            batch_texts = [t for _, t in batch]
            batch_indices = [i for i, _ in batch]

            try:
                response = await openai_client.create_embedding(
                    input=batch_texts,
                    model=self.model,
                )
                for j, embedding_data in enumerate(response.data):
                    original_idx = batch_indices[j]
                    all_vectors[original_idx] = embedding_data.embedding
            except Exception as e:
                logger.error(
                    "batch_embedding_failed",
                    error=str(e),
                    batch_size=len(batch_texts),
                )
                raise

        # Reconstruct results in original order
        results: list[list[float]] = []
        for i in range(len(texts)):
            results.append(all_vectors.get(i, []))

        logger.info(
            "batch_embedded",
            total_texts=len(texts),
            embedded_count=len(all_vectors),
        )
        return results


embedding_service = EmbeddingService()
