# yaatt Reference

## Required test file fields

Every file in `tests/` must include:

| Field | Type | Required |
|-------|------|----------|
| `name` | string | yes |
| `requests` | object | yes |
| `assertions` | array (min 1) | yes |
| `description` | string | no |

Empty files crash the entire suite with a schema validation error.

## Request types

### GET / DELETE

```yaml
requests:
  my_request:
    method: get
    url: "{{env:CAAS_BASE_URL}}/path"
    headers:
      x-api-key: "{{env:CAAS_API_KEY}}"
```

### POST / PUT / PATCH

`body` is required:

```yaml
requests:
  my_request:
    method: post
    url: "{{env:CAAS_BASE_URL}}/path"
    headers:
      x-api-key: "{{env:CAAS_API_KEY}}"
    body:
      field: value
```

### Delay (between requests)

```yaml
requests:
  wait:
    delay: 2
```

## Environment placeholders

| Placeholder | Maps to |
|-------------|---------|
| `{{env:CAAS_BASE_URL}}` | `.env` → `CAAS_BASE_URL` |
| `{{env:CAAS_API_KEY}}` | `.env` → `CAAS_API_KEY` |

Never hardcode URLs or API keys in test files.

## Assertion types

| Type | Required fields | Use for |
|------|-----------------|---------|
| `status_code` | `property`, `value` | HTTP status (value is number) |
| `is_equals` | `property`, `value` | Exact field match |
| `contains` | `property`, `value` | Substring or array element |
| `is_greater_than` | `property`, `value` | Numeric comparison |
| `is_less_than` | `property`, `value` | Numeric comparison |
| `is_not_empty` | `property` | **Arrays only** — not scalar fields |

### Property paths

Response JSON is cached under the request key. Access fields with dot notation:

```yaml
- property: create_order.status
  type: is_equals
  value: new
```

The request key in `requests` (e.g. `create_order`) becomes the root for assertions.

## Gotchas

1. **`is_not_empty` only works on arrays.** Do not use it for scalar fields like `id` or `patientId`. Use `is_equals` instead.
2. **Never leave empty `.yml` files in `tests/`.** yaatt loads every file in the directory.
3. **Large payloads:** Copy an existing CaaS test and change only the delta (e.g. one field in `patient.verification`).
4. **Apple Silicon:** Scripts pass `--platform linux/amd64` to Docker automatically.
5. **Slow tests:** CreateOrder happy path can take 10–15s. Use `make test-one` when iterating on faster error-path tests.

## Template tests

| File | Scenario |
|------|----------|
| `tests/2025_12_30T16_12_35Z_test.yml` | POST /orders → 201, new order |
| `tests/2025_12_30T16_59_57Z_test.yml` | POST /orders → 200, duplicate order |
| `tests/2025_12_30T16_54_22Z_test.yml` | POST /orders → 422, invalid verification |

## Commands

```bash
make build                              # Pull iamuzorr/yaatt:latest
make test                               # Run all tests
make test-one FILE=<filename>.yml       # Run one test file
./scripts/validate-test.sh <file>.yml   # Validate without calling API
make generate                           # Scaffold empty test (then fill in)
```
