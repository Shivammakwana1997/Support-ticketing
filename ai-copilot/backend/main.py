"""AI Customer Support Copilot — FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.exceptions import register_exception_handlers
from core.middleware import register_middleware

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown lifecycle events."""
    # --- Startup ---
    logger.info("app_starting", env=settings.APP_ENV)

    # Initialize database connection pool
    try:
        from integrations.supabase_client import async_session_factory

        async with async_session_factory() as session:
            from sqlalchemy import text

            await session.execute(text("SELECT 1"))
        logger.info("database_connected")
    except Exception as e:
        logger.error("database_connection_failed", error=str(e))

    # Initialize Redis
    try:
        from integrations.redis_client import redis_client

        await redis_client.ping()
        logger.info("redis_connected")
    except Exception as e:
        logger.warning("redis_connection_failed", error=str(e))

    # Setup structured logging
    try:
        from core.logging import setup_logging

        level = "DEBUG" if settings.DEBUG else "INFO"
        setup_logging(level)
    except Exception:
        pass

    logger.info("app_started", app=settings.APP_NAME, env=settings.APP_ENV)

    yield

    # --- Shutdown ---
    logger.info("app_shutting_down")

    try:
        from integrations.redis_client import redis_client

        await redis_client.close()
        logger.info("redis_disconnected")
    except Exception:
        pass

    logger.info("app_stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        description="AI-powered customer support copilot with multi-channel messaging, "
        "knowledge base, ticketing, and real-time agent assistance.",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    # Register middleware
    register_middleware(app)

    # Register exception handlers
    register_exception_handlers(app)

    # Include routers
    from api.routes.health import router as health_router
    from api.routes.auth import router as auth_router
    from api.routes.tickets import router as tickets_router
    from api.routes.conversations import router as conversations_router
    from api.routes.chat import router as chat_router
    from api.routes.copilot import router as copilot_router
    from api.routes.voice import router as voice_router
    from api.routes.knowledge import router as knowledge_router
    from api.routes.customers import router as customers_router
    from api.routes.admin import router as admin_router
    from api.routes.analytics import router as analytics_router
    from api.routes.webhooks import router as webhooks_router

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(tickets_router)
    app.include_router(conversations_router)
    app.include_router(chat_router)
    app.include_router(copilot_router)
    app.include_router(voice_router)
    app.include_router(knowledge_router)
    app.include_router(customers_router)
    app.include_router(admin_router)
    app.include_router(analytics_router)
    app.include_router(webhooks_router)

    return app


app = create_app()
