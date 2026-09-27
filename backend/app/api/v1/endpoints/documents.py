import os
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.document import ClaimDocumentRead, ClaimDocumentCreate
from app.services import document_service, claim_service
from app.services.storage_service import storage_service
from app.core.logging import logger

router = APIRouter()

@router.post(
    "/claims/{claim_id}/documents",
    response_model=ClaimDocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Claim Document",
    description="Uploads a claim-related document (PDF, Image, Word), stores the binary on disk, and saves file metadata in PostgreSQL."
)
async def upload_document_endpoint(
    claim_id: str,
    file: UploadFile = File(...),
    category: str = Form("Damage Photo", description="Document Category ('Police Report', 'Repair Estimate', 'Damage Photo', etc.)"),
    type: Optional[str] = Form(None, description="Document type ('PDF', 'IMAGE', 'WORD')"),
    db: AsyncSession = Depends(get_db)
):
    # Verify claim exists
    claim = await claim_service.get_claim_by_id(db, claim_id)
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim '{claim_id}' not found."
        )

    # Read content & save file via storage abstraction
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    file_name = file.filename or "uploaded_document"
    
    # Infer doc type if omitted
    doc_type = type
    if not doc_type:
        if file_name.lower().endswith(".pdf"):
            doc_type = "PDF"
        elif file_name.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            doc_type = "IMAGE"
        else:
            doc_type = "WORD"

    file_path, file_size_str, file_url = storage_service.save_file(
        file_name=file_name,
        content=content,
        claim_id=claim.id
    )

    now_iso = datetime.now(timezone.utc).isoformat()
    doc_payload = ClaimDocumentCreate(
        claim_id=claim.id,
        file_name=file_name,
        file_path=file_path,
        file_size=file_size_str,
        type=doc_type,
        category=category,
        upload_date=now_iso,
        url=file_url,
        ocr_status="Pending",
        verification_status="Pending"
    )

    doc = await document_service.create_document(db, doc_payload)

    # Immediately trigger Document Agent OCR processing on upload so extracted fields are ready right away
    try:
        agent_input = DocumentAgentInput(
            document_id=doc.id,
            file_path=doc.file_path,
            file_name=doc.file_name,
            category_hint=doc.category
        )
        result = await document_agent.process_document(agent_input)

        doc.category = result.document_type
        doc.ocr_status = "Completed"
        doc.verification_status = "Flagged" if result.is_flagged_for_human_review else "Verified"

        seen_fields = set()
        for f in result.extracted_fields:
            field_key = f.field_name.lower().strip()
            if field_key in seen_fields:
                continue
            seen_fields.add(field_key)

            ocr_item = OCRField(
                document_id=doc.id,
                field_name=f.field_name,
                extracted_value=f.extracted_value,
                confidence=f.confidence,
                status=f.status
            )
            db.add(ocr_item)

        await db.flush()
    except Exception as ocr_err:
        logger.warning(f"Auto-OCR extraction warning for {file_name}: {ocr_err}")

    return await document_service.get_document_by_id(db, doc.id)

@router.get(
    "",
    response_model=List[ClaimDocumentRead],
    summary="List All Stored Documents & OCR Database Records",
    description="Retrieves all stored claim documents and their permanently persisted PostgreSQL OCR fields."
)
async def list_all_documents_endpoint(
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.document import ClaimDocument
    stmt = select(ClaimDocument).options(selectinload(ClaimDocument.ocr_fields))
    res = await db.execute(stmt)
    return list(res.scalars().all())

@router.get(
    "/claims/{claim_id}/documents",
    response_model=List[ClaimDocumentRead],
    summary="List Claim Documents",
    description="Lists all document metadata records attached to a specific claim."
)
async def list_claim_documents_endpoint(
    claim_id: str,
    db: AsyncSession = Depends(get_db)
):
    claim = await claim_service.get_claim_by_id(db, claim_id)
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim '{claim_id}' not found."
        )
    return await document_service.list_documents_by_claim(db, claim.id)

@router.get(
    "/{document_id}",
    response_model=ClaimDocumentRead,
    summary="Get Document Metadata",
    description="Retrieves metadata and extracted OCR fields for a specific document."
)
async def get_document_endpoint(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    doc = await document_service.get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found."
        )
    return doc

@router.get(
    "/files/{claim_id}/{filename}",
    summary="Serve / Download Uploaded Document",
    description="Serves the uploaded binary file from local storage."
)
async def serve_file_endpoint(
    claim_id: str,
    filename: str
):
    file_path = os.path.join("uploads", "claims", claim_id, filename)
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server."
        )
    return FileResponse(file_path)

from app.agents.document_agent import document_agent
from app.agents.schemas import DocumentAgentInput, DocumentAgentOutput
from app.models.document import OCRField

@router.post(
    "/{document_id}/ocr",
    response_model=DocumentAgentOutput,
    summary="Trigger Document Agent OCR Processing",
    description="Executes the Document Agent OCR pipeline: file validation, document classification, text extraction, structured information extraction, and confidence evaluation."
)
async def process_document_ocr_endpoint(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    doc = await document_service.get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found."
        )

    agent_input = DocumentAgentInput(
        document_id=doc.id,
        file_path=doc.file_path,
        file_name=doc.file_name,
        category_hint=doc.category
    )
    result = await document_agent.process_document(agent_input)

    # Clear any previous OCR fields for this document before inserting fresh ones (Deduplication)
    from sqlalchemy import delete
    await db.execute(delete(OCRField).where(OCRField.document_id == doc.id))

    # Persist extracted OCR fields to PostgreSQL DB
    doc.category = result.document_type
    doc.ocr_status = "Completed"
    doc.verification_status = "Flagged" if result.is_flagged_for_human_review else "Verified"

    seen_fields = set()
    for f in result.extracted_fields:
        field_key = f.field_name.lower().strip()
        if field_key in seen_fields:
            continue
        seen_fields.add(field_key)

        ocr_item = OCRField(
            document_id=doc.id,
            field_name=f.field_name,
            extracted_value=f.extracted_value,
            confidence=f.confidence,
            status=f.status
        )
        db.add(ocr_item)

    await db.flush()
    return result

from app.services.vision_analysis_service import vision_analysis_service

@router.post(
    "/claims/{claim_id}/analyze-images",
    summary="Analyze Multi-Image Claim Visual Evidence",
    description="Analyzes all image files attached to a claim independently using Cloud Multimodal Vision model and returns structured visual analysis results for each image."
)
async def analyze_claim_images_endpoint(
    claim_id: str,
    db: AsyncSession = Depends(get_db)
):
    claim = await claim_service.get_claim_by_id(db, claim_id)
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim '{claim_id}' not found."
        )

    image_docs = [
        d for d in claim.documents 
        if d.file_name.lower().endswith((".jpg", ".jpeg", ".png", ".webp")) or d.type == "IMAGE"
    ]
    if not image_docs:
        return {
            "claim_id": claim.id,
            "images": [],
            "note": "No image files attached to this claim."
        }

    image_paths = [d.file_path for d in image_docs]
    return await vision_analysis_service.analyze_claim_images(claim.id, image_paths)
