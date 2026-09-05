"""Main FastAPI Application Entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure backend directory is in sys.path so 'app.*' imports always resolve
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from contextlib import asynccontextmanager
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
