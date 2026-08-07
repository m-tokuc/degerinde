#!/usr/bin/env bash
# Değerinde — Flutter Android APK release build
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/frontend"

API_BASE_URL="${API_BASE_URL:-http://10.0.2.2:8000}"

echo "==> flutter pub get"
flutter pub get

echo "==> flutter analyze (fatal infos off)"
flutter analyze --no-fatal-infos lib/

echo "==> flutter build apk --release"
flutter build apk --release \
  --dart-define=API_BASE_URL="$API_BASE_URL"

echo "✅ APK ready: frontend/build/app/outputs/flutter-apk/app-release.apk"
echo "   API_BASE_URL=$API_BASE_URL"
echo "   Tip: emulator→host API uses 10.0.2.2; device→use LAN IP or production URL."
