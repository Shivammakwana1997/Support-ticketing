"""Admin routes - agent management, AI config, API keys, and usage."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.auth import get_current_user, require_admin
from api.dependencies.database import get_db
from core.exceptions import NotFoundError, ForbiddenError
from models.user import User
from models.enums import UserRole
from schemas.admin import (
    AgentResponse,
    AgentUpdateRequest,
    AIConfigResponse,
    AIConfigUpdateRequest,
    APIKeyResponse,
    APIKeyCreateRequest,
    UsageResponse,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


# --- Agent Management ---


@router.get("/agents", response_model=list[AgentResponse])
async def list_agents(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> list[AgentResponse]:
    """List all support agents."""
    try:
        from repositories.agent import AgentRepository

        repo = AgentRepository()
        filters: dict = {"tenant_id": current_user.tenant_id}
        if status_filter:
            filters["status"] = status_filter

        agents = await repo.list_filtered(db, filters=filters)
        return [AgentResponse.model_validate(a) for a in agents]
    except Exception as e:
        logger.error("list_agents_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list agents",
        )


@router.patch("/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    request: AgentUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AgentResponse:
    """Update an agent's settings (status, skills, etc.)."""
    try:
        from repositories.agent import AgentRepository

        repo = AgentRepository()
        agent = await repo.get_by_id(db, agent_id)

        if not agent:
            raise NotFoundError(f"Agent {agent_id} not found")

        if getattr(agent, "tenant_id", None) != current_user.tenant_id:
            raise NotFoundError(f"Agent {agent_id} not found")

        updated = await repo.update(
            db,
            agent_id,
            request.model_dump(exclude_unset=True),
        )

        logger.info("agent_updated", agent_id=agent_id)
        return AgentResponse.model_validate(updated)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("update_agent_failed", agent_id=agent_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update agent",
        )


# --- AI Configuration ---


@router.get("/config/ai", response_model=AIConfigResponse)
async def get_ai_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AIConfigResponse:
    """Get AI configuration for the tenant."""
    try:
        from repositories.tenant import TenantRepository

        repo = TenantRepository()
        tenant = await repo.get_by_id(db, current_user.tenant_id)

        if not tenant:
            raise NotFoundError("Tenant not found")

        ai_config = getattr(tenant, "ai_config", {}) or {}

        return AIConfigResponse(
            model=ai_config.get("model", "gpt-4o"),
            temperature=ai_config.get("temperature", 0.3),
            max_tokens=ai_config.get("max_tokens", 1024),
            system_prompt=ai_config.get("system_prompt", ""),
            auto_reply_enabled=ai_config.get("auto_reply_enabled", False),
            auto_categorize_enabled=ai_config.get("auto_categorize_enabled", True),
            auto_route_enabled=ai_config.get("auto_route_enabled", True),
            sentiment_analysis_enabled=ai_config.get("sentiment_analysis_enabled", True),
            language_detection_enabled=ai_config.get("language_detection_enabled", True),
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("get_ai_config_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get AI configuration",
        )


@router.patch("/config/ai", response_model=AIConfigResponse)
async def update_ai_config(
    request: AIConfigUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AIConfigResponse:
    """Update AI configuration for the tenant."""
    try:
        from repositories.tenant import TenantRepository

        repo = TenantRepository()
        tenant = await repo.get_by_id(db, current_user.tenant_id)

        if not tenant:
            raise NotFoundError("Tenant not found")

        current_config = getattr(tenant, "ai_config", {}) or {}
        new_config = {**current_config, **request.model_dump(exclude_unset=True)}

        await repo.update(db, current_user.tenant_id, {"ai_config": new_config})

        logger.info("ai_config_updated", tenant_id=current_user.tenant_id)

        return AIConfigResponse(
            model=new_config.get("model", "gpt-4o"),
            temperature=new_config.get("temperature", 0.3),
            max_tokens=new_config.get("max_tokens", 1024),
            system_prompt=new_config.get("system_prompt", ""),
            auto_reply_enabled=new_config.get("auto_reply_enabled", False),
            auto_categorize_enabled=new_config.get("auto_categorize_enabled", True),
            auto_route_enabled=new_config.get("auto_route_enabled", True),
            sentiment_analysis_enabled=new_config.get("sentiment_analysis_enabled", True),
            language_detection_enabled=new_config.get("language_detection_enabled", True),
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("update_ai_config_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update AI configuration",
        )


# --- API Keys ---


@router.get("/api-keys", response_model=list[APIKeyResponse])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> list[APIKeyResponse]:
    """List API keys for the tenant."""
    try:
        from repositories.api_key import APIKeyRepository

        repo = APIKeyRepository()
        keys = await repo.list_by_tenant(db, current_user.tenant_id)
        return [APIKeyResponse.model_validate(k) for k in keys]
    except Exception as e:
        logger.error("list_api_keys_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list API keys",
        )


@router.post("/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: APIKeyCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> APIKeyResponse:
    """Create a new API key."""
    try:
        import secrets

        from repositories.api_key import APIKeyRepository

        repo = APIKeyRepository()

        # Generate a secure API key
        raw_key = f"sk-{secrets.token_urlsafe(32)}"
        key_prefix = raw_key[:12]

        # Hash the key for storage
        from core.security import hash_api_key

        key_hash = hash_api_key(raw_key)

        api_key = await repo.create(
            db,
            {
                "id": str(uuid.uuid4()),
                "tenant_id": current_user.tenant_id,
                "name": request.name,
                "key_hash": key_hash,
                "key_prefix": key_prefix,
                "created_by": str(current_user.id),
                "expires_at": request.expires_at,
                "scopes": request.scopes or ["read", "write"],
            },
        )

        logger.info("api_key_created", name=request.name, tenant_id=current_user.tenant_id)

        # Return the raw key only on creation
        response = APIKeyResponse.model_validate(api_key)
        response.key = raw_key  # Only visible on creation
        return response
    except Exception as e:
        logger.error("create_api_key_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key",
        )


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    """Delete an API key."""
    try:
        from repositories.api_key import APIKeyRepository

        repo = APIKeyRepository()
        api_key = await repo.get_by_id(db, key_id)

        if not api_key:
            raise NotFoundError(f"API key {key_id} not found")

        if getattr(api_key, "tenant_id", None) != current_user.tenant_id:
            raise NotFoundError(f"API key {key_id} not found")

        await repo.delete(db, key_id)
        logger.info("api_key_deleted", key_id=key_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("delete_api_key_failed", key_id=key_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete API key",
        )


# --- Usage ---


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> UsageResponse:
    """Get usage statistics for the tenant."""
    try:
        from repositories.ticket import TicketRepository
        from repositories.conversation import ConversationRepository

        ticket_repo = TicketRepository()
        conv_repo = ConversationRepository()

        tenant_id = current_user.tenant_id

        # Get counts
        ticket_count = await ticket_repo.count_by_tenant(db, tenant_id)
        conv_count = await conv_repo.count_by_tenant(db, tenant_id)

        return UsageResponse(
            tenant_id=tenant_id,
            total_tickets=ticket_count,
            total_conversations=conv_count,
            ai_requests_this_month=0,  # Would track via metrics
            storage_used_mb=0.0,
            api_calls_this_month=0,
        )
    except Exception as e:
        logger.error("get_usage_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get usage statistics",
        )
