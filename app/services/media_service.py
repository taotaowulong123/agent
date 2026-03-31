"""Media service: detect media type from file extension."""
from pathlib import Path
from app.core.constants import SUPPORTED_VIDEO_EXTENSIONS, SUPPORTED_AUDIO_EXTENSIONS


def detect_media_type(path: Path) -> str:
    """Return 'video' or 'audio' based on file extension."""
    suffix = path.suffix.lower()
    if suffix in SUPPORTED_VIDEO_EXTENSIONS:
        return "video"
    if suffix in SUPPORTED_AUDIO_EXTENSIONS:
        return "audio"
    raise ValueError(f"Unsupported file extension: {suffix}")
