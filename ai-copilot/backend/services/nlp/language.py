"""Language detection and translation service using OpenAI chat completions."""

from __future__ import annotations

import structlog

from integrations.openai_client import openai_client

logger = structlog.get_logger(__name__)

DETECT_SYSTEM_PROMPT = (
    "You are a language detection engine. "
    "Given a piece of text, respond with ONLY the ISO 639-1 two-letter language "
    'code (e.g. "en", "es", "fr", "de", "ja", "zh"). '
    "Do not include any other text, punctuation, or explanation."
)

TRANSLATE_SYSTEM_PROMPT = (
    "You are a professional translator for a customer support system. "
    "Translate the user message into the target language accurately, "
    "preserving tone and meaning. Return ONLY the translated text with "
    "no additional commentary."
)


class LanguageService:
    """Detect language and translate text via OpenAI."""

    async def detect_language(self, text: str) -> str:
        """Detect the language of the given text.

        Args:
            text: The text whose language should be identified.

        Returns:
            An ISO 639-1 two-letter language code (e.g. ``"en"``).

        Raises:
            RuntimeError: If the OpenAI call fails or returns an invalid code.
        """
        log = logger.bind(text_length=len(text))
        log.info("language_detection.started")

        try:
            response = await openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": DETECT_SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                temperature=0.0,
                max_tokens=10,
            )
        except Exception:
            log.exception("language_detection.openai_call_failed")
            raise RuntimeError("Failed to call OpenAI for language detection")

        raw = (response.choices[0].message.content or "").strip().lower()

        # Validate: must be exactly two ASCII letters (ISO 639-1).
        if len(raw) != 2 or not raw.isalpha():
            log.error("language_detection.invalid_code", raw=raw)
            raise RuntimeError(
                f"OpenAI returned an invalid language code: {raw!r}"
            )

        log.info("language_detection.completed", language=raw)
        return raw

    async def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: str | None = None,
    ) -> str:
        """Translate text into the target language.

        Args:
            text: The text to translate.
            target_lang: ISO 639-1 code of the desired output language.
            source_lang: Optional ISO 639-1 code of the source language.
                If ``None``, the model will auto-detect the source language.

        Returns:
            The translated text.

        Raises:
            RuntimeError: If the OpenAI call fails or returns empty output.
        """
        log = logger.bind(
            text_length=len(text),
            target_lang=target_lang,
            source_lang=source_lang,
        )
        log.info("translation.started")

        source_clause = (
            f" from {source_lang}" if source_lang else ""
        )
        user_prompt = (
            f"Translate the following text{source_clause} to {target_lang}:\n\n{text}"
        )

        try:
            response = await openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": TRANSLATE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
        except Exception:
            log.exception("translation.openai_call_failed")
            raise RuntimeError("Failed to call OpenAI for translation")

        translated = (response.choices[0].message.content or "").strip()
        if not translated:
            log.error("translation.empty_response")
            raise RuntimeError("OpenAI returned an empty translation")

        log.info(
            "translation.completed",
            target_lang=target_lang,
            translated_length=len(translated),
        )
        return translated


language_service = LanguageService()
