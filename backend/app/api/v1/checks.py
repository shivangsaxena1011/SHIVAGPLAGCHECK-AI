"""Checks and Submissions API Router."""

from __future__ import annotations

import asyncio
import hashlib
import os
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db, async_session_maker
from app.core.security import validate_file_signature, sanitize_filename
from app.models.entities import (
    Submission,
    Document,
    DocumentPage,
    MatchEvidence,
    AIFinding,
    Citation,
    Reference,
    Report,
)
from app.schemas.check import (
    CheckOptions,
    CheckStatusResponse,
    CheckResultResponse,
    SimilarityBreakdown,
    SourceContribution,
    AISummary,
    CitationSummary,
    DocumentPageSchema,
)
from app.schemas.evidence import MatchEvidenceSchema, AIFindingSchema, CitationItemSchema, ReferenceItemSchema
from app.workers.pipeline_worker import PipelineWorker

router = APIRouter(prefix="/checks", tags=["Checks"])
worker = PipelineWorker()


async def run_pipeline_task(submission_id: str, options: CheckOptions) -> None:
    """Background task to run document processing."""
    async with async_session_maker() as session:
        try:
            await worker.execute(session, submission_id, options)
        except Exception as e:
            print(f"Background task failed: {e}")


@router.post("", response_model=CheckStatusResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_check(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(None),
    scan_local_corpus: bool = Form(True),
    scan_external: bool = Form(False),
    run_ai_detection: bool = Form(True),
    verify_citations: bool = Form(True),
    exclude_quotes: bool = Form(True),
    exclude_bibliography: bool = Form(True),
    exclude_small_matches: bool = Form(True),
    exclude_citations: bool = Form(True),
    db: AsyncSession = Depends(get_db),
):
    """Upload a PDF, DOCX, or TXT document and start originality analysis."""
    # 1. Read content
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(content) > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File size exceeds maximum allowed limit (50 MB).")

    # 2. Validate file signature
    valid, ext = validate_file_signature(content, file.filename or "file.txt")
    if not valid:
        raise HTTPException(status_code=400, detail=ext)

    # 3. Save to storage
    checksum = hashlib.sha256(content).hexdigest()
    sub_id = str(uuid.uuid4())
    safe_name = sanitize_filename(file.filename or f"doc_{sub_id}.{ext}")
    dest_path = settings.UPLOAD_DIR / f"{sub_id}_{safe_name}"

    with open(dest_path, "wb") as f:
        f.write(content)

    doc_title = title.strip() if (title and title.strip()) else safe_name

    # 4. Create submission record
    submission = Submission(
        id=sub_id,
        title=doc_title,
        original_filename=safe_name,
        file_path=str(dest_path),
        file_type=ext,
        file_size=len(content),
        checksum=checksum,
        status="PENDING",
        progress=0,
        current_stage="Uploaded and Queued",
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    options = CheckOptions(
        scan_local_corpus=scan_local_corpus,
        scan_external=scan_external,
        run_ai_detection=run_ai_detection,
        verify_citations=verify_citations,
        exclude_quotes=exclude_quotes,
        exclude_bibliography=exclude_bibliography,
        exclude_small_matches=exclude_small_matches,
        exclude_citations=exclude_citations,
    )

    # 5. Dispatch background execution
    background_tasks.add_task(run_pipeline_task, sub_id, options)

    return CheckStatusResponse(
        id=submission.id,
        status=submission.status,
        progress=submission.progress,
        current_stage=submission.current_stage,
        created_at=submission.created_at,
        updated_at=submission.updated_at,
    )


@router.get("/{check_id}/status", response_model=CheckStatusResponse)
async def get_check_status(check_id: str, db: AsyncSession = Depends(get_db)):
    """Get live progress and stage of a check."""
    stmt = select(Submission).where(Submission.id == check_id)
    result = await db.execute(stmt)
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Analysis check not found.")

    return CheckStatusResponse(
        id=sub.id,
        status=sub.status,
        progress=sub.progress,
        current_stage=sub.current_stage,
        error_message=sub.error_message,
        created_at=sub.created_at,
        updated_at=sub.updated_at,
    )


@router.get("/{check_id}/result", response_model=CheckResultResponse)
async def get_check_result(check_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve full analysis result."""
    stmt = (
        select(Submission)
        .where(Submission.id == check_id)
        .options(
            selectinload(Submission.document).selectinload(Document.pages),
            selectinload(Submission.matches),
            selectinload(Submission.ai_findings),
            selectinload(Submission.citations),
            selectinload(Submission.references),
            selectinload(Submission.report),
        )
    )
    result = await db.execute(stmt)
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Analysis check not found.")
    if sub.status != "COMPLETED":
        raise HTTPException(status_code=400, detail=f"Analysis is not completed yet (current: {sub.status}, {sub.progress}%).")

    doc = sub.document
    rep = sub.report

    # Rebuild source contributions
    source_map: dict[str, SourceContribution] = {}
    c_idx = 0
    for m in sub.matches:
        s_id = m.source_id or "unknown"
        if s_id not in source_map:
            source_map[s_id] = SourceContribution(
                source_id=s_id,
                title=m.title or "Unknown Source",
                authors=m.authors,
                url=m.url,
                doi=m.doi,
                source_type=m.source_type,
                similarity_contribution=m.source_similarity_contribution,
                matched_words=len(m.submitted_text.split()),
                primary_match_type=m.detection_type,
                color_index=c_idx,
            )
            c_idx += 1
        else:
            source_map[s_id].matched_words += len(m.submitted_text.split())

    sources = sorted(source_map.values(), key=lambda x: -x.similarity_contribution)

    # Breakdown
    breakdown = SimilarityBreakdown(
        overall_similarity=rep.overall_similarity if rep else 0.0,
        exact_similarity=rep.exact_similarity if rep else 0.0,
        near_exact_similarity=rep.near_exact_similarity if rep else 0.0,
        semantic_similarity=rep.semantic_similarity if rep else 0.0,
        matched_word_count=sum(s.matched_words for s in sources),
        total_words=doc.word_count if doc else 0,
    )

    # AI summary
    high_ai = sum(1 for a in sub.ai_findings if a.likelihood_score >= 0.65)
    med_ai = sum(1 for a in sub.ai_findings if 0.40 <= a.likelihood_score < 0.65)
    ai_summary = AISummary(
        overall_likelihood=rep.ai_likelihood if rep else 0.0,
        confidence_band="High Signal Confidence" if high_ai > 5 else "Moderate Signal Confidence",
        high_signal_sections=high_ai,
        medium_signal_sections=med_ai,
        total_sentences=len(sub.ai_findings),
    )

    # Citation summary
    v_count = sum(1 for r in sub.references if r.verification_status == "VALID")
    m_count = sum(1 for r in sub.references if r.verification_status == "MISMATCH")
    h_count = sum(1 for r in sub.references if r.verification_status == "HALLUCINATED")
    u_count = sum(1 for r in sub.references if r.verification_status == "UNRESOLVABLE")
    citation_summary = CitationSummary(
        total_references=len(sub.references),
        verified_count=v_count,
        mismatch_count=m_count,
        hallucinated_count=h_count,
        unresolvable_count=u_count,
        in_text_citations_count=len(sub.citations),
    )

    pages = [
        DocumentPageSchema(
            page_number=p.page_number,
            char_start=p.char_start,
            char_end=p.char_end,
            text=p.text,
        )
        for p in (doc.pages if doc else [])
    ]

    matches = [
        MatchEvidenceSchema(
            id=m.id,
            submission_id=m.submission_id,
            source_id=m.source_id,
            source_type=m.source_type,
            detection_type=m.detection_type,
            confidence=m.confidence,
            similarity=m.similarity,
            source_similarity_contribution=m.source_similarity_contribution,
            submitted_text=m.submitted_text,
            source_text=m.source_text,
            submission_page=m.submission_page,
            submission_start=m.submission_start,
            submission_end=m.submission_end,
            evidence_reason=m.evidence_reason,
            url=m.url,
            doi=m.doi,
            title=m.title,
            authors=m.authors,
        )
        for m in sub.matches
    ]

    ai_findings = [
        AIFindingSchema(
            id=a.id,
            sentence_index=a.sentence_index,
            sentence_text=a.sentence_text,
            char_start=a.char_start,
            char_end=a.char_end,
            page_number=a.page_number,
            likelihood_score=a.likelihood_score,
            confidence=a.confidence,
            primary_signal=a.primary_signal,
        )
        for a in sub.ai_findings
    ]

    citations = [
        CitationItemSchema(
            id=c.id,
            raw_text=c.raw_text,
            cite_key=c.cite_key,
            page_number=c.page_number,
            char_start=c.char_start,
            char_end=c.char_end,
        )
        for c in sub.citations
    ]

    references = [
        ReferenceItemSchema(
            id=r.id,
            raw_text=r.raw_text,
            parsed_title=r.parsed_title,
            parsed_authors=r.parsed_authors,
            parsed_year=r.parsed_year,
            doi=r.doi,
            verification_status=r.verification_status,
            confidence=r.confidence,
            issues=r.issues_json.split("; ") if r.issues_json else [],
        )
        for r in sub.references
    ]

    return CheckResultResponse(
        id=sub.id,
        title=sub.title,
        original_filename=sub.original_filename,
        file_type=sub.file_type,
        word_count=doc.word_count if doc else 0,
        char_count=doc.char_count if doc else 0,
        page_count=doc.page_count if doc else 1,
        created_at=sub.created_at,
        scores=breakdown,
        sources=sources,
        ai_summary=ai_summary,
        citation_summary=citation_summary,
        options=CheckOptions(),
        pages=pages,
        matches=matches,
        ai_findings=ai_findings,
        citations=citations,
        references=references,
    )


@router.get("/{check_id}/report/pdf")
async def download_pdf_report(check_id: str, db: AsyncSession = Depends(get_db)):
    """Download the generated PDF report."""
    stmt = select(Report).where(Report.submission_id == check_id)
    result = await db.execute(stmt)
    rep = result.scalar_one_or_none()
    if not rep or not rep.pdf_path or not os.path.exists(rep.pdf_path):
        raise HTTPException(status_code=404, detail="PDF report not available.")

    return FileResponse(
        path=rep.pdf_path,
        media_type="application/pdf",
        filename=f"SHIVANG_PLAGCHECK_{check_id}.pdf",
    )


@router.get("/{check_id}/report/html")
async def download_html_report(check_id: str, db: AsyncSession = Depends(get_db)):
    """Download the standalone HTML report."""
    stmt = select(Report).where(Report.submission_id == check_id)
    result = await db.execute(stmt)
    rep = result.scalar_one_or_none()
    if not rep or not rep.html_path or not os.path.exists(rep.html_path):
        raise HTTPException(status_code=404, detail="HTML report not available.")

    return FileResponse(
        path=rep.html_path,
        media_type="text/html",
        filename=f"SHIVANG_PLAGCHECK_{check_id}.html",
    )


@router.get("", response_model=list[CheckStatusResponse])
async def list_checks(db: AsyncSession = Depends(get_db)):
    """List all previous analysis submissions."""
    stmt = select(Submission).order_by(Submission.created_at.desc()).limit(50)
    result = await db.execute(stmt)
    submissions = result.scalars().all()

    return [
        CheckStatusResponse(
            id=s.id,
            status=s.status,
            progress=s.progress,
            current_stage=s.current_stage,
            error_message=s.error_message,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in submissions
    ]


@router.delete("/{check_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_check(check_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a submission and all associated reports/findings."""
    stmt = select(Submission).where(Submission.id == check_id)
    result = await db.execute(stmt)
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Check not found.")

    await db.delete(sub)
    await db.commit()
    return None
