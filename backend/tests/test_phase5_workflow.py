import pytest
import io
from app.agents.coordinator_agent import CoordinatorAgent
from app.agents.state import ClaimWorkflowState

@pytest.mark.asyncio
async def test_phase5_workflow_on_seeded_claim(client):
    """Test 1: Run Phase 5 workflow on seeded claim-101 via API endpoint."""
    res = client.post("/api/v1/claims/claim-101/analyze")
    assert res.status_code == 200
    
    data = res.json()
    assert data["claimId"] == "claim-101"
    assert data["workflowStatus"] == "completed"
    assert "Claim Intake Agent" in data["completedAgents"]
    assert "Customer Verification Agent" in data["completedAgents"]
    assert "Document Analysis Agent" in data["completedAgents"]
    assert "Policy Validation Agent" in data["completedAgents"]
    assert "Claim History Agent" in data["completedAgents"]

    # Verify Intake Agent output
    intake = data["intakeAnalysis"]
    assert intake["claimDataAvailable"] is True
    assert intake["claimType"] == "Vehicle"
    assert intake["claimAmount"] == 18450.0

    # Verify Customer Verification Agent output
    cust_verif = data["customerVerification"]
    assert cust_verif["customerFound"] is True
    assert cust_verif["verified"] is True
    assert "customer_name" in cust_verif["matchedFields"]

    # Verify Document Analysis Agent output
    doc_analysis = data["documentAnalysis"]
    assert doc_analysis["documentsAnalyzed"] >= 1

    # Verify Policy Validation Agent output
    pol_val = data["policyValidation"]
    assert pol_val["policyFound"] is True
    assert pol_val["policyActive"] is True
    assert pol_val["coverageAvailable"] is True
    assert pol_val["policyClauseValidationStatus"] == "policy_clause_validation_pending"

    # Verify Claim History Agent output
    history = data["claimHistory"]
    assert isinstance(history["totalPreviousClaims"], int)

@pytest.mark.asyncio
async def test_phase5_cross_claim_dynamic_behavior(client):
    """Test 2 & 11: Create a SECOND distinct claim for a different customer (Elena Rostova)
    and verify that running the exact same workflow yields dynamic, non-static outcomes.
    """
    # 1. Register Customer B
    cust2 = client.post("/api/v1/customers", json={
        "name": "Elena Rostova", "phone": "555-890-1234", "email": "elena@healthcorp.org",
        "dob": "1976-03-22", "address": "Chicago, IL", "nationalId": "SSN-XXX-XX-8912", "memberSince": "2021-01-15"
    }).json()

    # 2. Register Policy B
    pol2 = client.post("/api/v1/policies", json={
        "policyNumber": "POL-HLTH-77310", "category": "Health", "startDate": "2026-01-01",
        "endDate": "2026-12-31", "coverageLimit": 250000.0, "deductible": 2500.0, "customerId": cust2["id"]
    }).json()

    # 3. Create Claim B (Health category, $45,000 amount)
    claim2 = client.post("/api/v1/claims", json={
        "title": "Emergency knee surgery hospital admission", "description": "Surgical procedure following sports injury",
        "category": "Health", "incidentDate": "2026-06-15", "incidentTime": "09:00",
        "location": "Chicago General Hospital", "claimAmount": 45000.0,
        "customerId": cust2["id"], "policyNumber": pol2["policyNumber"]
    }).json()

    # 4. Trigger Phase 5 workflow on Claim B
    res2 = client.post(f"/api/v1/claims/{claim2['id']}/analyze")
    assert res2.status_code == 200
    data2 = res2.json()

    # Assert DYNAMIC differences between Claim 101 and Claim B
    assert data2["claimId"] == claim2["id"]
    assert data2["intakeAnalysis"]["claimType"] == "Health"
    assert data2["intakeAnalysis"]["claimAmount"] == 45000.0
    assert data2["policyValidation"]["policyNumber"] == "POL-HLTH-77310"
    assert data2["policyValidation"]["coverageLimit"] == 250000.0
    assert data2["customerVerification"]["matchedFields"] != []
    assert data2["claimHistory"]["totalPreviousClaims"] == 0  # No prior claims for Elena

@pytest.mark.asyncio
async def test_phase5_invalid_claim_id(client):
    """Test 9 & 10: Invalid claim ID and failure state handling."""
    res = client.post("/api/v1/claims/claim-non-existent-99999/analyze")
    assert res.status_code == 404
