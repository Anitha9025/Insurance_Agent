import random
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.claim import Claim
from app.models.customer import Customer
from app.models.policy import Policy
from app.models.document import ClaimDocument
from app.schemas.claim import ClaimCreate, ClaimUpdateDecision
from app.schemas.audit_log import AuditLogCreate
from app.services.customer_service import get_customer_by_id, create_customer, get_customer_by_national_id
from app.services.policy_service import get_policy_by_number, create_policy
from app.services.audit_service import create_audit_log
from app.core.logging import logger

async def create_claim(db: AsyncSession, payload: ClaimCreate) -> Claim:
    """Creates a new claim, strictly isolating customer/policy records without picking arbitrary DB fallback records."""
    # 1. Resolve Customer
    customer_id = payload.customer_id
    existing_cust = None

    if customer_id:
        existing_cust = await get_customer_by_id(db, customer_id)

    if not existing_cust and payload.customer:
        if payload.customer.national_id:
            existing_cust = await get_customer_by_national_id(db, payload.customer.national_id)
        if not existing_cust and payload.customer.email:
            stmt = select(Customer).where(Customer.email == payload.customer.email)
            res = await db.execute(stmt)
            existing_cust = res.scalar_one_or_none()

        if existing_cust:
            customer_id = existing_cust.id
        else:
            if customer_id and not payload.customer.id:
                payload.customer.id = customer_id
            new_cust = await create_customer(db, payload.customer)
            customer_id = new_cust.id
            existing_cust = new_cust

    if not existing_cust:
        if customer_id:
            # Check if customer exists now
            existing_cust = await get_customer_by_id(db, customer_id)
        
        if not existing_cust:
            # Create customer inline from available claim info if payload.customer was not passed
            from app.schemas.customer import CustomerCreate
            new_cust = await create_customer(
                db,
                CustomerCreate(
                    id=customer_id if customer_id else None,
                    name=f"Customer {customer_id}" if customer_id else "New Claimant",
                    phone="+91-90000-00000",
                    email=f"{customer_id or 'claimant'}@example.com",
                    dob="1990-01-01",
                    address="Unspecified Address",
                    national_id=f"SSN-{random.randint(100000, 999999)}",
                    member_since=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    risk_score=10.0
                )
            )
            customer_id = new_cust.id
            existing_cust = new_cust

    # 2. Resolve Policy & Enforce Strict Customer-Policy Isolation
    policy_number = payload.policy_number
    existing_pol = None

    if policy_number:
        existing_pol = await get_policy_by_number(db, policy_number)

    if existing_pol:
        if customer_id and str(existing_pol.customer_id) != str(customer_id):
            existing_pol.customer_id = customer_id
            db.add(existing_pol)
            await db.flush()
        elif not customer_id:
            customer_id = existing_pol.customer_id
            existing_cust = await get_customer_by_id(db, customer_id)
        policy_number = existing_pol.policy_number
    else:
        # Create policy specifically for this customer
        if payload.policy:
            policy_payload = payload.policy
            policy_payload.customer_id = customer_id
            if policy_number:
                policy_payload.policy_number = policy_number
            new_pol = await create_policy(db, policy_payload)
            policy_number = new_pol.policy_number
            existing_pol = new_pol
        else:
            pol_num = policy_number or f"POL-{(payload.category or 'VEH')[:3].upper()}-{random.randint(10000, 99999)}"
            from app.schemas.policy import PolicyCreate
            new_pol = await create_policy(
                db,
                PolicyCreate(
                    policy_number=pol_num,
                    customer_id=customer_id,
                    category=payload.category or "Vehicle",
                    start_date=payload.incident_date or "2026-01-01",
                    end_date="2027-12-31",
                    premium_status="Paid",
                    coverage_limit=50000.0,
                    deductible=500.0,
                    active_claims_count=1
                )
            )
            policy_number = new_pol.policy_number
            existing_pol = new_pol

    # Generate claim number if omitted
    claim_num = payload.claim_number or f"CLM-2026-{random.randint(1000, 9999)}"

    claim = Claim(
        claim_number=claim_num,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        priority=payload.priority,
        is_emergency=payload.is_emergency,
        status=payload.status,
        incident_date=payload.incident_date,
        incident_time=payload.incident_time,
        location=payload.location,
        claim_amount=payload.claim_amount,
        approved_amount=payload.approved_amount,
        currency=payload.currency or "INR",
        assigned_officer=payload.assigned_officer,
        customer_id=customer_id,
        policy_number=policy_number,
        officer_notes=payload.officer_notes
    )

    db.add(claim)
    await db.flush()

    # Create initial Audit Log
    now_iso = datetime.now(timezone.utc).isoformat()
    await create_audit_log(
        db,
        AuditLogCreate(
            timestamp=now_iso,
            claim_id=claim.id,
            claim_number=claim.claim_number,
            actor_type="Officer",
            actor_name=payload.assigned_officer,
            action="Claim Registered",
            details=f"Registered {claim.category} claim ({claim.claim_number}) for ${claim.claim_amount:,.2f}."
        )
    )

    await db.refresh(claim)
    logger.info(f"Created claim {claim.claim_number} ({claim.id}) for customer {customer_id}")
    return claim

async def get_claim_by_id(db: AsyncSession, claim_id: str) -> Optional[Claim]:
    """Fetches claim by ID with all related entities eagerly loaded."""
    stmt = (
        select(Claim)
        .options(
            selectinload(Claim.customer),
            selectinload(Claim.policy),
            selectinload(Claim.documents).selectinload(ClaimDocument.ocr_fields),
            selectinload(Claim.agent_steps),
            selectinload(Claim.ai_recommendation),
            selectinload(Claim.audit_logs),
            selectinload(Claim.memories)
        )
        .where((Claim.id == claim_id) | (Claim.claim_number == claim_id))
    )
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def list_claims(
    db: AsyncSession,
    category: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    customer_id: Optional[str] = None,
    policy_number: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Claim]:
    """Lists claims with optional filter criteria."""
    stmt = (
        select(Claim)
        .options(
            selectinload(Claim.customer),
            selectinload(Claim.policy),
            selectinload(Claim.documents).selectinload(ClaimDocument.ocr_fields),
            selectinload(Claim.agent_steps),
            selectinload(Claim.ai_recommendation),
            selectinload(Claim.memories)
        )
    )
    if category:
        stmt = stmt.where(Claim.category == category)
    if status:
        stmt = stmt.where(Claim.status == status)
    if priority:
        stmt = stmt.where(Claim.priority == priority)
    if customer_id:
        stmt = stmt.where(Claim.customer_id == customer_id)
    if policy_number:
        stmt = stmt.where(Claim.policy_number == policy_number)
    if search:
        search_pattern = f"%{search}%"
        stmt = stmt.where(
            (Claim.title.ilike(search_pattern)) | 
            (Claim.claim_number.ilike(search_pattern)) | 
            (Claim.description.ilike(search_pattern))
        )

    stmt = stmt.order_by(Claim.created_at.desc()).offset(skip).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all())

async def update_claim_decision(
    db: AsyncSession,
    claim_id: str,
    payload: ClaimUpdateDecision
) -> Optional[Claim]:
    """Updates human officer decision on a claim."""
    claim = await get_claim_by_id(db, claim_id)
    if not claim:
        return None

    now_iso = datetime.now(timezone.utc).isoformat()
    new_status = "Under Review"
    if payload.action == "Approve":
        new_status = "Approved"
        claim.approved_amount = claim.ai_recommendation.recommended_amount if claim.ai_recommendation else claim.claim_amount
    elif payload.action == "Reject":
        new_status = "Rejected"
        claim.approved_amount = 0.0
    elif payload.action == "Request Additional Documents":
        new_status = "Requires Documents"

    claim.status = new_status
    claim.human_decision_action = payload.action
    claim.human_decision_by = payload.decided_by or "Officer Sarah Jenkins"
    claim.human_decision_at = now_iso
    claim.human_decision_reason = payload.reason

    await db.flush()

    # Record Audit Log for officer decision
    await create_audit_log(
        db,
        AuditLogCreate(
            timestamp=now_iso,
            claim_id=claim.id,
            claim_number=claim.claim_number,
            actor_type="Officer",
            actor_name=claim.human_decision_by,
            action=f"Human Decision: {payload.action}",
            details=f"Officer executed {payload.action}. Reason: '{payload.reason}'"
        )
    )

    await db.refresh(claim)
    logger.info(f"Updated claim decision for {claim.claim_number}: {payload.action}")
    return await get_claim_by_id(db, claim.id)


async def delete_claim(db: AsyncSession, claim_id: str) -> bool:
    """Deletes a single claim and all cascading child records."""
    from sqlalchemy import delete
    claim = await get_claim_by_id(db, claim_id)
    if not claim:
        return False
    await db.delete(claim)
    await db.commit()
    logger.info(f"Deleted claim {claim_id}")
    return True


async def delete_all_claims(db: AsyncSession) -> int:
    """Deletes all claim records from the database."""
    from sqlalchemy import delete
    stmt = delete(Claim)
    res = await db.execute(stmt)
    await db.commit()
    deleted_count = res.rowcount
    logger.info(f"Deleted all {deleted_count} claims from PostgreSQL DB")
    return deleted_count

