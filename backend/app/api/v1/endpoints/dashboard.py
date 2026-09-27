from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.claim import Claim
from app.models.agent_step import AIAgentStep
from app.schemas.claim import ClaimRead
from app.services import claim_service
from app.core.logging import logger

router = APIRouter()

@router.get(
    "/summary",
    summary="Get Dashboard Summary Metrics",
    description="Returns calculated metrics from actual PostgreSQL database records."
)
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    total_res = await db.execute(select(func.count(Claim.id)))
    total_claims = total_res.scalar() or 0

    pending_res = await db.execute(
        select(func.count(Claim.id)).where(Claim.status.in_(["Submitted", "Processing", "Under Review"]))
    )
    pending_claims = pending_res.scalar() or 0

    approved_res = await db.execute(
        select(func.count(Claim.id)).where(Claim.status == "Approved")
    )
    approved_claims = approved_res.scalar() or 0

    rejected_res = await db.execute(
        select(func.count(Claim.id)).where(Claim.status == "Rejected")
    )
    rejected_claims = rejected_res.scalar() or 0

    emergency_res = await db.execute(
        select(func.count(Claim.id)).where(Claim.is_emergency == True)
    )
    emergency_claims = emergency_res.scalar() or 0

    return {
        "total_claims": total_claims,
        "pending_claims": pending_claims,
        "approved_claims": approved_claims,
        "rejected_claims": rejected_claims,
        "emergency_claims": emergency_claims
    }

@router.get(
    "/category-breakdown",
    summary="Get Category Distribution",
    description="Calculates distribution of claims by category from PostgreSQL."
)
async def get_category_breakdown(db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Claim.category, func.count(Claim.id)).group_by(Claim.category)
    )
    rows = res.all()
    
    total = sum(r[1] for r in rows) or 1
    categories = [
        {
            "category": r[0],
            "count": r[1],
            "percentage": round((r[1] / total) * 100, 1)
        }
        for r in rows
    ]
    return {
        "total": total,
        "categories": categories
    }

@router.get(
    "/claim-volume",
    summary="Get Claim Volume Aggregations",
    description="Aggregates claim volume by status or created period."
)
async def get_claim_volume(db: AsyncSession = Depends(get_db)):
    # Group claims by incident date or month
    res = await db.execute(
        select(Claim.incident_date, func.count(Claim.id)).group_by(Claim.incident_date).order_by(Claim.incident_date.desc()).limit(14)
    )
    rows = res.all()
    volume = [{"date": r[0], "count": r[1]} for r in reversed(rows)]
    return {"volume": volume}

@router.get(
    "/priority-claims",
    response_model=List[ClaimRead],
    summary="Get Recent Priority Claims",
    description="Retrieves recent priority/emergency claims from PostgreSQL."
)
async def get_priority_claims(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    return await claim_service.list_claims(
        db,
        priority="Emergency",
        skip=0,
        limit=limit
    )

@router.get(
    "/ai-metrics",
    summary="Get Operational AI Agent Evaluation Metrics",
    description="Returns actual recorded execution metrics from agent logs without fabricated benchmarks."
)
async def get_ai_metrics(db: AsyncSession = Depends(get_db)):
    steps_res = await db.execute(select(func.count(AIAgentStep.id)))
    total_steps = steps_res.scalar() or 0

    completed_res = await db.execute(
        select(func.count(AIAgentStep.id)).where(AIAgentStep.status == "Completed")
    )
    completed_steps = completed_res.scalar() or 0

    if total_steps > 0:
        completion_rate = round((completed_steps / total_steps) * 100, 1)
        status_msg = f"Agent workflow completion rate: {completion_rate}%"
    else:
        status_msg = "Evaluation metrics not available"

    return {
        "status": status_msg,
        "total_agent_steps": total_steps,
        "completed_agent_steps": completed_steps,
        "evaluation_dataset_available": False,
        "note": "Metrics are derived directly from PostgreSQL recorded agent executions."
    }
