#!/usr/bin/env python3
"""Run a small, transparent smoke evaluation against a live stack."""

import argparse
import json
import os
import urllib.request
from pathlib import Path


def post_json(url: str, payload: dict, api_key: str | None) -> dict:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
    request = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
    with urllib.request.urlopen(request, timeout=600) as response:
        return json.loads(response.read())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://localhost:8000")
    args = parser.parse_args()
    api_key = os.getenv("RAG_API_KEY")
    cases = json.loads((Path(__file__).parent / "questions.json").read_text())
    passed = 0
    for case in cases:
        payload = {"question": case["question"]}
        if "score_threshold" in case:
            payload["score_threshold"] = case["score_threshold"]
        result = post_json(f"{args.api}/query", payload, api_key)
        answer = result["answer"].lower()
        ok = all(term.lower() in answer for term in case["expected_terms"])
        ok = ok and bool(result["grounded"]) == case["should_be_grounded"]
        passed += int(ok)
        print(f"{'PASS' if ok else 'FAIL'}: {case['question']} -> {result['answer']}")
    print(f"\n{passed}/{len(cases)} evaluation cases passed")
    raise SystemExit(0 if passed == len(cases) else 1)


if __name__ == "__main__":
    main()
