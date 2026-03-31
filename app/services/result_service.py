import uuid
from pathlib import Path
from typing import Dict, List, Optional

from app.core.config import settings, STORAGE_DIR
from app.schemas.job import JobResult, JobStatus
from app.core.logger import get_logger

logger = get_logger(__name__)

# In-memory job store (replace with DB for production)
_jobs: Dict[str, JobResult] = {}


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
    logger.info(f"Job created: {job_id} ({filename})")
    return job


def get_job(job_id: str) -> Optional[JobResult]:
    return _jobs.get(job_id)


def update_job(job: JobResult) -> None:
    _jobs[job.job_id] = job


def list_jobs() -> List[JobResult]:
    return list(_jobs.values())
