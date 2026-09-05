"""Main FastAPI Application Entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
import sys
from pathlib import Path

# Ensure backend directory is in sys.path for direct imports
_backend_dir = str(Path(__file__).resolve().parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.core.config import settings
from app.core.database import init_db, async_session_maker
from app.api.v1.checks import router as checks_router
from app.api.v1.corpus import router as corpus_router
from app.models.entities import Source
from app.services.corpus.manager import corpus_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize database and load corpus index into memory."""
    settings.ensure_directories()
    await init_db()

    # Hydrate in-memory corpus index from database
    async with async_session_maker() as session:
        await corpus_manager.load_from_db(session)

    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.SUBTITLE,
    version=settings.VERSION,
    lifespan=lifespan,
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(checks_router, prefix=settings.API_V1_STR)
app.include_router(corpus_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["System"])
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "platform": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "subtitle": settings.SUBTITLE,
        "corpus_documents_loaded": corpus_manager.total_documents(),
        "total_fingerprints_indexed": corpus_manager.total_fingerprints(),
    }


# Frontend static distribution
import os
from pathlib import Path
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

FRONTEND_DIST = (Path(__file__).resolve().parent.parent.parent / "frontend" / "out")
if not FRONTEND_DIST.exists():
    FRONTEND_DIST = Path("frontend/out").resolve()

from fastapi import HTTPException

# Dynamic route compatibility: redirect /checks/<id> to /checks/?id=<id>
@app.get("/checks/{check_id}")
async def redirect_check_by_id(check_id: str):
    """Serve static files inside /checks if they exist, otherwise redirect actual check IDs to /checks/?id=<id>."""
    static_file = FRONTEND_DIST / "checks" / check_id
    if static_file.is_file():
        return FileResponse(static_file)

    # Don't intercept static assets or files
    if "." in check_id:
        raise HTTPException(status_code=404, detail="File not found")

    return RedirectResponse(url=f"/checks/?id={check_id}", status_code=302)



if FRONTEND_DIST.exists():
    _next_dir = FRONTEND_DIST / "_next"
    if _next_dir.exists():
        app.mount("/_next", StaticFiles(directory=str(_next_dir)), name="next_assets")
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")

