from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel

class AgentExtractedField(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    field_name: str = Field(..., description="Target field name (e.g. 'customer_name', 'claim_amount')")
    extracted_value: str = Field(..., description="Extracted value from document")
    confidence: float = Field(..., description="Extraction confidence score (0 to 100)")
    status: str = Field("Extracted", description="Status ('Verified', 'Extracted', 'Flagged')")
    warning: Optional[str] = Field(None, description="Optional warning message if uncertain")

class DocumentAgentInput(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    document_id: str = Field(..., description="Target document ID")
    file_path: str = Field(..., description="Local file path on server")
    file_name: str = Field(..., description="Original file name")
    category_hint: Optional[str] = Field(None, description="Optional category hint from upload")

class DocumentAgentOutput(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    document_id: str = Field(..., description="Target document ID")
    document_type: str = Field(..., description="Classified document category")
    extracted_text: str = Field(..., description="Raw text extracted from OCR processing")
    extracted_fields: List[AgentExtractedField] = Field(default_factory=list, description="Structured key-value fields")
    confidence: float = Field(..., description="Overall extraction confidence score (0 to 100)")
    warnings: List[str] = Field(default_factory=list, description="Warnings or flagged extraction notes")
    is_flagged_for_human_review: bool = Field(False, description="Flag indicating document requires officer review")
    vision_analysis: Optional[Dict[str, Any]] = Field(None, description="Dynamic cloud multimodal vision analysis result if image")
