# Mini RAG Stack (Qdrant + Ollama + FastAPI)

A self-hosted Retrieval-Augmented Generation stack, built to run CPU-only on
modest hardware. Vector search with **Qdrant**, local LLM + embeddings with
**Ollama**, and a small **FastAPI** service tying them together.

## Architecture

```
   POST /ingest ──► embed (Ollama) ──► store vectors (Qdrant)
   POST /query  ──► embed question ──► search Qdrant ──► stuff context
                                                    └──► LLM answer (Ollama)
```

## Run it (inside the Ubuntu VM)

1. Install Docker + the compose plugin:
   ```bash
   sudo apt update && sudo apt install -y docker.io docker-compose-v2
   sudo usermod -aG docker $USER && newgrp docker
   ```

2. Bring the stack up:
   ```bash
   docker compose up -d --build
   ```

3. Pull the models **into the Ollama container** (one-time, downloads once):
   ```bash
   docker exec -it ollama ollama pull llama3.2:1b
   docker exec -it ollama ollama pull nomic-embed-text
   ```

4. Check health:
   ```bash
   curl localhost:8000/health
   ```

## Use it

Ingest some documents:
```bash
curl -X POST localhost:8000/ingest \
  -H 'content-type: application/json' \
  -d '{"texts": [
        "Qdrant is an open-source vector database written in Rust.",
        "Ollama runs large language models locally via a simple HTTP API.",
        "Rizwan is doing a two-month DevOps + AWS career push."
      ]}'
```

Ask a question:
```bash
curl -X POST localhost:8000/query \
  -H 'content-type: application/json' \
  -d '{"question": "What language is Qdrant written in?"}'
```

## Notes

- First `/query` after boot is slow — Ollama loads the model into RAM on first
  use. Subsequent calls are faster.
- Qdrant dashboard: `http://localhost:6333/dashboard`
- Data persists in the `qdrant_data` and `ollama_data` Docker volumes.

## Next step

Once this works locally, deploy the identical `docker-compose.yml` to a small
AWS EC2 instance via Terraform — that's the cloud/portfolio version.
