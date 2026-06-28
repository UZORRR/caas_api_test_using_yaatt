# CaaS API Test Agent

This repo contains API tests for CaaS, run via [yaatt](https://hub.docker.com/r/iamuzorr/yaatt) in Docker.

## One-time setup

1. Install Docker
2. Copy `.env.example` to `.env` and fill in `CAAS_BASE_URL` and `CAAS_API_KEY`
3. Pull the test image: `make build`

## Using the QA agent

Open Cursor Agent chat in this repo and describe what you want to test in plain English. The agent uses the **yaatt-qa** skill (`.cursor/skills/yaatt-qa/`) to generate YAML tests, validate them, run them, and report results.

### Example prompts

```
Create a yaatt test: POST /orders should return 422 when patient verification is not-verified. Run it and tell me if it passes.
```

```
Add a test that checks a duplicate order returns 200 with the same patientId.
```

```
Run all tests and summarize the results.
```

```
The invalid verification test is failing — run it and fix the assertions.
```

More examples: [.cursor/skills/yaatt-qa/examples.md](.cursor/skills/yaatt-qa/examples.md)

## Manual commands

| Command | Purpose |
|---------|---------|
| `make test` | Run all tests in `tests/` |
| `make test-one FILE=<file>.yml` | Run a single test file |
| `./scripts/validate-test.sh <file>.yml` | Validate YAML against schema (no API call) |
| `make generate` | Scaffold a new empty test file |

## Test file location

Tests live in `tests/*.yml`. Each file is one scenario with `name`, `requests`, and `assertions`. See [schema.json](schema.json) for the full spec.

## Existing scenarios

| File | Scenario |
|------|----------|
| `2025_12_30T16_12_35Z_test.yml` | POST /orders → 201, new order |
| `2025_12_30T16_59_57Z_test.yml` | POST /orders → 200, duplicate order |
| `2025_12_30T16_54_22Z_test.yml` | POST /orders → 422, invalid verification |
