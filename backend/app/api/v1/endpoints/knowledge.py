from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.knowledge_service import KnowledgeService
from app.agents.rag_agent import RAGKnowledgeAgent
from app.core.logging import logger

router = APIRouter()

class RAGQueryRequest(BaseModel):
    query: str
    category: Optional[str] = None

class IngestTextRequest(BaseModel):
    title: str
    content: str
    document_type: str = "policy"
    source_file: Optional[str] = None

@router.get(
    "/documents",
    summary="List Policy Knowledge Documents"
)
async def list_knowledge_documents(db: AsyncSession = Depends(get_db)):
    try:
        docs = await KnowledgeService.list_documents(db)
        return [
            {
                "id": d.id,
                "title": d.title,
                "document_type": d.document_type,
                "source_file": d.source_file,
                "policy_number": getattr(d, "policy_number", None),
                "is_active": d.is_active,
                "created_at": d.created_at.isoformat() if hasattr(d, "created_at") and d.created_at else "",
                "chunks_count": len(d.chunks) if hasattr(d, "chunks") and d.chunks else 0
            }
            for d in docs
        ]
    except Exception as e:
        import traceback
        err_msg = f"Failed to list knowledge documents: {type(e).__name__}: {str(e)} | {traceback.format_exc()[:300]}"
        logger.error(err_msg)
        raise HTTPException(status_code=500, detail=err_msg)



async def _extract_text_from_file(file: UploadFile, content_bytes: bytes) -> str:
    filename = (file.filename or "").lower()
    if filename.endswith(".pdf") or content_bytes.startswith(b"%PDF"):
        try:
            import io
            from pypdf import PdfReader
            pdf_file = io.BytesIO(content_bytes)
            reader = PdfReader(pdf_file)
            pages_text = []
            for page in reader.pages:
                t = page.extract_text() or ""
                if t.strip():
                    pages_text.append(t.strip())
            extracted = "\n\n".join(pages_text)
            if extracted.strip():
                return extracted.replace('\x00', '')
        except Exception as pdf_err:
            logger.warning(f"pypdf text extraction warning for {filename}: {pdf_err}")

    text = content_bytes.decode("utf-8", errors="ignore")
    return text.replace('\x00', '')

@router.post(
    "/upload",
    summary="Upload & Ingest Policy Knowledge Document"
)
async def upload_knowledge_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    document_type: str = Form("policy"),
    policy_number: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    try:
        content_bytes = await file.read()
        text_content = await _extract_text_from_file(file, content_bytes)

        if not text_content or not text_content.strip():
            text_content = f"Policy document {file.filename} uploaded."

        doc_title = title or file.filename or "Uploaded Policy Document"
        doc, chunks_cnt = await KnowledgeService.ingest_document(
            db=db,
            title=doc_title,
            content=text_content,
            document_type=document_type,
            source_file=file.filename,
            policy_number=policy_number
        )

        return {
            "message": f"Successfully ingested policy document '{doc_title}'",
            "document_id": doc.id,
            "title": doc.title,
            "policy_number": doc.policy_number,
            "chunks_created": chunks_cnt
        }
    except Exception as e:
        logger.error(f"Error uploading knowledge document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/ingest-text",
    summary="Ingest Raw Policy Text"
)
async def ingest_text_document(
    payload: IngestTextRequest,
    db: AsyncSession = Depends(get_db)
):
    doc, chunks_cnt = await KnowledgeService.ingest_document(
        db=db,
        title=payload.title,
        content=payload.content,
        document_type=payload.document_type,
        source_file=payload.source_file
    )
    return {
        "message": f"Ingested text document '{doc.title}'",
        "document_id": doc.id,
        "chunks_created": chunks_cnt
    }

@router.post(
    "/query",
    summary="Query Policy Knowledge Base (RAG)"
)
async def query_knowledge_base(
    payload: RAGQueryRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        res = await RAGKnowledgeAgent.query_policy_knowledge(
            db=db,
            query=payload.query,
            category=payload.category
        )
        return res
    except Exception as e:
        logger.error(f"Error querying policy knowledge base: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to query knowledge base: {str(e)}")

@router.delete(
    "/documents/{document_id}",
    summary="Delete Knowledge Document"
)
async def delete_knowledge_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    success = await KnowledgeService.delete_document(db, document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"message": "Knowledge document deleted successfully."}
