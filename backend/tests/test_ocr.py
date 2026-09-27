import os
import io
import pytest
from PIL import Image
from pypdf import PdfWriter

from app.ocr.validator import FileValidator, FileValidationError
from app.ocr.pdf_engine import PDFOCREngine
from app.ocr.image_engine import ImageOCREngine
from app.ocr.classifier import DocumentClassifier
from app.ocr.extractor import InformationExtractor
from app.agents.document_agent import DocumentAgent
from app.agents.schemas import DocumentAgentInput

@pytest.fixture
def sample_pdf(tmp_path):
    """Creates a temporary sample PDF file for testing."""
    pdf_path = str(tmp_path / "sample_police_report.pdf")
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    with open(pdf_path, "wb") as f:
        writer.write(f)
    return pdf_path

@pytest.fixture
def sample_image(tmp_path):
    """Creates a temporary sample PNG image file for testing."""
    img_path = str(tmp_path / "sample_receipt.png")
    img = Image.new("RGB", (400, 400), color=(255, 255, 255))
    img.save(img_path)
    return img_path


def test_file_validator(sample_pdf, tmp_path):
    # 1. Valid PDF
    ext, size = FileValidator.validate_file(sample_pdf)
    assert ext == ".pdf"
    assert size > 0

    # 2. Unsupported Extension
    unsupported = str(tmp_path / "test.exe")
    with open(unsupported, "w") as f:
        f.write("dummy")
    with pytest.raises(FileValidationError, match="Unsupported file format"):
        FileValidator.validate_file(unsupported)

    # 3. Non-existent File
    with pytest.raises(FileValidationError, match="File not found on disk"):
        FileValidator.validate_file(str(tmp_path / "missing.pdf"))


@pytest.mark.asyncio
async def test_pdf_ocr_engine(sample_pdf):
    engine = PDFOCREngine()
    res = await engine.extract_text(sample_pdf)
    assert res.page_count == 1
    assert res.confidence >= 40.0
    assert "PyPDF" in res.metadata["engine"]


@pytest.mark.asyncio
async def test_image_ocr_engine(sample_image):
    engine = ImageOCREngine()
    res = await engine.extract_text(sample_image)
    assert res.page_count == 1
    assert res.confidence == 90.0
    assert res.metadata["width"] == 400


def test_document_classifier():
    # 1. Police Report Text
    police_text = "Police Accident Incident Report. Officer Miller Badge #4412. Collision fault assigned."
    cat, conf = DocumentClassifier.classify(police_text)
    assert cat == "Police Report"
    assert conf > 80.0

    # 2. Repair Estimate Text
    estimate_text = "Auto Body Shop Estimate. Replacement parts and labor $4,500. Bumper repair."
    cat_est, conf_est = DocumentClassifier.classify(estimate_text)
    assert cat_est == "Repair Estimate"

    # 3. Category Hint Override
    cat_hint, conf_hint = DocumentClassifier.classify("generic text", category_hint="Medical Report")
    assert cat_hint == "Medical Report"
    assert conf_hint == 95.0


def test_information_extractor_no_fabrication():
    # Text with explicit Customer Name, Policy Number, and Amount
    text = "Insured: Alexander Vance. Policy Number: POL-AUTO-99824. Claim Amount: $18,450.00."
    fields, warnings = InformationExtractor.extract_fields(text, category="Police Report")

    field_dict = {f.field_name: f for f in fields}
    assert field_dict["customer_name"].extracted_value == "Alexander Vance"
    assert field_dict["customer_name"].status == "Verified"
    assert field_dict["policy_number"].extracted_value == "POL-AUTO-99824"
    assert field_dict["claim_amount"].extracted_value == "$18,450.00"

    # Test Missing Information (No Fabrication)
    empty_text = "Generic document text with no policy or name details."
    empty_fields, empty_warnings = InformationExtractor.extract_fields(empty_text)
    empty_field_dict = {f.field_name: f for f in empty_fields}

    assert empty_field_dict["customer_name"].extracted_value == "Not Found"
    assert empty_field_dict["customer_name"].status == "Flagged"
    assert "Customer name could not be automatically extracted." in empty_warnings


@pytest.mark.asyncio
async def test_information_extractor_async():
    text = "Insured Name: Smita Smita. Policy No: 36140031236803336579. Vehicle No: HR-98-4544."
    fields, warnings = await InformationExtractor.extract_fields_async(text, category="Motor Claim Form")
    field_dict = {f.field_name: f for f in fields}
    assert "customer_name" in field_dict
    assert field_dict["customer_name"].extracted_value == "Smita Smita"
    assert field_dict["policy_number"].extracted_value == "36140031236803336579"
    assert field_dict["vehicle_number"].extracted_value == "HR-98-4544"


@pytest.mark.asyncio
async def test_document_agent_end_to_end(sample_pdf):
    agent = DocumentAgent()
    payload = DocumentAgentInput(
        document_id="doc-test-101",
        file_path=sample_pdf,
        file_name="Police_Accident_Report.pdf",
        category_hint="Police Report"
    )
    result = await agent.process_document(payload)

    assert result.document_id == "doc-test-101"
    assert result.document_type == "Police Report"
    assert isinstance(result.extracted_fields, list)
    assert len(result.warnings) > 0  # Missing fields flagged for human review
    assert result.is_flagged_for_human_review is True


def test_ocr_api_endpoint(client, tmp_path):
    # 1. Setup Customer, Policy, Claim
    cust = client.post("/api/v1/customers", json={
        "name": "Sarah Connor", "phone": "555-0199", "email": "sarah@example.com",
        "dob": "1985-05-15", "address": "LA", "nationalId": "SSN-XXX-XX-9900", "memberSince": "2021-01-01"
    }).json()

    pol = client.post("/api/v1/policies", json={
        "policyNumber": "POL-AUTO-7711", "category": "Vehicle", "startDate": "2025-01-01",
        "endDate": "2027-01-01", "coverageLimit": 50000.0, "deductible": 500.0, "customerId": cust["id"]
    }).json()

    claim = client.post("/api/v1/claims", json={
        "title": "Vehicle collision on highway", "description": "Crash",
        "category": "Vehicle", "incidentDate": "2026-08-20", "incidentTime": "14:00",
        "location": "Highway 101", "claimAmount": 8500.0, "customerId": cust["id"], "policyNumber": pol["policyNumber"]
    }).json()

    # 2. Upload Document
    dummy_pdf = b"%PDF-1.4 Insured: Sarah Connor. Policy Number: POL-AUTO-7711. Claim Amount: $8,500.00."
    files = {"file": ("Police_Report.pdf", io.BytesIO(dummy_pdf), "application/pdf")}
    data = {"category": "Police Report", "type": "PDF"}
    doc_res = client.post(f"/api/v1/documents/claims/{claim['id']}/documents", files=files, data=data)
    assert doc_res.status_code == 201
    doc_id = doc_res.json()["id"]

    # 3. Trigger Document Agent OCR Endpoint
    ocr_res = client.post(f"/api/v1/documents/{doc_id}/ocr")
    assert ocr_res.status_code == 200
    agent_output = ocr_res.json()
    assert agent_output["documentId"] == doc_id
    assert agent_output["documentType"] == "Police Report"
    assert "extractedFields" in agent_output

    # 4. Verify OCR Metadata in GET Document
    doc_meta = client.get(f"/api/v1/documents/{doc_id}").json()
    assert doc_meta["ocrStatus"] == "Completed"
    assert len(doc_meta["ocrFields"]) >= 1
