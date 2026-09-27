import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal, engine, Base
from app.models.customer import Customer
from app.models.policy import Policy
from app.models.claim import Claim
from app.models.document import ClaimDocument, OCRField
from app.models.agent_step import AIAgentStep
from app.models.recommendation import AIRecommendation
from app.models.audit_log import AuditLog
from app.core.logging import logger

async def init_db(db: AsyncSession):
    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Check if seed data already exists
    from sqlalchemy import select
    res = await db.execute(select(Customer).where(Customer.id == "cust-901"))
    if res.scalar_one_or_none():
        logger.info("Seed data already present in database.")
        return

    logger.info("Seeding initial development database records...")

    # 1. Seed Customer
    cust = Customer(
        id="cust-901",
        name="Alexander Vance",
        phone="+1 (555) 234-5678",
        email="alex.vance@enterprise.com",
        dob="1984-11-14",
        address="742 Evergreen Terrace, Springfield, PA 19064",
        national_id="SSN-XXX-XX-4891",
        member_since="2019-04-12",
        risk_score=12.0
    )
    db.add(cust)
    await db.flush()

    # 2. Seed Policy
    pol = Policy(
        policy_number="POL-AUTO-99824",
        category="Vehicle",
        start_date="2025-05-01",
        end_date="2027-05-01",
        premium_status="Paid",
        coverage_limit=50000.00,
        deductible=500.00,
        active_claims_count=1,
        customer_id=cust.id
    )
    db.add(pol)
    await db.flush()

    # 3. Seed Claim
    claim = Claim(
        id="claim-101",
        claim_number="CLM-2026-8841",
        title="Multi-vehicle collision on Interstate 95 highway",
        description="Vehicle sustained heavy front bumper, hood, and radiator damage following a 3-car pileup during heavy rainfall. Third-party liability involved.",
        category="Vehicle",
        priority="Emergency",
        is_emergency=True,
        status="Under Review",
        incident_date="2026-08-01",
        incident_time="14:30",
        location="I-95 Exit 42, Philadelphia, PA",
        claim_amount=18450.00,
        approved_amount=16800.00,
        assigned_officer="Officer Sarah Jenkins",
        customer_id=cust.id,
        policy_number=pol.policy_number
    )
    db.add(claim)
    await db.flush()

    # 4. Seed Documents & OCR
    doc1 = ClaimDocument(
        id="doc-01",
        claim_id=claim.id,
        file_name="Police_Accident_Report_8841.pdf",
        file_path="uploads/claims/claim-101/Police_Accident_Report_8841.pdf",
        file_size="2.4 MB",
        type="PDF",
        category="Police Report",
        upload_date="2026-08-02T10:00:00Z",
        url="#",
        ocr_status="Completed",
        verification_status="Verified"
    )
    db.add(doc1)
    await db.flush()

    ocr1 = OCRField(
        id="ocr-1",
        document_id=doc1.id,
        field_name="Police Officer Name",
        extracted_value="Sgt. R. Miller (Badge #4012)",
        confidence=99.2,
        status="Verified"
    )
    ocr2 = OCRField(
        id="ocr-2",
        document_id=doc1.id,
        field_name="Fault Determination",
        extracted_value="Car #2 (Third Party) Failed to stop",
        confidence=96.5,
        status="Verified"
    )
    db.add_all([ocr1, ocr2])

    # 5. Seed Agent Steps
    step1 = AIAgentStep(
        id="step-1",
        claim_id=claim.id,
        agent_name="Intake Agent",
        status="Completed",
        timestamp="2026-08-02T10:15:01Z",
        duration_ms=420,
        output_summary="Parsed claim metadata. Verified policy holder Alexander Vance."
    )
    db.add(step1)

    # 6. Seed AI Recommendation
    rec = AIRecommendation(
        id="rec-1",
        claim_id=claim.id,
        verdict="Approve",
        confidence_score=94.8,
        fraud_risk_score=14.0,
        recommended_amount=17950.00,
        reasoning_summary="Claim registration meets all primary coverage criteria. Documentation is consistent with policy limits.",
        key_findings=["Policy is active with no overdue premiums.", "Claim amount within threshold."],
        risk_flags=[],
        retrieved_memories=[],
        retrieved_knowledge=[],
        tool_calls=[]
    )
    db.add(rec)

    # 7. Seed Audit Log
    log = AuditLog(
        id="log-501",
        timestamp="2026-08-02T10:15:07Z",
        claim_id=claim.id,
        claim_number=claim.claim_number,
        actor_type="AI Agent",
        actor_name="Recommendation Agent",
        action="AI Recommendation Generated",
        details="Synthesized final verdict: APPROVE payout of $17,950 after $500 deductible.",
        ip_address="10.240.12.89"
    )
    db.add(log)

    # 8. Seed Claim Memories
    from app.services.memory_service import MemoryService
    await MemoryService.add_memory(
        db=db,
        claim_id=claim.id,
        memory_type="officer_decision",
        memory_key="deductible_policy_approval",
        memory_value="Approved auto collision claim payout of $16,800. Applied mandatory $500 policy deductible based on Police Accident Report #8841.",
        confidence_score=0.98,
        source_agent="Coordinator Agent"
    )
    await MemoryService.add_memory(
        db=db,
        claim_id=claim.id,
        memory_type="fraud_analysis",
        memory_key="low_risk_verification",
        memory_value="Verified low fraud risk index (12/100). Policy premiums fully paid; police officer report badge #4012 confirmed third-party fault.",
        confidence_score=0.96,
        source_agent="Fraud Agent"
    )

    await db.commit()

    # 9. Seed Policy Knowledge Documents linked to policy_number
    from app.services.knowledge_service import KnowledgeService
    await KnowledgeService.ingest_document(
        db=db,
        title="POL-AUTO-99824 Master Comprehensive Auto Insurance Policy",
        content=(
            "POL-AUTO-99824 Comprehensive Auto Insurance Terms & Conditions. "
            "Section 1: Coverage Limits & Deductibles. Maximum bodily injury and property collision coverage is $50,000 per incident. "
            "A standard $500 deductible applies to collision damage repairs. "
            "Section 2: Exclusions. Excludes intentional acts, unauthorized racing, and unlisted drivers under 21. "
            "Section 3: Incident Reporting. Claims must be filed within 30 days of incident date accompanied by police accident reports."
        ),
        document_type="policy",
        policy_number="POL-AUTO-99824"
    )

    await KnowledgeService.ingest_document(
        db=db,
        title="DEV-AUTO-000001 Development Fictional Sample Vehicle Insurance Policy",
        content=(
            "DEV-AUTO-000001 Fictional Academic Sample Policy. "
            "Standard collision terms, $500 deductible, $50,000 maximum limit. "
            "Notice: This is a generic test template for RAG evaluation only and must not be treated as a real customer policy."
        ),
        document_type="policy",
        policy_number="DEV-AUTO-000001"
    )

    logger.info("Seed data successfully populated.")


async def main():
    async with AsyncSessionLocal() as session:
        await init_db(session)

if __name__ == "__main__":
    asyncio.run(main())
