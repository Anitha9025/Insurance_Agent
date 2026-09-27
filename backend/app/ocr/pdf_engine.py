import os
from typing import Optional

try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

from app.ocr.base import BaseOCREngine, OCRResult
from app.core.logging import logger

class PDFOCREngine(BaseOCREngine):
    """PDF text extraction engine using PyPDF."""

    async def extract_text(self, file_path: str, mime_type: Optional[str] = None) -> OCRResult:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        if not HAS_PYPDF:
            logger.warning("pypdf module not installed. Install with 'pip install pypdf'.")
            return OCRResult(
                raw_text="[PDF text extraction unavailable - pypdf module missing]",
                confidence=30.0,
                page_count=1,
                metadata={"error": "pypdf package missing"}
            )

        try:
            reader = PdfReader(file_path)
            pages_text = []
            total_pages = len(reader.pages)

            for page in reader.pages:
                text = page.extract_text() or ""
                if text.strip():
                    pages_text.append(text.strip())

            full_text = "\n\n".join(pages_text)
            
            # If PDF contains no digital text (e.g. scanned handwritten document), extract page image for Cloud Vision AI
            if not full_text.strip() and reader.pages:
                try:
                    for page_idx, page in enumerate(reader.pages):
                        if hasattr(page, "images") and page.images:
                            img_obj = page.images[0]
                            temp_img_path = f"{file_path}_scanned_p{page_idx}.png"
                            with open(temp_img_path, "wb") as img_file:
                                img_file.write(img_obj.data)
                            
                            logger.info(f"PDF {file_path} appears to be a scanned document. Routing handwritten page image to Cloud Vision AI...")
                            from app.ocr.image_engine import ImageOCREngine
                            img_engine = ImageOCREngine()
                            img_res = await img_engine.extract_text(temp_img_path)
                            
                            if os.path.exists(temp_img_path):
                                os.remove(temp_img_path)

                            if img_res and img_res.raw_text.strip():
                                return img_res
                except Exception as scan_err:
                    logger.warning(f"Scanned PDF handwriting extraction note: {str(scan_err)}")

            confidence = 98.0 if full_text.strip() else 40.0
            
            logger.info(f"Extracted {len(full_text)} chars from PDF {file_path} across {total_pages} pages.")
            return OCRResult(
                raw_text=full_text,
                confidence=confidence,
                page_count=total_pages,
                metadata={"engine": "PyPDF", "pages": total_pages}
            )
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {str(e)}")
            return OCRResult(
                raw_text="",
                confidence=0.0,
                page_count=0,
                metadata={"error": str(e)}
            )
