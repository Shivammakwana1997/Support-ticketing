from __future__ import annotations

import hmac
import hashlib
from urllib.parse import urlencode

from twilio.rest import Client as TwilioSDKClient

from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)


class TwilioClient:
    def __init__(self) -> None:
        self._client: TwilioSDKClient | None = None

    @property
    def client(self) -> TwilioSDKClient:
        if self._client is None:
            self._client = TwilioSDKClient(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN,
            )
        return self._client

    async def send_sms(self, to: str, body: str) -> str:
        logger.info("Sending SMS", extra={"extra_fields": {"to": to}})
        message = self.client.messages.create(
            body=body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to,
        )
        logger.info("SMS sent", extra={"extra_fields": {"sid": message.sid}})
        return message.sid

    async def send_whatsapp(self, to: str, body: str) -> str:
        logger.info("Sending WhatsApp message", extra={"extra_fields": {"to": to}})
        message = self.client.messages.create(
            body=body,
            from_=f"whatsapp:{settings.TWILIO_PHONE_NUMBER}",
            to=f"whatsapp:{to}",
        )
        logger.info("WhatsApp sent", extra={"extra_fields": {"sid": message.sid}})
        return message.sid

    def validate_webhook_signature(
        self, url: str, params: dict[str, str], signature: str
    ) -> bool:
        """Validate Twilio webhook signature."""
        sorted_params = urlencode(sorted(params.items()))
        data = url + sorted_params
        expected = hmac.new(
            settings.TWILIO_AUTH_TOKEN.encode("utf-8"),
            data.encode("utf-8"),
            hashlib.sha1,
        ).digest()
        import base64
        expected_sig = base64.b64encode(expected).decode("utf-8")
        return hmac.compare_digest(expected_sig, signature)


twilio_client = TwilioClient()
