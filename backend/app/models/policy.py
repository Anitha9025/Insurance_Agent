from typing import List, TYPE_CHECKING
from sqlalchemy import String, Numeric, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.claim import Claim
    from app.models.knowledge import KnowledgeDocument


class Policy(Base, TimestampMixin):
    __tablename__ = "policies"

    policy_number: Mapped[str] = mapped_column(String(64), primary_key=True)
    category: Mapped[str] = mapped_column(String(32), nullable=False, index=True) # Vehicle, Health, Home, Travel, Business
    start_date: Mapped[str] = mapped_column(String(16), nullable=False)
    end_date: Mapped[str] = mapped_column(String(16), nullable=False)
    premium_status: Mapped[str] = mapped_column(String(32), default="Paid", nullable=False) # Paid, Pending, Grace Period, Overdue
    coverage_limit: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    deductible: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    active_claims_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Foreign Key
    customer_id: Mapped[str] = mapped_column(String(64), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="policies")
    claims: Mapped[List["Claim"]] = relationship("Claim", back_populates="policy", cascade="all, delete-orphan")
    knowledge_documents: Mapped[List["KnowledgeDocument"]] = relationship("KnowledgeDocument", back_populates="policy", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_policies_customer_category", "customer_id", "category"),
    )

