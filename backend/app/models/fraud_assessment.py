import uuid
from typing import TYPE_CHECKING, Any
from sqlalchemy import String, Float, Boolean, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.claim import Claim


class FraudAssessment(Base, TimestampMixin):
    """Phase 7: Evidence-based fraud risk assessment for a claim.
    Uses rule-based scoring derived from prior agent outputs.
    Never constitutes a fraud determination. Always requires human review.
    """
    __tablename__ = "fraud_assessments"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"fa-{uuid.uuid4().hex[:10]}"
    )
    claim_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("claims.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # Risk outcome fields
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False)           # low, medium, high, unknown
    rule_based_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    score_rule_version: Mapped[str] = mapped_column(String(32), nullable=False, default="v1.0")
    signal_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assessment_status: Mapped[str] = mapped_column(String(32), nullable=False, default="completed")

    # JSON payloads
    signals_json: Mapped[Any] = mapped_column(JSON, default=list, nullable=False)
    supporting_evidence_json: Mapped[Any] = mapped_column(JSON, default=list, nullable=False)
    contradictory_evidence_json: Mapped[Any] = mapped_column(JSON, default=list, nullable=False)
    missing_information_json: Mapped[Any] = mapped_column(JSON, default=list, nullable=False)
    uncertainties_json: Mapped[Any] = mapped_column(JSON, default=list, nullable=False)
    normalized_evidence_json: Mapped[Any] = mapped_column(JSON, default=list, nullable=False)

    # Audit & compliance
    requires_human_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    llm_provider: Mapped[str] = mapped_column(String(64), nullable=True)
    llm_model: Mapped[str] = mapped_column(String(64), nullable=True)
    assessment_disclaimer: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationship
    claim: Mapped["Claim"] = relationship("Claim", back_populates="fraud_assessment")
