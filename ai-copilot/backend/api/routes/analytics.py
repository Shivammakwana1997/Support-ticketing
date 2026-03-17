"""Analytics routes."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.auth import get_current_user
from api.dependencies.database import get_db
from models.user import User
from schemas.analytics import DashboardResponse, AgentMetricsResponse, CallMetricsResponse
from services.analytics import analytics_service

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardResponse:
    """Get dashboard analytics."""
    try:
        result = await analytics_service.get_dashboard(
            db=db,
            tenant_id=current_user.tenant_id,
            start_date=start_date,
            end_date=end_date,
        )
        return DashboardResponse(**result)
    except Exception as e:
        logger.error("get_dashboard_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard analytics",
        )


@router.get("/agents", response_model=AgentMetricsResponse)
async def get_agent_metrics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentMetricsResponse:
    """Get per-agent performance metrics."""
    try:
        result = await analytics_service.get_agent_metrics(
            db=db,
            tenant_id=current_user.tenant_id,
            start_date=start_date,
            end_date=end_date,
        )
        return AgentMetricsResponse(agents=result)
    except Exception as e:
        logger.error("get_agent_metrics_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get agent metrics",
        )


@router.get("/calls", response_model=CallMetricsResponse)
async def get_call_metrics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CallMetricsResponse:
    """Get voice call quality metrics."""
    try:
        result = await analytics_service.get_call_metrics(
            db=db,
            tenant_id=current_user.tenant_id,
            start_date=start_date,
            end_date=end_date,
        )
        return CallMetricsResponse(**result)
    except Exception as e:
        logger.error("get_call_metrics_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get call metrics",
        )
