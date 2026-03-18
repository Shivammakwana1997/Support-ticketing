"""Intent detection service using OpenAI function calling."""

from __future__ import annotations

import json
from typing import Any

import structlog

from integrations.openai_client import openai_client

logger = structlog.get_logger(__name__)

VALID_INTENTS = [
    "fraud",
    "otp_issue",
    "password_reset",
    "technical",
    "general",
    "billing_inquiry",
]

INTENT_FUNCTION_SCHEMA: dict[str, Any] = {
    "name": "classify_intent",
    "description": (
        "Classify the customer message intent, confidence score, "
        "and extract relevant entities."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "enum": VALID_INTENTS,
                "description": "The detected customer intent.",
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Confidence score between 0 and 1.",
            },
            "entities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "description": "Entity type (e.g. order_id, product, date).",
                        },
                        "value": {
                            "type": "string",
                            "description": "Extracted entity value.",
                        },
                    },
                    "required": ["type", "value"],
                },
                "description": "Entities extracted from the message.",
            },
        },
        "required": ["intent", "confidence", "entities"],
    },
}

SYSTEM_PROMPT = (
    "You are an intent-classification engine for a customer support system. "
    "Analyze the customer message and classify it into exactly one intent. "
    "Extract any relevant entities such as order IDs, product names, dates, "
    "or account identifiers. Provide a confidence score reflecting how certain "
    "you are about the classification."
)


class IntentService:
    """Detect customer intent from free-text messages via OpenAI function calling."""

    async def detect_intent(self, text: str) -> dict[str, Any]:
        """Detect the intent of a customer message.

        Args:
            text: The raw customer message.

        Returns:
            A dict with keys ``intent`` (str), ``confidence`` (float),
            and ``entities`` (list of dicts with ``type`` and ``value``).

        Raises:
            ValueError: If the model returns an unrecognised intent.
            RuntimeError: If the OpenAI call fails or returns an unexpected shape.
        """
        log = logger.bind(text_length=len(text))
        log.info("intent_detection.started")

        try:
            response = await openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                functions=[INTENT_FUNCTION_SCHEMA],
                function_call={"name": "classify_intent"},
                temperature=0.0,
            )
        except Exception:
            log.exception("intent_detection.openai_call_failed")
            raise RuntimeError("Failed to call OpenAI for intent detection")

        choice = response.choices[0]
        if not choice.message.function_call:
            log.error("intent_detection.no_function_call_in_response")
            raise RuntimeError(
                "OpenAI response did not include the expected function call"
            )

        try:
            result: dict[str, Any] = json.loads(choice.message.function_call.arguments)
        except (json.JSONDecodeError, TypeError) as exc:
            log.error(
                "intent_detection.json_parse_failed",
                raw=choice.message.function_call.arguments,
            )
            raise RuntimeError("Failed to parse function call arguments") from exc

        intent = result.get("intent", "")
        if intent not in VALID_INTENTS:
            log.warning("intent_detection.invalid_intent", intent=intent)
            raise ValueError(f"Unrecognised intent returned by model: {intent}")

        confidence = float(result.get("confidence", 0.0))
        entities = result.get("entities", [])

        log.info(
            "intent_detection.completed",
            intent=intent,
            confidence=confidence,
            entity_count=len(entities),
        )
        return {
            "intent": intent,
            "confidence": confidence,
            "entities": entities,
        }


intent_service = IntentService()
