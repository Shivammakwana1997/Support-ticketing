import asyncio
import os
import tempfile
from collections.abc import AsyncGenerator

import structlog

from integrations.openai_client import openai_client

logger = structlog.get_logger(__name__)

# Minimum bytes to accumulate before sending a streaming transcription chunk.
_STREAM_CHUNK_THRESHOLD = 32_000  # ~2 seconds of 16-bit 8 kHz mono audio


class TranscriptionService:
    """Speech-to-text service backed by the OpenAI Whisper API."""

    async def transcribe(
        self,
        audio_data: bytes,
        format: str = "wav",
        language: str | None = None,
    ) -> dict:
        """Transcribe an audio buffer and return the full result.

        Args:
            audio_data: Raw audio bytes.
            format: Audio file extension / format (e.g. ``"wav"``, ``"mp3"``).
            language: Optional ISO-639-1 language hint for the model.

        Returns:
            A dict with keys ``text``, ``language``, ``duration_seconds``, and
            ``segments``.
        """
        log = logger.bind(audio_bytes=len(audio_data), format=format, language=language)
        log.info("transcription.started")

        tmp_path: str | None = None
        try:
            # Write audio to a temp file so the OpenAI client can read it.
            fd, tmp_path = tempfile.mkstemp(suffix=f".{format}")
            os.write(fd, audio_data)
            os.close(fd)

            with open(tmp_path, "rb") as audio_file:
                kwargs: dict = {
                    "model": "whisper-1",
                    "file": audio_file,
                    "response_format": "verbose_json",
                }
                if language is not None:
                    kwargs["language"] = language

                response = await openai_client.audio.transcriptions.create(**kwargs)

            result: dict = {
                "text": response.text,
                "language": getattr(response, "language", language or "en"),
                "duration_seconds": getattr(response, "duration", 0.0),
                "segments": [
                    {
                        "start": seg.start,
                        "end": seg.end,
                        "text": seg.text,
                    }
                    for seg in getattr(response, "segments", [])
                ],
            }

            log.info(
                "transcription.completed",
                text_length=len(result["text"]),
                duration_seconds=result["duration_seconds"],
            )
            return result

        except Exception:
            log.exception("transcription.failed")
            raise

        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    log.warning("transcription.temp_file_cleanup_failed", path=tmp_path)

    async def transcribe_stream(
        self,
        audio_stream,
    ) -> AsyncGenerator[dict, None]:
        """Incrementally transcribe an async stream of audio chunks.

        The generator collects incoming audio data and periodically sends
        accumulated chunks to the Whisper API, yielding partial transcripts as
        they become available.

        Args:
            audio_stream: An async iterable that yields ``bytes`` chunks.

        Yields:
            Dicts of the form ``{"partial_text": str, "is_final": bool}``.
        """
        log = logger.bind()
        log.info("transcription_stream.started")

        buffer = bytearray()
        full_text_parts: list[str] = []

        try:
            async for chunk in audio_stream:
                buffer.extend(chunk)

                if len(buffer) < _STREAM_CHUNK_THRESHOLD:
                    continue

                # Flush accumulated audio to the transcription endpoint.
                audio_bytes = bytes(buffer)
                buffer.clear()

                try:
                    result = await self.transcribe(audio_bytes)
                    partial = result.get("text", "")
                    if partial:
                        full_text_parts.append(partial)
                        yield {"partial_text": partial, "is_final": False}
                except Exception:
                    log.exception("transcription_stream.chunk_failed")
                    # Skip the failed chunk and continue with the stream.
                    continue

            # Process any remaining audio in the buffer.
            if buffer:
                try:
                    result = await self.transcribe(bytes(buffer))
                    partial = result.get("text", "")
                    if partial:
                        full_text_parts.append(partial)
                except Exception:
                    log.exception("transcription_stream.final_chunk_failed")

            final_text = " ".join(full_text_parts)
            log.info("transcription_stream.completed", text_length=len(final_text))
            yield {"partial_text": final_text, "is_final": True}

        except Exception:
            log.exception("transcription_stream.failed")
            raise


transcription_service = TranscriptionService()
