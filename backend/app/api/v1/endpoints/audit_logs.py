from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.audit_log import AuditLogRead
from app.services import audit_service

router = APIRouter()

@router.get(
    "",
    response_model=List[AuditLogRead],
    summary="List Audit Logs",
    description="Lists system audit logs with optional filters for claim ID or actor type ('Officer' vs 'AI Agent')."
)
async def list_audit_logs_endpoint(
    claim_id: Optional[str] = Query(None, description="Filter logs by Claim ID"),
    actor_type: Optional[str] = Query(None, description="Filter logs by actor type ('Officer' or 'AI Agent')"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    return await audit_service.list_audit_logs(
        db,
        claim_id=claim_id,
        actor_type=actor_type,
        skip=skip,
        limit=limit
    )

@router.delete(
    "/all",
    summary="Delete All Audit Logs",
    description="Deletes all system audit log records from the database."
)
async def delete_all_audit_logs_endpoint(
    db: AsyncSession = Depends(get_db)
):
    count = await audit_service.delete_all_audit_logs(db)
    return {"message": f"Successfully deleted {count} audit log records."}

@router.delete(
    "/{log_id}",
    summary="Delete Single Audit Log",
    description="Deletes a single audit log record by ID."
)
async def delete_audit_log_endpoint(
    log_id: str,
    db: AsyncSession = Depends(get_db)
):
    from fastapi import HTTPException
    success = await audit_service.delete_audit_log(db, log_id)
    if not success:
        raise HTTPException(status_code=404, detail="Audit log entry not found")
    return {"message": "Audit log entry deleted successfully."}

