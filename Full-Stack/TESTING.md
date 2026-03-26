# Testing Guide

## Test Layout

- `unit_tests/` - unit and rules-focused tests
- `API_tests/` - end-to-end API functional checks
- `run_tests.sh` - root test orchestrator

## What Unit Tests Cover

- auth lockout logic
- registration constraints and constants
- material file validation rules
- workflow valid/invalid transitions
- finance overspending threshold logic
- masking logic
- fingerprint/hash consistency
- metrics math examples
- backup parsing logic

## What API Functional Tests Cover

- login success/failure
- lockout behavior after repeated failures
- registration create and invalid payload rejection
- RBAC 403 case for unauthorized registration creation
- checklist read and material upload valid/invalid extension
- registration submission
- workflow transition valid/invalid
- workflow history retrieval
- batch review <=50 and >50
- finance account creation
- overspending confirmation path (409 then success)
- finance stats endpoint
- report export endpoints
- alerts endpoint
- similarity reserved endpoint behavior

## Run Command

From repository root:

```bash
./run_tests.sh
```

## Execution Behavior

`run_tests.sh`:

- runs unit tests in backend container context
- runs API tests against running services
- prints pass/fail for each group
- prints final summary
- exits non-zero if any group fails

## Preconditions

Before running tests:

```bash
docker compose up
```

The script expects backend API to be reachable at `http://localhost:8000`.
