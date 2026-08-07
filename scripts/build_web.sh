#!/usr/bin/env bash
# Değerinde — Flutter Web release build
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/frontend"

API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8000}"

echo "==> flutter pub get"
flutter pub get

echo "==> flutter analyze (fatal infos off)"
flutter analyze --no-fatal-infos lib/

echo "==> flutter build web --release"
flutter build web --release \
  --dart-define=API_BASE_URL="$API_BASE_URL"

echo "✅ Web build ready: frontend/build/web"
echo "   API_BASE_URL=$API_BASE_URL"
