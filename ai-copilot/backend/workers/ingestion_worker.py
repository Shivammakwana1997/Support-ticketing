"""Ingestion worker — polls Redis queue for document ingestion jobs."""

from __future__ import annotations

import asyncio
import json

import structlog

logger = structlog.get_logger(__name__)

QUEUE_KEY = "ingestion:queue"
POLL_INTERVAL = 2.0  # seconds


async def process_job(job_data: dict) -> None:
    """Process a single ingestion job."""
    document_id = job_data.get("document_id")
    tenant_id = job_data.get("tenant_id")

    logger.info("ingestion_job_started", document_id=document_id, tenant_id=tenant_id)

    try:
        from integrations.supabase_client import async_session_factory
        from services.rag.ingestion import ingestion_service

        async with async_session_factory() as db:
            try:
                await ingestion_service.process_document(
                    db=db,
                    document_id=document_id,
                    tenant_id=tenant_id,
                )
                await db.commit()
                logger.info("ingestion_job_completed", document_id=document_id)
            except Exception as e:
                await db.rollback()
                logger.error(
                    "ingestion_job_failed",
                    document_id=document_id,
                    error=str(e),
                )
                raise
    except Exception as e:
        logger.error("ingestion_job_error", document_id=document_id, error=str(e))


async def run_worker() -> None:
    """Main worker loop — poll Redis for ingestion jobs."""
    logger.info("ingestion_worker_starting")

    from integrations.redis_client import redis_client

    while True:
        try:
            # BLPOP with timeout for graceful shutdown support
            result = await redis_client.blpop(QUEUE_KEY, timeout=int(POLL_INTERVAL))

            if result is None:
                continue

            # result is (key, value) tuple
            _, raw = result
            job_data = json.loads(raw if isinstance(raw, str) else raw.decode("utf-8"))

            await process_job(job_data)

        except asyncio.CancelledError:
            logger.info("ingestion_worker_cancelled")
            break
        except json.JSONDecodeError as e:
            logger.error("ingestion_invalid_job_payload", error=str(e))
        except Exception as e:
            logger.error("ingestion_worker_error", error=str(e))
            await asyncio.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    asyncio.run(run_worker())
