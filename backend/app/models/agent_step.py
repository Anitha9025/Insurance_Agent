import uuid
from typing import TYPE_CHECKING, Optional, Any
from sqlalchemy import String, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.claim import Claim

class AIAgentStep(Base):
    __tablename__ = "agent_steps"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"step-{uuid.uuid4().hex[:8]}"
    )
    claim_id: Mapped[str] = mapped_column(String(64), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="Pending", nullable=False) # Pending, Running, Completed, Warning, Failed
    timestamp: Mapped[str] = mapped_column(String(32), nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    output_summary: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    # Relationship
    claim: Mapped["Claim"] = relationship("Claim", back_populates="agent_steps")
