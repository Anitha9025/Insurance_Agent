from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel

class OCRFieldBase(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    field_name: str = Field(..., description="Extracted field label")
    extracted_value: str = Field(..., description="Extracted value string")
    confidence: float = Field(..., description="OCR extraction confidence score (0-100)")
    status: str = Field("Extracted", description="Status ('Verified', 'Flagged', 'Extracted')")

class OCRFieldCreate(OCRFieldBase):
    pass

class OCRFieldRead(OCRFieldBase):
    id: str = Field(..., description="OCR field unique ID")

class ClaimDocumentBase(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    file_name: str = Field(..., description="Original file name")
    file_size: str = Field(..., description="Formatted file size (e.g. '2.4 MB')")
    type: str = Field(..., description="Document type ('PDF', 'IMAGE', 'WORD')")
    category: str = Field(..., description="Document category ('Police Report', 'Repair Estimate', etc.)")
    upload_date: str = Field(..., description="Upload timestamp")
    url: str = Field("#", description="Accessible file URL")
    ocr_status: str = Field("Pending", description="OCR status ('Pending', 'In Progress', 'Completed', 'Failed')")
    verification_status: str = Field("Pending", description="Verification status ('Verified', 'Flagged', 'Mismatch', 'Pending')")

class ClaimDocumentCreate(ClaimDocumentBase):
    claim_id: str = Field(..., description="Claim ID this document belongs to")
    file_path: str = Field(..., description="Physical disk storage path")
    ocr_fields: Optional[List[OCRFieldCreate]] = Field(default_factory=list)

class ClaimDocumentRead(ClaimDocumentBase):
    id: str = Field(..., description="Document ID")
    claim_id: str = Field(..., description="Claim ID")
    ocr_fields: List[OCRFieldRead] = Field(default_factory=list)
