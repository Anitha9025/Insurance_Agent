import io
import pytest

def test_customer_api_flow(client):
    # 1. Create Customer
    payload = {
        "name": "Sarah Miller",
        "phone": "+1 (555) 777-8888",
        "email": "sarah.miller@example.com",
        "dob": "1991-03-25",
        "address": "55 Park Ave, San Francisco, CA",
        "nationalId": "SSN-XXX-XX-3344",
        "memberSince": "2022-04-10",
        "riskScore": 14.0
    }
    res = client.post("/api/v1/customers", json=payload)
    assert res.status_code == 201
    data = res.json()
    customer_id = data["id"]
    assert data["name"] == "Sarah Miller"
    assert data["nationalId"] == "SSN-XXX-XX-3344"

    # 2. Get Customer
    res_get = client.get(f"/api/v1/customers/{customer_id}")
    assert res_get.status_code == 200
    assert res_get.json()["email"] == "sarah.miller@example.com"

    # 3. List Customers
    res_list = client.get("/api/v1/customers")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # 4. Update Customer
    update_payload = {"phone": "+1 (555) 999-0000", "riskScore": 18.5}
    res_up = client.put(f"/api/v1/customers/{customer_id}", json=update_payload)
    assert res_up.status_code == 200
    assert res_up.json()["phone"] == "+1 (555) 999-0000"
    assert res_up.json()["riskScore"] == 18.5


def test_policy_api_flow(client):
    # Setup Customer
    cust_res = client.post("/api/v1/customers", json={
        "name": "David Clark",
        "phone": "+1 (555) 222-3333",
        "email": "david.clark@example.com",
        "dob": "1985-07-12",
        "address": "88 Oak Blvd, Seattle, WA",
        "nationalId": "SSN-XXX-XX-6655",
        "memberSince": "2020-01-15",
        "riskScore": 7.0
    })
    cust_id = cust_res.json()["id"]

    # 1. Create Policy
    policy_payload = {
        "policyNumber": "POL-AUTO-33221",
        "category": "Vehicle",
        "startDate": "2025-01-01",
        "endDate": "2027-01-01",
        "premiumStatus": "Paid",
        "coverageLimit": 60000.0,
        "deductible": 500.0,
        "activeClaimsCount": 0,
        "customerId": cust_id
    }
    res = client.post("/api/v1/policies", json=policy_payload)
    assert res.status_code == 201
    assert res.json()["policyNumber"] == "POL-AUTO-33221"

    # 2. Get Policy
    res_get = client.get("/api/v1/policies/POL-AUTO-33221")
    assert res_get.status_code == 200
    assert res_get.json()["category"] == "Vehicle"

    # 3. List Policies with Customer filter
    res_list = client.get(f"/api/v1/policies?customerId={cust_id}")
    assert res_list.status_code == 200
    assert len(res_list.json()) == 1


def test_claim_api_flow_and_decision(client):
    # Create Customer & Policy inline or setup
    cust_res = client.post("/api/v1/customers", json={
        "name": "Emily Watson",
        "phone": "+1 (555) 444-5555",
        "email": "emily.w@example.com",
        "dob": "1993-10-10",
        "address": "12 Maple St, Austin, TX",
        "nationalId": "SSN-XXX-XX-1122",
        "memberSince": "2021-08-01",
        "riskScore": 9.0
    })
    cust_id = cust_res.json()["id"]

    pol_res = client.post("/api/v1/policies", json={
        "policyNumber": "POL-HOME-99112",
        "category": "Home",
        "startDate": "2025-01-01",
        "endDate": "2027-01-01",
        "premiumStatus": "Paid",
        "coverageLimit": 150000.0,
        "deductible": 1000.0,
        "activeClaimsCount": 0,
        "customerId": cust_id
    })
    pol_num = pol_res.json()["policyNumber"]

    # 1. Create Claim
    claim_payload = {
        "title": "Roof storm damage from hail",
        "description": "Severe hailstorm damaged roof shingles and caused water leaks.",
        "category": "Home",
        "priority": "High",
        "isEmergency": False,
        "status": "Submitted",
        "incidentDate": "2026-08-15",
        "incidentTime": "16:00",
        "location": "12 Maple St, Austin, TX",
        "claimAmount": 12500.0,
        "assignedOfficer": "Officer Sarah Jenkins",
        "customerId": cust_id,
        "policyNumber": pol_num
    }
    res_claim = client.post("/api/v1/claims", json=claim_payload)
    assert res_claim.status_code == 201
    claim_data = res_claim.json()
    claim_id = claim_data["id"]
    assert claim_data["category"] == "Home"
    assert claim_data["customer"]["name"] == "Emily Watson"

    # 2. Get Claim Details
    res_get = client.get(f"/api/v1/claims/{claim_id}")
    assert res_get.status_code == 200
    assert res_get.json()["title"] == "Roof storm damage from hail"

    # 3. List Claims with Category Filter
    res_list = client.get("/api/v1/claims?category=Home")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # 4. Submit Human Officer Decision (Approve)
    decision_payload = {
        "action": "Approve",
        "reason": "Inspection confirms severe weather damage matching policy rider.",
        "decidedBy": "Officer Sarah Jenkins"
    }
    res_dec = client.patch(f"/api/v1/claims/{claim_id}/decision", json=decision_payload)
    assert res_dec.status_code == 200
    updated_claim = res_dec.json()
    assert updated_claim["status"] == "Approved"
    assert updated_claim["humanDecision"]["action"] == "Approve"


def test_document_upload_and_download(client):
    # Setup Customer, Policy, Claim
    cust = client.post("/api/v1/customers", json={
        "name": "Tom Hanks", "phone": "555-8888", "email": "tom@example.com",
        "dob": "1970-01-01", "address": "LA", "nationalId": "SSN-XXX-XX-5555", "memberSince": "2020-01-01"
    }).json()
    pol = client.post("/api/v1/policies", json={
        "policyNumber": "POL-TRAVEL-101", "category": "Travel", "startDate": "2025-01-01",
        "endDate": "2027-01-01", "coverageLimit": 20000.0, "deductible": 100.0, "customerId": cust["id"]
    }).json()
    claim = client.post("/api/v1/claims", json={
        "title": "Hospital stay during flight delay", "description": "Medical emergency",
        "category": "Travel", "incidentDate": "2026-08-01", "incidentTime": "12:00",
        "location": "Airport", "claimAmount": 3200.0, "customerId": cust["id"], "policyNumber": pol["policyNumber"]
    }).json()

    # 1. Upload Document (Multipart Form Data)
    dummy_file_content = b"%PDF-1.4 Dummy Hospital Receipt Content"
    files = {
        "file": ("Hospital_Invoice.pdf", io.BytesIO(dummy_file_content), "application/pdf")
    }
    data = {
        "category": "Invoice / Receipt",
        "type": "PDF"
    }
    res_up = client.post(f"/api/v1/documents/claims/{claim['id']}/documents", files=files, data=data)
    assert res_up.status_code == 201
    doc_data = res_up.json()
    doc_id = doc_data["id"]
    file_url = doc_data["url"]
    assert doc_data["fileName"] == "Hospital_Invoice.pdf"
    assert doc_data["category"] == "Invoice / Receipt"

    # 2. List Claim Documents
    res_docs = client.get(f"/api/v1/documents/claims/{claim['id']}/documents")
    assert res_docs.status_code == 200
    assert len(res_docs.json()) == 1

    # 3. Get Document Metadata
    res_meta = client.get(f"/api/v1/documents/{doc_id}")
    assert res_meta.status_code == 200
    assert res_meta.json()["id"] == doc_id

    # 4. Serve / Download File
    res_file = client.get(file_url)
    assert res_file.status_code == 200
    assert res_file.content == dummy_file_content


def test_audit_logs_api(client):
    res = client.get("/api/v1/audit-logs")
    assert res.status_code == 200
    logs = res.json()
    assert isinstance(logs, list)
