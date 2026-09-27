import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.customer import Customer
from app.models.policy import Policy
from app.models.claim import Claim
from app.models.knowledge import KnowledgeDocument
from app.services.policy_service import verify_policy, create_policy
from app.services.knowledge_service import KnowledgeService
from app.agents.rag_agent import RAGKnowledgeAgent
from app.agents.policy_validation_agent import PolicyValidationAgent
from app.agents.coordinator_agent import CoordinatorAgent


@pytest.mark.asyncio
async def test_scenario_a_policy_found_with_document(db_session: AsyncSession):
    """
    Test Scenario A:
    - Policy POL-AUTO-99824 exists in PostgreSQL.
    - Customer policy document ingested for POL-AUTO-99824.
    - Claim registered using policy number without uploading policy PDF again.
    - RAG retrieves correct policy clauses for POL-AUTO-99824.
    """
    # 1. Ingest policy document for POL-AUTO-99824
    content = (
        "POL-AUTO-99824 Standard Comprehensive Auto Policy. "
        "Comprehensive collision coverage includes bumper, fender, and engine repair with $500 deductible. "
        "Compulsory third-party liability coverage up to $50,000 limit."
    )
    doc, chunks_count = await KnowledgeService.ingest_document(
        db=db_session,
        title="POL-AUTO-99824 Policy Terms",
        content=content,
        document_type="policy",
        policy_number="POL-AUTO-99824"
    )
    assert doc.policy_number == "POL-AUTO-99824"
    assert chunks_count > 0

    # 2. Verify Policy via parameterized DB service
    verification = await verify_policy(db_session, "POL-AUTO-99824", incident_date="2026-08-01")
    assert verification["status"] == "policy_found"
    assert verification["policy_exists"] is True
    assert verification["is_active"] is True
    assert verification["policy_document_available"] is True
    assert verification["policy_document_title"] == "POL-AUTO-99824 Policy Terms"

    # 3. Test RAG Retrieval with policy_number filter
    rag_res = await RAGKnowledgeAgent.query_policy_knowledge(
        db=db_session,
        query="collision coverage deductible",
        category="Vehicle",
        policy_number="POL-AUTO-99824"
    )
    assert rag_res["is_grounded"] is True
    assert len(rag_res["citations"]) > 0
    assert rag_res["citations"][0]["document_title"] == "POL-AUTO-99824 Policy Terms"


@pytest.mark.asyncio
async def test_scenario_b_policy_found_document_unavailable(db_session: AsyncSession):
    """
    Test Scenario B:
    - Policy exists in PostgreSQL (e.g. create a test policy POL-TEST-NODOC).
    - No customer policy document is ingested in Knowledge Base for POL-TEST-NODOC.
    - System returns policy_document_unavailable status and RAG returns insufficient evidence warning.
    - System DOES NOT substitute generic development sample policy as fallback.
    """
    # 1. Create policy without document
    pol = Policy(
        policy_number="POL-TEST-NODOC",
        category="Vehicle",
        start_date="2025-01-01",
        end_date="2027-01-01",
        premium_status="Paid",
        coverage_limit=30000.0,
        deductible=250.0,
        customer_id="cust-901"
    )
    db_session.add(pol)
    await db_session.flush()

    # 2. Verify Policy
    verification = await verify_policy(db_session, "POL-TEST-NODOC", incident_date="2026-05-01")
    assert verification["status"] == "policy_document_unavailable"
    assert verification["policy_exists"] is True
    assert verification["policy_document_available"] is False
    assert any("No customer-specific policy document" in w for w in verification["warnings"])

    # 3. Test RAG Retrieval with policy_number="POL-TEST-NODOC"
    rag_res = await RAGKnowledgeAgent.query_policy_knowledge(
        db=db_session,
        query="collision deductible coverage",
        category="Vehicle",
        policy_number="POL-TEST-NODOC"
    )
    assert rag_res["confidence"] == 0.0
    assert rag_res["is_grounded"] is False
    assert rag_res["uncertainty_flag"] is True
    assert "Customer-specific policy document is unavailable" in rag_res["answer"]


@pytest.mark.asyncio
async def test_scenario_c_policy_not_found(db_session: AsyncSession):
    """
    Test Scenario C:
    - Policy number POL-NONEXISTENT does not exist.
    - Verification returns policy_not_found status and clear error message.
    - No synthetic policy is created.
    """
    verification = await verify_policy(db_session, "POL-NONEXISTENT")
    assert verification["status"] == "policy_not_found"
    assert verification["policy_exists"] is False
    assert any("not found in PostgreSQL" in issue for issue in verification["issues"])

    # Verify no synthetic policy record was inserted
    res = await db_session.execute(select(Policy).where(Policy.policy_number == "POL-NONEXISTENT"))
    assert res.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_scenario_d_policy_expired(db_session: AsyncSession):
    """
    Test Scenario D:
    - Policy POL-EXPIRED exists but expired in 2024.
    - Incident date is 2026-06-01 (outside coverage window).
    - Verification returns policy_expired status and issues warning.
    - PolicyValidationAgent flags incident date outside active date range.
    """
    pol = Policy(
        policy_number="POL-EXPIRED-2024",
        category="Vehicle",
        start_date="2023-01-01",
        end_date="2024-01-01",
        premium_status="Paid",
        coverage_limit=25000.0,
        deductible=500.0,
        customer_id="cust-901"
    )
    db_session.add(pol)
    await db_session.flush()

    verification = await verify_policy(db_session, "POL-EXPIRED-2024", incident_date="2026-06-01")
    assert verification["status"] == "policy_expired"
    assert verification["is_expired"] is True
    assert verification["is_active"] is False

    val_res = PolicyValidationAgent.validate(
        policy_data={
            "policy_number": "POL-EXPIRED-2024",
            "category": "Vehicle",
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
            "premium_status": "Paid"
        },
        claim_data={"incident_date": "2026-06-01", "category": "Vehicle"}
    )
    assert val_res.policy_active is False
    assert any("outside active policy date range" in issue for issue in val_res.issues)
