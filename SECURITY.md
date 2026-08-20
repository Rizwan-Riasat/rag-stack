# Security policy

## Supported version

Security fixes are applied to the current `main` branch.

## Deployment warning

The default Compose configuration binds the API to `127.0.0.1`; Qdrant and Ollama are not published on host ports. Do not change those bindings for internet access without TLS, strong authentication, authorization, rate limiting, firewall rules, monitoring, and backups.

The optional `X-API-Key` is a lightweight control for a private single-user installation. It is not multi-user identity or document-level authorization.

## Document safety

Only ingest documents you are authorized to process. Vector payloads contain extracted source text and must be protected like the original documents. Document prompt injection is mitigated, not eliminated.

Never commit `.env`, real API keys, private documents, Qdrant snapshots, model credentials, or unredacted production logs.

## Reporting

Do not open a public issue containing an exploitable vulnerability or sensitive data. Contact the repository owner privately through their GitHub profile.
