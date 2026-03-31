"""ASR service: use faster-whisper locally for speech-to-text."""
from pathlib import Path
from typing import List

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

_model = None


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        logger.info("Loading faster-whisper model (first time may download ~150MB)...")
        # small model: good balance of speed/accuracy on M1
        _model = WhisperModel("large-v3", device="cpu", compute_type="int8")
        logger.info("faster-whisper model loaded")
    return _model


def _transcribe_chunk(audio_path: Path) -> str:
    """Transcribe one audio chunk using local faster-whisper."""
    model = _get_model()
    segments, info = model.transcribe(str(audio_path), beam_size=5)
    logger.info(f"Detected language: {info.language} (prob: {info.language_probability:.2f})")
    return " ".join(seg.text.strip() for seg in segments)


def run_asr(chunk_paths: List[Path]) -> str:
    """Transcribe multiple audio chunks and join into one transcript."""
    parts = []
    for i, p in enumerate(chunk_paths):
        logger.info(f"ASR chunk {i+1}/{len(chunk_paths)}: {p.name}")
        try:
            text = _transcribe_chunk(p)
        except Exception as e:
            logger.warning(f"ASR failed for {p.name}: {e}")
            text = ""
        if text:
            parts.append(text)
    return " ".join(parts)
