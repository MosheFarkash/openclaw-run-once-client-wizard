#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
NAME="ai-ad-agency-pack"
OUT_DIR="$ROOT/dist"
TMP_DIR="$ROOT/tmp/release"

rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR/packs/$NAME" "$OUT_DIR"

rsync -a \
  --exclude '.git' \
  --exclude 'dist' \
  --exclude 'tmp' \
  "$ROOT/" "$TMP_DIR/packs/$NAME/"

tar -czf "$OUT_DIR/$NAME-$VERSION.tgz" -C "$TMP_DIR" "packs/$NAME"

echo "$OUT_DIR/$NAME-$VERSION.tgz"
