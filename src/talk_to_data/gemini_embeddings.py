"""Gemini embeddings for pgvector-backed PDF chunk search (optional)."""

from __future__ import annotations

from google import genai

_EMBEDDING_MODEL = "text-embedding-004"


def embed_query(text: str, api_key: str) -> tuple[list[float] | None, str | None]:
    """Single query vector for similarity search."""
    if not (text or "").strip():
        return None, "Empty query."
    try:
        client = genai.Client(api_key=api_key)
        r = client.models.embed_content(model=_EMBEDDING_MODEL, contents=text.strip())
        if not r.embeddings:
            return None, "No embedding returned."
        return list(r.embeddings[0].values), None
    except Exception as exc:
        return None, str(exc)


def embed_documents(texts: list[str], api_key: str) -> tuple[list[list[float]] | None, str | None]:
    """Batch document embeddings (preserves order)."""
    if not texts:
        return [], None
    try:
        client = genai.Client(api_key=api_key)
        r = client.models.embed_content(model=_EMBEDDING_MODEL, contents=texts)
        if not r.embeddings or len(r.embeddings) != len(texts):
            return None, "Embedding batch size mismatch."
        return [list(e.values) for e in r.embeddings], None
    except Exception as exc:
        return None, str(exc)
