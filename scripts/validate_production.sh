#!/usr/bin/env bash
# Validate env (model + DB + CORS) then optionally print health
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 validate_env.py
curl -fsS "${API_URL:-http://127.0.0.1:8000}/" | python3 -m json.tool || true
