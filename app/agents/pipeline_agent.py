"""Pipeline agent: orchestrates the full media -> text pipeline for one job."""
from pathlib import Path

from app.core.config import STORAGE_DIR
from app.core.constants import JOB_STATUS_PROCESSING, JOB_STATUS_DONE, JOB_STATUS_FAILED
from app.core.logger import get_logger
from app.schemas.job import JobResult, JobStatus
from app.services import (
    audio_service,
    frame_service,
    ocr_service,
    asr_service,
    llm_service,
    result_service,
)

logger = get_logger(__name__)


def run_pipeline(job: JobResult) -> JobResult:
    """
    Full pipeline:
      video  -> extract audio -> split chunks -> ASR
             -> extract frames -> OCR
      audio  -> split chunks -> ASR
      both   -> merge -> summarize -> keywords
    Updates job status in result_service throughout.
    """
    job.status = JobStatus.processing
    result_service.update_job(job)

    try:
        upload_path = STORAGE_DIR / "uploads" / job.filename

        # ── 1. Audio extraction (video only) ─────────────────────────────────
        if job.media_type == "video":
            logger.info(f"[{job.job_id}] Extracting audio from video")
            audio_path, audio_url = audio_service.extract_audio(upload_path, job.job_id)
            job.audio_url = audio_url
            result_service.update_job(job)
        else:
            # Direct audio upload
            audio_path = upload_path
            job.audio_url = job.file_url
            result_service.update_job(job)

        # ── 2. Frame extraction (video only) ─────────────────────────────────
        if job.media_type == "video":
            logger.info(f"[{job.job_id}] Extracting frames")
            frames = frame_service.extract_frames(upload_path, job.job_id)
            job.frames = frames
            result_service.update_job(job)
        else:
            frames = []

        # ── 3. ASR ────────────────────────────────────────────────────────────
        logger.info(f"[{job.job_id}] Splitting audio and running ASR")
        chunks = audio_service.split_audio_chunks(audio_path, job.job_id)
        chunk_paths = [c[0] for c in chunks]
        if not chunk_paths:
            chunk_paths = [audio_path]
        asr_text = asr_service.run_asr(chunk_paths)
        job.asr_text = asr_text
        result_service.update_job(job)

        # ── 4. OCR ────────────────────────────────────────────────────────────
        if frames:
            logger.info(f"[{job.job_id}] Running OCR on {len(frames)} frames")
            frame_dir = STORAGE_DIR / "frames" / job.job_id
            frame_paths = sorted(frame_dir.glob("frame_*.jpg"))
            ocr_texts = ocr_service.run_ocr_on_frames(frame_paths)
            job.ocr_texts = [t for t in ocr_texts if t]
            result_service.update_job(job)
        else:
            ocr_texts = []

        # ── 5. Merge + summarize + keywords ───────────────────────────────────
        logger.info(f"[{job.job_id}] Merging, summarizing, extracting keywords")
        ocr_combined = "\n".join(t for t in ocr_texts if t)
        merged = llm_service.merge_texts(asr_text, ocr_combined)
        job.merged_text = merged
        result_service.update_job(job)

        job.summary = llm_service.summarize(merged)
        job.keywords = llm_service.extract_keywords(merged)

        job.status = JobStatus.done
        result_service.update_job(job)
        logger.info(f"[{job.job_id}] Pipeline complete")

    except Exception as e:
        logger.error(f"[{job.job_id}] Pipeline failed: {e}", exc_info=True)
        job.status = JobStatus.failed
        job.error = str(e)
        result_service.update_job(job)

    return job
