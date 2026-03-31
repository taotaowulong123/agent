from enum import Enum
from typing import Optional, List
from pydantic import BaseModel


class JobStatus(str, Enum):
    uploaded = "uploaded"
    processing = "processing"
    done = "done"
    failed = "failed"


class FrameInfo(BaseModel):
    index: int
    timestamp_sec: float
    file_url: str


class JobCreate(BaseModel):
    filename: str
    file_url: str
    media_type: str  # "video" | "audio"


class JobResult(BaseModel):
    job_id: str
    status: JobStatus
    filename: str
    file_url: str
    media_type: str
    audio_url: Optional[str] = None
    frames: List[FrameInfo] = []
    ocr_texts: List[str] = []
    asr_text: Optional[str] = None
    merged_text: Optional[str] = None
    summary: Optional[str] = None
    keywords: List[str] = []
    error: Optional[str] = None
