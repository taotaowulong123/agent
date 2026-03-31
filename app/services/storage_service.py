import shutil
from pathlib import Path

from app.core.config import settings, STORAGE_DIR
from app.core.logger import get_logger

logger = get_logger(__name__)


def save_upload(file_bytes: bytes, filename: str) -> tuple[Path, str]:
    """Save uploaded file, return (local_path, public_url)."""
    dest_dir = STORAGE_DIR / "uploads"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filename
    dest.write_bytes(file_bytes)
    url = f"{settings.BASE_URL}/files/uploads/{filename}"
    logger.info(f"Saved upload: {dest} -> {url}")
    return dest, url


def get_storage_path(subdir: str, filename: str) -> tuple[Path, str]:
    """Return (local_path, public_url) for a file in storage subdirectory."""
    dest_dir = STORAGE_DIR / subdir
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / filename
    url = f"{settings.BASE_URL}/files/{subdir}/{filename}"
    return path, url
