#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="$ROOT_DIR/site"
TARGET_URL="${1:-https://pigsheadbbq.com/}"

run_wget() {
  local url="$1"
  shift

  wget \
    --mirror \
    --convert-links \
    --adjust-extension \
    --page-requisites \
    --no-parent \
    --domains pigsheadbbq.com,www.pigsheadbbq.com \
    --directory-prefix "$OUTPUT_DIR" \
    "$@" \
    "$url"
}

echo "Mirroring $TARGET_URL into $OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

if run_wget "$TARGET_URL"; then
  echo "Done. Static mirror available under: $OUTPUT_DIR"
  exit 0
fi

echo

echo "Initial mirror attempt failed. Retrying without proxy environment variables..."

if (
  unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
  run_wget "$TARGET_URL" --no-proxy
); then
  echo "Done. Static mirror available under: $OUTPUT_DIR"
  exit 0
fi

echo

echo "Mirror failed after both proxy and direct attempts."
echo "If this environment blocks pigsheadbbq.com, run this script from a machine with outbound access and commit the generated site/ directory."
exit 1
