"""SLA worker — periodically checks for SLA breaches and sends notifications."""

from __future__ import annotations

import asyncio

import structlog

logger = structlog.get_logger(__name__)

CHECK_INTERVAL = 60.0  # seconds


async def check_sla_breaches() -> None:
    """Check all open tickets for SLA breaches and trigger notifications."""
    try:
        from integrations.supabase_client import async_session_factory
        from services.automation.sla import sla_service

        async with async_session_factory() as db:
            try:
                breached = await sla_service.check_breaches(db)

                if breached:
                    logger.info("sla_breaches_detected", count=len(breached))

                    for breach in breached:
                        try:
                            await sla_service.handle_breach(db, breach)
                        except Exception as e:
                            logger.error(
                                "sla_breach_handling_failed",
                                ticket_id=getattr(breach, "id", str(breach)),
                                error=str(e),
                            )

                await db.commit()
            except Exception as e:
                await db.rollback()
                logger.error("sla_check_failed", error=str(e))
    except Exception as e:
        logger.error("sla_worker_session_error", error=str(e))


async def run_worker() -> None:
    """Main worker loop — periodically check SLA compliance."""
    logger.info("sla_worker_starting", interval_seconds=CHECK_INTERVAL)

    while True:
        try:
            await check_sla_breaches()
        except asyncio.CancelledError:
            logger.info("sla_worker_cancelled")
            break
        except Exception as e:
            logger.error("sla_worker_error", error=str(e))

        await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(run_worker())
