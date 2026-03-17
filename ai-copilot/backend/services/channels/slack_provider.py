from __future__ import annotations

import hashlib
import hmac
import time

import httpx
import structlog

from core.config import settings
from services.channels.base import ChannelProvider

logger = structlog.get_logger(__name__)

SLACK_API_BASE = "https://slack.com/api"
SLACK_TIMESTAMP_MAX_AGE_SECONDS = 60 * 5  # 5 minutes


class SlackChannelProvider(ChannelProvider):
    """Channel provider for Slack messaging via the Slack Web API."""

    def __init__(self) -> None:
        self.bot_token: str = settings.SLACK_BOT_TOKEN
        self.signing_secret: str = settings.SLACK_SIGNING_SECRET
        self._http_client = httpx.AsyncClient(
            base_url=SLACK_API_BASE,
            headers={
                "Authorization": f"Bearer {self.bot_token}",
                "Content-Type": "application/json; charset=utf-8",
            },
            timeout=httpx.Timeout(30.0),
        )

    async def send_message(
        self,
        recipient: str,
        content: str,
        metadata: dict | None = None,
    ) -> dict:
        """Post a message to a Slack channel or DM.

        Args:
            recipient: A Slack channel ID (e.g. ``C0123ABCDEF``) or user ID
                for a direct message.
            content: The message text (supports Slack mrkdwn formatting).
            metadata: Optional dict.  Supported keys:
                - ``thread_ts`` (str): Reply within a thread.
                - ``blocks`` (list[dict]): Slack Block Kit block elements.
                - ``unfurl_links`` (bool): Whether to unfurl links.
                - ``unfurl_media`` (bool): Whether to unfurl media.

        Returns:
            A dict with ``message_id`` (the ``ts`` value) and ``status``.
        """
        metadata = metadata or {}
        log = logger.bind(recipient=recipient, channel="slack")

        payload: dict = {
            "channel": recipient,
            "text": content,
        }

        if "thread_ts" in metadata:
            payload["thread_ts"] = metadata["thread_ts"]
        if "blocks" in metadata:
            payload["blocks"] = metadata["blocks"]
        if "unfurl_links" in metadata:
            payload["unfurl_links"] = metadata["unfurl_links"]
        if "unfurl_media" in metadata:
            payload["unfurl_media"] = metadata["unfurl_media"]

        try:
            response = await self._http_client.post("/chat.postMessage", json=payload)
            response.raise_for_status()
            data = response.json()

            if not data.get("ok"):
                error = data.get("error", "unknown_error")
                log.error("slack_api_error", error=error)
                return {
                    "message_id": "",
                    "status": "failed",
                    "channel": "slack",
                    "error": error,
                }

            message_ts = data.get("ts", "")
            channel_id = data.get("channel", recipient)

            log.info(
                "slack_message_sent",
                message_ts=message_ts,
                channel_id=channel_id,
            )

            return {
                "message_id": message_ts,
                "status": "sent",
                "channel": "slack",
                "channel_id": channel_id,
            }

        except httpx.HTTPStatusError:
            log.exception("slack_send_http_error")
            raise
        except Exception:
            log.exception("slack_send_message_failed")
            raise

    async def receive_message(self, raw_payload: dict) -> dict:
        """Normalize an inbound Slack Events API payload.

        Handles ``event_callback`` events of type ``message`` and
        ``app_mention``.

        Args:
            raw_payload: The full Slack event wrapper, containing an ``event``
                key with the message details.

        Returns:
            Normalized message dict.
        """
        event: dict = raw_payload.get("event", {})
        event_type = event.get("type", "")
        sender = event.get("user", "")
        text = event.get("text", "")
        channel_id = event.get("channel", "")
        thread_ts = event.get("thread_ts", "")
        event_ts = event.get("ts", "")
        team = raw_payload.get("team_id", "")
        bot_id = event.get("bot_id", "")

        normalized: dict = {
            "sender": sender,
            "content": text,
            "channel": "slack",
            "metadata": {
                "channel_id": channel_id,
                "event_type": event_type,
                "thread_ts": thread_ts,
                "event_ts": event_ts,
                "team_id": team,
                "bot_id": bot_id,
                "raw_event_type": raw_payload.get("type", ""),
            },
        }

        logger.info(
            "slack_message_received",
            sender=sender,
            channel_id=channel_id,
            event_type=event_type,
        )

        return normalized

    async def validate_webhook(
        self,
        request_data: dict,
        signature: str,
    ) -> bool:
        """Validate a Slack webhook request using the signing secret.

        Implements Slack's recommended signature verification flow:
        1. Check that the timestamp is not older than 5 minutes.
        2. Compute ``HMAC-SHA256("v0:{timestamp}:{body}", signing_secret)``.
        3. Compare against the provided ``X-Slack-Signature`` header.

        Args:
            request_data: Must contain:
                - ``"timestamp"`` (str): The ``X-Slack-Request-Timestamp`` header.
                - ``"body"`` (str): The raw request body as a string.
            signature: The ``X-Slack-Signature`` header value (e.g.
                ``v0=abc123...``).

        Returns:
            ``True`` if the signature is valid and the timestamp is fresh.
        """
        timestamp_str = request_data.get("timestamp", "")
        body = request_data.get("body", "")

        # Reject requests with missing data
        if not timestamp_str or not body or not signature:
            logger.warning("slack_webhook_missing_fields")
            return False

        # Guard against replay attacks
        try:
            request_timestamp = int(timestamp_str)
        except (ValueError, TypeError):
            logger.warning("slack_webhook_invalid_timestamp", timestamp=timestamp_str)
            return False

        current_time = int(time.time())
        if abs(current_time - request_timestamp) > SLACK_TIMESTAMP_MAX_AGE_SECONDS:
            logger.warning(
                "slack_webhook_timestamp_too_old",
                request_timestamp=request_timestamp,
                current_time=current_time,
            )
            return False

        # Compute expected signature
        sig_basestring = f"v0:{timestamp_str}:{body}"
        expected_hash = hmac.new(
            self.signing_secret.encode("utf-8"),
            sig_basestring.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        expected_signature = f"v0={expected_hash}"

        is_valid = hmac.compare_digest(expected_signature, signature)

        if not is_valid:
            logger.warning("slack_webhook_signature_mismatch")

        return is_valid

    async def close(self) -> None:
        """Close the underlying HTTP client.

        Should be called during application shutdown to release connection
        pool resources.
        """
        await self._http_client.aclose()
