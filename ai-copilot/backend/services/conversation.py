"""Service layer for conversation management.

Handles business logic for creating, retrieving, updating, and managing
conversations and their associated messages in the AI Customer Support Copilot.
"""

import datetime
import math
import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ForbiddenError, NotFoundError
from models.conversation import Conversation
from models.enums import ChannelType, ConversationStatus, SenderType
from models.message import Message
from repositories.conversation import ConversationRepository
from repositories.message import MessageRepository
from schemas.common import PaginatedResponse
from schemas.conversation import (
    ConversationCreate,
    ConversationListParams,
    ConversationUpdate,
)
from schemas.message import MessageCreate

logger = structlog.get_logger(__name__)


class ConversationService:
    """Service for managing customer support conversations.

    Encapsulates all business logic related to conversations including
    creation, retrieval, updates, message handling, agent assignment,
    and conversation lifecycle management.
    """

    def __init__(self) -> None:
        self.conversation_repo = ConversationRepository()
        self.message_repo = MessageRepository()

    async def create_conversation(
        self,
        db: AsyncSession,
        tenant_id: str,
        customer_id: str,
        channel: ChannelType,
        metadata: dict | None = None,
    ) -> Conversation:
        """Create a new conversation.

        Args:
            db: Async database session.
            tenant_id: Tenant identifier for multi-tenancy isolation.
            customer_id: Identifier of the customer initiating the conversation.
            channel: Communication channel the conversation originated from.
            metadata: Optional additional metadata for the conversation.

        Returns:
            The newly created Conversation instance.

        Raises:
            Exception: If conversation creation fails due to a database error.
        """
        try:
            logger.info(
                "creating_conversation",
                tenant_id=tenant_id,
                customer_id=customer_id,
                channel=channel.value if channel else None,
            )

            conversation_data = ConversationCreate(
                tenant_id=tenant_id,
                customer_id=customer_id,
                channel=channel,
                status=ConversationStatus.OPEN,
                metadata=metadata or {},
            )

            conversation = await self.conversation_repo.create(
                db, conversation_data
            )

            logger.info(
                "conversation_created",
                conversation_id=str(conversation.id),
                tenant_id=tenant_id,
                customer_id=customer_id,
                channel=channel.value if channel else None,
            )

            return conversation

        except Exception:
            logger.exception(
                "conversation_creation_failed",
                tenant_id=tenant_id,
                customer_id=customer_id,
            )
            raise

    async def get_conversation(
        self,
        db: AsyncSession,
        tenant_id: str,
        conversation_id: str,
    ) -> dict:
        """Retrieve a conversation with its messages.

        Args:
            db: Async database session.
            tenant_id: Tenant identifier for access verification.
            conversation_id: Unique identifier of the conversation.

        Returns:
            Dictionary containing the conversation object and its messages.

        Raises:
            NotFoundError: If the conversation does not exist or does not
                belong to the specified tenant.
        """
        try:
            logger.info(
                "getting_conversation",
                tenant_id=tenant_id,
                conversation_id=conversation_id,
            )

            conversation = await self.conversation_repo.get(
                db, conversation_id
            )

            if conversation is None or conversation.tenant_id != tenant_id:
                raise NotFoundError(
                    f"Conversation {conversation_id} not found"
                )

            messages = await self.message_repo.list_by_conversation(
                db, conversation_id
            )

            logger.info(
                "conversation_retrieved",
                conversation_id=conversation_id,
                tenant_id=tenant_id,
                message_count=len(messages),
            )

            return {
                "conversation": conversation,
                "messages": messages,
            }

        except NotFoundError:
            raise
        except Exception:
            logger.exception(
                "conversation_retrieval_failed",
                tenant_id=tenant_id,
                conversation_id=conversation_id,
            )
            raise

    async def list_conversations(
        self,
        db: AsyncSession,
        tenant_id: str,
        status: ConversationStatus | None = None,
        customer_id: str | None = None,
        channel: ChannelType | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """List conversations with filtering and pagination.

        Args:
            db: Async database session.
            tenant_id: Tenant identifier for multi-tenancy isolation.
            status: Optional filter by conversation status.
            customer_id: Optional filter by customer identifier.
            channel: Optional filter by communication channel.
            page: Page number (1-indexed). Defaults to 1.
            page_size: Number of items per page. Defaults to 20.

        Returns:
            PaginatedResponse containing the filtered conversation list,
            total count, and pagination metadata.
        """
        try:
            logger.info(
                "listing_conversations",
                tenant_id=tenant_id,
                status=status.value if status else None,
                customer_id=customer_id,
                channel=channel.value if channel else None,
                page=page,
                page_size=page_size,
            )

            params = ConversationListParams(
                tenant_id=tenant_id,
                status=status,
                customer_id=customer_id,
                channel=channel,
                page=page,
                page_size=page_size,
            )

            items, total = await self.conversation_repo.list_filtered(
                db, params
            )

            pages = math.ceil(total / page_size) if total > 0 else 0

            logger.info(
                "conversations_listed",
                tenant_id=tenant_id,
                total=total,
                page=page,
                pages=pages,
            )

            return PaginatedResponse(
                items=items,
                total=total,
                page=page,
                page_size=page_size,
                pages=pages,
            )

        except Exception:
            logger.exception(
                "conversation_listing_failed",
                tenant_id=tenant_id,
            )
            raise

    async def update_conversation(
        self,
        db: AsyncSession,
        tenant_id: str,
        conversation_id: str,
        data: dict,
    ) -> Conversation:
        """Update conversation fields.

        Args:
            db: Async database session.
            tenant_id: Tenant identifier for access verification.
            conversation_id: Unique identifier of the conversation to update.
            data: Dictionary of fields and their new values.

        Returns:
            The updated Conversation instance.

        Raises:
            NotFoundError: If the conversation does not exist or does not
                belong to the specified tenant.
        """
        try:
            logger.info(
                "updating_conversation",
                tenant_id=tenant_id,
                conversation_id=conversation_id,
                update_fields=list(data.keys()),
            )

            conversation = await self.conversation_repo.get(
                db, conversation_id
            )

            if conversation is None or conversation.tenant_id != tenant_id:
                raise NotFoundError(
                    f"Conversation {conversation_id} not found"
                )

            update_data = ConversationUpdate(**data)
            conversation = await self.conversation_repo.update(
                db, conversation, update_data
            )

            logger.info(
                "conversation_updated",
                conversation_id=conversation_id,
                tenant_id=tenant_id,
                updated_fields=list(data.keys()),
            )

            return conversation

        except NotFoundError:
            raise
        except Exception:
            logger.exception(
                "conversation_update_failed",
                tenant_id=tenant_id,
                conversation_id=conversation_id,
            )
            raise

    async def add_message(
        self,
        db: AsyncSession,
        tenant_id: str,
        conversation_id: str,
        sender_type: SenderType,
        sender_id: str,
        content: str,
        channel: ChannelType | None = None,
    ) -> Message:
        """Add a message to an existing conversation.

        Creates the message record and updates the conversation's
        updated_at and last_message_at timestamps.

        Args:
            db: Async database session.
            tenant_id: Tenant identifier for access verification.
            conversation_id: Identifier of the conversation to add the message to.
            sender_type: Type of the sender (customer, agent, bot, etc.).
            sender_id: Identifier of the message sender.
            content: Text content of the message.
            channel: Optional channel override for the message.

        Returns:
            The newly created Message instance.

        Raises:
            NotFoundError: If the conversation does not exist or does not
                belong to the specified tenant.
        """
        try:
            logger.info(
                "adding_message",
                tenant_id=tenant_id,
                conversation_id=conversation_id,
                sender_type=sender_type.value if sender_type else None,
                sender_id=sender_id,
            )

            conversation = await self.conversation_repo.get(
                db, conversation_id
            )

            if conversation is None or conversation.tenant_id != tenant_id:
                raise NotFoundError(
                    f"Conversation {conversation_id} not found"
                )

            message_data = MessageCreate(
                conversation_id=conversation_id,
                sender_type=sender_type,
                sender_id=sender_id,
                content=content,
                channel=channel,
            )

            message = await self.message_repo.create(db, message_data)

            now = datetime.datetime.now(datetime.timezone.utc)
            update_data = ConversationUpdate(
                updated_at=now,
                last_message_at=now,
            )
            await self.conversation_repo.update(
                db, conversation, update_data
            )

            logger.info(
                "message_added",
                message_id=str(message.id),
                conversation_id=conversation_id,
                tenant_id=tenant_id,
                sender_type=sender_type.value if sender_type else None,
            )

            return message

        except NotFoundError:
            raise
        except Exception:
            logger.exception(
                "message_add_failed",
                tenant_id=tenant_id,
                conversation_id=conversation_id,
            )
            raise

    async def close_conversation(
        self,
        db: AsyncSession,
        tenant_id: str,
        conversation_id: str,
    ) -> Conversation:
        """Close a conversation.

        Sets the conversation status to CLOSED and records the closed_at
        timestamp.

        Args:
            db: Async database session.
            tenant_id: Tenant identifier for access verification.
            conversation_id: Identifier of the conversation to close.

        Returns:
            The updated Conversation instance with CLOSED status.

        Raises:
            NotFoundError: If the conversation does not exist or does not
                belong to the specified tenant.
        """
        try:
            logger.info(
                "closing_conversation",
                tenant_id=tenant_id,
                conversation_id=conversation_id,
            )

            conversation = await self.conversation_repo.get(
                db, conversation_id
            )

            if conversation is None or conversation.tenant_id != tenant_id:
                raise NotFoundError(
                    f"Conversation {conversation_id} not found"
                )

            now = datetime.datetime.now(datetime.timezone.utc)
            update_data = ConversationUpdate(
                status=ConversationStatus.CLOSED,
                closed_at=now,
            )
            conversation = await self.conversation_repo.update(
                db, conversation, update_data
            )

            logger.info(
                "conversation_closed",
                conversation_id=conversation_id,
                tenant_id=tenant_id,
                closed_at=now.isoformat(),
            )

            return conversation

        except NotFoundError:
            raise
        except Exception:
            logger.exception(
                "conversation_close_failed",
                tenant_id=tenant_id,
                conversation_id=conversation_id,
            )
            raise

    async def assign_agent(
        self,
        db: AsyncSession,
        tenant_id: str,
        conversation_id: str,
        agent_id: str,
    ) -> Conversation:
        """Assign an agent to a conversation.

        Args:
            db: Async database session.
            tenant_id: Tenant identifier for access verification.
            conversation_id: Identifier of the conversation.
            agent_id: Identifier of the agent to assign.

        Returns:
            The updated Conversation instance with the assigned agent.

        Raises:
            NotFoundError: If the conversation does not exist or does not
                belong to the specified tenant.
        """
        try:
            logger.info(
                "assigning_agent",
                tenant_id=tenant_id,
                conversation_id=conversation_id,
                agent_id=agent_id,
            )

            conversation = await self.conversation_repo.get(
                db, conversation_id
            )

            if conversation is None or conversation.tenant_id != tenant_id:
                raise NotFoundError(
                    f"Conversation {conversation_id} not found"
                )

            update_data = ConversationUpdate(
                assigned_agent_id=agent_id,
            )
            conversation = await self.conversation_repo.update(
                db, conversation, update_data
            )

            logger.info(
                "agent_assigned",
                conversation_id=conversation_id,
                tenant_id=tenant_id,
                agent_id=agent_id,
            )

            return conversation

        except NotFoundError:
            raise
        except Exception:
            logger.exception(
                "agent_assignment_failed",
                tenant_id=tenant_id,
                conversation_id=conversation_id,
                agent_id=agent_id,
            )
            raise


conversation_service = ConversationService()
