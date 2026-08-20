# Operations runbook

## Start and verify

```bash
docker compose up -d --build
docker compose exec ollama ollama pull llama3.2:3b
docker compose exec ollama ollama pull nomic-embed-text
docker compose ps
curl -fsS http://localhost:8000/ready
```

## Observe

```bash
docker compose logs --tail=200 api
docker compose logs --tail=200 qdrant
docker compose logs --tail=200 ollama
docker stats
```

Never publish raw document payloads or prompts in logs.

## Upgrade

1. Back up persistent data or prove the index is reproducible.
2. Review upstream release notes and update pinned versions deliberately.
3. Rebuild and run unit tests plus the live evaluation.
4. Test document ingestion, supported queries, refusals, and deletion.
5. Roll back to the prior image/version if regression gates fail.

## Backup and restore

Qdrant snapshots are preferable to blindly copying a live volume. Follow the Qdrant snapshot procedure for the pinned version, copy the snapshot to protected storage, and perform a test restore. Ollama models can normally be pulled again; protect custom model definitions separately.

## Incident response

If the API or host was exposed unintentionally:

1. Restrict network access immediately.
2. Rotate the API key and any reverse-proxy credentials.
3. Review proxy, host, and container logs.
4. Assume indexed documents may have been queried or deleted.
5. Restore Qdrant from a known-good snapshot when integrity is uncertain.
