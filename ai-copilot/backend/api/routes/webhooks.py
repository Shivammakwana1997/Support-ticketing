"""Webhook endpoints for external service integrations."""

from __future__ import annotations

import hashlib
import hmac
import time

import structlog
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.database import get_db
from core.config import settings
from models.enums import ChannelType, SenderType
from services.conversation import conversation_service

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


@router.post("/twilio")
async def twilio_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Handle inbound Twilio messages (SMS/WhatsApp).

    Validates the Twilio signature, parses the message,
    and creates or updates a conversation with the message.
    """
    try:
        # Parse form data from Twilio
        form_data = await request.form()
        body = dict(form_data)

        # Validate Twilio signature
        signature = request.headers.get("X-Twilio-Signature", "")
        if settings.TWILIO_AUTH_TOKEN and signature:
            try:
                from services.channels.twilio_provider import TwilioChannelProvider

                provider = TwilioChannelProvider()
                url = str(request.url)
                is_valid = await provider.validate_webhook(
                    {"url": url, "params": body},
                    signature,
                )
                if not is_valid:
                    logger.warning("twilio_invalid_signature")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Invalid signature",
                    )
            except ImportError:
                logger.warning("twilio_validation_skipped")

        # Extract message data
        from_number = body.get("From", "")
        to_number = body.get("To", "")
        message_body = body.get("Body", "")
        message_sid = body.get("MessageSid", "")

        # Determine channel
        channel = ChannelType.WHATSAPP if "whatsapp:" in from_number else ChannelType.SMS
        clean_from = from_number.replace("whatsapp:", "")

        if not message_body:
            return {"status": "ignored", "reason": "empty message"}

        # Find or create conversation for this sender
        # Use tenant from config or a default tenant for inbound
        tenant_id = getattr(settings, "DEFAULT_TENANT_ID", "default")

        # Look up customer by phone number
        try:
            from repositories.customer import CustomerRepository

            customer_repo = CustomerRepository()
            customer = await customer_repo.get_by_phone(db, tenant_id, clean_from)
            customer_id = str(customer.id) if customer else clean_from
        except Exception:
            customer_id = clean_from

        # Find existing open conversation or create new one
        try:
            from repositories.conversation import ConversationRepository

            conv_repo = ConversationRepository()
            existing = await conv_repo.find_open_by_customer(
                db,
                tenant_id=tenant_id,
                customer_id=customer_id,
                channel=channel,
            )

            if existing:
                conversation_id = str(existing.id)
            else:
                conv = await conversation_service.create_conversation(
                    db=db,
                    tenant_id=tenant_id,
                    customer_id=customer_id,
                    channel=channel,
                    metadata={"source_phone": clean_from, "destination_phone": to_number},
                )
                conversation_id = str(conv.id) if hasattr(conv, "id") else str(conv)
        except Exception as e:
            logger.error("twilio_conversation_lookup_failed", error=str(e))
            raise

        # Add message to conversation
        await conversation_service.add_message(
            db=db,
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            sender_type=SenderType.CUSTOMER,
            sender_id=customer_id,
            content=message_body,
            channel=channel,
        )

        logger.info(
            "twilio_message_received",
            channel=channel.value if hasattr(channel, "value") else str(channel),
            from_number=clean_from,
            message_sid=message_sid,
            conversation_id=conversation_id,
        )

        # Return TwiML response
        return {
            "status": "received",
            "conversation_id": conversation_id,
            "message_sid": message_sid,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("twilio_webhook_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed",
        )


@router.post("/email")
async def email_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Handle inbound email webhooks (SendGrid Inbound Parse).

    Parses the inbound email, creates a ticket, and starts a conversation.
    """
    try:
        form_data = await request.form()
        body = dict(form_data)

        from_email = body.get("from", body.get("sender", ""))
        to_email = body.get("to", "")
        subject = body.get("subject", "No Subject")
        text_body = body.get("text", "")
        html_body = body.get("html", "")

        content = text_body or html_body
        if not content and not subject:
            return {"status": "ignored", "reason": "empty email"}

        tenant_id = getattr(settings, "DEFAULT_TENANT_ID", "default")

        # Look up or create customer
        try:
            from repositories.customer import CustomerRepository

            customer_repo = CustomerRepository()
            customer = await customer_repo.get_by_email(db, tenant_id, from_email)
            customer_id = str(customer.id) if customer else from_email
        except Exception:
            customer_id = from_email

        # Create conversation
        conv = await conversation_service.create_conversation(
            db=db,
            tenant_id=tenant_id,
            customer_id=customer_id,
            channel=ChannelType.EMAIL,
            metadata={"from_email": from_email, "to_email": to_email, "subject": subject},
        )
        conversation_id = str(conv.id) if hasattr(conv, "id") else str(conv)

        # Add message
        await conversation_service.add_message(
            db=db,
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            sender_type=SenderType.CUSTOMER,
            sender_id=customer_id,
            content=content,
            channel=ChannelType.EMAIL,
        )

        # Create ticket from email
        try:
            from services.ticketing import ticketing_service

            ticket = await ticketing_service.create_ticket(
                db=db,
                tenant_id=tenant_id,
                customer_id=customer_id,
                subject=subject,
                description=content[:1000] if content else "",
                conversation_id=conversation_id,
            )
            ticket_id = str(ticket.id) if hasattr(ticket, "id") else None
        except Exception as e:
            logger.warning("email_ticket_creation_failed", error=str(e))
            ticket_id = None

        logger.info(
            "email_received",
            from_email=from_email,
            subject=subject,
            conversation_id=conversation_id,
            ticket_id=ticket_id,
        )

        return {
            "status": "received",
            "conversation_id": conversation_id,
            "ticket_id": ticket_id,
        }

    except Exception as e:
        logger.error("email_webhook_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email webhook processing failed",
        )


@router.post("/slack")
async def slack_webhook(
    request: Request,
    x_slack_signature: str = Header("", alias="X-Slack-Signature"),
    x_slack_request_timestamp: str = Header("", alias="X-Slack-Request-Timestamp"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Handle Slack event webhooks.

    Validates the Slack signing secret, processes events, and routes messages.
    """
    try:
        raw_body = await request.body()
        body_str = raw_body.decode("utf-8")

        # Validate Slack signature
        signing_secret = getattr(settings, "SLACK_SIGNING_SECRET", "")
        if signing_secret and x_slack_signature:
            timestamp = x_slack_request_timestamp

            # Prevent replay attacks (5 min window)
            if abs(time.time() - float(timestamp)) > 300:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Request timestamp too old",
                )

            sig_basestring = f"v0:{timestamp}:{body_str}"
            computed = "v0=" + hmac.new(
                signing_secret.encode(),
                sig_basestring.encode(),
                hashlib.sha256,
            ).hexdigest()

            if not hmac.compare_digest(computed, x_slack_signature):
                logger.warning("slack_invalid_signature")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid signature",
                )

        import json
        data = json.loads(body_str)

        # Handle URL verification challenge
        if data.get("type") == "url_verification":
            return {"challenge": data.get("challenge", "")}

        # Handle event callback
        if data.get("type") == "event_callback":
            event = data.get("event", {})
            event_type = event.get("type", "")

            if event_type == "message" and not event.get("bot_id"):
                user_id = event.get("user", "")
                text = event.get("text", "")
                channel_id = event.get("channel", "")

                if text:
                    tenant_id = getattr(settings, "DEFAULT_TENANT_ID", "default")

                    # Create or find conversation
                    try:
                        from repositories.conversation import ConversationRepository

                        conv_repo = ConversationRepository()
                        existing = await conv_repo.find_open_by_customer(
                            db,
                            tenant_id=tenant_id,
                            customer_id=user_id,
                            channel=ChannelType.SLACK,
                        )

                        if existing:
                            conversation_id = str(existing.id)
                        else:
                            conv = await conversation_service.create_conversation(
                                db=db,
                                tenant_id=tenant_id,
                                customer_id=user_id,
                                channel=ChannelType.SLACK,
                                metadata={"slack_channel": channel_id, "slack_user": user_id},
                            )
                            conversation_id = str(conv.id) if hasattr(conv, "id") else str(conv)
                    except Exception as e:
                        logger.error("slack_conversation_lookup_failed", error=str(e))
                        return {"status": "error"}

                    # Add message
                    await conversation_service.add_message(
                        db=db,
                        tenant_id=tenant_id,
                        conversation_id=conversation_id,
                        sender_type=SenderType.CUSTOMER,
                        sender_id=user_id,
                        content=text,
                        channel=ChannelType.SLACK,
                    )

                    logger.info(
                        "slack_message_received",
                        user_id=user_id,
                        channel_id=channel_id,
                        conversation_id=conversation_id,
                    )

            return {"status": "ok"}

        return {"status": "ignored"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("slack_webhook_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Slack webhook processing failed",
        )


@router.post("/teams")
async def teams_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Handle Microsoft Teams webhook events."""
    try:
        data = await request.json()

        event_type = data.get("type", "")

        # Handle Teams Bot Framework messages
        if event_type == "message":
            text = data.get("text", "")
            from_user = data.get("from", {})
            user_id = from_user.get("id", "")
            user_name = from_user.get("name", "")
            conversation_info = data.get("conversation", {})
            conv_id_teams = conversation_info.get("id", "")

            if text and user_id:
                tenant_id = getattr(settings, "DEFAULT_TENANT_ID", "default")

                conv = await conversation_service.create_conversation(
                    db=db,
                    tenant_id=tenant_id,
                    customer_id=user_id,
                    channel=ChannelType.TEAMS,
                    metadata={
                        "teams_conversation_id": conv_id_teams,
                        "teams_user_name": user_name,
                    },
                )
                conversation_id = str(conv.id) if hasattr(conv, "id") else str(conv)

                await conversation_service.add_message(
                    db=db,
                    tenant_id=tenant_id,
                    conversation_id=conversation_id,
                    sender_type=SenderType.CUSTOMER,
                    sender_id=user_id,
                    content=text,
                    channel=ChannelType.TEAMS,
                )

                logger.info(
                    "teams_message_received",
                    user_id=user_id,
                    conversation_id=conversation_id,
                )

                return {"status": "received", "conversation_id": conversation_id}

        return {"status": "ok"}

    except Exception as e:
        logger.error("teams_webhook_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Teams webhook processing failed",
        )
