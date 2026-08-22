#!/usr/bin/env bash
# Build a source tarball you can extract and run with ./install.sh.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-$ROOT/dist}"

PKG="prayer-times-indicator"
VERSION="$(sed -n 's/^__version__ = "\(.*\)"$/\1/p' "$ROOT/prayertimes/__init__.py")"

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
DIR="$STAGE/${PKG}-${VERSION}"
mkdir -p "$DIR"

cp -r "$ROOT/prayertimes" "$ROOT/data" "$DIR/"
cp "$ROOT/run.py" "$ROOT/install.sh" "$ROOT/uninstall.sh" \
   "$ROOT/README.md" "$ROOT/LICENSE" "$DIR/"
find "$DIR" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true

mkdir -p "$OUT"
TAR="$OUT/${PKG}-${VERSION}.tar.gz"
tar -czf "$TAR" -C "$STAGE" "${PKG}-${VERSION}"
cp "$TAR" "$OUT/${PKG}.tar.gz"

echo "$TAR"
