import os
import uuid

import httpx
from fastapi import FastAPI
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# --- Config (overridable via env / docker-compose) ---
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2:1b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

COLLECTION = "docs"
VECTOR_SIZE = 768  # nomic-embed-text output dimension

app = FastAPI(title="Mini RAG")
qdrant = QdrantClient(url=QDRANT_URL)


def ensure_collection() -> None:
    """Create the vector collection if it doesn't exist yet (idempotent)."""
    existing = [c.name for c in qdrant.get_collections().collections]
    if COLLECTION not in existing:
        qdrant.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )


async def embed(text: str) -> list[float]:
    """Turn text into a vector using the Ollama embedding model."""
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
        )
        r.raise_for_status()
        return r.json()["embedding"]


async def generate(prompt: str) -> str:
    """Ask the LLM to answer. stream=False so we get one JSON response back."""
    async with httpx.AsyncClient(timeout=300) as client:
        r = await client.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": LLM_MODEL, "prompt": prompt, "stream": False},
        )
        r.raise_for_status()
        return r.json()["response"]


class IngestReq(BaseModel):
    texts: list[str]


class QueryReq(BaseModel):
    question: str
    top_k: int = 3


@app.post("/ingest")
async def ingest(req: IngestReq):
    """Embed each chunk of text and store it in Qdrant."""
    ensure_collection()
    points = []
    for text in req.texts:
        vec = await embed(text)
        points.append(
            PointStruct(id=str(uuid.uuid4()), vector=vec, payload={"text": text})
        )
    qdrant.upsert(collection_name=COLLECTION, points=points)
    return {"ingested": len(points)}


@app.post("/query")
async def query(req: QueryReq):
    """The RAG loop: embed question -> retrieve top_k -> stuff into prompt -> answer."""
    ensure_collection()
    qvec = await embed(req.question)
    result = qdrant.query_points(
        collection_name=COLLECTION, query=qvec, limit=req.top_k
    )
    hits = result.points
    context = "\n\n".join(h.payload["text"] for h in hits)
    prompt = (
        "Answer the question using ONLY the context below. "
        "If the answer isn't in the context, say you don't know.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {req.question}\nAnswer:"
    )
    answer = await generate(prompt)
    return {
        "answer": answer,
        "sources": [{"text": h.payload["text"], "score": h.score} for h in hits],
    }


@app.get("/health")
def health():
    return {"status": "ok"}
