import os
import shutil
import uuid
from typing import Tuple
from app.core.config import settings
from app.core.logging import logger

class StorageService:
    """Abstract interface for document file storage."""
    
    def save_file(self, file_name: str, content: bytes, claim_id: str) -> Tuple[str, str, str]:
        """Saves file content and returns (file_path, file_size_str, url)."""
        raise NotImplementedError

    def delete_file(self, file_path: str) -> bool:
        """Deletes file from storage."""
        raise NotImplementedError


class LocalStorageService(StorageService):
    """Disk storage implementation saving files under local uploads/ directory."""

    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)

    def save_file(self, file_name: str, content: bytes, claim_id: str) -> Tuple[str, str, str]:
        claim_dir = os.path.join(self.upload_dir, "claims", claim_id)
        os.makedirs(claim_dir, exist_ok=True)

        ext = os.path.splitext(file_name)[1]
        unique_name = f"{uuid.uuid4().hex[:12]}{ext}"
        file_path = os.path.join(claim_dir, unique_name)

        with open(file_path, "wb") as f:
            f.write(content)

        size_bytes = len(content)
        if size_bytes >= 1024 * 1024:
            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            size_str = f"{size_bytes / 1024:.1f} KB"

        file_url = f"/api/v1/documents/files/{claim_id}/{unique_name}"
        logger.info(f"Saved file {file_name} to {file_path} ({size_str})")
        return file_path, size_str, file_url

    def delete_file(self, file_path: str) -> bool:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Deleted file {file_path}")
                return True
            except Exception as e:
                logger.error(f"Error deleting file {file_path}: {str(e)}")
                return False
        return False

# Export singleton instance
storage_service = LocalStorageService()
