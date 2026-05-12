"""
Postgres + pgvector storage for PDF chunk embeddings (Docker service `db`).

Requires DATABASE_URL (e.g. postgresql://natwest:natwest@localhost:5432/talkdata).
Embeddings use Gemini text-embedding-004 (768-dim) — same key as chat.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

import psycopg2
from pgvector.psycopg2 import register_vector

# Must match Gemini text-embedding-004 output (768).
EMBEDDING_DIMENSION = 768

_DDL_TABLE = f"""
CREATE TABLE IF NOT EXISTS pdf_chunks (
    id BIGSERIAL PRIMARY KEY,
    doc_key TEXT NOT NULL,
    filename TEXT NOT NULL,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    embedding vector({EMBEDDING_DIMENSION}) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (doc_key, chunk_index)
)
"""


def database_url() -> str | None:
    url = (os.environ.get("DATABASE_URL") or "").strip()
    return url or None


def is_configured() -> bool:
    return bool(database_url())


def chunk_text_for_indexing(text: str, max_chars: int = 1400, overlap: int = 200) -> list[str]:
    """Split PDF text into overlapping windows for embedding."""
    t = (text or "").strip()
    if not t:
        return []
    chunks: list[str] = []
    i = 0
    step = max(1, max_chars - overlap)
    while i < len(t):
        chunks.append(t[i : i + max_chars])
        i += step
    return chunks[:300]


@contextmanager
def _connection() -> Generator[psycopg2.extensions.connection, None, None]:
    url = database_url()
    if not url:
        raise RuntimeError("DATABASE_URL is not set.")
    conn = psycopg2.connect(url, connect_timeout=8)
    try:
        register_vector(conn)
        yield conn
    finally:
        conn.close()


def ensure_schema() -> tuple[bool, str | None]:
    """CREATE EXTENSION + table + optional HNSW index."""
    try:
        with _connection() as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.autocommit = False
            with conn.cursor() as cur:
                cur.execute(_DDL_TABLE)
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS pdf_chunks_doc_key_idx ON pdf_chunks (doc_key)"
                )
                try:
                    cur.execute(
                        "CREATE INDEX IF NOT EXISTS pdf_chunks_embedding_hnsw ON pdf_chunks "
                        "USING hnsw (embedding vector_cosine_ops)"
                    )
                except Exception:
                    pass
            conn.commit()
        return True, None
    except Exception as exc:
        return False, str(exc)


def replace_pdf_chunks(
    doc_key: str,
    filename: str,
    indexed: list[tuple[int, str, list[float]]],
) -> tuple[bool, str | None]:
    """Replace all chunks for doc_key with new rows."""
    if not indexed:
        return False, "No chunks to store."
    try:
        with _connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM pdf_chunks WHERE doc_key = %s", (doc_key,))
                for chunk_index, content, embedding in indexed:
                    if len(embedding) != EMBEDDING_DIMENSION:
                        return False, f"Embedding dim {len(embedding)} != {EMBEDDING_DIMENSION}."
                    cur.execute(
                        """
                        INSERT INTO pdf_chunks (doc_key, filename, chunk_index, content, embedding)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (doc_key, filename, chunk_index, content, embedding),
                    )
            conn.commit()
        return True, None
    except Exception as exc:
        return False, str(exc)


def search_similar_chunks(
    doc_key: str,
    query_embedding: list[float],
    top_k: int = 5,
) -> tuple[list[tuple[str, int, float]], str | None]:
    """Cosine distance (<=>); lower is closer. Return (content, chunk_index, distance)."""
    if len(query_embedding) != EMBEDDING_DIMENSION:
        return [], f"Query embedding dim {len(query_embedding)} != {EMBEDDING_DIMENSION}."
    try:
        with _connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT content, chunk_index, embedding <=> %s::vector AS dist
                    FROM pdf_chunks
                    WHERE doc_key = %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (query_embedding, doc_key, query_embedding, top_k),
                )
                rows = cur.fetchall()
        out: list[tuple[str, int, float]] = [
            (str(r[0]), int(r[1]), float(r[2])) for r in rows
        ]
        return out, None
    except Exception as exc:
        return [], str(exc)


def count_chunks(doc_key: str) -> int:
    try:
        with _connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM pdf_chunks WHERE doc_key = %s",
                    (doc_key,),
                )
                row = cur.fetchone()
                return int(row[0]) if row else 0
    except Exception:
        return 0
