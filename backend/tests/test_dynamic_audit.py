import pytest
from app.agents.state import ClaimWorkflowState
from app.agents.intake_agent import ClaimIntakeAgent
from app.agents.document_analysis_agent import DocumentAnalysisAgent
from app.agents.customer_verification_agent import CustomerVerificationAgent

def test_intake_agent_document_count_fix():
    claim_data = {
        "id": "claim-test-1",
        "category": "Vehicle",
        "claim_amount": 15000.0,
        "incident_date": "2026-08-01",
        "description": "Vehicle accident description for testing intake count.",
        "customer_id": "cust-901",
        "policy_number": "POL-AUTO-99824"
    }
    
    # 2 documents attached
    documents_data = [
        {"id": "doc-1", "file_name": "police_report.pdf"},
        {"id": "doc-2", "file_name": "damage_photo.jpg"}
    ]

    result = ClaimIntakeAgent.analyze(claim_data, documents_data)
    assert result.is_complete is True
    assert result.documents_submitted_count == 2
    assert "No supporting documents submitted with claim." not in result.warnings

def test_document_analysis_cross_document_mismatch():
    documents_data = [
        {
            "id": "doc-101",
            "file_name": "claim_form_external.pdf",
            "category": "Police Report",
            "verification_status": "Flagged",
            "ocr_fields": [
                {"field_name": "customer_name", "extracted_value": "Smita Smita"},
                {"field_name": "incident_date", "extracted_value": "23-12-2023"},
                {"field_name": "policy_number", "extracted_value": "36140031236803336579"}
            ]
        }
    ]

    claim_data = {
        "id": "claim-101",
        "customer_name": "Alexander Vance",
        "incident_date": "2026-08-01",
        "policy_number": "POL-AUTO-99824"
    }

    customer_data = {
        "name": "Alexander Vance"
    }

    policy_data = {
        "policy_number": "POL-AUTO-99824"
    }

    res = DocumentAnalysisAgent.analyze(documents_data, claim_data, customer_data, policy_data)
    
    assert res.has_flagged_documents is True
    assert len(res.uncertainties) > 0
    # Assert structured mismatch evidence lines exist
    mismatch_text = " ".join(res.uncertainties)
    assert "Smita Smita" in mismatch_text
    assert "Alexander Vance" in mismatch_text
    assert "Document Mismatch" in mismatch_text

def test_customer_verification_agent_matching():
    customer_data = {
        "id": "cust-901",
        "name": "Alexander Vance",
        "email": "alex.vance@enterprise.com",
        "phone": "+1 (555) 234-5678",
        "national_id": "SSN-XXX-XX-4891"
    }

    claim_data = {
        "customer_id": "cust-901",
        "customer_name": "Alexander Vance",
        "email": "alex.vance@enterprise.com",
        "phone": "+1 (555) 234-5678",
        "national_id": "SSN-XXX-XX-4891"
    }

    res = CustomerVerificationAgent.verify(customer_data, claim_data)
    assert res.customer_found is True
    assert res.verification_status == "Verified"
    assert len(res.mismatches) == 0
