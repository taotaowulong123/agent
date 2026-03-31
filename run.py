"""Entry point: run the FastAPI app with uvicorn."""
import uvicorn
from dotenv import load_dotenv

load_dotenv()  # load .env before importing app (so Settings picks up values)

from app.api.main import app  # noqa: E402
from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level="info",
    )
