#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BASE_IMAGE="${BASE_IMAGE:-iamuzorr/yaatt:latest}"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <test-file.yml> [test-file2.yml ...]" >&2
  exit 1
fi

for file in "$@"; do
  basename="${file##*/}"
  filepath="$ROOT_DIR/tests/$basename"

  if [[ ! -f "$filepath" ]]; then
    echo "Error: file not found: tests/$basename" >&2
    exit 1
  fi

  if [[ ! -s "$filepath" ]]; then
    echo "Error: tests/$basename is empty" >&2
    exit 1
  fi

  echo "Validating tests/$basename ..."

  docker run --rm \
    --platform linux/amd64 \
    -v "$ROOT_DIR/tests:/app/tests" \
    -v "$ROOT_DIR/schema.json:/app/validate-schema.json:ro" \
    --entrypoint bun \
    "$BASE_IMAGE" \
    -e "
import yaml from 'js-yaml';
import fs from 'fs';
import { Ajv } from 'ajv';

const file = process.argv[1];
const content = yaml.load(fs.readFileSync('/app/tests/' + file, 'utf8'));
const schema = JSON.parse(fs.readFileSync('/app/validate-schema.json', 'utf8'));

if (!content || typeof content !== 'object') {
  console.error('Error: invalid or empty YAML');
  process.exit(1);
}

const ajv = new Ajv();
const validate = ajv.compile(schema);
const valid = validate(content);

if (!valid) {
  console.error('Schema validation failed:');
  for (const err of validate.errors ?? []) {
    console.error('  -', err.instancePath || '(root)', err.message);
  }
  process.exit(1);
}

console.log('OK: tests/' + file);
" \
    "$basename"

done
