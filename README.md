# Activity Registration and Funding Audit Management Platform

Production-oriented, offline-deployable platform for applicant registration, checklist material submission with version control, reviewer workflow auditing, finance management, local alerts/metrics, exports, and backup/recovery.

## Project Overview

This system provides a closed-loop internal management workflow for four roles:

- `applicant`
- `reviewer`
- `financial_admin`
- `system_admin`

It is designed for local/offline deployment using Docker Compose only, with local PostgreSQL and local filesystem storage.

## Start Command (How to Run)

```bash
docker compose up
```

That command is sufficient for first run:

- database starts
- backend waits for database readiness
- Alembic migrations run automatically
- seed data is initialized idempotently
- frontend starts

No manual `.env` creation is required.

## Service Address (Services List)

- Frontend UI: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- FastAPI docs: `http://localhost:8000/docs`
- Health endpoint: `http://localhost:8000/api/health`
- PostgreSQL host mapping (for diagnostics): `localhost:55432`

## Default Seed Accounts

- `admin` / `Admin@123456` (`system_admin`)
- `applicant` / `Applicant@123456` (`applicant`)
- `reviewer` / `Reviewer@123456` (`reviewer`)
- `finance` / `Finance@123456` (`financial_admin`)

## Verification Method

1. Start services:

   ```bash
   docker compose up
   ```

2. Confirm services:

   ```bash
   docker compose ps
   ```

3. Confirm backend health:

   ```bash
   curl http://localhost:8000/api/health
   ```

4. Confirm login:

   ```bash
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"Admin@123456"}'
   ```

5. Confirm UI works:
   - open `http://localhost:5173/login`
   - sign in with a seeded user
   - verify role-based navigation and pages load

## Core Business Workflow Verification Examples

### Applicant flow

- Go to Applicant Wizard
- Create registration (future deadline required)
- Upload checklist materials (PDF/JPG/PNG)
- Confirm duplicate warning appears for identical files
- Submit registration

### Reviewer flow

- Go to Reviewer Queue
- Filter/search queue
- Apply valid transition
- Open timeline drawer and confirm workflow history
- Attempt batch >50 and confirm rejection

### Finance flow

- Create funding account
- Create expense that exceeds budget by >10%
- Confirm first attempt returns warning/confirmation required
- Confirm second attempt with confirmation succeeds
- View finance stats by category/day

### Admin flow

- Recompute metrics and view alerts
- Export reconciliation/audit/compliance/whitelist CSVs
- Create backup and trigger recovery action

## Test Execution

Run all tests from repository root:

```bash
./run_tests.sh
```

This runs:

- unit tests (`unit_tests/`)
- API functional tests (`API_tests/`)

It prints group-level pass/fail and exits non-zero on failure.

## Project Directory Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── jobs/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── storage/
│   │   └── utils/
│   ├── alembic/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── layouts/
│   │   ├── router/
│   │   ├── stores/
│   │   ├── styles/
│   │   └── views/
│   └── Dockerfile
├── unit_tests/
├── API_tests/
├── docker-compose.yml
├── run_tests.sh
├── ARCHITECTURE.md
├── TESTING.md
└── SELF_TEST_REPORT.md
```

## Security and Offline Deployment Notes

- username/password authentication only
- password hashing with Argon2 (`pwdlib[argon2]`)
- JWT-based auth for SPA/API
- lockout policy: 10 failed attempts in 5 minutes -> 30-minute lock
- role-based authorization and route controls
- sensitive field masking foundation for non-authorized roles
- audit logging for sensitive actions
- structured operational JSON logs with request IDs and redaction middleware
- sensitive field redaction strategy for log contexts (`password`, `token`, `id_number`, `contact_phone`, etc.)
- log taxonomy is explicit via `category` and `channel` fields:
  - `category=operational` for request/runtime events
  - `category=security` for auth/lockout events
  - `category=business` for workflow/finance/audit domain events
  - `channel` mirrors level (`INFO`, `WARNING`, `ERROR`)
- no cloud runtime dependency
- local PostgreSQL and local filesystem storage only

## Backup/Recovery Verification Notes

- Create backup endpoint: `POST /api/backups/create`
- List backups endpoint: `GET /api/backups`
- Recover backup endpoint: `POST /api/backups/{id}/recover`

Backup includes DB SQL dump + uploaded files archive. Recovery restores both from local artifact.

## Export Feature Verification Notes

Endpoints:

- `POST /api/reports/reconciliation`
- `POST /api/reports/audit`
- `POST /api/reports/compliance`
- `POST /api/reports/whitelist`

Generated files are stored locally under reports backup directory.

## Data Persistence

Docker volumes:

- `postgres_data`
- `uploads_data`
- `backups_data`

## Troubleshooting

- If stale state causes unexpected behavior:

  ```bash
  docker compose down -v
  docker compose up --build
  ```

- If browser login fails, verify CORS-enabled backend and use `http://localhost:5173`.

## Known Limitations

- Backup recovery currently restores by applying SQL dump and file archive directly; it is operational for local acceptance but not yet a full transactional rollback orchestrator with dry-run mode.
- Similarity service is intentionally reserved/disabled by default and performs no external calls.
