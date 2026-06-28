#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BASE_IMAGE="${BASE_IMAGE:-iamuzorr/yaatt:latest}"
SLOW_THRESHOLD_SEC="${SLOW_THRESHOLD_SEC:-5}"
FILE="${1:?Usage: run-test-one.sh <filename>.yml}"

if [[ -f "$ROOT_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env"
  set +a
fi

strip_ansi() {
  sed $'s/\x1b\\[[0-9;]*m//g'
}

if [[ ! -f "$ROOT_DIR/tests/$FILE" ]]; then
  echo "Error: tests/$FILE not found" >&2
  exit 1
fi

echo "============================================================"
echo "CaaS API Tests (yaatt) — single file: $FILE"
echo "Target: ${CAAS_BASE_URL:-<CAAS_BASE_URL not set>}"
echo "Started: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "============================================================"
echo

OUTPUT="$(mktemp)"
trap 'rm -f "$OUTPUT"' EXIT

set +e
docker run \
  --platform linux/amd64 \
  --env-file "$ROOT_DIR/.env" \
  -v "$ROOT_DIR/tests:/app/tests" \
  -t "$BASE_IMAGE" \
  bun index.ts "$FILE" \
  2>&1 | tee "$OUTPUT" | strip_ansi
EXIT_CODE="${PIPESTATUS[0]}"
set -e

CLEAN_OUTPUT="$(strip_ansi < "$OUTPUT" | tr -d '\r')"

echo
echo "============================================================"
echo "Slow requests"
echo "============================================================"

SLOW_FOUND=false
while IFS= read -r line; do
  if [[ "$line" =~ 🚀[[:space:]]+([^[:space:]]+)[[:space:]]+([0-9]+)[[:space:]]+([0-9.]+)[[:space:]]+secs ]]; then
    REQUEST="${BASH_REMATCH[1]}"
    STATUS="${BASH_REMATCH[2]}"
    SECS="${BASH_REMATCH[3]}"
    if awk -v seconds="$SECS" -v threshold="$SLOW_THRESHOLD_SEC" 'BEGIN { exit !(seconds > threshold) }'; then
      echo "⚠️  ${REQUEST} → ${STATUS} in ${SECS}s (threshold: ${SLOW_THRESHOLD_SEC}s)"
      SLOW_FOUND=true
    fi
  fi
done <<< "$CLEAN_OUTPUT"

if [[ "$SLOW_FOUND" == false ]]; then
  echo "None (all requests completed within ${SLOW_THRESHOLD_SEC}s)"
fi

exit "$EXIT_CODE"
