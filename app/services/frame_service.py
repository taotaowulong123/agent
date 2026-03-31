"""Frame service: extract key frames from video using ffmpeg."""
from pathlib import Path
from typing import List
import subprocess

from app.core.config import settings, STORAGE_DIR
from app.core.logger import get_logger
from app.schemas.job import FrameInfo

logger = get_logger(__name__)


def extract_frames(video_path: Path, job_id: str) -> List[FrameInfo]:
    """
    Extract one frame every FRAME_INTERVAL_SEC seconds.
    Returns list of FrameInfo with public URLs.
    """
    out_dir = STORAGE_DIR / "frames" / job_id
    out_dir.mkdir(parents=True, exist_ok=True)

    interval = settings.FRAME_INTERVAL_SEC
    pattern = str(out_dir / "frame_%04d.jpg")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vf", f"fps=1/{interval}",
        "-q:v", "2",
        pattern,
    ]
    logger.info(f"Extracting frames every {interval}s from {video_path.name}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg frame extraction failed: {result.stderr}")

    frames: List[FrameInfo] = []
    for idx, p in enumerate(sorted(out_dir.glob("frame_*.jpg"))):
        timestamp = idx * interval
        url = f"{settings.BASE_URL}/files/frames/{job_id}/{p.name}"
        frames.append(FrameInfo(index=idx, timestamp_sec=float(timestamp), file_url=url))

    logger.info(f"Extracted {len(frames)} frames for job {job_id}")
    return frames
