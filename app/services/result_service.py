import json
import shutil
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from app.core.config import settings, STORAGE_DIR
from app.schemas.job import JobResult, JobStatus
from app.core.logger import get_logger

logger = get_logger(__name__)

JOBS_FILE = STORAGE_DIR / "jobs.json"

# In-memory job store, synced to disk
_jobs: Dict[str, JobResult] = {}


def _save_to_disk():
    """Persist all jobs to jobs.json."""
    data = {jid: job.dict() for jid, job in _jobs.items()}
    JOBS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_from_disk():
    """Load jobs from jobs.json on startup."""
    global _jobs
    if not JOBS_FILE.exists():
        return
    try:
        data = json.loads(JOBS_FILE.read_text(encoding="utf-8"))
        for jid, jdata in data.items():
            _jobs[jid] = JobResult(**jdata)
        logger.info(f"Loaded {len(_jobs)} jobs from disk")
    except Exception as e:
        logger.warning(f"Failed to load jobs from disk: {e}")


# Load on import
_load_from_disk()


def create_job(filename: str, file_url: str, media_type: str) -> JobResult:
    job_id = str(uuid.uuid4())
    job = JobResult(
        job_id=job_id,
        status=JobStatus.uploaded,
        filename=filename,
        file_url=file_url,
        media_type=media_type,
    )
    _jobs[job_id] = job
    _save_to_disk()
    logger.info(f"Job created: {job_id} ({filename})")
    return job


def get_job(job_id: str) -> Optional[JobResult]:
    return _jobs.get(job_id)


def update_job(job: JobResult) -> None:
    _jobs[job.job_id] = job
    _save_to_disk()


def list_jobs() -> List[JobResult]:
    return list(_jobs.values())


def delete_job(job_id: str) -> bool:
    """Delete a job and all its associated local files."""
    job = _jobs.get(job_id)
    if not job:
        return False

    # Delete uploaded file
    upload_dir = STORAGE_DIR / "uploads"
    if job.filename:
        upload_file = upload_dir / job.filename
        if upload_file.exists():
            upload_file.unlink()
            logger.info(f"Deleted upload: {upload_file}")

    # Delete audio file
    audio_dir = STORAGE_DIR / "audio"
    audio_file = audio_dir / f"{job_id}.mp3"
    if audio_file.exists():
        audio_file.unlink()
        logger.info(f"Deleted audio: {audio_file}")

    # Delete audio chunks
    chunks_dir = audio_dir / f"{job_id}_chunks"
    if chunks_dir.exists():
        shutil.rmtree(chunks_dir)
        logger.info(f"Deleted audio chunks: {chunks_dir}")

    # Delete frames
    frames_dir = STORAGE_DIR / "frames" / job_id
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
        logger.info(f"Deleted frames: {frames_dir}")

    # Delete results
    result_file = STORAGE_DIR / "results" / f"{job_id}.json"
    if result_file.exists():
        result_file.unlink()
        logger.info(f"Deleted result: {result_file}")

    # Remove from memory and save
    del _jobs[job_id]
    _save_to_disk()
    logger.info(f"Job deleted: {job_id}")
    return True
