"""Upload route: accept file, create job, kick off background pipeline."""
import threading
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.constants import SUPPORTED_AUDIO_EXTENSIONS, SUPPORTED_VIDEO_EXTENSIONS
from app.core.logger import get_logger
from app.schemas.job import JobResult
from app.services import result_service, storage_service
from app.agents.pipeline_agent import run_pipeline

router = APIRouter()
logger = get_logger(__name__)


@router.post("/upload", response_model=JobResult)
async def upload_file(file: UploadFile = File(...)):
    suffix = Path(file.filename).suffix.lower()
    if suffix in SUPPORTED_VIDEO_EXTENSIONS:
        media_type = "video"
    elif suffix in SUPPORTED_AUDIO_EXTENSIONS:
        media_type = "audio"
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. "
                   f"Supported: {SUPPORTED_VIDEO_EXTENSIONS | SUPPORTED_AUDIO_EXTENSIONS}",
        )

    file_bytes = await file.read()
    local_path, file_url = storage_service.save_upload(file_bytes, file.filename)

    job = result_service.create_job(
        filename=file.filename,
        file_url=file_url,
        media_type=media_type,
    )

    # Run pipeline in background thread so the response returns immediately
    thread = threading.Thread(target=run_pipeline, args=(job,), daemon=True)
    thread.start()

    logger.info(f"Job {job.job_id} queued for processing")
    return job
