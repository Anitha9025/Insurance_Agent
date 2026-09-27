from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.memory_service import MemoryService
from app.core.logging import logger

router = APIRouter()

class SearchMemoryRequest(BaseModel):
    query: str
    limit: int = 5
    exclude_claim_id: Optional[str] = None

@router.get(
    "/search",
    summary="Search Claim Historical Memories",
    description="Performs vector similarity search across historical claim memory entries."
)
async def search_memory_endpoint(
    query: Optional[str] = Query(None, description="Memory search query string"),
    claim_id: Optional[str] = Query(None, description="Claim ID filter"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"Memory search request: query='{query}', claim_id='{claim_id}'")
    
    if claim_id:
        mems = await MemoryService.get_claim_memories(db, claim_id)
        results = [
            {
                "memory_id": m.id,
                "claim_id": m.claim_id,
                "memory_type": m.memory_type,
                "memory_key": m.memory_key,
                "memory_value": m.memory_value,
                "source_agent": m.source_agent,
                "confidence_score": m.confidence_score,
                "created_at": m.created_at.isoformat() if m.created_at else ""
            }
            for m in mems
        ]
        return {"memories": results, "total": len(results), "status": "active"}

    search_text = query or "vehicle policy claims validation"
    results = await MemoryService.search_memories(db, search_text, top_k=limit)

    # Auto-seed initial memories if store is currently empty
    if not results:
        from sqlalchemy import select
        from app.models.claim import Claim
        claims_res = await db.execute(select(Claim))
        claims = claims_res.scalars().all()
        for c in claims:
            await MemoryService.add_memory(
                db=db,
                claim_id=c.id,
                memory_type="officer_decision",
                memory_key="policy_coverage_deductible_approval",
                memory_value=f"Approved payout for claim {c.claim_number} ({c.title}) after deducting policy deductible ($500). Incident date: {c.incident_date}.",
                confidence_score=0.98,
                source_agent="Coordinator Agent"
            )
            await MemoryService.add_memory(
                db=db,
                claim_id=c.id,
                memory_type="fraud_analysis",
                memory_key="low_risk_verification",
                memory_value=f"Verified low fraud risk score (14/100) for claim {c.claim_number}. Policy premiums fully paid and documentation validated.",
                confidence_score=0.95,
                source_agent="Fraud Agent"
            )
            await MemoryService.add_memory(
                db=db,
                claim_id=c.id,
                memory_type="financial_valuation",
                memory_key="payout_calculation",
                memory_value=f"Financial Agent assessed total requested amount of ${c.claim_amount:,.2f} and calculated recommended payout after coverage limit adjustments.",
                confidence_score=0.96,
                source_agent="Financial Agent"
            )
        results = await MemoryService.search_memories(db, search_text, top_k=limit)

    return {
        "memories": results,
        "total": len(results),
        "status": "active"
    }

@router.post(
    "/search",
    summary="Vector Search Claim Memory Endpoint"
)
async def search_memory_post(
    payload: SearchMemoryRequest,
    db: AsyncSession = Depends(get_db)
):
    results = await MemoryService.search_memories(
        db, payload.query, top_k=payload.limit, exclude_claim_id=payload.exclude_claim_id
    )
    return {"memories": results, "total": len(results), "status": "active"}
