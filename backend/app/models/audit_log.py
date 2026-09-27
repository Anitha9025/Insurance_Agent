import uuid
from typing import TYPE_CHECKING, Optional, Any
from sqlalchemy import String, ForeignKey, Text, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.claim import Claim

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"log-{uuid.uuid4().hex[:8]}"
    )
    timestamp: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    claim_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("claims.id", ondelete="SET NULL"), nullable=True, index=True)
    claim_number: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True) # Officer, AI Agent
    actor_name: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    memory_used: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    knowledge_used: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    tools_called: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    # Relationship
    claim: Mapped[Optional["Claim"]] = relationship("Claim", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_logs_actor_action", "actor_type", "action"),
    )
