import uuid
from typing import TYPE_CHECKING, Any
from sqlalchemy import String, Float, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.claim import Claim


class RecommendationRecord(Base, TimestampMixin):
    """Phase 7: AI-assisted claim recommendation record.
    Advisory only — never constitutes a final decision.
    Officer retains full decision authority.
    """
    __tablename__ = "recommendation_records"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"rr-{uuid.uuid4().hex[:10]}"
    )
    claim_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("claims.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # Recommendation outcome
    recommendation: Mapped[str] = mapped_column(String(64), nullable=False)
    recommendation_label: Mapped[str] = mapped_column(String(128), nullable=False)

    # Narrative
    reasoning_summary: Mapped[str] = mapped_column(Text, nullable=False)

    # JSON payloads
    policy_references_json: Mapped[Any] = mapped_column(JSON, default=list, nullable=False)
    risk_summary_json: Mapped[Any] = mapped_column(JSON, default=list, nullable=False)
    missing_information_json: Mapped[Any] = mapped_column(JSON, default=list, nullable=False)
    required_next_actions_json: Mapped[Any] = mapped_column(JSON, default=list, nullable=False)

    # Override tracking
    override_reason: Mapped[str] = mapped_column(Text, nullable=True)
    confidence_basis: Mapped[str] = mapped_column(String(32), nullable=False, default="evidence")

    # Compliance
    requires_human_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    final_decision_made: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Audit
    llm_provider: Mapped[str] = mapped_column(String(64), nullable=True)
    llm_model: Mapped[str] = mapped_column(String(64), nullable=True)
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=False, default="v1.0")

    # Relationship
    claim: Mapped["Claim"] = relationship("Claim", back_populates="recommendation_record")
