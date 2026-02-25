#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="$ROOT_DIR/site"
TARGET_URL="https://pigsheadbbq.com/"

echo "Mirroring $TARGET_URL into $OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

wget \
  --mirror \
  --convert-links \
  --adjust-extension \
  --page-requisites \
  --no-parent \
  --domains pigsheadbbq.com,www.pigsheadbbq.com \
  --directory-prefix "$OUTPUT_DIR" \
  "$TARGET_URL"

echo "Done. Static mirror available under: $OUTPUT_DIR"
