"""SQLAlchemy ORM Entities for SHIVANG PLAGCHECK AI."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    BigInteger,
    Index,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default="RESEARCHER", nullable=False)  # ADMIN, TEACHER, STUDENT, RESEARCHER
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    submissions = relationship("Submission", back_populates="user", cascade="all, delete-orphan")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf, docx, txt
    file_size = Column(Integer, nullable=False)
    checksum = Column(String(64), index=True, nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)  # PENDING, PROCESSING, COMPLETED, FAILED
    progress = Column(Integer, default=0, nullable=False)
    current_stage = Column(String(100), default="Queued", nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="submissions")
    document = relationship("Document", back_populates="submission", uselist=False, cascade="all, delete-orphan")
    matches = relationship("MatchEvidence", back_populates="submission", cascade="all, delete-orphan")
    ai_findings = relationship("AIFinding", back_populates="submission", cascade="all, delete-orphan")
    citations = relationship("Citation", back_populates="submission", cascade="all, delete-orphan")
    references = relationship("Reference", back_populates="submission", cascade="all, delete-orphan")
    report = relationship("Report", back_populates="submission", uselist=False, cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_id = Column(String(36), ForeignKey("submissions.id", ondelete="CASCADE"), unique=True, nullable=False)
    word_count = Column(Integer, default=0, nullable=False)
    char_count = Column(Integer, default=0, nullable=False)
    page_count = Column(Integer, default=1, nullable=False)
    extracted_text = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=True)

    submission = relationship("Submission", back_populates="document")
    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    sections = relationship("DocumentSection", back_populates="document", cascade="all, delete-orphan")


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=False)
    char_start = Column(Integer, nullable=False)
    char_end = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)

    document = relationship("Document", back_populates="pages")

    __table_args__ = (
        Index("idx_doc_page", "document_id", "page_number"),
    )


class DocumentSection(Base):
    __tablename__ = "document_sections"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    section_type = Column(String(50), nullable=False)  # TITLE, BODY, QUOTE, BIBLIOGRAPHY, CITATION
    title = Column(String(255), nullable=True)
    char_start = Column(Integer, nullable=False)
    char_end = Column(Integer, nullable=False)

    document = relationship("Document", back_populates="sections")


class Source(Base):
    __tablename__ = "sources"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(500), nullable=False)
    authors = Column(String(500), nullable=True)
    publication = Column(String(255), nullable=True)
    year = Column(String(20), nullable=True)
    url = Column(String(1000), nullable=True)
    doi = Column(String(255), nullable=True, index=True)
    source_type = Column(String(50), default="LOCAL_CORPUS", nullable=False)  # LOCAL_CORPUS, WEB, CROSSREF, OPENALEX
    checksum = Column(String(64), unique=True, index=True, nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    chunks = relationship("SourceChunk", back_populates="source", cascade="all, delete-orphan")
    matches = relationship("MatchEvidence", back_populates="source", cascade="all, delete-orphan")


class SourceChunk(Base):
    __tablename__ = "source_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    source_id = Column(String(36), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    char_start = Column(Integer, nullable=False)
    char_end = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)

    source = relationship("Source", back_populates="chunks")
    fingerprints = relationship("Fingerprint", back_populates="chunk", cascade="all, delete-orphan")


class Fingerprint(Base):
    __tablename__ = "fingerprints"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    source_id = Column(String(36), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    chunk_id = Column(String(36), ForeignKey("source_chunks.id", ondelete="CASCADE"), nullable=False)
    hash_value = Column(BigInteger, nullable=False, index=True)

    chunk = relationship("SourceChunk", back_populates="fingerprints")


class MatchEvidence(Base):
    __tablename__ = "match_evidence"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_id = Column(String(36), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    source_id = Column(String(36), ForeignKey("sources.id", ondelete="CASCADE"), nullable=True)
    source_type = Column(String(50), default="LOCAL_CORPUS", nullable=False)
    detection_type = Column(String(50), nullable=False)  # EXACT, NEAR_EXACT, SEMANTIC, NGRAM, SELF_PLAGIARISM
    confidence = Column(Float, default=1.0, nullable=False)
    similarity = Column(Float, default=1.0, nullable=False)
    source_similarity_contribution = Column(Float, default=0.0, nullable=False)
    submitted_text = Column(Text, nullable=False)
    source_text = Column(Text, nullable=True)
    submission_page = Column(Integer, default=1, nullable=False)
    source_page = Column(Integer, default=1, nullable=True)
    submission_start = Column(Integer, nullable=False)
    submission_end = Column(Integer, nullable=False)
    source_start = Column(Integer, default=0, nullable=True)
    source_end = Column(Integer, default=0, nullable=True)
    sentence_index = Column(Integer, default=0, nullable=False)
    paragraph_index = Column(Integer, default=0, nullable=False)
    evidence_reason = Column(String(500), nullable=True)
    url = Column(String(1000), nullable=True)
    doi = Column(String(255), nullable=True)
    title = Column(String(500), nullable=True)
    authors = Column(String(500), nullable=True)

    submission = relationship("Submission", back_populates="matches")
    source = relationship("Source", back_populates="matches")

    __table_args__ = (
        Index("idx_submission_matches", "submission_id", "submission_start"),
    )


class AIFinding(Base):
    __tablename__ = "ai_findings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_id = Column(String(36), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    sentence_index = Column(Integer, nullable=False)
    sentence_text = Column(Text, nullable=False)
    char_start = Column(Integer, default=0, nullable=False)
    char_end = Column(Integer, default=0, nullable=False)
    page_number = Column(Integer, default=1, nullable=False)
    likelihood_score = Column(Float, nullable=False)  # 0.0 - 1.0 (e.g. 0.71 = 71%)
    confidence = Column(Float, default=0.8, nullable=False)
    primary_signal = Column(String(255), nullable=False)  # e.g. "Unusually uniform sentence structure"
    details_json = Column(Text, nullable=True)

    submission = relationship("Submission", back_populates="ai_findings")


class Citation(Base):
    __tablename__ = "citations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_id = Column(String(36), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    raw_text = Column(String(500), nullable=False)
    cite_key = Column(String(100), nullable=True)
    char_start = Column(Integer, nullable=False)
    char_end = Column(Integer, nullable=False)
    page_number = Column(Integer, default=1, nullable=False)
    claimed_authors = Column(String(500), nullable=True)
    claimed_year = Column(String(20), nullable=True)
    claimed_title = Column(String(500), nullable=True)
    doi = Column(String(255), nullable=True)

    submission = relationship("Submission", back_populates="citations")


class Reference(Base):
    __tablename__ = "references"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_id = Column(String(36), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    raw_text = Column(Text, nullable=False)
    parsed_title = Column(String(500), nullable=True)
    parsed_authors = Column(String(500), nullable=True)
    parsed_year = Column(String(20), nullable=True)
    doi = Column(String(255), nullable=True)
    verification_status = Column(String(50), default="UNVERIFIED", nullable=False)  # VALID, MISMATCH, HALLUCINATED, NOT_FOUND, UNRESOLVABLE
    confidence = Column(Float, default=1.0, nullable=False)
    issues_json = Column(Text, nullable=True)

    submission = relationship("Submission", back_populates="references")


class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_id = Column(String(36), ForeignKey("submissions.id", ondelete="CASCADE"), unique=True, nullable=False)
    overall_similarity = Column(Float, default=0.0, nullable=False)
    exact_similarity = Column(Float, default=0.0, nullable=False)
    near_exact_similarity = Column(Float, default=0.0, nullable=False)
    semantic_similarity = Column(Float, default=0.0, nullable=False)
    ai_likelihood = Column(Float, default=0.0, nullable=False)
    total_sources = Column(Integer, default=0, nullable=False)
    total_words = Column(Integer, default=0, nullable=False)
    total_pages = Column(Integer, default=1, nullable=False)
    verified_references_count = Column(Integer, default=0, nullable=False)
    issue_references_count = Column(Integer, default=0, nullable=False)
    summary_json = Column(Text, nullable=True)
    html_path = Column(String(512), nullable=True)
    pdf_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    submission = relationship("Submission", back_populates="report")
