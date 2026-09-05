"""Security, authentication, and file validation utilities."""

from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Magic numbers / file signatures
FILE_SIGNATURES = {
    "pdf": b"%PDF-",
    "docx": b"PK\x03\x04",  # ZIP container header
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate bcrypt hash of a plain password."""
    return pwd_context.hash(password)


def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except Exception:
        return None


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and unsafe characters."""
    clean = os.path.basename(filename)
    clean = re.sub(r"[^\w\s\.-]", "_", clean)
    return clean


def validate_file_signature(content: bytes, filename: str) -> tuple[bool, str]:
    """Validate genuine file signature rather than trusting extension alone."""
    ext = Path(filename).suffix.lower().lstrip(".")
    if not ext:
        return False, "File has no extension"

    if ext == "pdf":
        if not content.startswith(FILE_SIGNATURES["pdf"]):
            return False, "Invalid PDF: Missing %PDF- signature"
    elif ext == "docx":
        if not content.startswith(FILE_SIGNATURES["docx"]):
            return False, "Invalid DOCX: Missing standard ZIP container signature"
    elif ext == "txt":
        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content.decode("latin-1")
            except UnicodeDecodeError:
                return False, "Invalid text file: Cannot decode content"
    else:
        return False, f"Unsupported file type: .{ext}"

    return True, ext
