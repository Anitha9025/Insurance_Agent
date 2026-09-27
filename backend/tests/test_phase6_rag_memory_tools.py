import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.cloud_llm import generate_text, generate_json
from app.core.cloud_embedding import generate_embedding, generate_embeddings_batch
from app.models.customer import Customer
from app.models.policy import Policy
from app.models.claim import Claim
from app.agents.tools import (
    get_claim_by_id,
    get_customer_by_id,
    get_policy_by_number,
    get_customer_claims_history,
    get_claim_documents
)
from app.services.knowledge_service import KnowledgeService
from app.services.memory_service import MemoryService
from app.agents.rag_agent import RAGKnowledgeAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.coordinator_agent import CoordinatorAgent

@pytest.mark.asyncio
async def test_cloud_llm_and_embedding_abstractions():
    # 1. Test Text Generation
    text_res = await generate_text("Summarize insurance policy coverage in 1 line.", temperature=0.1)
    assert isinstance(text_res, str)
    assert len(text_res) > 0

    # 2. Test JSON Generation
    json_res = await generate_json("Return JSON with keys status='ok' and code=200")
    assert isinstance(json_res, dict)

    # 3. Test Embedding Vector Generation
    emb = await generate_embedding("Collision coverage deductible clause")
    assert isinstance(emb, list)
    assert len(emb) == 768

    batch_emb = await generate_embeddings_batch(["Text one", "Text two"])
    assert len(batch_emb) == 2
    assert len(batch_emb[0]) == 768

@pytest.mark.asyncio
async def test_controlled_db_tools(db_session: AsyncSession):
    # Setup test DB records
    cust = Customer(
        id="cust-test-1",
        name="Elena Rostova",
        email="elena.rostova@example.com",
        phone="+1-555-0199",
        national_id="ID-9921",
        address="101 Pine St",
        is_verified=True,
        risk_score=0.1
    )
    pol = Policy(
        policy_number="POL-AUTO-999",
        category="Vehicle",
        start_date="2025-01-01",
        end_date="2026-12-31",
        premium_status="Paid",
        coverage_limit=50000.0,
        deductible=500.0,
        customer_id=cust.id
    )
    claim = Claim(
        id="claim-test-1",
        claim_number="CLM-TEST-001",
        title="Vehicle Accident Frontal Bumper",
        description="Collision at intersection causing bumper damage",
        category="Vehicle",
        priority="Medium",
        is_emergency=False,
        status="Submitted",
        incident_date="2026-03-10",
        incident_time="14:30",
        location="Main St",
        claim_amount=2500.0,
        customer_id=cust.id,
        policy_number=pol.policy_number
    )
    db_session.add(cust)
    db_session.add(pol)
    db_session.add(claim)
    await db_session.commit()

    # Test get_claim_by_id tool
    tool_claim = await get_claim_by_id(db_session, "claim-test-1")
    assert tool_claim.success is True
    assert tool_claim.data["claim_number"] == "CLM-TEST-001"

    # Test get_customer_by_id tool
    tool_cust = await get_customer_by_id(db_session, "cust-test-1")
    assert tool_cust.success is True
    assert tool_cust.data["name"] == "Elena Rostova"

    # Test get_policy_by_number tool
    tool_pol = await get_policy_by_number(db_session, "POL-AUTO-999")
    assert tool_pol.success is True
    assert tool_pol.data["coverage_limit"] == 50000.0

@pytest.mark.asyncio
async def test_knowledge_service_and_rag_agent(db_session: AsyncSession):
    # 1. Ingest Policy Document into RAG store
    doc = await KnowledgeService.ingest_document(
        db=db_session,
        title="Master Vehicle Comprehensive Policy 2026",
        content="Section 4.1 Collision Coverage: The insurer covers front bumper and radiator damage up to $50,000 subject to a standard $500 deductible.",
        document_type="policy"
    )
    assert doc.id is not None
    assert len(doc.chunks) >= 1

    # 2. Search Knowledge Base via Vector Similarity
    search_results = await KnowledgeService.search_knowledge(
        db=db_session,
        query="front bumper radiator collision deductible limit",
        top_k=2
    )
    assert len(search_results) >= 1
    assert "Section 4.1" in search_results[0]["content"]

    # 3. Test RAGKnowledgeAgent
    rag_out = await RAGKnowledgeAgent.query_policy_knowledge(
        db=db_session,
        query="What is the collision deductible and coverage limit for front bumper damage?",
        category="Vehicle"
    )
    assert "answer" in rag_out
    assert len(rag_out["citations"]) >= 1

@pytest.mark.asyncio
async def test_memory_service_and_memory_agent(db_session: AsyncSession):
    # Setup test claim
    claim = Claim(
        id="claim-mem-1",
        claim_number="CLM-MEM-001",
        title="Side Door Dent Claim",
        description="Parking lot side door dent",
        category="Vehicle",
        priority="Low",
        status="Approved",
        incident_date="2026-02-01",
        incident_time="10:00",
        location="Parking Lot",
        claim_amount=850.0,
        customer_id="cust-1",
        policy_number="pol-1"
    )
    db_session.add(claim)
    await db_session.commit()

    # 1. Add Memory
    mem = await MemoryService.add_memory(
        db=db_session,
        claim_id=claim.id,
        memory_type="decision_rationale",
        memory_key="status_approved",
        memory_value="Approved parking lot side door dent claim within deductible limit",
        confidence_score=1.0,
        source_agent="Officer Sarah Jenkins"
    )
    assert mem.id is not None

    # 2. Search Memories
    search_mems = await MemoryService.search_memories(
        db=db_session,
        query="parking lot dent decision approved",
        top_k=3
    )
    assert len(search_mems) >= 1

    # 3. Test MemoryAgent
    mem_out = await MemoryAgent.retrieve_relevant_memories(
        db=db_session,
        claim_id="claim-mem-new",
        category="Vehicle",
        description="Side door parking scratch"
    )
    assert "summary" in mem_out

@pytest.mark.asyncio
async def test_coordinator_agent_phase6_swarm(db_session: AsyncSession):
    # Setup database record for full workflow execution
    cust = Customer(
        id="cust-swarm-1",
        name="Mark Watson",
        email="mark.watson@example.com",
        phone="+1-555-0821",
        national_id="ID-8812",
        address="404 Elm St",
        is_verified=True,
        risk_score=0.05
    )
    pol = Policy(
        policy_number="POL-SWARM-100",
        category="Vehicle",
        start_date="2025-01-01",
        end_date="2026-12-31",
        premium_status="Paid",
        coverage_limit=100000.0,
        deductible=250.0,
        customer_id=cust.id
    )
    claim = Claim(
        id="claim-swarm-1",
        claim_number="CLM-SWARM-100",
        title="Hail Storm Windshield Crack",
        description="Heavy hail storm cracked windshield while parked outside",
        category="Vehicle",
        priority="Medium",
        is_emergency=False,
        status="Submitted",
        incident_date="2026-04-12",
        incident_time="18:15",
        location="Residential Driveway",
        claim_amount=1200.0,
        customer_id=cust.id,
        policy_number=pol.policy_number
    )
    db_session.add(cust)
    db_session.add(pol)
    db_session.add(claim)
    await db_session.commit()

    state = await CoordinatorAgent.run_workflow(db_session, claim.id)
    assert state.workflow_status == "completed"
    assert "RAG Knowledge Agent" in state.completed_agents
    assert "Memory Agent" in state.completed_agents
    assert len(state.db_tool_calls) >= 1
