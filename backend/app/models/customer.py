import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Float, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.policy import Policy
    from app.models.claim import Claim

class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"cust-{uuid.uuid4().hex[:8]}"
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    dob: Mapped[str] = mapped_column(String(16), nullable=False)
    address: Mapped[str] = mapped_column(String(256), nullable=False)
    national_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    member_since: Mapped[str] = mapped_column(String(16), nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Relationships
    policies: Mapped[List["Policy"]] = relationship("Policy", back_populates="customer", cascade="all, delete-orphan")
    claims: Mapped[List["Claim"]] = relationship("Claim", back_populates="customer", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_customers_national_id_email", "national_id", "email"),
    )
