import uuid

import structlog

from integrations.openai_client import openai_client
from integrations.s3_client import s3_client

logger = structlog.get_logger(__name__)

# Voices supported by the OpenAI TTS API.
AVAILABLE_VOICES: list[str] = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

# Rough estimate: ~150 words per minute at normal speaking pace, average word
# length ~5 characters.  This gives a very approximate duration for the caller
# to use while the real audio is being streamed / downloaded.
_CHARS_PER_SECOND = 150 * 5 / 60  # ≈ 12.5


class SynthesisService:
    """Text-to-speech service backed by the OpenAI TTS API."""

    async def synthesize(
        self,
        text: str,
        voice: str = "alloy",
        model: str = "tts-1",
        response_format: str = "mp3",
    ) -> dict:
        """Convert *text* to speech and return the raw audio bytes.

        Args:
            text: The text to synthesize.
            voice: One of the :data:`AVAILABLE_VOICES`.
            model: OpenAI TTS model identifier (``"tts-1"`` or ``"tts-1-hd"``).
            response_format: Output audio format (``"mp3"``, ``"opus"``,
                ``"aac"``, ``"flac"``).

        Returns:
            A dict with ``audio_data`` (bytes), ``format`` (str), and
            ``duration_estimate_seconds`` (float).
        """
        log = logger.bind(
            text_length=len(text),
            voice=voice,
            model=model,
            response_format=response_format,
        )
        log.info("synthesis.started")

        if voice not in AVAILABLE_VOICES:
            raise ValueError(
                f"Unsupported voice '{voice}'. Choose from: {', '.join(AVAILABLE_VOICES)}"
            )

        try:
            response = await openai_client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                response_format=response_format,
            )

            audio_data: bytes = await response.aread()

            duration_estimate = len(text) / _CHARS_PER_SECOND if text else 0.0

            result: dict = {
                "audio_data": audio_data,
                "format": response_format,
                "duration_estimate_seconds": round(duration_estimate, 2),
            }

            log.info(
                "synthesis.completed",
                audio_bytes=len(audio_data),
                duration_estimate_seconds=result["duration_estimate_seconds"],
            )
            return result

        except Exception:
            log.exception("synthesis.failed")
            raise

    async def synthesize_to_url(
        self,
        text: str,
        voice: str = "alloy",
    ) -> str:
        """Synthesize speech and upload the resulting audio file to S3.

        Args:
            text: The text to synthesize.
            voice: One of the :data:`AVAILABLE_VOICES`.

        Returns:
            A publicly-accessible URL pointing to the uploaded audio file.
        """
        log = logger.bind(text_length=len(text), voice=voice)
        log.info("synthesis_to_url.started")

        try:
            result = await self.synthesize(text=text, voice=voice)
            audio_data: bytes = result["audio_data"]
            audio_format: str = result["format"]

            object_key = f"voice/synthesis/{uuid.uuid4()}.{audio_format}"

            url: str = await s3_client.upload(
                data=audio_data,
                key=object_key,
                content_type=f"audio/{audio_format}",
            )

            log.info("synthesis_to_url.completed", url=url, audio_bytes=len(audio_data))
            return url

        except Exception:
            log.exception("synthesis_to_url.failed")
            raise


synthesis_service = SynthesisService()
