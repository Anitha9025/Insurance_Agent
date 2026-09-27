import uuid
from typing import Optional
from sqlalchemy import String, Text, Float, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

class ClaimMemory(Base, TimestampMixin):
    __tablename__ = "claim_memories"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"mem-{uuid.uuid4().hex[:8]}"
    )
    claim_id: Mapped[str] = mapped_column(String(64), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True)
    memory_type: Mapped[str] = mapped_column(String(64), nullable=False) # e.g. decision_rationale, ocr_insight, policy_validation, risk_flag
    memory_key: Mapped[str] = mapped_column(String(128), nullable=False)
    memory_value: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[list]] = mapped_column(JSON, nullable=True) # Vector embedding for semantic search
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    source_agent: Mapped[str] = mapped_column(String(64), nullable=False, default="system")

    # Relationship to Claim
    claim: Mapped["Claim"] = relationship("Claim", back_populates="memories")
