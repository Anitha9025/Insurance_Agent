import os
from typing import Optional
from PIL import Image, ImageEnhance, ImageFilter
from app.ocr.base import BaseOCREngine, OCRResult
from app.services.vision_analysis_service import vision_analysis_service
from app.core.logging import logger

class ImageOCREngine(BaseOCREngine):
    """Image processing and text extraction engine.
    Applies PIL image preprocessing (grayscale, contrast adjustment, sharpening)
    and executes dynamic Cloud Multimodal Vision Analysis via VisionAnalysisService.
    """

    def preprocess_image(self, file_path: str) -> Image.Image:
        """Preprocesses image to enhance readability (Grayscale, Contrast, Sharpness)."""
        img = Image.open(file_path)
        img = img.convert("L")
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        img = img.filter(ImageFilter.SHARPEN)
        return img

    async def extract_text(self, file_path: str, mime_type: Optional[str] = None) -> OCRResult:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image file not found: {file_path}")

        try:
            # Local Image Preprocessing
            img = self.preprocess_image(file_path)
            width, height = img.size

            # Dynamic Cloud Multimodal Vision Model Analysis
            analysis = await vision_analysis_service.analyze_single_image(file_path)

            obs_str = "\n".join([f"- {o}" for o in analysis.observations]) if analysis.observations else "- None"
            inf_str = "\n".join([f"- {i}" for i in analysis.inferences]) if analysis.inferences else "- None"
            obj_str = ", ".join(analysis.objects_detected) if analysis.objects_detected else "None"

            raw_text = (
                f"SCENE DESCRIPTION:\n{analysis.scene_description}\n\n"
                f"OBJECTS DETECTED: {obj_str}\n\n"
                f"OBSERVATIONS:\n{obs_str}\n\n"
                f"INFERENCES:\n{inf_str}"
            )

            logger.info(f"Dynamic Vision Analysis completed for image {file_path} ({width}x{height} px). Confidence={analysis.confidence}%")
            
            return OCRResult(
                raw_text=raw_text,
                confidence=analysis.confidence,
                page_count=1,
                metadata={
                    "width": width,
                    "height": height,
                    "format": img.format or "JPEG",
                    "vision_analysis": analysis.model_dump(by_alias=True)
                }
            )
        except Exception as e:
            logger.error(f"Error processing image {file_path}: {str(e)}")
            return OCRResult(
                raw_text="",
                confidence=0.0,
                page_count=1,
                metadata={"error": str(e)}
            )
