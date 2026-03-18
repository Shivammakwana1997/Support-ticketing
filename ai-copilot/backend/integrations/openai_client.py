from __future__ import annotations

import base64
from typing import Any

import openai

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


class OpenAIClient:
    def __init__(self) -> None:
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.embedding_model = settings.OPENAI_EMBEDDING_MODEL

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> str:
        model = model or self.model
        logger.info(
            "OpenAI chat completion request",
            extra={"extra_fields": {"model": model, "message_count": len(messages)}},
        )
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        content = response.choices[0].message.content or ""
        logger.info(
            "OpenAI chat completion response",
            extra={
                "extra_fields": {
                    "model": model,
                    "usage_prompt": response.usage.prompt_tokens if response.usage else 0,
                    "usage_completion": response.usage.completion_tokens if response.usage else 0,
                }
            },
        )
        return content

    async def create_embedding(
        self, text: str | list[str], *, model: str | None = None
    ) -> list[list[float]]:
        model = model or self.embedding_model
        input_text = text if isinstance(text, list) else [text]
        logger.info(
            "OpenAI embedding request",
            extra={"extra_fields": {"model": model, "input_count": len(input_text)}},
        )
        response = await self.client.embeddings.create(model=model, input=input_text)
        return [item.embedding for item in response.data]

    async def transcribe_audio(
        self,
        audio_data: bytes,
        *,
        language: str = "en",
        filename: str = "audio.webm",
    ) -> dict[str, Any]:
        logger.info("OpenAI transcription request", extra={"extra_fields": {"language": language}})
        response = await self.client.audio.transcriptions.create(
            model="whisper-1",
            file=(filename, audio_data),
            language=language,
            response_format="verbose_json",
        )
        return {
            "text": response.text,
            "language": getattr(response, "language", language),
            "duration": getattr(response, "duration", None),
            "segments": getattr(response, "segments", []),
        }

    async def synthesize_speech(
        self,
        text: str,
        *,
        voice: str = "alloy",
        response_format: str = "mp3",
    ) -> bytes:
        logger.info(
            "OpenAI TTS request",
            extra={"extra_fields": {"voice": voice, "text_length": len(text)}},
        )
        response = await self.client.audio.speech.create(
            model="tts-1",
            voice=voice,  # type: ignore[arg-type]
            input=text,
            response_format=response_format,  # type: ignore[arg-type]
        )
        return response.content


# Singleton
openai_client = OpenAIClient()
