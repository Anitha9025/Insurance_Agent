import uuid
from typing import List, TYPE_CHECKING, Optional
from sqlalchemy import String, Boolean, Numeric, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.policy import Policy
    from app.models.document import ClaimDocument
    from app.models.agent_step import AIAgentStep
    from app.models.recommendation import AIRecommendation
    from app.models.audit_log import AuditLog
    from app.models.memory import ClaimMemory
    from app.models.fraud_assessment import FraudAssessment
    from app.models.recommendation_record import RecommendationRecord

class Claim(Base, TimestampMixin):
    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"claim-{uuid.uuid4().hex[:8]}"
    )
    claim_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False, index=True) # Vehicle, Health, Home, Travel, Business
    priority: Mapped[str] = mapped_column(String(32), default="Medium", nullable=False, index=True) # Low, Medium, High, Emergency
    is_emergency: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="Submitted", nullable=False, index=True) # Draft, Submitted, Processing, Under Review, Approved, Rejected, Requires Documents
    incident_date: Mapped[str] = mapped_column(String(16), nullable=False)
    incident_time: Mapped[str] = mapped_column(String(16), nullable=False)
    location: Mapped[str] = mapped_column(String(256), nullable=False)
    claim_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    approved_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    assigned_officer: Mapped[str] = mapped_column(String(128), default="Officer Sarah Jenkins", nullable=False)


    # Foreign Keys
    customer_id: Mapped[str] = mapped_column(String(64), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    policy_number: Mapped[str] = mapped_column(String(64), ForeignKey("policies.policy_number", ondelete="CASCADE"), nullable=False, index=True)

    # Officer Notes & Human Decision
    officer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    human_decision_action: Mapped[Optional[str]] = mapped_column(String(64), nullable=True) # Approve, Reject, Request Additional Documents
    human_decision_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    human_decision_at: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    human_decision_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="claims")
    policy: Mapped["Policy"] = relationship("Policy", back_populates="claims")
    documents: Mapped[List["ClaimDocument"]] = relationship("ClaimDocument", back_populates="claim", cascade="all, delete-orphan")
    agent_steps: Mapped[List["AIAgentStep"]] = relationship("AIAgentStep", back_populates="claim", cascade="all, delete-orphan")
    ai_recommendation: Mapped[Optional["AIRecommendation"]] = relationship("AIRecommendation", back_populates="claim", uselist=False, cascade="all, delete-orphan")
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="claim")
    memories: Mapped[List["ClaimMemory"]] = relationship("ClaimMemory", back_populates="claim", cascade="all, delete-orphan")
    # Phase 7
    fraud_assessment: Mapped[Optional["FraudAssessment"]] = relationship("FraudAssessment", back_populates="claim", uselist=False, cascade="all, delete-orphan")
    recommendation_record: Mapped[Optional["RecommendationRecord"]] = relationship("RecommendationRecord", back_populates="claim", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_claims_status_priority", "status", "priority"),
        Index("ix_claims_customer_status", "customer_id", "status"),
    )

    @property
    def human_decision(self) -> Optional[dict]:
        if self.human_decision_action:
            return {
                "action": self.human_decision_action,
                "decided_by": self.human_decision_by or "Officer Sarah Jenkins",
                "decided_at": self.human_decision_at or "",
                "reason": self.human_decision_reason or ""
            }
        return None
