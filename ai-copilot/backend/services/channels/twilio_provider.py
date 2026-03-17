from __future__ import annotations

import structlog
from twilio.request_validator import RequestValidator

from core.config import settings
from integrations.twilio_client import twilio_client
from services.channels.base import ChannelProvider

logger = structlog.get_logger(__name__)


class TwilioChannelProvider(ChannelProvider):
    """Channel provider for Twilio SMS and WhatsApp messaging."""

    def __init__(self) -> None:
        self.account_sid: str = settings.TWILIO_ACCOUNT_SID
        self.auth_token: str = settings.TWILIO_AUTH_TOKEN
        self.phone_number: str = settings.TWILIO_PHONE_NUMBER
        self._request_validator = RequestValidator(self.auth_token)

    @property
    def channel(self) -> str:
        """Return the active channel type based on the configured phone number.

        Twilio WhatsApp numbers are prefixed with ``whatsapp:``.
        """
        if self.phone_number.startswith("whatsapp:"):
            return "whatsapp"
        return "sms"

    async def send_message(
        self,
        recipient: str,
        content: str,
        metadata: dict | None = None,
    ) -> dict:
        """Send an SMS or WhatsApp message via Twilio.

        Args:
            recipient: The recipient phone number (E.164 format).  For WhatsApp
                messages, prefix with ``whatsapp:``.
            content: The text body of the message.
            metadata: Optional dict.  Supported keys:
                - ``media_url`` (str | list[str]): MMS/WhatsApp media URLs.

        Returns:
            A dict with ``message_id`` and ``status``.
        """
        metadata = metadata or {}
        log = logger.bind(recipient=recipient, channel=self.channel)

        try:
            send_kwargs: dict = {
                "to": recipient,
                "from_": self.phone_number,
                "body": content,
            }

            media_url = metadata.get("media_url")
            if media_url:
                if isinstance(media_url, str):
                    media_url = [media_url]
                send_kwargs["media_url"] = media_url

            message = await twilio_client.messages.create_async(**send_kwargs)

            log.info(
                "twilio_message_sent",
                message_sid=message.sid,
                status=message.status,
            )

            return {
                "message_id": message.sid,
                "status": message.status,
                "channel": self.channel,
            }

        except Exception:
            log.exception("twilio_send_message_failed")
            raise

    async def receive_message(self, raw_payload: dict) -> dict:
        """Normalize an inbound Twilio webhook payload.

        Args:
            raw_payload: The form-encoded Twilio webhook data parsed as a dict.

        Returns:
            Normalized message dict.
        """
        sender = raw_payload.get("From", "")
        body = raw_payload.get("Body", "")
        message_sid = raw_payload.get("MessageSid", "")
        to = raw_payload.get("To", "")
        num_media = int(raw_payload.get("NumMedia", "0"))

        media_items: list[dict] = []
        for i in range(num_media):
            media_items.append(
                {
                    "url": raw_payload.get(f"MediaUrl{i}", ""),
                    "content_type": raw_payload.get(f"MediaContentType{i}", ""),
                }
            )

        # Determine channel from sender prefix
        channel = "whatsapp" if sender.startswith("whatsapp:") else "sms"

        normalized: dict = {
            "sender": sender,
            "content": body,
            "channel": channel,
            "metadata": {
                "message_sid": message_sid,
                "to": to,
                "media": media_items,
                "raw_from": sender,
            },
        }

        logger.info(
            "twilio_message_received",
            sender=sender,
            channel=channel,
            message_sid=message_sid,
        )

        return normalized

    async def validate_webhook(
        self,
        request_data: dict,
        signature: str,
    ) -> bool:
        """Validate a Twilio webhook request signature.

        Uses Twilio's ``RequestValidator`` to verify the ``X-Twilio-Signature``
        header against the request URL and POST parameters.

        Args:
            request_data: Must contain ``"url"`` (the full webhook URL) and
                ``"params"`` (the POST body parameters as a dict).
            signature: The value of the ``X-Twilio-Signature`` header.

        Returns:
            ``True`` if the signature is valid.
        """
        url: str = request_data.get("url", "")
        params: dict = request_data.get("params", {})

        is_valid = self._request_validator.validate(url, params, signature)

        if not is_valid:
            logger.warning(
                "twilio_webhook_validation_failed",
                url=url,
            )

        return is_valid
