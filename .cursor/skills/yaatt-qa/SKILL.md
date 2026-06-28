---
name: yaatt-qa
description: >-
  Generate, validate, and run CaaS API tests using yaatt (iamuzorr/yaatt Docker
  image). Use when the user asks to create, add, run, or debug yaatt tests,
  API test scenarios, or CaaS CreateOrder tests from natural language.
---

# yaatt QA Agent

End-to-end workflow for generating and running yaatt API tests in this repo.

## Prerequisites

Before generating or running tests, verify:

1. Docker is running
2. `.env` exists with `CAAS_BASE_URL` and `CAAS_API_KEY` (copy from `.env.example` if missing)
3. Image pulled: `make build`

If `.env` is missing, stop and tell the user to create it. Never hardcode secrets.

## Workflow

Copy this checklist and track progress:

```
Task Progress:
- [ ] Step 1: Parse intent from natural language
- [ ] Step 2: Choose template test file
- [ ] Step 3: Generate YAML test file
- [ ] Step 4: Validate against schema
- [ ] Step 5: Run test(s)
- [ ] Step 6: Report results
```

### Step 1: Parse intent

From the user's message, extract:

- HTTP method and path (e.g. `POST /orders`)
- Scenario name (behavior-focused)
- Expected status code and response fields to assert
- What differs from an existing scenario (one field vs. new endpoint)

If anything is ambiguous, ask one clarifying question before writing the file.

### Step 2: Choose a template

For CaaS CreateOrder tests, **copy the nearest existing file** and apply a minimal diff. Do not write large payloads from scratch.

| Scenario type | Template file |
|---------------|---------------|
| Happy path (201) | `tests/2025_12_30T16_12_35Z_test.yml` |
| Duplicate order (200) | `tests/2025_12_30T16_59_57Z_test.yml` |
| Validation error (422) | `tests/2025_12_30T16_54_22Z_test.yml` |

See [reference.md](reference.md) for schema details and [examples.md](examples.md) for sample prompts.

### Step 3: Generate the YAML file

Create `tests/<UTC_timestamp>_test.yml` using:

```bash
date -u +"%Y_%m_%dT%H_%M_%SZ"
```

Required structure:

```yaml
name: <behavior-focused scenario name>
description: <one sentence from the user's request>
requests:
  <request_key>:
    description: <what this request does>
    method: post
    url: "{{env:CAAS_BASE_URL}}/orders"
    headers:
      x-api-key: "{{env:CAAS_API_KEY}}"
    body: ...
assertions:
  - property: <request_key>
    type: status_code
    value: <code>
  - property: <request_key>.<field>
    type: is_equals
    value: <expected>
```

Rules:

- Always use `{{env:CAAS_BASE_URL}}` and `{{env:CAAS_API_KEY}}` for URL and auth
- Filename pattern: `YYYY_MM_DDTHH_MM_SSZ_test.yml`
- Never create empty or placeholder files in `tests/`
- Minimum assertions: status code + at least one response field that proves the scenario

### Step 4: Validate

Run validation before hitting the API:

```bash
./scripts/validate-test.sh <filename>.yml
```

If validation fails, fix the YAML and re-validate. Do not run tests until validation passes.

### Step 5: Run tests

| Goal | Command |
|------|---------|
| Run one new/changed test | `make test-one FILE=<filename>.yml` |
| Run full suite | `make test` |

Prefer `make test-one` when iterating on a single scenario. Use `make test` before finishing to confirm nothing else broke.

### Step 6: Report results

**On pass:** Report scenario name, status code, assertion count, duration, and any slow-request warnings.

**On fail:** Quote the failing assertion (yaatt shows expected vs actual). Explain whether the test expectation or the API is likely wrong. Offer to fix the YAML.

## Quick reference

- Schema: [schema.json](../../../schema.json)
- Assertion types and gotchas: [reference.md](reference.md)
- Example QA prompts: [examples.md](examples.md)
