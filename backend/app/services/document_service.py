from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.document import ClaimDocument, OCRField
from app.schemas.document import ClaimDocumentCreate
from app.core.logging import logger

async def create_document(db: AsyncSession, payload: ClaimDocumentCreate) -> ClaimDocument:
    """Creates a claim document metadata record and optional OCR fields."""
    doc = ClaimDocument(
        claim_id=payload.claim_id,
        file_name=payload.file_name,
        file_path=payload.file_path,
        file_size=payload.file_size,
        type=payload.type,
        category=payload.category,
        upload_date=payload.upload_date,
        url=payload.url,
        ocr_status=payload.ocr_status,
        verification_status=payload.verification_status
    )
    db.add(doc)
    await db.flush()

    if payload.ocr_fields:
        for field in payload.ocr_fields:
            ocr_item = OCRField(
                document_id=doc.id,
                field_name=field.field_name,
                extracted_value=field.extracted_value,
                confidence=field.confidence,
                status=field.status
            )
            db.add(ocr_item)
        await db.flush()

    logger.info(f"Created document {doc.file_name} ({doc.id}) for claim {doc.claim_id}")
    return doc

async def get_document_by_id(db: AsyncSession, doc_id: str) -> Optional[ClaimDocument]:
    """Fetches document by ID with eagerly loaded OCR fields."""
    stmt = select(ClaimDocument).options(selectinload(ClaimDocument.ocr_fields)).where(ClaimDocument.id == doc_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

async def list_documents_by_claim(db: AsyncSession, claim_id: str) -> List[ClaimDocument]:
    """Lists documents belonging to a claim."""
    stmt = select(ClaimDocument).options(selectinload(ClaimDocument.ocr_fields)).where(ClaimDocument.claim_id == claim_id)
    res = await db.execute(stmt)
    return list(res.scalars().all())
