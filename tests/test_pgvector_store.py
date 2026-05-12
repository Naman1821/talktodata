"""Unit tests for PDF chunking (no DB required)."""

from talk_to_data.pgvector_store import chunk_text_for_indexing, is_configured


def test_chunk_text_for_indexing_splits():
    t = "x" * 3000
    chunks = chunk_text_for_indexing(t, max_chars=1000, overlap=100)
    assert len(chunks) >= 3
    assert all(len(c) <= 1000 for c in chunks)


def test_chunk_empty():
    assert chunk_text_for_indexing("") == []
    assert chunk_text_for_indexing("   ") == []


def test_is_configured_without_env(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert is_configured() is False
