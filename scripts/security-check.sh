#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
status=0

if git ls-files | grep -Eiq '\.(pdf|env|pem|key|p12|pfx|sqlite|db|snapshot|log)$'; then
  echo "FAIL: potentially sensitive document, secret, database, or log is tracked"
  git ls-files | grep -Ei '\.(pdf|env|pem|key|p12|pfx|sqlite|db|snapshot|log)$'
  status=1
fi

patterns='(AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|-----BEGIN ([A-Z ]+ )?PRIVATE KEY-----|github_pat_[A-Za-z0-9_]+|ghp_[A-Za-z0-9]{20,}|RAG_API_KEY=[A-Za-z0-9+/=_-]{16,})'
files="$(git ls-files | grep -Ev '^scripts/security-check\.sh$' || true)"
if [[ -n "$files" ]] && grep -EnI "$patterns" $files; then
  echo "FAIL: possible credential material detected"
  status=1
fi

if [[ "$status" -eq 0 ]]; then
  echo "PASS: no known high-risk tracked artifacts or credential patterns found"
fi
exit "$status"
