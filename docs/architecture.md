# Architecture and trust boundaries

## Query sequence

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant API as FastAPI
    participant Ollama
    participant Qdrant

    User->>API: POST /query + bounded question
    API->>API: Validate input and API key
    API->>Ollama: Batch embed question
    Ollama-->>API: 768-dimensional vector
    API->>Qdrant: Cosine search + top-k + threshold
    Qdrant-->>API: Chunks, metadata, scores
    alt No relevant chunks
        API-->>User: Refusal, grounded=false
    else Relevant chunks
        API->>API: Delimit excerpts and source labels
        API->>Ollama: Grounded prompt, temperature=0
        Ollama-->>API: Answer with source labels
        API-->>User: Answer + structured sources
    end
```

## Ingestion sequence

```mermaid
sequenceDiagram
    autonumber
    actor Operator
    participant Tool as ingest_file.py
    participant API as FastAPI
    participant Ollama
    participant Qdrant

    Operator->>Tool: Select authorized PDF/text/Markdown
    Tool->>Tool: Extract pages and create overlap chunks
    Tool->>Tool: Add content-derived document ID + metadata
    Tool->>API: Bounded chunk batches
    API->>Ollama: Batch embedding request
    Ollama-->>API: Embedding vectors
    API->>Qdrant: Deterministic upsert, wait=true
    Qdrant-->>API: Acknowledged
    API-->>Tool: Ingested count
```

## Trust boundaries

| Boundary | Assumption | Control |
|---|---|---|
| Document → ingestion tool | Content may be malformed or hostile | Type checks, encrypted/empty PDF detection, bounded chunks |
| Client → API | Host clients are not automatically trusted | Localhost binding; optional API key; strict request limits |
| API → model | Retrieved text may contain instructions | Explicit data delimiters and grounding rules |
| API → Qdrant/Ollama | Backing services should not be public | Internal Compose network only |
| Host → internet | External access requires more controls | TLS/authenticated reverse proxy and firewall required |

## Persistence

Qdrant vectors/payloads and Ollama models use named Docker volumes. Removing containers does not delete them; `docker compose down -v` does. Back up `qdrant_data` before destructive maintenance when the index cannot be recreated cheaply.
