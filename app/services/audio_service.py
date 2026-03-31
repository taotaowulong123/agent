"""Audio service: extract audio from video, split into chunks."""
from pathlib import Path
from typing import List, Tuple
import subprocess

from app.core.config import settings, STORAGE_DIR
from app.core.logger import get_logger
from app.services.storage_service import get_storage_path

logger = get_logger(__name__)


def extract_audio(video_path: Path, job_id: str) -> Tuple[Path, str]:
    """Extract audio from video using ffmpeg. Returns (local_path, public_url)."""
    out_path, url = get_storage_path("audio", f"{job_id}.mp3")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vn",
        "-ar", "16000",
        "-ac", "1",
        "-b:a", "64k",
        str(out_path),
    ]
    logger.info(f"Extracting audio: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg audio extraction failed: {result.stderr}")
    return out_path, url


def split_audio_chunks(audio_path: Path, job_id: str) -> List[Tuple[Path, str]]:
    """
    Split audio into fixed-length chunks for ASR.
    Returns list of (local_path, public_url) for each chunk.
    """
    chunk_dir = STORAGE_DIR / "audio" / f"{job_id}_chunks"
    chunk_dir.mkdir(parents=True, exist_ok=True)

    chunk_sec = settings.AUDIO_CHUNK_SEC
    pattern = str(chunk_dir / "chunk_%04d.mp3")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(audio_path),
        "-f", "segment",
        "-segment_time", str(chunk_sec),
        "-c", "copy",
        pattern,
    ]
    logger.info(f"Splitting audio into {chunk_sec}s chunks")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg chunk split failed: {result.stderr}")

    chunks = []
    for p in sorted(chunk_dir.glob("chunk_*.mp3")):
        url = f"{settings.BASE_URL}/files/audio/{job_id}_chunks/{p.name}"
        chunks.append((p, url))
    return chunks
