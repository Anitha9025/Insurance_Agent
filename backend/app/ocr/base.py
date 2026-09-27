from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel

class OCRResult(BaseModel):
    raw_text: str
    confidence: float  # Overall extraction confidence score (0 to 100)
    page_count: int = 1
    metadata: Dict[str, Any] = {}

class BaseOCREngine(ABC):
    """Abstract Base Class for OCR / Vision provider engines.
    Allows easy swapping of underlying OCR engines (Tesseract, EasyOCR, PyPDF, Vision API).
    """

    @abstractmethod
    async def extract_text(self, file_path: str, mime_type: Optional[str] = None) -> OCRResult:
        """Extracts raw text and metadata from a document or image file."""
        pass
