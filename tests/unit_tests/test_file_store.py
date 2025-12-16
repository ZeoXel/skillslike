"""Unit tests for file storage."""

import tempfile
from pathlib import Path

import pytest

from skillslike.storage.file_store import FileStore


@pytest.fixture
def temp_store_dir() -> Path:
    """Create a temporary directory for file store."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def file_store(temp_store_dir: Path) -> FileStore:
    """Create a FileStore instance."""
    return FileStore(temp_store_dir)


def test_store_initialization(temp_store_dir: Path) -> None:
    """Test FileStore initialization."""
    store = FileStore(temp_store_dir)

    assert store.base_dir == temp_store_dir
    assert temp_store_dir.exists()


def test_store_bytes(file_store: FileStore) -> None:
    """Test storing bytes."""
    data = b"test file content"
    file_id = file_store.store(data, filename="test.txt", content_type="text/plain")

    assert file_id is not None
    assert len(file_id) > 0


def test_retrieve_file(file_store: FileStore) -> None:
    """Test retrieving stored file."""
    data = b"test content"
    file_id = file_store.store(data, filename="test.txt")

    retrieved = file_store.retrieve(file_id)

    assert retrieved == data


def test_retrieve_nonexistent_file(file_store: FileStore) -> None:
    """Test retrieving non-existent file."""
    retrieved = file_store.retrieve("nonexistent-id")

    assert retrieved is None


def test_get_metadata(file_store: FileStore) -> None:
    """Test getting file metadata."""
    data = b"test content"
    file_id = file_store.store(data, filename="test.txt", content_type="text/plain")

    metadata = file_store.get_metadata(file_id)

    assert metadata is not None
    assert metadata["file_id"] == file_id
    assert metadata["filename"] == "test.txt"
    assert metadata["content_type"] == "text/plain"


def test_delete_file(file_store: FileStore) -> None:
    """Test deleting a file."""
    data = b"test content"
    file_id = file_store.store(data, filename="test.txt")

    # Verify file exists
    assert file_store.retrieve(file_id) is not None

    # Delete file
    result = file_store.delete(file_id)
    assert result is True

    # Verify file no longer exists
    assert file_store.retrieve(file_id) is None


def test_delete_nonexistent_file(file_store: FileStore) -> None:
    """Test deleting non-existent file."""
    result = file_store.delete("nonexistent-id")
    assert result is False


def test_list_files(file_store: FileStore) -> None:
    """Test listing all files."""
    # Store multiple files
    file_store.store(b"content1", filename="file1.txt")
    file_store.store(b"content2", filename="file2.txt")

    files = file_store.list_files()

    assert len(files) == 2
    assert all("file_id" in f for f in files)
    assert all("filename" in f for f in files)


def test_store_preserves_extension(file_store: FileStore) -> None:
    """Test that file extension is preserved."""
    data = b"test content"
    file_id = file_store.store(data, filename="document.pdf")

    # Check that file exists with .pdf extension
    matches = list(file_store.base_dir.glob(f"{file_id}.pdf"))
    assert len(matches) == 1
