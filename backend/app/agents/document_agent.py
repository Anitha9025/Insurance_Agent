from typing import List
from app.agents.schemas import DocumentAgentInput, DocumentAgentOutput, AgentExtractedField
from app.ocr.engine import ocr_engine
from app.ocr.classifier import DocumentClassifier
from app.ocr.extractor import InformationExtractor
from app.ocr.validator import FileValidator, FileValidationError
from app.core.logging import logger

class DocumentAgent:
    """Document Processing Agent responsible for converting raw uploaded files (PDF, JPG, PNG)
    into structured information with classification, OCR text extraction, field extraction,
    and confidence evaluation.
    """

    async def process_document(self, payload: DocumentAgentInput) -> DocumentAgentOutput:
        logger.info(f"DocumentAgent starting processing for document {payload.document_id} ({payload.file_name})")
        warnings: List[str] = []

        # 1. File Validation
        try:
            ext, file_size = FileValidator.validate_file(payload.file_path)
        except FileValidationError as e:
            logger.warning(f"File validation failed for {payload.file_name}: {str(e)}")
            return DocumentAgentOutput(
                document_id=payload.document_id,
                document_type="Unknown",
                extracted_text="",
                extracted_fields=[],
                confidence=0.0,
                warnings=[str(e)],
                is_flagged_for_human_review=True
            )

        # 2. Text Extraction via OCR Engine Abstraction
        ocr_result = await ocr_engine.extract_text(payload.file_path)
        if not ocr_result.raw_text.strip() and ocr_result.confidence < 50.0:
            warnings.append("OCR engine extracted minimal or low-quality text from document.")

        # 3. Document Classification
        classified_type, class_confidence = DocumentClassifier.classify(
            raw_text=ocr_result.raw_text,
            file_name=payload.file_name,
            category_hint=payload.category_hint
        )

        # 4. Structured Field Extraction & Factuality Check
        fields, extraction_warnings = await InformationExtractor.extract_fields_async(
            raw_text=ocr_result.raw_text,
            category=classified_type
        )
        warnings.extend(extraction_warnings)

        # 5. Transform Extracted Fields into Agent Output Format
        agent_fields: List[AgentExtractedField] = []
        low_confidence_count = 0

        for f in fields:
            if f.confidence < 80.0 or f.status == "Flagged":
                low_confidence_count += 1
            
            agent_fields.append(AgentExtractedField(
                field_name=f.field_name,
                extracted_value=f.extracted_value,
                confidence=f.confidence,
                status=f.status,
                warning=f.warning
            ))

        # 6. Overall Confidence Evaluation & Human Review Flagging
        field_confidences = [f.confidence for f in fields] if fields else [ocr_result.confidence]
        avg_confidence = sum(field_confidences) / len(field_confidences) if field_confidences else 50.0
        
        # Overall confidence is weighted average of OCR text confidence & field confidence
        overall_confidence = round(0.4 * ocr_result.confidence + 0.6 * avg_confidence, 1)

        is_flagged = overall_confidence < 80.0 or low_confidence_count > 0 or len(warnings) > 0

        if is_flagged and "Document flagged for human officer verification." not in warnings:
            warnings.append(f"Document marked for human review due to {low_confidence_count} uncertain field(s).")

        logger.info(
            f"DocumentAgent completed for {payload.document_id}: "
            f"Type='{classified_type}', Confidence={overall_confidence}%, Flagged={is_flagged}"
        )

        vision_analysis_meta = ocr_result.metadata.get("vision_analysis") if isinstance(ocr_result.metadata, dict) else None

        return DocumentAgentOutput(
            document_id=payload.document_id,
            document_type=classified_type,
            extracted_text=ocr_result.raw_text,
            extracted_fields=agent_fields,
            confidence=overall_confidence,
            warnings=warnings,
            is_flagged_for_human_review=is_flagged,
            vision_analysis=vision_analysis_meta
        )

# Singleton Agent Instance
document_agent = DocumentAgent()
