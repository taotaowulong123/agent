from pathlib import Path

_DIR = Path(__file__).parent


def ocr_prompt_text() -> str:
    return (_DIR / "ocr_prompt.txt").read_text(encoding="utf-8")
