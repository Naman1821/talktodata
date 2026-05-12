"""Load PDF and CSV uploads (no cloud; CSV → DataFrame, PDF → extracted text)."""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Literal

import pandas as pd
from pypdf import PdfReader


MAX_PDF_STORE_CHARS = 500_000


@dataclass
class LoadedDocument:
    kind: Literal["csv", "pdf"]
    filename: str
    """Full extracted PDF text (empty for CSV). Capped for very large files."""
    pdf_text: str
    df: pd.DataFrame | None = None


def _cap_pdf_text(text: str) -> str:
    if len(text) <= MAX_PDF_STORE_CHARS:
        return text
    return text[: MAX_PDF_STORE_CHARS - 60] + "\n[... PDF text truncated for local processing ...]"


def extract_pdf_text(raw: bytes) -> str:
    reader = PdfReader(io.BytesIO(raw))
    parts: list[str] = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts).strip()


def csv_bytes_to_dataframe(raw: bytes) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(raw))


def load_uploaded_file(filename: str, raw: bytes) -> LoadedDocument:
    """Parse upload bytes. Raises ValueError on failure."""
    lower = filename.lower()
    if lower.endswith(".pdf"):
        try:
            text = extract_pdf_text(raw)
        except Exception as exc:
            raise ValueError("Could not read PDF.") from exc
        stored = _cap_pdf_text(text if text else "")
        return LoadedDocument(kind="pdf", filename=filename, pdf_text=stored, df=None)

    if lower.endswith(".csv"):
        try:
            df = csv_bytes_to_dataframe(raw)
        except Exception as exc:
            raise ValueError("Could not read CSV.") from exc
        if df.empty:
            raise ValueError("CSV has no rows.")
        return LoadedDocument(kind="csv", filename=filename, pdf_text="", df=df)

    raise ValueError("Unsupported file type.")
