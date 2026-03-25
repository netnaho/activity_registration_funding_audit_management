# Architecture

## High-Level Design

The project is a Dockerized full-stack system with three runtime services:

- `postgres` (data persistence)
- `backend` (FastAPI business APIs)
- `frontend` (Vue SPA)

All runtime dependencies are declared in `docker-compose.yml`.

## Backend Layering

Implemented structure in `backend/app`:

- `api/` - routers, dependencies, response contract
- `core/` - settings, security, exception primitives
- `db/` - SQLAlchemy session and seed bootstrap
- `models/` - SQLAlchemy entities and enums
- `schemas/` - Pydantic request models
- `services/` - business logic (registration, materials, workflow, finance, metrics, reports, backup)
- `storage/` - local storage and hashing utilities
- `jobs/` - scheduler jobs for periodic operations
- `utils/` - masking and helpers

## Frontend Structure

Implemented structure in `frontend/src`:

- `api/` - HTTP client and endpoint wrappers
- `router/` - role-aware route guards
- `stores/` - auth state via Pinia
- `layouts/` - premium app shell
- `views/` - feature pages per module
- `components/` - reusable UI components
- `styles/` - global theme system and UI tokens
- `utils/` - user notifications and helpers

## Core Domain Modules

- Authentication and account lockout
- Applicant registration and checklist materials
- File versioning (max 3) + duplicate detection (SHA-256)
- Reviewer state machine and batch review constraints
- Finance account/transaction management with overspending controls
- Metrics and local alerting
- Report exports (CSV)
- Backup and recovery

## State Machine

Main registration state transitions:

- `draft -> submitted`
- `submitted -> approved | rejected | canceled | supplemented`
- `supplemented -> approved | rejected | canceled | promoted_from_waitlist`
- `rejected -> promoted_from_waitlist`

Invalid transitions are rejected at service layer.

## Security Model

- Argon2 password hashing
- JWT bearer authentication
- RBAC authorization (`applicant`, `reviewer`, `financial_admin`, `system_admin`)
- server-side lockout policy
- audit logging across sensitive operations
- structured operational logging with JSON formatter, request middleware, and request IDs
- log redaction utility for sensitive fields to prevent accidental leakage in future extended logs
- sensitive field masking strategy for protected fields

## Storage and Offline Constraints

- local PostgreSQL only
- local files only (`/app/uploads`, `/app/backups`)
- no cloud storage or external auth
- similarity interface is reserved and disabled by default

## Operations

- startup migration and idempotent seeding at backend startup
- periodic jobs:
  - daily backup
  - periodic metrics recomputation

## Logging and Redaction

- `backend/app/logging/logger.py` configures JSON log output and level handling.
- `backend/app/core/middleware.py` adds request/response operational logs with `x-request-id`.
- `backend/app/logging/redaction.py` redacts sensitive fields before emitting contextual logs.
- `backend/app/services/audit_service.py` applies redaction before audit event logging.
