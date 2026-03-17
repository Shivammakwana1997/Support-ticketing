"""Sentiment analysis service using OpenAI chat completions."""

from __future__ import annotations

import json
from typing import Any

import structlog

from integrations.openai_client import openai_client

logger = structlog.get_logger(__name__)

VALID_SENTIMENTS = ("positive", "negative", "neutral", "mixed")
VALID_URGENCIES = ("low", "medium", "high", "critical")

SYSTEM_PROMPT = (
    "You are a sentiment analysis engine for a customer support system. "
    "Analyze the customer message and return a JSON object with exactly three keys:\n"
    '  "sentiment": one of "positive", "negative", "neutral", "mixed"\n'
    '  "score": a float from -1.0 (most negative) to 1.0 (most positive)\n'
    '  "urgency": one of "low", "medium", "high", "critical"\n\n'
    "Urgency guidelines:\n"
    "  - critical: customer threatens legal action, churn, or reports a service outage\n"
    "  - high: customer is clearly frustrated or the issue blocks their work\n"
    "  - medium: customer is dissatisfied but patient\n"
    "  - low: neutral or positive inquiry\n\n"
    "Return ONLY the JSON object with no surrounding text."
)


class SentimentService:
    """Analyze sentiment and urgency of customer messages via OpenAI."""

    async def analyze_sentiment(self, text: str) -> dict[str, Any]:
        """Analyze sentiment and urgency for a customer message.

        Args:
            text: The raw customer message.

        Returns:
            A dict with keys ``sentiment`` (str), ``score`` (float), and
            ``urgency`` (str).

        Raises:
            ValueError: If the model returns an invalid sentiment or urgency value.
            RuntimeError: If the OpenAI call fails or returns unparseable output.
        """
        log = logger.bind(text_length=len(text))
        log.info("sentiment_analysis.started")

        try:
            response = await openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
            )
        except Exception:
            log.exception("sentiment_analysis.openai_call_failed")
            raise RuntimeError("Failed to call OpenAI for sentiment analysis")

        raw_content = response.choices[0].message.content
        if not raw_content:
            log.error("sentiment_analysis.empty_response")
            raise RuntimeError("OpenAI returned an empty response")

        try:
            result: dict[str, Any] = json.loads(raw_content)
        except (json.JSONDecodeError, TypeError) as exc:
            log.error("sentiment_analysis.json_parse_failed", raw=raw_content)
            raise RuntimeError("Failed to parse sentiment response JSON") from exc

        sentiment = result.get("sentiment", "")
        if sentiment not in VALID_SENTIMENTS:
            log.warning("sentiment_analysis.invalid_sentiment", sentiment=sentiment)
            raise ValueError(f"Invalid sentiment value: {sentiment}")

        score = float(result.get("score", 0.0))
        score = max(-1.0, min(1.0, score))

        urgency = result.get("urgency", "")
        if urgency not in VALID_URGENCIES:
            log.warning("sentiment_analysis.invalid_urgency", urgency=urgency)
            raise ValueError(f"Invalid urgency value: {urgency}")

        log.info(
            "sentiment_analysis.completed",
            sentiment=sentiment,
            score=score,
            urgency=urgency,
        )
        return {
            "sentiment": sentiment,
            "score": score,
            "urgency": urgency,
        }


sentiment_service = SentimentService()
