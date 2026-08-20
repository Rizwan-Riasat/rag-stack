import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).parents[1] / "app"))
from main import ChunkInput, IngestRequest, QueryRequest, stable_point_id  # noqa: E402


def test_ingest_accepts_legacy_texts() -> None:
    request = IngestRequest(texts=["hello world"])
    assert request.normalized_chunks()[0].text == "hello world"


def test_ingest_requires_one_input_shape() -> None:
    with pytest.raises(ValidationError):
        IngestRequest()
    with pytest.raises(ValidationError):
        IngestRequest(texts=["a"], chunks=[ChunkInput(text="b")])


def test_query_limits_top_k() -> None:
    with pytest.raises(ValidationError):
        QueryRequest(question="valid question", top_k=1000)


def test_point_ids_deduplicate_identical_chunks() -> None:
    chunk = ChunkInput(text="same", document_id="doc", source="doc.pdf", page=1, chunk_index=0)
    assert stable_point_id(chunk) == stable_point_id(chunk)
    assert stable_point_id(chunk) != stable_point_id(chunk.model_copy(update={"page": 2}))
