"""LLM service: merge OCR+ASR, summarize, extract keywords via API."""
from pathlib import Path
from typing import List

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
def _chat(system_prompt: str, user_content: str) -> str:
    payload = {
        "model": settings.LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "max_tokens": 2048,
        "temperature": 0.3,
    }
    headers = {
        "Authorization": f"Bearer {settings.LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=120) as client:
        resp = client.post(
            f"{settings.LLM_API_BASE}/chat/completions",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()


def merge_texts(asr_text: str, ocr_text: str) -> str:
    """Merge ASR and OCR results into a coherent transcript."""
    if not asr_text and not ocr_text:
        return ""
    if not ocr_text:
        return asr_text
    if not asr_text:
        return ocr_text

    template = _load_prompt("merge_prompt.txt")
    prompt = template.format(asr_text=asr_text, ocr_text=ocr_text)
    logger.info("Calling LLM to merge ASR+OCR texts")
    return _chat("You are a helpful text fusion assistant.", prompt)


def summarize(merged_text: str) -> str:
    """Produce a concise summary of the merged transcript."""
    if not merged_text:
        return ""
    template = _load_prompt("summary_prompt.txt")
    prompt = template.format(merged_text=merged_text)
    logger.info("Calling LLM for summarization")
    return _chat("You are a summarization assistant.", prompt)


def extract_keywords(merged_text: str) -> List[str]:
    """Extract keywords from the merged transcript."""
    if not merged_text:
        return []
    template = _load_prompt("keyword_prompt.txt")
    prompt = template.format(merged_text=merged_text)
    logger.info("Calling LLM for keyword extraction")
    raw = _chat("You are a keyword extraction assistant.", prompt)
    return [line.strip() for line in raw.splitlines() if line.strip()]
