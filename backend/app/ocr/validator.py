import os
from typing import Tuple

SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".docx", ".txt"}
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB limit

class FileValidationError(Exception):
    """Exception raised when an uploaded document fails validation."""
    pass

class FileValidator:
    """Validates document extension, size, and integrity."""

    @staticmethod
    def validate_file(file_path: str) -> Tuple[str, int]:
        """Validates file exists, checks extension and file size limit.
        Returns normalized extension and file size in bytes.
        """
        if not os.path.exists(file_path):
            raise FileValidationError(f"File not found on disk: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise FileValidationError(
                f"Unsupported file format '{ext}'. Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )

        file_size = os.path.getsize(file_path)
        if file_size <= 0:
            raise FileValidationError("Uploaded file is empty (0 bytes).")

        if file_size > MAX_FILE_SIZE_BYTES:
            max_mb = MAX_FILE_SIZE_BYTES / (1024 * 1024)
            raise FileValidationError(f"File size exceeds maximum threshold of {max_mb:.0f} MB.")

        return ext, file_size
