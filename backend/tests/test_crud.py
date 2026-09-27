import pytest
from app.schemas.customer import CustomerCreate
from app.schemas.policy import PolicyCreate
from app.schemas.claim import ClaimCreate
from app.schemas.document import ClaimDocumentCreate, OCRFieldCreate
from app.schemas.audit_log import AuditLogCreate
from app.services.customer_service import create_customer, get_customer_by_id
from app.services.policy_service import create_policy, get_policy_by_number, list_policies_by_customer
from app.services.claim_service import create_claim, get_claim_by_id
from app.services.document_service import create_document, get_document_by_id
from app.services.audit_service import create_audit_log, list_audit_logs

@pytest.mark.asyncio
async def test_create_customer(db_session):
    payload = CustomerCreate(
        id="cust-test-101",
        name="Jane Doe",
        phone="+1 (555) 111-2222",
        email="jane.doe@example.com",
        dob="1992-05-15",
        address="123 Main Street, New York, NY",
        national_id="SSN-XXX-XX-9999",
        member_since="2021-01-01",
        risk_score=5.0
    )
    customer = await create_customer(db_session, payload)
    assert customer.id == "cust-test-101"
    assert customer.name == "Jane Doe"
    assert customer.email == "jane.doe@example.com"
    assert customer.national_id == "SSN-XXX-XX-9999"

    # Fetch back
    fetched = await get_customer_by_id(db_session, "cust-test-101")
    assert fetched is not None
    assert fetched.name == "Jane Doe"

@pytest.mark.asyncio
async def test_create_policy_and_customer_relationship(db_session):
    # Create Customer first
    cust_payload = CustomerCreate(
        id="cust-test-102",
        name="Robert Smith",
        phone="+1 (555) 333-4444",
        email="robert.smith@example.com",
        dob="1980-08-20",
        address="456 Elm St, Boston, MA",
        national_id="SSN-XXX-XX-8888",
        member_since="2020-03-15",
        risk_score=10.0
    )
    customer = await create_customer(db_session, cust_payload)

    # Create Policy for customer
    pol_payload = PolicyCreate(
        policy_number="POL-HEALTH-7711",
        category="Health",
        start_date="2025-01-01",
        end_date="2027-01-01",
        premium_status="Paid",
        coverage_limit=100000.0,
        deductible=1000.0,
        active_claims_count=0,
        customer_id=customer.id
    )
    policy = await create_policy(db_session, pol_payload)
    assert policy.policy_number == "POL-HEALTH-7711"
    assert policy.customer_id == customer.id

    # Verify Customer -> Policy relationship
    user_policies = await list_policies_by_customer(db_session, customer.id)
    assert len(user_policies) == 1
    assert user_policies[0].policy_number == "POL-HEALTH-7711"

@pytest.mark.asyncio
async def test_create_claim_and_policy_relationship(db_session):
    # Setup Customer and Policy
    cust_payload = CustomerCreate(
        id="cust-test-103",
        name="Alice Johnson",
        phone="+1 (555) 555-6666",
        email="alice.j@example.com",
        dob="1988-12-04",
        address="789 Pine Ave, Chicago, IL",
        national_id="SSN-XXX-XX-7777",
        member_since="2022-06-10",
        risk_score=8.0
    )
    customer = await create_customer(db_session, cust_payload)

    pol_payload = PolicyCreate(
        policy_number="POL-AUTO-5544",
        category="Vehicle",
        start_date="2025-02-01",
        end_date="2027-02-01",
        premium_status="Paid",
        coverage_limit=40000.0,
        deductible=500.0,
        active_claims_count=1,
        customer_id=customer.id
    )
    policy = await create_policy(db_session, pol_payload)

    # Create Claim
    claim_payload = ClaimCreate(
        claim_number="CLM-2026-9900",
        title="Side fender scratch at parking lot",
        description="Damage incurred while parked at shopping mall lot.",
        category="Vehicle",
        priority="Medium",
        is_emergency=False,
        status="Submitted",
        incident_date="2026-08-10",
        incident_time="11:15",
        location="Downtown Mall Parking, Chicago IL",
        claim_amount=1500.0,
        assigned_officer="Officer Sarah Jenkins",
        customer_id=customer.id,
        policy_number=policy.policy_number
    )
    claim = await create_claim(db_session, claim_payload)
    assert claim.id is not None
    assert claim.claim_number == "CLM-2026-9900"
    assert claim.customer_id == customer.id
    assert claim.policy_number == policy.policy_number

    # Fetch complete claim with relations
    fetched_claim = await get_claim_by_id(db_session, claim.id)
    assert fetched_claim is not None
    assert fetched_claim.customer.name == "Alice Johnson"
    assert fetched_claim.policy.category == "Vehicle"
    assert len(fetched_claim.audit_logs) >= 1

@pytest.mark.asyncio
async def test_document_and_audit_logs(db_session):
    # Setup Customer, Policy, Claim
    cust = await create_customer(db_session, CustomerCreate(
        id="cust-test-104", name="Charlie Brown", phone="555-0000", email="charlie@example.com",
        dob="1995-01-01", address="100 Oak St", national_id="SSN-XXX-XX-1234", member_since="2023-01-01"
    ))
    pol = await create_policy(db_session, PolicyCreate(
        policy_number="POL-HOME-123", category="Home", start_date="2025-01-01", end_date="2027-01-01",
        coverage_limit=200000.0, deductible=1000.0, customer_id=cust.id
    ))
    claim = await create_claim(db_session, ClaimCreate(
        claim_number="CLM-2026-1122", title="Water pipe burst in kitchen", description="Flooding damage",
        category="Home", incident_date="2026-08-12", incident_time="08:00", location="Home", claim_amount=8500.0,
        customer_id=cust.id, policy_number=pol.policy_number
    ))

    # Add Document
    doc_payload = ClaimDocumentCreate(
        claim_id=claim.id,
        file_name="Plumber_Invoice.pdf",
        file_path="uploads/claims/claim-104/Plumber_Invoice.pdf",
        file_size="1.2 MB",
        type="PDF",
        category="Repair Estimate",
        upload_date="2026-08-12T10:00:00Z",
        ocr_status="Completed",
        verification_status="Verified",
        ocr_fields=[
            OCRFieldCreate(field_name="Total Cost", extractedValue="$8,500.00", confidence=99.0, status="Verified")
        ]
    )
    doc = await create_document(db_session, doc_payload)
    assert doc.id is not None
    assert doc.claim_id == claim.id

    fetched_doc = await get_document_by_id(db_session, doc.id)
    assert fetched_doc is not None
    assert len(fetched_doc.ocr_fields) == 1
    assert fetched_doc.ocr_fields[0].field_name == "Total Cost"

    # Verify Audit Logs
    logs = await list_audit_logs(db_session, claim_id=claim.id)
    assert len(logs) >= 1
    assert logs[0].action == "Claim Registered"
