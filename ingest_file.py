#!/usr/bin/env python3
"""Chunk a text/markdown file and load it into the RAG stack via POST /ingest.

Stdlib only — no pip install needed. Run it wherever the API is reachable:

    python3 ingest_file.py server-setup.md
    python3 ingest_file.py notes.md --api http://localhost:8000 --chunk 900

Chunking strategy: split on blank lines into paragraphs, then greedily pack
paragraphs into chunks up to ~CHUNK_CHARS characters so related lines stay
together. Simple, dependency-free, and good enough for retrieval on docs.
"""
import argparse
import json
import sys
import urllib.request


def chunk_text(text: str, max_chars: int) -> list[str]:
    """Pack paragraphs (blank-line separated) into chunks up to max_chars."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buf = ""
    for para in paragraphs:
        # A single huge paragraph gets hard-split so it never exceeds the cap.
        if len(para) > max_chars:
            if buf:
                chunks.append(buf)
                buf = ""
            for i in range(0, len(para), max_chars):
                chunks.append(para[i : i + max_chars])
            continue
        if len(buf) + len(para) + 2 > max_chars:
            chunks.append(buf)
            buf = para
        else:
            buf = f"{buf}\n\n{para}" if buf else para
    if buf:
        chunks.append(buf)
    return chunks


def ingest(api: str, texts: list[str], batch: int) -> int:
    """POST texts to /ingest in batches. Returns total ingested."""
    total = 0
    for start in range(0, len(texts), batch):
        payload = json.dumps({"texts": texts[start : start + batch]}).encode()
        req = urllib.request.Request(
            f"{api.rstrip('/')}/ingest",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=600) as resp:
            body = json.loads(resp.read())
        total += body.get("ingested", 0)
        print(f"  batch {start // batch + 1}: ingested {body.get('ingested', 0)}")
    return total


def main() -> None:
    ap = argparse.ArgumentParser(description="Ingest a file into the RAG stack.")
    ap.add_argument("file", help="path to the .md/.txt file to ingest")
    ap.add_argument("--api", default="http://localhost:8000", help="API base URL")
    ap.add_argument("--chunk", type=int, default=900, help="max chars per chunk")
    ap.add_argument("--batch", type=int, default=16, help="chunks per POST")
    args = ap.parse_args()

    with open(args.file, encoding="utf-8") as f:
        text = f.read()

    chunks = chunk_text(text, args.chunk)
    if not chunks:
        sys.exit("Nothing to ingest — file is empty.")
    print(f"Split {args.file} into {len(chunks)} chunks. Ingesting -> {args.api}")
    total = ingest(args.api, chunks, args.batch)
    print(f"Done. Ingested {total} chunks.")


if __name__ == "__main__":
    main()
