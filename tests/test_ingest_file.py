from pathlib import Path

import pytest

from ingest_file import build_chunks, chunk_text


def test_chunk_text_respects_limit_and_overlap() -> None:
    text = "A" * 180 + "\n\n" + "B" * 180
    chunks = chunk_text(text, max_chars=200, overlap_chars=20)
    assert len(chunks) >= 2
    assert all(0 < len(chunk) <= 200 for chunk in chunks)
    assert chunks[0][-20:] in chunks[1]


def test_chunk_text_rejects_invalid_limits() -> None:
    with pytest.raises(ValueError):
        chunk_text("content", max_chars=50)
    with pytest.raises(ValueError):
        chunk_text("content", max_chars=100, overlap_chars=100)


def test_build_chunks_is_deterministic(tmp_path: Path) -> None:
    document = tmp_path / "guide.md"
    document.write_text("# Guide\n\nThe service uses Qdrant for vector search.", encoding="utf-8")
    first = build_chunks(document, max_chars=300, overlap_chars=20)
    second = build_chunks(document, max_chars=300, overlap_chars=20)
    assert first == second
    assert first[0].source == "guide.md"
    assert first[0].document_id.startswith("guide-")
