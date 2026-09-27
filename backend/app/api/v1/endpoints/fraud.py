"""
Phase 7: Fraud Detection + Recommendation API endpoints.
Provides GET access to stored fraud assessments, recommendations, and normalized evidence items.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.logging import logger
from app.models.fraud_assessment import FraudAssessment
from app.models.recommendation_record import RecommendationRecord
from app.schemas.fraud_assessment import (
    FraudAssessmentRead,
    RecommendationRecordRead,
    Phase7AnalysisResponse,
)

router = APIRouter()


@router.get(
    "/claims/{claim_id}/fraud-assessment",
    response_model=FraudAssessmentRead,
    summary="Get Stored Fraud Risk Assessment",
    description=(
        "Returns the Phase 7 rule-based fraud risk assessment for a claim. "
        "Assessment is evidence-derived and advisory only — not a fraud determination. "
        "Run POST /claims/{id}/analyze first to generate."
    )
)
async def get_fraud_assessment(
    claim_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(FraudAssessment).where(FraudAssessment.claim_id == claim_id)
    )
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No fraud assessment found for claim '{claim_id}'. "
                "Run POST /api/v1/claims/{id}/analyze to generate one."
            )
        )
    return assessment


@router.get(
    "/claims/{claim_id}/recommendation",
    response_model=RecommendationRecordRead,
    summary="Get Stored AI Claim Recommendation",
    description=(
        "Returns the Phase 7 AI-assisted advisory recommendation for a claim. "
        "This is not a final decision — the human insurance officer retains full authority. "
        "Run POST /claims/{id}/analyze first to generate."
    )
)
async def get_recommendation(
    claim_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(RecommendationRecord).where(RecommendationRecord.claim_id == claim_id)
    )
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No recommendation found for claim '{claim_id}'. "
                "Run POST /api/v1/claims/{id}/analyze to generate one."
            )
        )
    return rec


@router.get(
    "/claims/{claim_id}/phase7",
    response_model=Phase7AnalysisResponse,
    summary="Get Full Phase 7 Analysis (Fraud + Recommendation)",
    description=(
        "Returns both the fraud risk assessment and recommendation for a claim in a single response. "
        "Both fields are optional — only present if Phase 7 workflow has been executed."
    )
)
async def get_phase7_analysis(
    claim_id: str,
    db: AsyncSession = Depends(get_db)
):
    fa_result = await db.execute(
        select(FraudAssessment).where(FraudAssessment.claim_id == claim_id)
    )
    fa = fa_result.scalar_one_or_none()

    rr_result = await db.execute(
        select(RecommendationRecord).where(RecommendationRecord.claim_id == claim_id)
    )
    rr = rr_result.scalar_one_or_none()

    if not fa and not rr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No Phase 7 analysis found for claim '{claim_id}'. "
                "Run POST /api/v1/claims/{id}/analyze to generate one."
            )
        )

    evidence_count = len(fa.normalized_evidence_json) if fa and fa.normalized_evidence_json else 0

    return Phase7AnalysisResponse(
        claim_id=claim_id,
        fraud_assessment=FraudAssessmentRead.model_validate(fa) if fa else None,
        recommendation=RecommendationRecordRead.model_validate(rr) if rr else None,
        normalized_evidence_count=evidence_count,
        workflow_status="completed" if fa else "pending",
        message="Phase 7 fraud detection and recommendation analysis retrieved successfully."
    )
