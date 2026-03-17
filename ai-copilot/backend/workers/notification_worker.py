"""Notification worker — sends pending notifications via appropriate channels."""

from __future__ import annotations

import asyncio
import json

import structlog

logger = structlog.get_logger(__name__)

QUEUE_KEY = "notifications:queue"
POLL_INTERVAL = 2.0  # seconds


async def send_notification(notification: dict) -> None:
    """Route and send a notification via the appropriate channel."""
    channel = notification.get("channel", "email")
    recipient = notification.get("recipient", "")
    subject = notification.get("subject", "")
    body = notification.get("body", "")
    tenant_id = notification.get("tenant_id", "")

    logger.info(
        "sending_notification",
        channel=channel,
        recipient=recipient,
        tenant_id=tenant_id,
    )

    try:
        if channel == "email":
            from services.channels.email_provider import EmailChannelProvider

            provider = EmailChannelProvider()
            await provider.send_message(
                recipient=recipient,
                content=body,
                metadata={"subject": subject},
            )

        elif channel == "slack":
            from services.channels.slack_provider import SlackChannelProvider

            provider = SlackChannelProvider()
            await provider.send_message(
                recipient=recipient,
                content=body,
            )

        elif channel in ("sms", "whatsapp"):
            from services.channels.twilio_provider import TwilioChannelProvider

            provider = TwilioChannelProvider()
            await provider.send_message(
                recipient=recipient,
                content=body,
                metadata={"channel": channel},
            )

        else:
            logger.warning("unknown_notification_channel", channel=channel)
            return

        logger.info("notification_sent", channel=channel, recipient=recipient)

    except Exception as e:
        logger.error(
            "notification_send_failed",
            channel=channel,
            recipient=recipient,
            error=str(e),
        )


async def run_worker() -> None:
    """Main worker loop — poll Redis for notification jobs."""
    logger.info("notification_worker_starting")

    from integrations.redis_client import redis_client

    while True:
        try:
            result = await redis_client.blpop(QUEUE_KEY, timeout=int(POLL_INTERVAL))

            if result is None:
                continue

            _, raw = result
            notification = json.loads(raw if isinstance(raw, str) else raw.decode("utf-8"))

            await send_notification(notification)

        except asyncio.CancelledError:
            logger.info("notification_worker_cancelled")
            break
        except json.JSONDecodeError as e:
            logger.error("notification_invalid_payload", error=str(e))
        except Exception as e:
            logger.error("notification_worker_error", error=str(e))
            await asyncio.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    asyncio.run(run_worker())
