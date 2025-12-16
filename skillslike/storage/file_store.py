"""File storage for skill outputs."""

import logging
import uuid
from pathlib import Path
from typing import BinaryIO

logger = logging.getLogger(__name__)


class FileStore:
    """File storage for skill execution outputs.

    Stores files locally with unique IDs. Can be extended to support
    S3, MinIO, or other object storage backends.
    """

    def __init__(self, base_dir: str | Path = "data/files") -> None:
        """Initialize the file store.

        Args:
            base_dir: Base directory for file storage.
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info("File store initialized at: %s", self.base_dir)

    def store(
        self,
        file_data: bytes | BinaryIO,
        *,
        filename: str | None = None,
        content_type: str | None = None,
    ) -> str:
        """Store a file and return its ID.

        Args:
            file_data: File content as bytes or file-like object.
            filename: Original filename (optional).
            content_type: MIME type (optional).

        Returns:
            Unique file ID.
        """
        # Generate unique file ID
        file_id = str(uuid.uuid4())

        # Determine file extension
        ext = ""
        if filename:
            ext = Path(filename).suffix

        # Create file path
        file_path = self.base_dir / f"{file_id}{ext}"

        # Write file
        if isinstance(file_data, bytes):
            file_path.write_bytes(file_data)
        else:
            with file_path.open("wb") as f:
                f.write(file_data.read())

        # Store metadata (could be in a database in production)
        metadata_path = self.base_dir / f"{file_id}.meta"
        metadata = {
            "file_id": file_id,
            "filename": filename or f"{file_id}{ext}",
            "content_type": content_type or "application/octet-stream",
        }

        import json

        metadata_path.write_text(json.dumps(metadata))

        logger.info("Stored file: %s (original: %s)", file_id, filename)

        return file_id

    def retrieve(self, file_id: str) -> bytes | None:
        """Retrieve file content by ID.

        Args:
            file_id: The file ID.

        Returns:
            File content as bytes, or `None` if not found.
        """
        # Find file with any extension
        matches = list(self.base_dir.glob(f"{file_id}.*"))

        # Filter out .meta files
        matches = [m for m in matches if m.suffix != ".meta"]

        if not matches:
            logger.warning("File not found: %s", file_id)
            return None

        file_path = matches[0]
        logger.debug("Retrieving file: %s", file_path)

        return file_path.read_bytes()

    def get_metadata(self, file_id: str) -> dict[str, str] | None:
        """Get file metadata by ID.

        Args:
            file_id: The file ID.

        Returns:
            File metadata dictionary, or `None` if not found.
        """
        metadata_path = self.base_dir / f"{file_id}.meta"

        if not metadata_path.exists():
            logger.warning("Metadata not found: %s", file_id)
            return None

        import json

        return json.loads(metadata_path.read_text())

    def delete(self, file_id: str) -> bool:
        """Delete a file by ID.

        Args:
            file_id: The file ID.

        Returns:
            `True` if file was deleted, `False` if not found.
        """
        # Find and delete file
        matches = list(self.base_dir.glob(f"{file_id}.*"))

        if not matches:
            logger.warning("File not found for deletion: %s", file_id)
            return False

        for file_path in matches:
            file_path.unlink()
            logger.info("Deleted file: %s", file_path)

        return True

    def list_files(self) -> list[dict[str, str]]:
        """List all stored files.

        Returns:
            List of file metadata dictionaries.
        """
        metadata_files = self.base_dir.glob("*.meta")
        files = []

        for meta_file in metadata_files:
            import json

            metadata = json.loads(meta_file.read_text())
            files.append(metadata)

        return files
