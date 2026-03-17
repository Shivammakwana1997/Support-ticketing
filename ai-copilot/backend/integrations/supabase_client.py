"""
Supabase Integration Client

Provides access to:
- Database (PostgreSQL via Supabase)
- Auth (Supabase authentication)
- Storage (Supabase Storage buckets)
- Realtime (Supabase Realtime subscriptions)
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any, Optional

from supabase import AsyncClient, create_client

from backend.core.config import settings

# SQLAlchemy Async Engine (for existing database operations)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session (SQLAlchemy)."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Supabase Client (for Auth, Storage, Realtime)
_supabase_client: Optional[AsyncClient] = None


async def get_supabase_client() -> AsyncClient:
    """
    Get Supabase async client.
    
    Usage:
        from backend.integrations.supabase_client import get_supabase_client
        
        @app.get("/users")
        async def get_users(supabase: AsyncClient = Depends(get_supabase_client)):
            response = await supabase.from_("users").select("*").execute()
            return response.data
    """
    global _supabase_client
    
    if not settings.SUPABASE_URL:
        raise ValueError("SUPABASE_URL is not set in environment variables")
    
    if _supabase_client is None:
        _supabase_client = await create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY,
        )
    
    return _supabase_client


async def create_supabase_client(url: str, key: str) -> AsyncClient:
    """Create a new Supabase client with custom credentials."""
    return await create_client(url, key)


def get_supabase_service_role_key() -> str:
    """Get Supabase service role key (for admin operations)."""
    service_role_key = settings.SUPABASE_SERVICE_ROLE_KEY
    if not service_role_key:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY is not set")
    return service_role_key


async def get_supabase_admin_client() -> AsyncClient:
    """
    Get Supabase client with service role key (admin privileges).
    Use only for server-side admin operations!
    """
    if not settings.SUPABASE_URL:
        raise ValueError("SUPABASE_URL is not set")
    
    service_key = get_supabase_service_role_key()
    
    return await create_client(
        settings.SUPABASE_URL,
        service_key,
    )


# Storage bucket names
class StorageBuckets:
    """Constants for Supabase Storage buckets."""
    AVATARS = "avatars"
    DOCUMENTS = "documents"
    TICKET_ATTACHMENTS = "ticket-attachments"
    KNOWLEDGE_BASE = "knowledge-base"


# Database table names
class Tables:
    """Constants for Supabase tables."""
    USERS = "users"
    TENANTS = "tenants"
    CONVERSATIONS = "conversations"
    MESSAGES = "messages"
    TICKETS = "tickets"
    KNOWLEDGE = "knowledge"


# Helper functions for common Supabase operations
async def upload_file(
    bucket: str,
    path: str,
    file_data: bytes,
    content_type: str = "application/octet-stream",
) -> dict[str, Any]:
    """Upload a file to Supabase Storage."""
    supabase = await get_supabase_client()
    response = await supabase.storage.from_(bucket).upload(
        path,
        file_data,
        {"content-type": content_type},
    )
    return response


async def get_public_url(bucket: str, path: str) -> str:
    """Get public URL for a file in Supabase Storage."""
    supabase = await get_supabase_client()
    return supabase.storage.from_(bucket).get_public_url(path)


async def delete_file(bucket: str, path: str) -> dict[str, Any]:
    """Delete a file from Supabase Storage."""
    supabase = await get_supabase_client()
    response = await supabase.storage.from_(bucket).remove([path])
    return response


async def sign_up(email: str, password: str) -> dict[str, Any]:
    """Sign up a new user with email and password."""
    supabase = await get_supabase_client()
    response = await supabase.auth.sign_up({"email": email, "password": password})
    return response


async def sign_in(email: str, password: str) -> dict[str, Any]:
    """Sign in with email and password."""
    supabase = await get_supabase_client()
    response = await supabase.auth.sign_in_with_password({"email": email, "password": password})
    return response


async def sign_out() -> dict[str, Any]:
    """Sign out the current user."""
    supabase = await get_supabase_client()
    response = await supabase.auth.sign_out()
    return response


async def get_user() -> Optional[dict[str, Any]]:
    """Get current authenticated user."""
    supabase = await get_supabase_client()
    response = await supabase.auth.get_user()
    return response.user if response.user else None


async def verify_token(token: str) -> dict[str, Any]:
    """Verify a JWT token."""
    supabase = await get_supabase_client()
    response = await supabase.auth.get_user(token)
    return response.user if response.user else None