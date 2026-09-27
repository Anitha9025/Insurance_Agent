from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogCreate
from app.core.logging import logger

async def create_audit_log(db: AsyncSession, payload: AuditLogCreate) -> AuditLog:
    """Creates a new audit log record."""
    log_entry = AuditLog(
        timestamp=payload.timestamp,
        claim_id=payload.claim_id,
        claim_number=payload.claim_number,
        actor_type=payload.actor_type,
        actor_name=payload.actor_name,
        action=payload.action,
        details=payload.details,
        memory_used=payload.memory_used,
        knowledge_used=payload.knowledge_used,
        tools_called=payload.tools_called,
        ip_address=payload.ip_address
    )
    db.add(log_entry)
    await db.flush()
    logger.info(f"Audit Log recorded: [{log_entry.actor_type}] {log_entry.action} on claim {log_entry.claim_number}")
    return log_entry

async def list_audit_logs(
    db: AsyncSession,
    claim_id: Optional[str] = None,
    actor_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[AuditLog]:
    """Lists audit logs with optional filters."""
    stmt = select(AuditLog)
    if claim_id:
        stmt = stmt.where(AuditLog.claim_id == claim_id)
    if actor_type:
        stmt = stmt.where(AuditLog.actor_type == actor_type)
    
    stmt = stmt.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all())

async def delete_all_audit_logs(db: AsyncSession) -> int:
    """Deletes all audit logs from the database."""
    from sqlalchemy import delete
    stmt = delete(AuditLog)
    res = await db.execute(stmt)
    await db.commit()
    logger.info("Cleared all audit logs from database.")
    return res.rowcount

async def delete_audit_log(db: AsyncSession, log_id: str) -> bool:
    """Deletes a single audit log by ID."""
    from sqlalchemy import delete
    stmt = delete(AuditLog).where(AuditLog.id == log_id)
    res = await db.execute(stmt)
    await db.commit()
    return res.rowcount > 0

