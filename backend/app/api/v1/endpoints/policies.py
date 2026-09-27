from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.policy import PolicyCreate, PolicyRead, PolicyVerificationRequest, PolicyVerificationResult
from app.services import policy_service, customer_service
from app.core.logging import logger

router = APIRouter()

@router.post(
    "/verify",
    response_model=PolicyVerificationResult,
    summary="Verify Policy Status",
    description="Validates a policy number against PostgreSQL database, customer link, date validity, and knowledge document availability."
)
async def verify_policy_post_endpoint(
    payload: PolicyVerificationRequest,
    db: AsyncSession = Depends(get_db)
):
    return await policy_service.verify_policy(db, payload.policy_number, payload.incident_date)

@router.get(
    "/{policy_number}/verify",
    response_model=PolicyVerificationResult,
    summary="Verify Policy by Number",
    description="Validates a policy number against PostgreSQL database records."
)
async def verify_policy_get_endpoint(
    policy_number: str,
    incident_date: Optional[str] = Query(None, description="Incident date to test policy validity window"),
    db: AsyncSession = Depends(get_db)
):
    return await policy_service.verify_policy(db, policy_number, incident_date)

@router.post(
    "",
    response_model=PolicyRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Policy",
    description="Registers a new insurance policy associated with a customer."
)
async def create_policy_endpoint(
    payload: PolicyCreate,
    db: AsyncSession = Depends(get_db)
):
    # Verify customer exists
    customer = await customer_service.get_customer_by_id(db, payload.customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Associated customer '{payload.customer_id}' not found."
        )

    # Check duplicate policy number
    existing = await policy_service.get_policy_by_number(db, payload.policy_number)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Policy number '{payload.policy_number}' already exists."
        )

    return await policy_service.create_policy(db, payload)

@router.get(
    "",
    response_model=List[PolicyRead],
    summary="List Policies",
    description="Lists insurance policies with optional customer filtering."
)
async def list_policies_endpoint(
    customer_id: Optional[str] = Query(None, description="Filter policies by Customer ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    return await policy_service.list_policies(db, customer_id=customer_id, skip=skip, limit=limit)

@router.get(
    "/{policy_number}",
    response_model=PolicyRead,
    summary="Get Policy",
    description="Fetches a policy record by its unique policy number."
)
async def get_policy_endpoint(
    policy_number: str,
    db: AsyncSession = Depends(get_db)
):
    policy = await policy_service.get_policy_by_number(db, policy_number)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy '{policy_number}' not found."
        )
    return policy

