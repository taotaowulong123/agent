from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
STORAGE_DIR = BASE_DIR / "storage"


class Settings(BaseSettings):
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    BASE_URL: str = "http://127.0.0.1:8000"

    # OCR
    OCR_PROVIDER: str = "openai"
    OCR_API_KEY: str = ""
    OCR_API_BASE: str = "https://api.openai.com/v1"
    OCR_MODEL: str = "gpt-4o"

    # ASR
    ASR_PROVIDER: str = "openai"
    ASR_API_KEY: str = ""
    ASR_API_BASE: str = "https://api.openai.com/v1"
    ASR_MODEL: str = "whisper-1"

    # LLM
    LLM_PROVIDER: str = "openai"
    LLM_API_KEY: str = ""
    LLM_API_BASE: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4o"

    # Processing
    FRAME_INTERVAL_SEC: int = 5
    AUDIO_CHUNK_SEC: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
