from __future__ import annotations

import hashlib
import hmac

import structlog

from core.config import settings
from integrations.email_client import email_client
from services.channels.base import ChannelProvider

logger = structlog.get_logger(__name__)


class EmailChannelProvider(ChannelProvider):
    """Channel provider for transactional email via SendGrid."""

    def __init__(self) -> None:
        self.api_key: str = settings.SENDGRID_API_KEY
        self.from_email: str = settings.FROM_EMAIL

    async def send_message(
        self,
        recipient: str,
        content: str,
        metadata: dict | None = None,
    ) -> dict:
        """Send an email message via SendGrid.

        Args:
            recipient: The destination email address.
            content: Plain-text email body.
            metadata: Optional dict.  Supported keys:
                - ``subject`` (str): Email subject line.  Defaults to
                  ``"Support Notification"``.
                - ``html_content`` (str): HTML version of the email body.
                - ``attachments`` (list[dict]): List of attachment dicts, each
                  containing ``filename``, ``content`` (base64), and ``type``.
                - ``reply_to`` (str): Reply-to email address.
                - ``cc`` (list[str]): CC recipients.
                - ``bcc`` (list[str]): BCC recipients.

        Returns:
            A dict with ``message_id`` and ``status``.
        """
        metadata = metadata or {}
        subject = metadata.get("subject", "Support Notification")
        html_content = metadata.get("html_content")
        attachments = metadata.get("attachments")
        reply_to = metadata.get("reply_to")
        cc = metadata.get("cc")
        bcc = metadata.get("bcc")

        log = logger.bind(recipient=recipient, subject=subject)

        try:
            send_kwargs: dict = {
                "from_email": self.from_email,
                "to_email": recipient,
                "subject": subject,
                "plain_text_content": content,
            }

            if html_content:
                send_kwargs["html_content"] = html_content
            if attachments:
                send_kwargs["attachments"] = attachments
            if reply_to:
                send_kwargs["reply_to"] = reply_to
            if cc:
                send_kwargs["cc"] = cc
            if bcc:
                send_kwargs["bcc"] = bcc

            response = await email_client.send(**send_kwargs)

            message_id = response.get("message_id", "")
            status = response.get("status", "sent")

            log.info(
                "email_message_sent",
                message_id=message_id,
                status=status,
            )

            return {
                "message_id": message_id,
                "status": status,
                "channel": "email",
            }

        except Exception:
            log.exception("email_send_message_failed")
            raise

    async def receive_message(self, raw_payload: dict) -> dict:
        """Normalize an inbound SendGrid Inbound Parse webhook payload.

        Args:
            raw_payload: The parsed webhook body from SendGrid's Inbound Parse.

        Returns:
            Normalized message dict.
        """
        sender = raw_payload.get("from", raw_payload.get("sender", ""))
        to = raw_payload.get("to", "")
        subject = raw_payload.get("subject", "")
        text_body = raw_payload.get("text", "")
        html_body = raw_payload.get("html", "")
        envelope = raw_payload.get("envelope", {})
        attachments_count = int(raw_payload.get("attachments", 0))
        spam_score = raw_payload.get("spam_score", "")
        message_id = raw_payload.get("message_id", "")

        normalized: dict = {
            "sender": sender,
            "content": text_body,
            "channel": "email",
            "metadata": {
                "to": to,
                "subject": subject,
                "html_body": html_body,
                "envelope": envelope,
                "attachments_count": attachments_count,
                "spam_score": spam_score,
                "message_id": message_id,
            },
        }

        logger.info(
            "email_message_received",
            sender=sender,
            subject=subject,
            to=to,
        )

        return normalized

    async def validate_webhook(
        self,
        request_data: dict,
        signature: str,
    ) -> bool:
        """Validate an inbound SendGrid webhook request.

        Performs basic validation by checking the presence of required fields
        and optionally verifying the SendGrid Event Webhook signature if a
        verification key is configured.

        Args:
            request_data: The webhook request data.  May contain a
                ``"verification_key"`` for HMAC-based validation, along with
                ``"timestamp"`` and ``"payload"`` used to compute the digest.
            signature: The signature header from the request.

        Returns:
            ``True`` if the request passes validation.
        """
        # Require minimum expected fields
        required_fields = ("from", "to", "subject")
        payload = request_data.get("payload", request_data)
        if not all(payload.get(field) for field in required_fields):
            logger.warning(
                "email_webhook_missing_required_fields",
                present_fields=list(payload.keys()),
            )
            return False

        # If a verification key is available, perform HMAC validation
        verification_key = request_data.get("verification_key", "")
        if verification_key and signature:
            timestamp = request_data.get("timestamp", "")
            token = request_data.get("token", "")
            verification_payload = f"{timestamp}{token}"

            expected = hmac.new(
                verification_key.encode("utf-8"),
                verification_payload.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

            is_valid = hmac.compare_digest(expected, signature)

            if not is_valid:
                logger.warning("email_webhook_signature_mismatch")
                return False

        return True
