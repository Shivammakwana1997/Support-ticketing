from __future__ import annotations

from typing import Any

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, Content, Email, To

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


class EmailClient:
    def __init__(self) -> None:
        self._client: SendGridAPIClient | None = None

    @property
    def client(self) -> SendGridAPIClient:
        if self._client is None:
            self._client = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        return self._client

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        *,
        html: bool = False,
        from_email: str | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> str:
        from_addr = from_email or settings.EMAIL_FROM
        logger.info("Sending email", extra={"extra_fields": {"to": to, "subject": subject}})

        message = Mail(
            from_email=Email(from_addr),
            to_emails=To(to),
            subject=subject,
        )
        if html:
            message.content = Content("text/html", body)
        else:
            message.content = Content("text/plain", body)

        if attachments:
            for att in attachments:
                attachment = Attachment()
                attachment.file_content = att.get("content", "")
                attachment.file_type = att.get("type", "application/octet-stream")
                attachment.file_name = att.get("filename", "attachment")
                attachment.disposition = att.get("disposition", "attachment")
                message.add_attachment(attachment)

        response = self.client.send(message)
        logger.info(
            "Email sent",
            extra={"extra_fields": {"status_code": response.status_code}},
        )
        return str(response.status_code)

    @staticmethod
    def parse_inbound(payload: dict[str, Any]) -> dict[str, Any]:
        """Parse inbound email webhook payload into normalized format."""
        return {
            "from_email": payload.get("from", payload.get("from_email", "")),
            "to": payload.get("to", ""),
            "subject": payload.get("subject", ""),
            "text": payload.get("text", ""),
            "html": payload.get("html", ""),
            "attachments": payload.get("attachments", []),
        }


email_client = EmailClient()
