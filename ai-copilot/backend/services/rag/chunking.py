"""Document chunking service for RAG pipeline."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    pass

logger = structlog.get_logger(__name__)


@dataclass
class Chunk:
    """Represents a text chunk with metadata."""

    text: str
    index: int
    start_char: int
    end_char: int
    metadata: dict = field(default_factory=dict)

    @property
    def token_estimate(self) -> int:
        return len(self.text.split())

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.text.encode()).hexdigest()


class ChunkingService:
    """Service for splitting documents into chunks for embedding."""

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> list[Chunk]:
        """Split text into overlapping chunks by character count.

        Args:
            text: The input text to chunk.
            chunk_size: Target size of each chunk in characters.
            overlap: Number of overlapping characters between chunks.

        Returns:
            List of Chunk objects with metadata.
        """
        if not text or not text.strip():
            return []

        text = text.strip()
        chunks: list[Chunk] = []
        start = 0
        index = 0

        while start < len(text):
            end = start + chunk_size

            if end < len(text):
                # Try to break at sentence boundary
                search_start = max(start + chunk_size - 100, start)
                search_region = text[search_start:end + 100]
                sentence_ends = list(re.finditer(r'[.!?]\s+', search_region))

                if sentence_ends:
                    best_break = sentence_ends[-1]
                    end = search_start + best_break.end()
                else:
                    # Fall back to word boundary
                    space_pos = text.rfind(' ', start, end + 50)
                    if space_pos > start:
                        end = space_pos + 1

            end = min(end, len(text))
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    Chunk(
                        text=chunk_text,
                        index=index,
                        start_char=start,
                        end_char=end,
                        metadata={
                            "chunk_size": len(chunk_text),
                            "method": "text",
                        },
                    )
                )
                index += 1

            start = end - overlap if end < len(text) else end

        logger.debug(
            "chunked_text",
            num_chunks=len(chunks),
            total_chars=len(text),
            chunk_size=chunk_size,
            overlap=overlap,
        )
        return chunks

    def chunk_pdf(self, file_path: str) -> list[Chunk]:
        """Extract text from a PDF and chunk it.

        Args:
            file_path: Path to the PDF file.

        Returns:
            List of Chunk objects.
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            logger.warning("pymupdf_not_available", fallback="basic_text_extraction")
            # Fallback: try pdfplumber
            try:
                import pdfplumber

                all_text = ""
                with pdfplumber.open(file_path) as pdf:
                    for page_num, page in enumerate(pdf.pages):
                        page_text = page.extract_text() or ""
                        all_text += f"\n--- Page {page_num + 1} ---\n{page_text}"
                return self.chunk_text(all_text)
            except ImportError:
                raise RuntimeError(
                    "No PDF library available. Install pymupdf or pdfplumber."
                )

        all_text = ""
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text()
            all_text += f"\n--- Page {page_num + 1} ---\n{page_text}"
        doc.close()

        chunks = self.chunk_text(all_text)
        for chunk in chunks:
            chunk.metadata["method"] = "pdf"
            chunk.metadata["source_file"] = file_path

        logger.info("chunked_pdf", file_path=file_path, num_chunks=len(chunks))
        return chunks

    def chunk_html(self, html_content: str) -> list[Chunk]:
        """Strip HTML tags and chunk the resulting text.

        Args:
            html_content: Raw HTML content.

        Returns:
            List of Chunk objects.
        """
        # Remove script and style elements
        clean = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
        clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.DOTALL)

        # Replace block-level elements with newlines
        clean = re.sub(r'<(?:br|p|div|h[1-6]|li|tr)[^>]*/?>', '\n', clean, flags=re.IGNORECASE)

        # Remove remaining HTML tags
        clean = re.sub(r'<[^>]+>', '', clean)

        # Decode HTML entities
        try:
            import html
            clean = html.unescape(clean)
        except ImportError:
            pass

        # Normalize whitespace
        clean = re.sub(r'\n{3,}', '\n\n', clean)
        clean = re.sub(r'[ \t]+', ' ', clean)
        clean = clean.strip()

        chunks = self.chunk_text(clean)
        for chunk in chunks:
            chunk.metadata["method"] = "html"

        logger.info("chunked_html", num_chunks=len(chunks), original_len=len(html_content))
        return chunks


chunking_service = ChunkingService()
