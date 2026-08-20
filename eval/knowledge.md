# RAG Stack Facts

The stack uses Qdrant as its vector database. Ollama runs both the embedding model and the local language model. FastAPI orchestrates ingestion, retrieval, and answer generation.

The API binds to localhost by default. Qdrant and Ollama are reachable only on the internal Docker network. PDF chunks retain the source filename and page number so answers can return citations.
