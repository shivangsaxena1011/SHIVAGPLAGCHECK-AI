"""Analysis Pipeline Worker.

Executes the full end-to-end analysis workflow:
- Text extraction & Page coordinate mapping
- Exact & Near-verbatim matching (Winnowing + Seed-and-Extend)
- Semantic Paraphrase matching (SBERT)
- Multi-signal AI writing likelihood estimation
- Citation & Reference verification
- Deterministic score fusion & exclusion filtering
- Report generation (HTML & PDF)
- Real-time progress updates (0% -> 100%).
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.config import settings
from app.models.entities import (
    Submission,
    Document,
    DocumentPage,
    DocumentSection,
    MatchEvidence,
    AIFinding,
    Citation,
    Reference,
    Report,
)
from app.schemas.evidence import MatchEvidenceSchema
from app.schemas.check import CheckOptions
from app.services.document.extractor import DocumentExtractor
from app.services.plagiarism.exact.winnowing import fingerprint
from app.services.plagiarism.exact.alignment import align
from app.services.plagiarism.semantic.semantic import SemanticDetector
from app.services.ai_detection.ai_detector import AIContentDetector
from app.services.citations.citation_detector import CitationDetector
from app.services.corpus.manager import corpus_manager
from app.services.scoring.score_fusion import ScoreFusionEngine
from app.services.reporting.html_generator import HTMLReportGenerator
from app.services.reporting.pdf_generator import PDFReportGenerator

logger = logging.getLogger(__name__)


class PipelineWorker:
    """Orchestrates end-to-end document verification."""

    def __init__(self):
        self.extractor = DocumentExtractor()
        self.semantic_detector = SemanticDetector(
            model_name=settings.SEMANTIC_MODEL_NAME,
            cosine_threshold=settings.SEMANTIC_SIMILARITY_THRESHOLD,
            device=settings.DEVICE,
        )
        self.ai_detector = AIContentDetector()
        self.citation_detector = CitationDetector(
            email=settings.CROSSREF_API_EMAIL,
            offline=False,
        )
        self.fusion_engine = ScoreFusionEngine()
        self.html_generator = HTMLReportGenerator()
        self.pdf_generator = PDFReportGenerator()

    async def update_progress(
        self,
        session: AsyncSession,
        submission_id: str,
        progress: int,
        stage: str,
        status: str = "PROCESSING",
    ) -> None:
        """Update progress in database."""
        stmt = (
            update(Submission)
            .where(Submission.id == submission_id)
            .values(progress=progress, current_stage=stage, status=status)
        )
        await session.execute(stmt)
        await session.commit()
        logger.info(f"Submission {submission_id} [{progress}%]: {stage}")

    async def execute(
        self,
        session: AsyncSession,
        submission_id: str,
        options: CheckOptions,
    ) -> None:
        """Run the complete pipeline for a submission."""
        try:
            # 1. Fetch submission
            stmt = select(Submission).where(Submission.id == submission_id)
            result = await session.execute(stmt)
            submission = result.scalar_one_or_none()
            if not submission:
                logger.error(f"Submission {submission_id} not found.")
                return

            await self.update_progress(session, submission_id, 10, "Extracting text and structure")

            # 2. Extract document text and coordinates
            file_path = Path(submission.file_path)
            extracted = self.extractor.extract_file(file_path)

            doc = Document(
                submission_id=submission_id,
                word_count=extracted.word_count,
                char_count=extracted.char_count,
                page_count=extracted.page_count,
                extracted_text=extracted.raw_text,
            )
            session.add(doc)
            await session.flush()

            # Save pages
            for p in extracted.pages:
                session.add(
                    DocumentPage(
                        document_id=doc.id,
                        page_number=p.page_number,
                        char_start=p.char_start,
                        char_end=p.char_end,
                        text=p.text,
                    )
                )

            # Save sections
            for sec in extracted.sections:
                session.add(
                    DocumentSection(
                        document_id=doc.id,
                        section_type=sec.section_type,
                        title=sec.title,
                        char_start=sec.char_start,
                        char_end=sec.char_end,
                    )
                )
            await session.commit()

            await self.update_progress(session, submission_id, 20, "Building document position map")

            # Prepare sentence dicts for downstream detectors
            sentence_dicts = [
                {
                    "sentence_index": s.sentence_index,
                    "paragraph_index": s.paragraph_index,
                    "page_number": s.page_number,
                    "char_start": s.char_start,
                    "char_end": s.char_end,
                    "text": s.text,
                }
                for s in extracted.sentences
            ]

            raw_matches: list[MatchEvidenceSchema] = []

            # 3. Exact Plagiarism Detection (35%)
            await self.update_progress(session, submission_id, 35, "Running Winnowing & Seed-Extend matching")

            if options.scan_local_corpus and corpus_manager.total_documents() > 0:
                # Winnowing fingerprint of submitted document
                sub_fps = fingerprint(extracted.raw_text, k=settings.WINNOWING_K, w=settings.WINNOWING_W)
                candidates = corpus_manager.query_fingerprints(sub_fps, min_overlap=2)

                # Track unique candidate source IDs
                seen_sources = set()
                for cand in candidates[:15]:
                    src_doc = corpus_manager.get_source(cand.source_id)
                    if not src_doc or cand.source_id in seen_sources:
                        continue
                    seen_sources.add(cand.source_id)

                    # Run seed-and-extend passage alignment
                    aligned_passages = align(
                        extracted.raw_text,
                        src_doc.text,
                        min_seed_len=settings.MIN_SEED_LEN,
                        extend_tolerance=settings.EXTEND_TOLERANCE,
                        min_passage_len=settings.MIN_PASSAGE_LEN,
                    )

                    for ap in aligned_passages:
                        sub_text = extracted.raw_text[ap.query_start : ap.query_end]
                        src_text = src_doc.text[ap.candidate_start : ap.candidate_end]
                        
                        # Find page in submission
                        p_num = 1
                        for p in extracted.pages:
                            if p.char_start <= ap.query_start <= p.char_end:
                                p_num = p.page_number
                                break

                        raw_matches.append(
                            MatchEvidenceSchema(
                                id=str(uuid.uuid4()),
                                submission_id=submission_id,
                                source_id=src_doc.source_id,
                                source_type="LOCAL_CORPUS",
                                detection_type="EXACT" if ap.match_type == "EXACT" else "NEAR_EXACT",
                                confidence=ap.score,
                                similarity=ap.score,
                                submitted_text=sub_text,
                                source_text=src_text,
                                submission_page=p_num,
                                submission_start=ap.query_start,
                                submission_end=ap.query_end,
                                source_start=ap.candidate_start,
                                source_end=ap.candidate_end,
                                evidence_reason=f"Verbatim alignment (match ratio: {int(ap.score * 100)}%)",
                                url=src_doc.url,
                                doi=src_doc.doi,
                                title=src_doc.title,
                                authors=src_doc.authors,
                            )
                        )

            # 4. Semantic Similarity Matching (50%)
            await self.update_progress(session, submission_id, 50, "Running SBERT semantic similarity")

            if options.scan_local_corpus and corpus_manager.total_documents() > 0:
                for src_id, src_doc in list(corpus_manager.sources.items())[:10]:
                    cand_sentences = [
                        s.strip() for s in src_doc.text.split(".") if len(s.strip().split()) >= 6
                    ]
                    sem_matches = self.semantic_detector.find_matches(
                        sentence_dicts,
                        source_id=src_id,
                        source_title=src_doc.title,
                        candidate_sentences=cand_sentences,
                        top_k=2,
                    )

                    for sm in sem_matches:
                        raw_matches.append(
                            MatchEvidenceSchema(
                                id=str(uuid.uuid4()),
                                submission_id=submission_id,
                                source_id=sm.source_id,
                                source_type="LOCAL_CORPUS",
                                detection_type="SEMANTIC",
                                confidence=sm.cosine_score,
                                similarity=sm.cosine_score,
                                submitted_text=sm.query_sentence,
                                source_text=sm.source_sentence,
                                submission_page=sm.page_number,
                                submission_start=sm.query_start,
                                submission_end=sm.query_end,
                                evidence_reason=f"Semantic paraphrase (cosine similarity: {sm.cosine_score:.2f})",
                                url=src_doc.url,
                                doi=src_doc.doi,
                                title=src_doc.title,
                                authors=src_doc.authors,
                            )
                        )

            # 5. AI Writing Analysis (65%)
            await self.update_progress(session, submission_id, 65, "Evaluating AI writing likelihood")

            ai_result = self.ai_detector.analyze_document(extracted.raw_text, sentence_dicts)

            for sig in ai_result.sentence_signals:
                session.add(
                    AIFinding(
                        submission_id=submission_id,
                        sentence_index=sig.sentence_index,
                        sentence_text=sig.sentence_text,
                        char_start=sig.char_start,
                        char_end=sig.char_end,
                        page_number=sig.page_number,
                        likelihood_score=sig.likelihood,
                        confidence=sig.confidence,
                        primary_signal=sig.primary_signal,
                    )
                )

            # 6. Citation & Reference Verification (75%)
            await self.update_progress(session, submission_id, 75, "Verifying citations & references")

            in_text_cites = self.citation_detector.find_in_text_citations(
                extracted.raw_text, extracted.pages
            )
            for itc in in_text_cites:
                session.add(
                    Citation(
                        submission_id=submission_id,
                        raw_text=itc.raw_text,
                        cite_key=itc.cite_key,
                        char_start=itc.char_start,
                        char_end=itc.char_end,
                        page_number=itc.page_number,
                    )
                )

            # Detect bibliography start
            bib_sec = next((s for s in extracted.sections if s.section_type == "BIBLIOGRAPHY"), None)
            bib_start = bib_sec.char_start if bib_sec else None

            ref_entries = self.citation_detector.extract_and_verify_references(
                extracted.raw_text, bib_section_start=bib_start
            )
            for ref in ref_entries:
                session.add(
                    Reference(
                        submission_id=submission_id,
                        raw_text=ref.raw_text,
                        parsed_title=ref.parsed_title,
                        parsed_authors=", ".join(ref.parsed_authors),
                        parsed_year=ref.parsed_year,
                        doi=ref.doi,
                        verification_status=ref.verification_status,
                        confidence=ref.confidence,
                        issues_json="; ".join(ref.issues) if ref.issues else None,
                    )
                )

            # 7. Match Fusion & Deterministic Scoring (85%)
            await self.update_progress(session, submission_id, 85, "Aggregating evidence & fusing scores")

            quote_spans = [
                (s.char_start, s.char_end) for s in extracted.sections if s.section_type == "QUOTE"
            ]
            bib_spans = [
                (s.char_start, s.char_end) for s in extracted.sections if s.section_type == "BIBLIOGRAPHY"
            ]
            citation_spans = [(c.char_start, c.char_end) for c in in_text_cites]

            fusion_result = self.fusion_engine.fuse(
                matches=raw_matches,
                total_chars=extracted.char_count,
                total_words=extracted.word_count,
                quote_spans=quote_spans,
                bib_spans=bib_spans,
                citation_spans=citation_spans,
                options=options,
            )

            # Save filtered matches
            for m in fusion_result.filtered_matches:
                session.add(
                    MatchEvidence(
                        submission_id=submission_id,
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
                        source_start=m.source_start,
                        source_end=m.source_end,
                        evidence_reason=m.evidence_reason,
                        url=m.url,
                        doi=m.doi,
                        title=m.title,
                        authors=m.authors,
                    )
                )

            # 8. Report Generation (95%)
            await self.update_progress(session, submission_id, 95, "Generating PDF & HTML reports")

            html_filename = f"report_{submission_id}.html"
            pdf_filename = f"report_{submission_id}.pdf"
            html_path = settings.REPORT_DIR / html_filename
            pdf_path = settings.REPORT_DIR / pdf_filename

            # Generate HTML report
            self.html_generator.generate_file(
                output_path=html_path,
                submission=submission,
                document=extracted,
                breakdown=fusion_result.breakdown,
                sources=fusion_result.source_contributions,
                ai_result=ai_result,
                references=ref_entries,
                matches=fusion_result.filtered_matches,
            )

            # Generate PDF report
            self.pdf_generator.generate_file(
                output_path=pdf_path,
                submission=submission,
                document=extracted,
                breakdown=fusion_result.breakdown,
                sources=fusion_result.source_contributions,
                ai_result=ai_result,
                references=ref_entries,
                matches=fusion_result.filtered_matches,
            )

            # Save report record
            verified_refs = sum(1 for r in ref_entries if r.verification_status == "VALID")
            issue_refs = sum(1 for r in ref_entries if r.verification_status in ["MISMATCH", "HALLUCINATED", "UNRESOLVABLE"])

            report = Report(
                submission_id=submission_id,
                overall_similarity=fusion_result.breakdown.overall_similarity,
                exact_similarity=fusion_result.breakdown.exact_similarity,
                near_exact_similarity=fusion_result.breakdown.near_exact_similarity,
                semantic_similarity=fusion_result.breakdown.semantic_similarity,
                ai_likelihood=ai_result.overall_likelihood,
                total_sources=len(fusion_result.source_contributions),
                total_words=extracted.word_count,
                total_pages=extracted.page_count,
                verified_references_count=verified_refs,
                issue_references_count=issue_refs,
                html_path=str(html_path),
                pdf_path=str(pdf_path),
            )
            session.add(report)

            # Complete!
            await self.update_progress(
                session, submission_id, 100, "Analysis Complete", status="COMPLETED"
            )

        except Exception as e:
            logger.exception(f"Pipeline error for submission {submission_id}: {e}")
            stmt = (
                update(Submission)
                .where(Submission.id == submission_id)
                .values(status="FAILED", error_message=str(e), progress=0)
            )
            await session.execute(stmt)
            await session.commit()
            raise
