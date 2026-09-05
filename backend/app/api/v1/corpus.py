"""Corpus Management API Router."""

from __future__ import annotations

import hashlib
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.entities import Source, SourceChunk, Fingerprint
from app.schemas.corpus import (
    CorpusDocumentCreate,
    CorpusDocumentResponse,
    CorpusStatsResponse,
)
from app.services.corpus.manager import corpus_manager
from app.services.document.extractor import DocumentExtractor

router = APIRouter(prefix="/corpus", tags=["Corpus"])
extractor = DocumentExtractor()


@router.post("/add", response_model=CorpusDocumentResponse, status_code=status.HTTP_201_CREATED)
async def add_corpus_document(
    doc_in: CorpusDocumentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add a reference document to the local corpus from JSON payload."""
    if not doc_in.text.strip():
        raise HTTPException(status_code=400, detail="Document text cannot be empty.")

    source_id = str(uuid.uuid4())
    checksum = hashlib.sha256(doc_in.text.encode("utf-8")).hexdigest()

    stmt = select(Source).where(Source.checksum == checksum)
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()
    if existing:
        if existing.id not in corpus_manager.sources:
            corpus_manager.add_document(
                source_id=existing.id,
                title=existing.title,
                text=existing.text,
                authors=existing.authors,
                publication=existing.publication,
                year=existing.year,
                url=existing.url,
                doi=existing.doi,
            )
        raise HTTPException(status_code=409, detail="A document with identical content already exists in the corpus.")

    # 1. Index in memory
    indexed = corpus_manager.add_document(
        source_id=source_id,
        title=doc_in.title,
        text=doc_in.text,
        authors=doc_in.authors,
        publication=doc_in.publication,
        year=doc_in.year,
        url=doc_in.url,
        doi=doc_in.doi,
    )

    # 2. Persist to database
    source_row = Source(
        id=source_id,
        title=doc_in.title,
        authors=doc_in.authors,
        publication=doc_in.publication,
        year=doc_in.year,
        url=doc_in.url,
        doi=doc_in.doi,
        checksum=checksum,
        text=doc_in.text,
    )
    db.add(source_row)
    await db.flush()

    for chunk in indexed.chunks:
        chunk_row = SourceChunk(
            source_id=source_id,
            chunk_index=chunk.chunk_index,
            char_start=chunk.char_start,
            char_end=chunk.char_end,
            text=chunk.text,
        )
        db.add(chunk_row)
        await db.flush()

        # Add fingerprints
        fps = indexed.fingerprints_by_chunk.get(chunk.chunk_index, [])
        for fp in fps:
            db.add(
                Fingerprint(
                    source_id=source_id,
                    chunk_id=chunk_row.id,
                    hash_value=fp,
                )
            )

    await db.commit()
    await db.refresh(source_row)

    return CorpusDocumentResponse(
        id=source_row.id,
        title=source_row.title,
        authors=source_row.authors,
        publication=source_row.publication,
        year=source_row.year,
        url=source_row.url,
        doi=source_row.doi,
        source_type=source_row.source_type,
        checksum=source_row.checksum,
        word_count=indexed.word_count,
        chunks_count=len(indexed.chunks),
        created_at=source_row.created_at,
    )


@router.post("/upload", response_model=CorpusDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_corpus_document(
    file: UploadFile = File(...),
    title: str = Form(None),
    authors: str = Form(None),
    publication: str = Form(None),
    year: str = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Upload a PDF, DOCX, or TXT file directly into the comparison corpus."""
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    ext = (file.filename or "doc.txt").split(".")[-1].lower()
    extracted = extractor.extract(content, ext, filename=file.filename or "corpus_doc")
    doc_title = title if (title and title.strip()) else (file.filename or "Corpus Document")

    return await add_corpus_document(
        CorpusDocumentCreate(
            title=doc_title,
            authors=authors,
            publication=publication,
            year=year,
            text=extracted.raw_text,
        ),
        db=db,
    )


@router.get("", response_model=list[CorpusDocumentResponse])
async def list_corpus(db: AsyncSession = Depends(get_db)):
    """List all documents indexed in the local comparison corpus."""
    stmt = select(Source).order_by(Source.created_at.desc())
    result = await db.execute(stmt)
    sources = result.scalars().all()

    return [
        CorpusDocumentResponse(
            id=s.id,
            title=s.title,
            authors=s.authors,
            publication=s.publication,
            year=s.year,
            url=s.url,
            doi=s.doi,
            source_type=s.source_type,
            checksum=s.checksum,
            word_count=len(s.text.split()),
            chunks_count=len(corpus_manager.get_source(s.id).chunks) if corpus_manager.get_source(s.id) else 0,
            created_at=s.created_at,
        )
        for s in sources
    ]


@router.get("/stats", response_model=CorpusStatsResponse)
async def get_corpus_stats():
    """Get total documents, chunks, and fingerprints in index."""
    return CorpusStatsResponse(
        total_documents=corpus_manager.total_documents(),
        total_chunks=corpus_manager.total_chunks(),
        total_fingerprints=corpus_manager.total_fingerprints(),
    )


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_corpus_document(source_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a document from the comparison corpus."""
    stmt = select(Source).where(Source.id == source_id)
    result = await db.execute(stmt)
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Source not found.")

    await db.delete(s)
    await db.commit()
    # Remove from in-memory manager
    corpus_manager.sources.pop(source_id, None)
    return None
