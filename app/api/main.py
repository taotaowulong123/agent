from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.core.config import STORAGE_DIR
from app.api.routes import upload, jobs, pages

app = FastAPI(title="Media AI Agent", version="0.1.0")

# Serve uploaded/processed files as static assets
app.mount("/files", StaticFiles(directory=str(STORAGE_DIR)), name="files")

# Serve frontend static assets (JS, CSS)
STATIC_DIR = Path(__file__).parent.parent / "web" / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(pages.router)
app.include_router(upload.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
