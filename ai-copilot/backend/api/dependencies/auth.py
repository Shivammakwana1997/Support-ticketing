from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.database import get_db
from core.security import get_current_user as _get_current_user
from models.enums import UserRoleEnum
from repositories.user import UserRepository


async def get_current_user(
    token_payload: dict[str, Any] = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Resolve token payload into full user data, ensuring user exists and is active."""
    user_id = token_payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    repo = UserRepository(db)
    user = await repo.get(UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return {
        "id": str(user.id),
        "tenant_id": str(user.tenant_id),
        "email": user.email,
        "role": user.role.value,
        "display_name": user.display_name,
    }


async def get_current_admin(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    if current_user["role"] != UserRoleEnum.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def get_current_agent(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    if current_user["role"] not in (UserRoleEnum.ADMIN.value, UserRoleEnum.AGENT.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agent access required",
        )
    return current_user


async def require_admin(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    from core.exceptions import ForbiddenError
    from models.enums import UserRoleEnum
    # Because get_current_user returns a dict with "role": user.role.value
    if current_user.get("role") != UserRoleEnum.ADMIN.value:
        raise ForbiddenError("Admin privileges required.")
    # Return a mocked User object because some routes expect `current_user: User`
    from models.user import User
    user_obj = User(
        id=UUID(current_user["id"]),
        tenant_id=UUID(current_user["tenant_id"]),
        email=current_user["email"],
        role=UserRoleEnum(current_user["role"]),
        display_name=current_user["display_name"]
    )
    return user_obj

async def require_tenant(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> UUID:
    """Extract and return the tenant_id from the current user."""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant context required",
        )
    return UUID(tenant_id)
