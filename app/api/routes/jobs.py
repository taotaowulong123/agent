"""Jobs route: poll job status and results."""
from typing import List

from fastapi import APIRouter, HTTPException

from app.schemas.job import JobResult
from app.services import result_service

router = APIRouter()


@router.get("/jobs", response_model=List[JobResult])
def list_jobs():
    return result_service.list_jobs()


@router.get("/jobs/{job_id}", response_model=JobResult)
def get_job(job_id: str):
    job = result_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
