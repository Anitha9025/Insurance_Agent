import os
from typing import Optional
from app.ocr.base import BaseOCREngine, OCRResult
from app.ocr.pdf_engine import PDFOCREngine
from app.ocr.image_engine import ImageOCREngine
from app.ocr.validator import FileValidator
from app.core.logging import logger

class HybridOCREngine(BaseOCREngine):
    """Hybrid OCR Engine dispatching to specialized engines (PDF vs Image)."""

    def __init__(self):
        self.pdf_engine = PDFOCREngine()
        self.image_engine = ImageOCREngine()

    async def extract_text(self, file_path: str, mime_type: Optional[str] = None) -> OCRResult:
        ext, file_size = FileValidator.validate_file(file_path)

        if ext == ".pdf":
            logger.info(f"Dispatching {file_path} to PDFOCREngine")
            return await self.pdf_engine.extract_text(file_path, mime_type)
        elif ext in [".txt", ".log", ".csv"]:
            logger.info(f"Extracting plain text from {file_path}")
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                return OCRResult(
                    raw_text=text,
                    confidence=100.0,
                    page_count=1,
                    metadata={"engine": "PlainTextReader"}
                )
            except Exception as e:
                return OCRResult(raw_text="", confidence=0.0, page_count=0, metadata={"error": str(e)})
        elif ext in [".docx", ".doc"]:
            logger.info(f"Extracting text from DOCX file {file_path}")
            try:
                import docx
                doc = docx.Document(file_path)
                full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
                return OCRResult(
                    raw_text=full_text,
                    confidence=98.0,
                    page_count=1,
                    metadata={"engine": "DocxReader"}
                )
            except Exception as e:
                logger.warning(f"python-docx error or not installed for {file_path}: {str(e)}")
                # Fallback to plain text read if binary parse fails
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    raw_content = f.read()
                return OCRResult(raw_text=raw_content, confidence=50.0, page_count=1, metadata={"engine": "DocxFallback"})
        else:
            logger.info(f"Dispatching {file_path} to ImageOCREngine")
            return await self.image_engine.extract_text(file_path, mime_type)

# Singleton instance
ocr_engine = HybridOCREngine()
