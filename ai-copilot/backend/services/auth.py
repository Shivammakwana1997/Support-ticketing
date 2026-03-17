"""Authentication service for the AI Customer Support Copilot.

Handles user registration, login, token refresh, and current-user resolution.
All operations are fully async and use structured logging via structlog.
"""

from __future__ import annotations

import uuid
from typing import Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.exceptions import AuthenticationError, ConflictError, NotFoundError
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from models.enums import UserRole
from models.user import User
from repositories.user import UserRepository
from schemas.auth import LoginRequest, TokenResponse

logger = structlog.get_logger(__name__)


class AuthService:
    """Service layer responsible for all authentication and authorization logic."""

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    async def register(
        self,
        db: AsyncSession,
        tenant_id: str,
        email: str,
        password: str,
        display_name: str,
        role: UserRole = UserRole.AGENT,
    ) -> User:
        """Register a new user within a tenant.

        Parameters
        ----------
        db:
            Active async database session.
        tenant_id:
            Identifier for the tenant the user belongs to.
        email:
            Email address (must be unique within the tenant).
        password:
            Plain-text password; will be hashed before storage.
        display_name:
            Human-readable name shown in the UI.
        role:
            The role to assign. Defaults to ``UserRole.AGENT``.

        Returns
        -------
        User
            The newly created user model instance.

        Raises
        ------
        ConflictError
            If a user with the same email already exists for the tenant.
        """
        log = logger.bind(tenant_id=tenant_id, email=email, role=role.value)
        log.info("auth.register.started")

        repo = UserRepository(db)

        existing_user: Optional[User] = await repo.get_by_email(email, tenant_id=tenant_id)
        if existing_user is not None:
            log.warning("auth.register.conflict", reason="email_already_registered")
            raise ConflictError(
                f"A user with email '{email}' already exists for this tenant."
            )

        hashed = hash_password(password)
        user_id = str(uuid.uuid4())

        user: User = await repo.create(
            id=user_id,
            tenant_id=tenant_id,
            email=email,
            hashed_password=hashed,
            display_name=display_name,
            role=role,
        )

        log.info("auth.register.completed", user_id=user.id)
        return user

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    async def login(
        self,
        db: AsyncSession,
        email: str,
        password: str,
    ) -> TokenResponse:
        """Authenticate a user by email and password.

        Parameters
        ----------
        db:
            Active async database session.
        email:
            The user's email address.
        password:
            Plain-text password to verify against the stored hash.

        Returns
        -------
        TokenResponse
            Contains ``access_token``, ``refresh_token``, ``token_type``,
            and ``expires_in`` (seconds).

        Raises
        ------
        AuthenticationError
            If the email is not found or the password does not match.
        """
        log = logger.bind(email=email)
        log.info("auth.login.started")

        repo = UserRepository(db)
        user: Optional[User] = await repo.get_by_email(email)

        if user is None:
            log.warning("auth.login.failed", reason="user_not_found")
            raise AuthenticationError("Invalid email or password.")

        if not verify_password(password, user.hashed_password):
            log.warning("auth.login.failed", reason="invalid_password", user_id=user.id)
            raise AuthenticationError("Invalid email or password.")

        token_payload = {
            "sub": str(user.id),
            "tenant_id": str(user.tenant_id),
            "role": user.role.value if isinstance(user.role, UserRole) else user.role,
        }

        access_token: str = create_access_token(data=token_payload)
        refresh: str = create_refresh_token(data=token_payload)

        log.info("auth.login.completed", user_id=user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # ------------------------------------------------------------------
    # Token refresh
    # ------------------------------------------------------------------

    async def refresh_token(
        self,
        db: AsyncSession,
        refresh_token: str,
    ) -> TokenResponse:
        """Exchange a valid refresh token for a new access/refresh token pair.

        Parameters
        ----------
        db:
            Active async database session.
        refresh_token:
            The refresh token issued during login or a previous refresh.

        Returns
        -------
        TokenResponse
            A fresh pair of tokens.

        Raises
        ------
        AuthenticationError
            If the refresh token is invalid, expired, or the referenced
            user no longer exists.
        """
        log = logger.bind()
        log.info("auth.refresh_token.started")

        try:
            payload: dict = decode_token(refresh_token)
        except Exception as exc:
            log.warning("auth.refresh_token.failed", reason="invalid_token", error=str(exc))
            raise AuthenticationError("Invalid or expired refresh token.") from exc

        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            log.warning("auth.refresh_token.failed", reason="missing_sub_claim")
            raise AuthenticationError("Invalid refresh token payload.")

        repo = UserRepository(db)
        user: Optional[User] = await repo.get_by_id(user_id)

        if user is None:
            log.warning("auth.refresh_token.failed", reason="user_not_found", user_id=user_id)
            raise AuthenticationError("User associated with this token no longer exists.")

        token_payload = {
            "sub": str(user.id),
            "tenant_id": str(user.tenant_id),
            "role": user.role.value if isinstance(user.role, UserRole) else user.role,
        }

        new_access: str = create_access_token(data=token_payload)
        new_refresh: str = create_refresh_token(data=token_payload)

        log.info("auth.refresh_token.completed", user_id=user.id)

        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # ------------------------------------------------------------------
    # Current user resolution
    # ------------------------------------------------------------------

    async def get_current_user(
        self,
        db: AsyncSession,
        token: str,
    ) -> User:
        """Resolve the currently authenticated user from a bearer token.

        Parameters
        ----------
        db:
            Active async database session.
        token:
            The raw JWT access token (without the ``Bearer `` prefix).

        Returns
        -------
        User
            The user model corresponding to the token's ``sub`` claim.

        Raises
        ------
        AuthenticationError
            If the token is invalid, expired, or the user cannot be found.
        """
        log = logger.bind()
        log.info("auth.get_current_user.started")

        try:
            payload: dict = decode_token(token)
        except Exception as exc:
            log.warning("auth.get_current_user.failed", reason="invalid_token", error=str(exc))
            raise AuthenticationError("Could not validate credentials.") from exc

        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            log.warning("auth.get_current_user.failed", reason="missing_sub_claim")
            raise AuthenticationError("Invalid token payload.")

        repo = UserRepository(db)
        user: Optional[User] = await repo.get_by_id(user_id)

        if user is None:
            log.warning(
                "auth.get_current_user.failed",
                reason="user_not_found",
                user_id=user_id,
            )
            raise AuthenticationError("User not found or has been deactivated.")

        log.info("auth.get_current_user.completed", user_id=user.id)
        return user


# Module-level convenience instance
auth_service = AuthService()
