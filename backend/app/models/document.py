import uuid
from typing import List, TYPE_CHECKING, Optional
from sqlalchemy import String, Float, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.claim import Claim

class ClaimDocument(Base, TimestampMixin):
    __tablename__ = "claim_documents"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"doc-{uuid.uuid4().hex[:8]}"
    )
    claim_id: Mapped[str] = mapped_column(String(64), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(256), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False) # Local disk storage path
    file_size: Mapped[str] = mapped_column(String(32), nullable=False)
    type: Mapped[str] = mapped_column(String(16), nullable=False) # PDF, IMAGE, WORD
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True) # Medical Report, Police Report, etc.
    upload_date: Mapped[str] = mapped_column(String(32), nullable=False)
    url: Mapped[str] = mapped_column(String(512), default="#", nullable=False)
    ocr_status: Mapped[str] = mapped_column(String(32), default="Pending", nullable=False) # Pending, In Progress, Completed, Failed
    verification_status: Mapped[str] = mapped_column(String(32), default="Pending", nullable=False) # Verified, Flagged, Mismatch, Pending

    # Relationships
    claim: Mapped["Claim"] = relationship("Claim", back_populates="documents")
    ocr_fields: Mapped[List["OCRField"]] = relationship("OCRField", back_populates="document", cascade="all, delete-orphan")


class OCRField(Base):
    __tablename__ = "ocr_fields"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"ocr-{uuid.uuid4().hex[:8]}"
    )
    document_id: Mapped[str] = mapped_column(String(64), ForeignKey("claim_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name: Mapped[str] = mapped_column(String(128), nullable=False)
    extracted_value: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="Extracted", nullable=False) # Verified, Flagged, Extracted

    # Relationship
    document: Mapped["ClaimDocument"] = relationship("ClaimDocument", back_populates="ocr_fields")
