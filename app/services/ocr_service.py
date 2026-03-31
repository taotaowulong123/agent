"""OCR service: call vision API to extract text from frame images."""
import base64
from pathlib import Path
from typing import List

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logger import get_logger
from app.prompts import ocr_prompt_text

logger = get_logger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
def _ocr_single(image_path: Path) -> str:
    """Call vision API on one image, return extracted text."""
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    payload = {
        "model": settings.OCR_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": ocr_prompt_text()},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                    },
                ],
            }
        ],
        "max_tokens": 1024,
    }
    headers = {
        "Authorization": f"Bearer {settings.OCR_API_KEY}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=60) as client:
        resp = client.post(
            f"{settings.OCR_API_BASE}/chat/completions",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"].strip()
        return "" if text == "[NO TEXT]" else text


def run_ocr_on_frames(frame_paths: List[Path]) -> List[str]:
    """Run OCR on a list of frame images. Returns list of text strings."""
    results = []
    for i, p in enumerate(frame_paths):
        logger.info(f"OCR frame {i+1}/{len(frame_paths)}: {p.name}")
        try:
            text = _ocr_single(p)
        except Exception as e:
            logger.warning(f"OCR failed for {p.name}: {e}")
            text = ""
        results.append(text)
    return results
