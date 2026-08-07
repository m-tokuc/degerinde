#!/usr/bin/env bash
# Run backend integration tests
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 -m pip install -q pytest httpx python-dotenv 2>/dev/null || true
python3 -m pytest tests/test_api.py -v --tb=short
