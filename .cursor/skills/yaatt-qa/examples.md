# Example QA Prompts

## Create and run a validation-error test

**Prompt:**

> Create a yaatt test: POST /orders should return 422 when patient verification is `not-verified`. Run it and tell me if it passes.

**Expected agent behavior:**

1. Copy `tests/2025_12_30T16_54_22Z_test.yml` (or the 201 template with `verification: not-verified`)
2. Set `name` to something like `POST /orders returns 422 when verification is not-verified`
3. Assert status 422, `code: 422`, `message: PatientVerificationException`
4. Run `make test-one FILE=<new_file>.yml`
5. Report pass/fail with assertion details

---

## Create a happy-path test

**Prompt:**

> Add a test that creates a new order for a verified patient and checks the response status is 201 and status field is "new".

**Expected agent behavior:**

1. Copy `tests/2025_12_30T16_12_35Z_test.yml`
2. Adjust patient id or other unique fields if needed to avoid duplicate-order 200
3. Assert status 201, `status: new`, `patientId` matches request
4. Run with `make test-one`, then optionally `make test`

---

## Debug a failing test

**Prompt:**

> The invalid verification test is failing — run it and fix the assertions.

**Expected agent behavior:**

1. Run `make test-one FILE=2025_12_30T16_54_22Z_test.yml`
2. Read expected vs actual from yaatt output
3. Update assertions or request payload
4. Re-validate with `./scripts/validate-test.sh`
5. Re-run until pass

---

## Run the full suite

**Prompt:**

> Run all CaaS API tests and summarize the results.

**Expected agent behavior:**

1. Confirm `.env` exists
2. Run `make test`
3. Summarize: pass/fail count, per-scenario status, slow requests, total duration

---

## What not to do

- Do not create `tests/example.yml` as an empty placeholder
- Do not use `is_not_empty` on `create_order.id` (arrays only)
- Do not hardcode `CAAS_API_KEY` in YAML files
