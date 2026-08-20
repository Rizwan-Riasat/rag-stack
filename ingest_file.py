#!/usr/bin/env python3
"""Extract, chunk, and ingest a text, Markdown, or PDF document."""

import argparse
import hashlib
import json
import os
import sys
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Chunk:
    text: str
    document_id: str
    source: str
    page: int | None
    chunk_index: int


def chunk_text(text: str, max_chars: int, overlap_chars: int = 150) -> list[str]:
    """Create paragraph-aware chunks with bounded character overlap."""
    if max_chars < 100:
        raise ValueError("max_chars must be at least 100")
    if overlap_chars < 0 or overlap_chars >= max_chars:
        raise ValueError("overlap_chars must be between 0 and max_chars")

    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    normalized = "\n\n".join(paragraphs)
    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + max_chars, len(normalized))
        if end < len(normalized):
            minimum_break = start + max_chars // 2
            paragraph_break = normalized.rfind("\n\n", minimum_break, end)
            word_break = normalized.rfind(" ", minimum_break, end)
            boundary = max(paragraph_break, word_break)
            if boundary > start:
                end = boundary
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(normalized):
            break
        start = max(start + 1, end - overlap_chars)
    return chunks


def extract_pages(path: Path) -> list[tuple[int | None, str]]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise SystemExit(
                "PDF support requires: python3 -m pip install -r requirements-tools.txt"
            ) from exc
        reader = PdfReader(path)
        if reader.is_encrypted:
            raise SystemExit(
                "Encrypted PDFs are unsupported; provide an authorized decrypted copy."
            )
        pages = [
            (index, page.extract_text() or "") for index, page in enumerate(reader.pages, start=1)
        ]
        if not any(text.strip() for _, text in pages):
            raise SystemExit(
                "No extractable PDF text found. This may be a scanned PDF that requires OCR."
            )
        return pages
    if suffix not in {".txt", ".md"}:
        raise SystemExit("Supported file types: .pdf, .txt, and .md")
    return [(None, path.read_text(encoding="utf-8"))]


def build_chunks(path: Path, max_chars: int, overlap_chars: int) -> list[Chunk]:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    document_id = f"{path.stem}-{digest}"
    chunks: list[Chunk] = []
    index = 0
    for page, text in extract_pages(path):
        for content in chunk_text(text, max_chars=max_chars, overlap_chars=overlap_chars):
            chunks.append(Chunk(content, document_id, path.name, page, index))
            index += 1
    return chunks


def ingest(api: str, chunks: list[Chunk], batch_size: int, api_key: str | None) -> int:
    total = 0
    for start in range(0, len(chunks), batch_size):
        payload = json.dumps(
            {"chunks": [asdict(chunk) for chunk in chunks[start : start + batch_size]]}
        ).encode()
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["X-API-Key"] = api_key
        request = urllib.request.Request(f"{api.rstrip('/')}/ingest", data=payload, headers=headers)
        with urllib.request.urlopen(request, timeout=600) as response:
            body = json.loads(response.read())
        ingested = int(body.get("ingested", 0))
        total += ingested
        print(f"  batch {start // batch_size + 1}: ingested {ingested}")
    return total


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest a PDF, Markdown, or text document into the RAG stack."
    )
    parser.add_argument("file", type=Path, help="path to a .pdf, .md, or .txt file")
    parser.add_argument("--api", default="http://localhost:8000", help="API base URL")
    parser.add_argument(
        "--api-key", default=os.getenv("RAG_API_KEY"), help="API key (prefer RAG_API_KEY)"
    )
    parser.add_argument("--chunk", type=int, default=1_200, help="maximum characters per chunk")
    parser.add_argument("--overlap", type=int, default=150, help="character overlap between chunks")
    parser.add_argument("--batch", type=int, default=16, help="chunks per request")
    parser.add_argument(
        "--dry-run", action="store_true", help="extract and chunk without sending data"
    )
    args = parser.parse_args()

    if not args.file.is_file():
        parser.error(f"file does not exist: {args.file}")
    if args.batch < 1 or args.batch > 128:
        parser.error("--batch must be between 1 and 128")
    chunks = build_chunks(args.file, args.chunk, args.overlap)
    if not chunks:
        sys.exit("Nothing to ingest: the document contains no extractable text.")
    print(
        f"Extracted {len(chunks)} chunks from {args.file.name} "
        f"(document_id={chunks[0].document_id})"
    )
    if args.dry_run:
        print("Dry run complete; nothing was uploaded.")
        return
    total = ingest(args.api, chunks, args.batch, args.api_key)
    print(f"Done. Ingested {total} chunks with source metadata.")


if __name__ == "__main__":
    main()
