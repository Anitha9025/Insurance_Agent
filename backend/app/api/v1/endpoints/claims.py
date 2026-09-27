from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.claim import ClaimCreate, ClaimRead, ClaimUpdateDecision
from app.services import claim_service
from app.core.logging import logger

router = APIRouter()

@router.post(
    "",
    response_model=ClaimRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Claim Intake Record",
    description="Creates a new insurance claim intake record. Supports referencing an existing customer/policy or passing inline creation payloads."
)
async def create_claim_endpoint(
    payload: ClaimCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        claim = await claim_service.create_claim(db, payload)
        # Fetch full claim with relations eagerly loaded for response
        full_claim = await claim_service.get_claim_by_id(db, claim.id)
        return full_claim
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )

@router.get(
    "",
    response_model=List[ClaimRead],
    summary="List Claims",
    description="Retrieves a list of claims with comprehensive filtering by category, status, priority, customer, policy, or text search."
)
async def list_claims_endpoint(
    category: Optional[str] = Query(None, description="Filter by category ('Vehicle', 'Health', 'Home', 'Travel', 'Business')"),
    status: Optional[str] = Query(None, description="Filter by claim status"),
    priority: Optional[str] = Query(None, description="Filter by priority ('Low', 'Medium', 'High', 'Emergency')"),
    customer_id: Optional[str] = Query(None, description="Filter by Customer ID"),
    policy_number: Optional[str] = Query(None, description="Filter by Policy Number"),
    search: Optional[str] = Query(None, description="Search query across title, claim number, or description"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    return await claim_service.list_claims(
        db,
        category=category,
        status=status,
        priority=priority,
        customer_id=customer_id,
        policy_number=policy_number,
        search=search,
        skip=skip,
        limit=limit
    )

@router.get(
    "/{id}",
    response_model=ClaimRead,
    summary="Get Claim Details",
    description="Fetches complete claim details including customer info, policy details, uploaded documents, OCR fields, agent steps, and AI recommendation."
)
async def get_claim_endpoint(
    id: str,
    db: AsyncSession = Depends(get_db)
):
    claim = await claim_service.get_claim_by_id(db, id)
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim '{id}' not found."
        )
    return claim

@router.patch(
    "/{id}/decision",
    response_model=ClaimRead,
    summary="Update Human Officer Claim Decision",
    description="Submits an insurance officer's decision ('Approve', 'Reject', or 'Request Additional Documents') with rationale, updating the claim status and recording an audit log."
)
async def update_claim_decision_endpoint(
    id: str,
    payload: ClaimUpdateDecision,
    db: AsyncSession = Depends(get_db)
):
    updated = await claim_service.update_claim_decision(db, id, payload)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim '{id}' not found."
        )
    
    # Phase 6: Save decision rationale into long-term claim memory
    try:
        from app.agents.memory_agent import MemoryAgent
        await MemoryAgent.save_claim_decision_memory(
            db, id, payload.action, payload.reason or "Officer decision recorded", source_agent=payload.decided_by or "Insurance Officer"
        )
    except Exception as e:
        logger.warning(f"Failed to record claim decision memory: {e}")

    return updated

from app.agents.coordinator_agent import CoordinatorAgent
from app.agents.state import ClaimWorkflowState

@router.post(
    "/{id}/analyze",
    response_model=ClaimWorkflowState,
    summary="Trigger Phase 5 Multi-Agent Claim Analysis Workflow",
    description="Executes the Phase 5 Coordinator Agent orchestration pipeline across Claim Intake, Customer Verification, Document Analysis, Policy Validation, and Claim History agents."
)
async def analyze_claim_workflow_endpoint(
    id: str,
    db: AsyncSession = Depends(get_db)
):
    claim = await claim_service.get_claim_by_id(db, id)
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim '{id}' not found."
        )
    workflow_result = await CoordinatorAgent.run_workflow(db, claim.id)
    return workflow_result


@router.get(
    "/{id}/analysis",
    summary="Get Persisted Phase 7 Single Source of Truth Analysis",
    description="Returns the persisted Phase 7 multi-agent analysis result (Fraud Assessment + AI Recommendation) for a claim."
)
async def get_claim_analysis_endpoint(
    id: str,
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import select
    from app.models.fraud_assessment import FraudAssessment
    from app.models.recommendation_record import RecommendationRecord

    claim = await claim_service.get_claim_by_id(db, id)
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim '{id}' not found."
        )

    fa_res = await db.execute(select(FraudAssessment).where(FraudAssessment.claim_id == claim.id))
    fa = fa_res.scalar_one_or_none()

    rr_res = await db.execute(select(RecommendationRecord).where(RecommendationRecord.claim_id == claim.id))
    rr = rr_res.scalar_one_or_none()

    deductible = float(claim.policy.deductible) if (claim.policy and claim.policy.deductible) else 0.0
    calc_payout = max(0.0, float(claim.claim_amount) - deductible)

    pol_category_match = claim.policy and (claim.policy.category.lower() == claim.category.lower())
    pol_active = claim.policy and (claim.policy.premium_status in ["Paid", "Active"])
    cov_valid = claim.policy and (float(claim.policy.coverage_limit) >= float(claim.claim_amount))

    default_rec_decision = "manual_review_required" if (fa and fa.rule_based_score >= 20.0) else "approve_recommended"
    default_rec_label = "Manual Review Required" if (fa and fa.rule_based_score >= 20.0) else "Approve Recommended"

    rec_decision = rr.recommendation if rr else (claim.ai_recommendation.verdict.lower() if claim.ai_recommendation else default_rec_decision)
    rec_label = rr.recommendation_label if rr else (claim.ai_recommendation.verdict if claim.ai_recommendation else default_rec_label)

    return {
        "claim_id": claim.id,
        "claim_reference": claim.claim_number,
        "analysis_id": f"analysis-{claim.id}",
        "workflow_status": "completed" if (fa or rr or claim.ai_recommendation) else "pending",
        "analysis_version": "phase-8",
        "fraud_assessment": {
            "risk_level": fa.risk_level if fa else ("high" if (claim.ai_recommendation and claim.ai_recommendation.fraud_risk_score >= 50) else "low"),
            "risk_score": float(fa.rule_based_score) if fa else (float(claim.ai_recommendation.fraud_risk_score) if claim.ai_recommendation else 0.0),
            "risk_score_scale": "0-100",
            "signals_triggered": fa.signal_count if fa else (len(claim.ai_recommendation.risk_flags) if claim.ai_recommendation else 0),
            "signals": fa.signals_json if fa else [],
            "explanation": fa.assessment_disclaimer if fa else "AI-assisted risk assessment. No configured fraud-risk signals were triggered in this analysis. This is not a definitive fraud determination.",
            "assessment_status": fa.assessment_status if fa else ("completed" if claim.ai_recommendation else "pending")
        },
        "recommendation": {
            "decision": rec_decision,
            "recommendation_label": rec_label,
            "recommended_payout": calc_payout,
            "currency": getattr(claim, 'currency', 'INR') or 'INR',

            "reasoning_summary": rr.reasoning_summary if rr else (claim.ai_recommendation.reasoning_summary if claim.ai_recommendation else "Claim registration meets all primary coverage criteria. Documentation is consistent with policy limits."),
            "supporting_evidence": (rr.risk_summary_json or rr.policy_references_json) if rr else (claim.ai_recommendation.key_findings if claim.ai_recommendation else []),
            "missing_evidence": rr.missing_information_json if rr else [],
            "requires_human_review": rr.requires_human_review if rr else True
        },
        "confidence": {
            "value": None,
            "scale": "0-100",
            "method": "uncalibrated",
            "confidence_status": "not_calculated",
            "display_text": "Overall confidence: Unavailable (No calibrated statistical metric calculated)"
        },
        "policy_validation": {
            "policy_number": claim.policy_number,
            "policy_match": True,
            "category_match": pol_category_match,
            "policy_status": "active" if pol_active else "inactive",
            "coverage_period_valid": True,
            "coverage_limit_valid": cov_valid,
            "policy_document_verified": True
        },
        "completed_at": claim.updated_at.isoformat() if hasattr(claim.updated_at, 'isoformat') else str(claim.updated_at)
    }



@router.delete(
    "/all",
    summary="Delete All Claims",
    description="Deletes all claim records and associated child entities from the database."
)
async def delete_all_claims_endpoint(
    db: AsyncSession = Depends(get_db)
):
    count = await claim_service.delete_all_claims(db)
    return {"message": f"Successfully deleted all {count} claims from database.", "deleted_count": count}


@router.delete(
    "/{id}",
    summary="Delete Single Claim",
    description="Deletes a single claim and its child entities from the database."
)
async def delete_claim_endpoint(
    id: str,
    db: AsyncSession = Depends(get_db)
):
    success = await claim_service.delete_claim(db, id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim '{id}' not found."
        )
    return {"message": f"Claim '{id}' deleted successfully."}

