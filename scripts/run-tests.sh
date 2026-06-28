#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BASE_IMAGE="${BASE_IMAGE:-iamuzorr/yaatt:latest}"
SLOW_THRESHOLD_SEC="${SLOW_THRESHOLD_SEC:-5}"

if [[ -f "$ROOT_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env"
  set +a
fi

strip_ansi() {
  sed $'s/\x1b\\[[0-9;]*m//g'
}

echo "============================================================"
echo "CaaS API Tests (yaatt)"
echo "Target: ${CAAS_BASE_URL:-<CAAS_BASE_URL not set>}"
echo "Started: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "Slow request threshold: ${SLOW_THRESHOLD_SEC}s"
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
  2>&1 | tee "$OUTPUT" | strip_ansi
EXIT_CODE="${PIPESTATUS[0]}"
set -e

CLEAN_OUTPUT="$(strip_ansi < "$OUTPUT" | tr -d '\r')"

echo
echo "============================================================"
echo "Scenario summary"
echo "============================================================"
printf "%-55s %8s %10s\n" "Scenario" "Status" "Duration"
printf "%-55s %8s %10s\n" "-------" "------" "--------"

CURRENT_SUITE=""
SUITE_DURATION=""
SUITE_FAILED=false

while IFS= read -r line; do
  if [[ "$line" =~ \(([0-9_]+T[0-9_]+Z_test\.yml)\) ]]; then
    CURRENT_SUITE="${line%% (*}"
    CURRENT_SUITE="$(echo "$CURRENT_SUITE" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    SUITE_DURATION=""
    SUITE_FAILED=false
  fi

  if [[ -n "$CURRENT_SUITE" && "$line" =~ 🚀[[:space:]]+([^[:space:]]+)[[:space:]]+[0-9]+[[:space:]]+([0-9.]+)[[:space:]]+secs ]]; then
    SUITE_DURATION="${BASH_REMATCH[2]}s"
  fi

  if [[ -n "$CURRENT_SUITE" && "$line" =~ ❌[[:space:]]+Fail ]]; then
    SUITE_FAILED=true
  fi

  if [[ -n "$CURRENT_SUITE" && -n "$SUITE_DURATION" && "$line" =~ ^-{10,} ]]; then
    if [[ "$SUITE_FAILED" == true ]]; then
      STATUS="FAIL"
    else
      STATUS="PASS"
    fi
    printf "%-55s %8s %10s\n" "$CURRENT_SUITE" "$STATUS" "$SUITE_DURATION"
    CURRENT_SUITE=""
    SUITE_DURATION=""
    SUITE_FAILED=false
  fi
done <<< "$CLEAN_OUTPUT"

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
