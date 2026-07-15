# Self-Hosted RAG Stack (Qdrant + Ollama + FastAPI)

A **Retrieval-Augmented Generation** pipeline that runs entirely on your own
machine — no OpenAI, no API keys, no data leaving the box. It ingests your
documents and answers questions about them in plain language, grounded in the
actual text it retrieves. Built to run **CPU-only** on modest hardware.

- **Qdrant** — vector database (stores text as searchable "meaning" vectors)
- **Ollama** — runs the local models: embeddings + the LLM
- **FastAPI** — the service that orchestrates the two into a RAG loop
- **Docker Compose** — one command brings the whole thing up

## What is RAG, and why?

An LLM only knows what it was trained on — it has never seen *your* documents.
Ask it about your private notes and it will make something up. RAG fixes this by
**retrieving the relevant part of your document first, then asking the LLM to
answer using only that.** The answer stays grounded in your real content.

## How it works

```
INGEST (load your docs)
  text ──► Ollama embeds it into a 768-number vector ──► stored in Qdrant

QUERY (ask a question)
  question ──► Ollama embeds it ──► Qdrant finds the closest stored chunks
           ──► FastAPI stuffs those chunks into a prompt
           ──► Ollama's LLM writes an answer from that context ──► you
```

An **embedding** is a list of numbers that captures the *meaning* of text.
Similar meanings get similar numbers, so Qdrant can find "which stored chunk is
closest to this question" — semantic search, not keyword matching. Each result
comes back with a **score** (higher = more relevant); low scores are a signal
the answer probably isn't in your documents.

## Run it

Inside an Ubuntu box (a local VM is perfect):

```bash
# 1. Install Docker + Compose v2
sudo apt update && sudo apt install -y docker.io docker-compose-v2 git
sudo usermod -aG docker $USER && newgrp docker

# 2. Clone + start the stack (builds the API, pulls Qdrant + Ollama images)
git clone https://github.com/Rizwan-Riasat/rag-stack.git
cd rag-stack
docker compose up -d --build

# 3. Pull the models into the running Ollama container (one-time download)
docker compose exec ollama ollama pull llama3.2:3b
docker compose exec ollama ollama pull nomic-embed-text

# 4. Health check
curl localhost:8000/health          # -> {"status":"ok"}
```

> **Tip:** on a flaky connection the big Ollama image pull can reset. This
> auto-retries until it succeeds: `until docker pull ollama/ollama:latest; do sleep 5; done`

## Use it

**Ingest a whole file** (chunks it and loads every piece):

```bash
python3 ingest_file.py server-setup.md
```

**Or ingest raw text directly:**

```bash
curl -X POST localhost:8000/ingest -H 'content-type: application/json' \
  -d '{"texts": ["Qdrant is an open-source vector database written in Rust."]}'
```

**Ask a question:**

```bash
curl -X POST localhost:8000/query -H 'content-type: application/json' \
  -d '{"question": "What language is Qdrant written in?"}'
```

Response includes the `answer` and the `sources` it retrieved (with scores).

## Configuration

Copy `.env.example` to `.env` to change models:

```bash
cp .env.example .env      # then edit LLM_MODEL / EMBED_MODEL
docker compose up -d api  # recreate the API to pick up changes
```

Default LLM is `llama3.2:3b` (good answers, ~2GB RAM). See `.env.example` for
smaller/faster options.

## Endpoints

| Method | Path      | Purpose                                  |
|--------|-----------|------------------------------------------|
| POST   | `/ingest` | Embed and store a list of texts          |
| POST   | `/query`  | Retrieve relevant chunks + LLM answer    |
| GET    | `/health` | Liveness check                           |

## Notes

- First `/query` after boot is slow — Ollama loads the model into RAM on first
  use, then stays warm.
- Qdrant dashboard: `http://localhost:6333/dashboard`
- Data persists in the `qdrant_data` and `ollama_data` Docker volumes.

## Roadmap

- [ ] Deploy the identical stack to AWS EC2 via **Terraform** (the cloud/IaC version)
- [ ] Auto-pull models on first boot (init step) so setup is a single command
- [ ] Manual rebuild without Docker (systemd units + nginx) as a second learning pass
