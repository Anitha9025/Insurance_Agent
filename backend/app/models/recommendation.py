import uuid
from typing import TYPE_CHECKING, Any
from sqlalchemy import String, Float, Numeric, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.claim import Claim

class AIRecommendation(Base, TimestampMixin):
    __tablename__ = "ai_recommendations"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"rec-{uuid.uuid4().hex[:8]}"
    )
    claim_id: Mapped[str] = mapped_column(String(64), ForeignKey("claims.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    verdict: Mapped[str] = mapped_column(String(64), nullable=False) # Approve, Reject, Request Additional Documents
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False) # 0 to 100
    fraud_risk_score: Mapped[float] = mapped_column(Float, nullable=False) # 0 to 100
    recommended_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    reasoning_summary: Mapped[str] = mapped_column(Text, nullable=False)
    key_findings: Mapped[Any] = mapped_column(JSON, default=list, nullable=False)
    risk_flags: Mapped[Any] = mapped_column(JSON, default=list, nullable=False)
    retrieved_memories: Mapped[Any] = mapped_column(JSON, default=list, nullable=False)
    retrieved_knowledge: Mapped[Any] = mapped_column(JSON, default=list, nullable=False)
    tool_calls: Mapped[Any] = mapped_column(JSON, default=list, nullable=False)

    # Relationship
    claim: Mapped["Claim"] = relationship("Claim", back_populates="ai_recommendation")
