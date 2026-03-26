# API Specification

## Activity Registration and Funding Audit Management Platform

**Base URL:** `http://localhost:8000`  
**Authentication:** Bearer JWT token in `Authorization` header  
**Content-Type:** `application/json` (unless stated otherwise)

---

## Response Envelope

All endpoints return a consistent envelope:

```json
{
  "code": 200,
  "msg": "Description of result",
  "data": { ... }
}
```

Error responses use the same format with appropriate HTTP status codes.

| Code | Meaning |
|---|---|
| 200 | Success |
| 400 | Validation error / business rule violation |
| 401 | Not authenticated or invalid credentials |
| 403 | Insufficient permissions |
| 404 | Resource not found |
| 409 | Conflict (e.g., overspend requires confirmation) |
| 422 | Request body validation failure |
| 500 | Internal server error |

---

## 1. Health

### `GET /api/health`

Service healthcheck. No authentication required.

**Response:**
```json
{
  "code": 200,
  "msg": "Service is healthy",
  "data": { "status": "healthy" }
}
```

---

## 2. Authentication

### `POST /api/auth/login`

Authenticate a user and receive a JWT token.

**Request Body:**
```json
{
  "username": "string (3-64 chars)",
  "password": "string (8-256 chars)"
}
```

**Success Response (200):**
```json
{
  "code": 200,
  "msg": "Login successful",
  "data": {
    "access_token": "eyJ...",
    "token_type": "bearer"
  }
}
```

**Error Responses:**
- `401` — Invalid credentials or account locked
  - `"msg": "Account is locked until ..."` — when account is locked after ≥10 failed attempts

**Lockout Policy:**
- ≥10 failed attempts within 5 minutes → account locked for 30 minutes.
- Each attempt is recorded in `login_attempt_logs` with IP address and user agent.

---

### `GET /api/auth/me`

Get the authenticated user's profile.

**Headers:** `Authorization: Bearer <token>`  
**Roles:** Any authenticated user

**Response (200):**
```json
{
  "code": 200,
  "msg": "User profile",
  "data": {
    "id": 1,
    "username": "admin",
    "full_name": "System Admin",
    "role": "system_admin"
  }
}
```

---

## 3. Registrations

### `GET /api/registrations`

List registrations. Applicants see only their own; reviewers/admins see all.

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `applicant`, `reviewer`, `system_admin`

**Query Parameters:**
| Parameter | Type | Default | Description |
|---|---|---|---|
| skip | int | 0 | Pagination offset |
| limit | int | 20 | Page size |

**Response (200):**
```json
{
  "code": 200,
  "msg": "Registrations",
  "data": {
    "items": [
      {
        "id": 1,
        "title": "Activity Registration 2026",
        "description": "...",
        "contact_phone": "123*****90",
        "id_number": "AB****12",
        "status": "draft",
        "is_locked": false,
        "submitted_at": null,
        "deadline_at": "2030-12-31T10:00:00Z",
        "created_at": "2026-01-01T00:00:00Z"
      }
    ]
  }
}
```

> **Note:** `contact_phone` and `id_number` are masked for non-owner/non-admin viewers.

---

### `POST /api/registrations`

Create a new registration (draft status).

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `applicant`, `system_admin`

**Request Body:**
```json
{
  "title": "string (3-200 chars)",
  "description": "string (10-4000 chars)",
  "contact_phone": "string (6-32 chars)",
  "id_number": "string (4-32 chars)",
  "deadline_at": "2030-12-31T10:00:00Z"
}
```

**Response (200):**
```json
{
  "code": 200,
  "msg": "Registration created",
  "data": {
    "id": 5,
    "title": "Activity Registration 2026",
    "status": "draft",
    "...": "..."
  }
}
```

**Validation:**
- `deadline_at` must be in the future.
- All fields are required.

---

### `POST /api/registrations/submit`

Submit a registration. Changes status from `draft` → `submitted`.

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `applicant`, `system_admin`

**Request Body:**
```json
{
  "registration_id": 5
}
```

**Response (200):**
```json
{
  "code": 200,
  "msg": "Registration submitted",
  "data": { "id": 5, "status": "submitted" }
}
```

**Validation:**
- Registration must be in `draft` status.
- All **mandatory** checklist items must have at least one uploaded material version.
- Caller must be the registration owner.
- Registration must not be locked (past deadline).

**Error:** `400` — "Checklist mandatory materials are incomplete"

---

### `POST /api/registrations/supplementary`

Open a one-time supplementary submission window (72 hours).

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `applicant`, `reviewer`, `system_admin`

**Request Body:**
```json
{
  "registration_id": 5,
  "reason": "string (5-500 chars)"
}
```

**Response (200):**
```json
{
  "code": 200,
  "msg": "Supplementary window opened",
  "data": {
    "id": 1,
    "expires_at": "2026-04-01T12:00:00Z",
    "reason": "..."
  }
}
```

**Business Rules:**
- Registration must be in `rejected` or `supplemented` status.
- Only one supplementary window per registration (one-time).
- Must be within 72 hours of the last reviewer action.
- Opens lock (`is_locked = false`).

---

## 4. Checklists

### `GET /api/checklists`

List active material checklists with their items.

**Headers:** `Authorization: Bearer <token>`  
**Roles:** All authenticated

**Response (200):**
```json
{
  "code": 200,
  "msg": "Checklist list",
  "data": {
    "items": [
      {
        "id": 1,
        "name": "Default Checklist",
        "description": "Standard document checklist",
        "items": [
          {
            "id": 1,
            "item_code": "ID_DOC",
            "item_name": "Identity Document",
            "required": true,
            "max_size_mb": 20
          }
        ]
      }
    ]
  }
}
```

---

## 5. Materials

### `POST /api/materials/upload`

Upload a material file for a registration checklist item.

**Headers:** `Authorization: Bearer <token>`  
**Content-Type:** `multipart/form-data`  
**Roles:** `applicant`, `system_admin`

**Form Fields:**
| Field | Type | Required | Description |
|---|---|---|---|
| registration_id | int | Yes | Target registration |
| checklist_item_id | int | Yes | Target checklist item |
| file | File | Yes | The material file |

**Response (200):**
```json
{
  "code": 200,
  "msg": "Material uploaded",
  "data": {
    "material_version_id": 12,
    "version_number": 1,
    "status": "pending_submission",
    "original_filename": "id_doc.pdf",
    "sha256_hash": "a1b2c3...",
    "file_size_bytes": 102400,
    "duplicate_detected": false
  }
}
```

**Validation:**
- **File types:** `.pdf`, `.jpg`, `.jpeg`, `.png` only.
- **Single file size:** ≤ 20MB.
- **Total per registration:** ≤ 200MB (cumulative across all materials).
- **Max versions:** 3 per checklist item per registration.
- **SHA-256:** Computed on upload; `duplicate_detected` is `true` if the same hash exists.
- Registration must not be locked.
- Caller must be the registration owner.

**Errors:**
- `400` — Invalid file type, file too large, max versions exceeded, or registration locked.
- `403` — Not the registration owner.

---

### `GET /api/materials/{registration_id}`

List all materials for a registration, grouped by checklist item with version history.

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `applicant`, `reviewer`, `system_admin`

**Response (200):**
```json
{
  "code": 200,
  "msg": "Materials",
  "data": {
    "items": [
      {
        "checklist_item_id": 1,
        "item_code": "ID_DOC",
        "item_name": "Identity Document",
        "versions": [
          {
            "material_version_id": 12,
            "version_number": 1,
            "status": "submitted",
            "original_filename": "id_doc.pdf",
            "file_size_bytes": 102400,
            "uploaded_at": "2026-01-15T10:00:00Z"
          }
        ]
      }
    ]
  }
}
```

---

### `PATCH /api/materials/status`

Update a material version's status.

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `reviewer`, `system_admin`

**Request Body:**
```json
{
  "material_version_id": 12,
  "status": "needs_correction"
}
```

**Valid Status Transitions:**
- `pending_submission` → `submitted`
- `submitted` → `needs_correction`
- `needs_correction` → `pending_submission`

**Error:** `400` — Invalid transition.

---

## 6. Workflows

### `GET /api/workflows/queue`

Get the reviewer queue of registrations pending review.

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `reviewer`, `system_admin`

**Query Parameters:**
| Parameter | Type | Default | Description |
|---|---|---|---|
| status_filter | string | null | Filter by status (e.g., `submitted`) |
| search | string | null | Search by title |
| skip | int | 0 | Pagination offset |
| limit | int | 20 | Page size |

**Response (200):**
```json
{
  "code": 200,
  "msg": "Reviewer queue",
  "data": {
    "items": [
      {
        "id": 5,
        "title": "Activity Registration 2026",
        "status": "submitted",
        "applicant_name": "John Doe",
        "submitted_at": "2026-01-15T10:00:00Z"
      }
    ],
    "total": 42
  }
}
```

---

### `POST /api/workflows/transition`

Perform a single registration state transition.

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `reviewer`, `system_admin`

**Request Body:**
```json
{
  "registration_id": 5,
  "target_status": "approved",
  "comment": "string (2-1000 chars)"
}
```

**Valid `target_status` values:** `submitted`, `supplemented`, `approved`, `rejected`, `canceled`, `promoted_from_waitlist`

**Allowed Transitions:**

| From | To |
|---|---|
| `draft` | `submitted` |
| `submitted` | `approved`, `rejected`, `canceled`, `supplemented` |
| `supplemented` | `approved`, `rejected`, `canceled`, `promoted_from_waitlist` |
| `rejected` | `promoted_from_waitlist` |

**Side Effects:**
- Transition to `supplemented` → unlocks registration, marks latest material versions as `needs_correction`.
- Each transition creates a `ReviewWorkflowRecord` entry.
- Audit log entry created.

**Errors:**
- `400` — Invalid transition.
- `400` — Comment required for `rejected`, `supplemented`, `canceled`.

---

### `POST /api/workflows/batch-transition`

Perform batch state transitions on multiple registrations (max 50).

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `reviewer`, `system_admin`

**Request Body:**
```json
{
  "registration_ids": [5, 6, 7],
  "target_status": "approved",
  "comment": "Batch approval (2-1000 chars)"
}
```

**Constraints:**
- `registration_ids` must contain 1–50 IDs.
- Same transition rules and side effects as single transition.
- Each transition gets its own `ReviewWorkflowRecord` sharing the same `batch_ref`.

**Response (200):**
```json
{
  "code": 200,
  "msg": "Batch transition completed",
  "data": {
    "transitioned": 3,
    "batch_ref": "batch_20260115_abc123"
  }
}
```

**Errors:**
- `400` — More than 50 registration IDs.

---

### `GET /api/workflows/{registration_id}/history`

Get the workflow transition history (timeline) for a registration.

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `applicant` (own registrations only), `reviewer`, `system_admin`

**Response (200):**
```json
{
  "code": 200,
  "msg": "Workflow history",
  "data": {
    "items": [
      {
        "id": 1,
        "from_status": "submitted",
        "to_status": "approved",
        "comment": "Approved by reviewer",
        "reviewer_id": 2,
        "batch_ref": null,
        "created_at": "2026-01-16T14:00:00Z"
      }
    ]
  }
}
```

---

## 7. Finance

### `GET /api/finance/accounts`

List all funding accounts.

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `financial_admin`, `system_admin`

**Response (200):**
```json
{
  "code": 200,
  "msg": "Funding accounts",
  "data": {
    "items": [
      {
        "id": 1,
        "account_name": "Operations Budget 2026",
        "category": "ops",
        "period": "2026Q1",
        "budget_amount": 50000.00,
        "created_at": "2026-01-01T00:00:00Z"
      }
    ]
  }
}
```

---

### `POST /api/finance/accounts`

Create a new funding account.

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `financial_admin`, `system_admin`

**Request Body:**
```json
{
  "account_name": "string (2-150 chars, unique)",
  "category": "string (2-64 chars)",
  "period": "string (2-32 chars)",
  "budget_amount": 50000.00
}
```

**Validation:** `budget_amount` must be > 0.

---

### `POST /api/finance/transactions`

Record a financial transaction. Supports `multipart/form-data` for invoice attachment.

**Headers:** `Authorization: Bearer <token>`  
**Content-Type:** `application/x-www-form-urlencoded` or `multipart/form-data`  
**Roles:** `financial_admin`, `system_admin`

**Form Fields:**
| Field | Type | Required | Description |
|---|---|---|---|
| funding_account_id | int | Yes | Target account |
| transaction_type | string | Yes | `income` or `expense` |
| amount | float | Yes | Must be > 0 |
| transaction_time | datetime | Yes | ISO 8601 format |
| category | string | Yes | Expense category (2-64 chars) |
| note | string | No | Free-text note (max 500 chars) |
| overspend_confirmed | bool | No | Default `false`; set `true` to confirm overspend |
| invoice_file | File | No | Invoice attachment |

**Overspend Flow:**
1. If cumulative expenses + amount > budget × 1.10 and `overspend_confirmed = false`:
   - Returns `409` with warning message.
2. Frontend shows confirmation dialog, retries with `overspend_confirmed = true`:
   - Returns `200`, creates an alert record.

**Response (200):**
```json
{
  "code": 200,
  "msg": "Transaction recorded",
  "data": {
    "id": 10,
    "amount": 120.00,
    "transaction_type": "expense",
    "overspend_warning": true,
    "invoice_stored": true
  }
}
```

**Error:** `409` — "Overspend would exceed 10% threshold. Set overspend_confirmed=true to proceed."

---

### `GET /api/finance/stats`

Get financial statistics aggregated by category and by day.

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `financial_admin`, `system_admin`

**Response (200):**
```json
{
  "code": 200,
  "msg": "Finance statistics",
  "data": {
    "by_category": [
      { "category": "ops", "total": 15000.00 }
    ],
    "by_day": [
      { "day": "2026-01-15", "total": 5000.00 }
    ]
  }
}
```

---

## 8. Metrics

### `POST /api/metrics/recompute`

Trigger recomputation of quality metrics and threshold-based alerts.

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `reviewer`, `system_admin`

**Response (200):**
```json
{
  "code": 200,
  "msg": "Metrics recomputed",
  "data": {
    "approval_rate": 0.72,
    "correction_rate": 0.18,
    "overspending_rate": 0.05,
    "alerts_generated": 0
  }
}
```

**Alert Thresholds (configurable):**
- `approval_rate < 0.4` → WARNING alert
- `correction_rate > 0.5` → WARNING alert
- `overspending_rate > 0.2` → CRITICAL alert

---

## 9. Alerts

### `GET /api/alerts`

List system alerts (most recent 200).

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `system_admin`, `financial_admin`, `reviewer`

**Response (200):**
```json
{
  "code": 200,
  "msg": "Alerts",
  "data": {
    "items": [
      {
        "id": 1,
        "alert_type": "overspend_threshold",
        "severity": "warning",
        "message": "Account 'Ops Budget' overspend confirmed at 120%",
        "is_resolved": false,
        "created_at": "2026-01-15T14:00:00Z"
      }
    ]
  }
}
```

---

### `POST /api/alerts/{alert_id}/resolve`

Mark an alert as resolved.

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `system_admin`

**Response (200):**
```json
{
  "code": 200,
  "msg": "Alert resolved",
  "data": { "id": 1, "is_resolved": true }
}
```

---

## 10. Reports

### `POST /api/reports/reconciliation`

Generate a reconciliation report (CSV).

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `financial_admin`, `system_admin`

**Response (200):**
```json
{
  "code": 200,
  "msg": "Reconciliation report generated",
  "data": { "file_path": "/app/backups/reports/reconciliation_20260115.csv" }
}
```

---

### `POST /api/reports/audit`

Generate an audit trail report (CSV).

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `reviewer`, `system_admin`

---

### `POST /api/reports/compliance`

Generate a compliance report (CSV).

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `system_admin`

---

### `POST /api/reports/whitelist`

Generate a whitelist policies report (CSV).

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `system_admin`

> All report endpoints share the same response format: `{ "file_path": "..." }`.

---

## 11. Backups

### `GET /api/backups`

List backup records.

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `system_admin`

**Response (200):**
```json
{
  "code": 200,
  "msg": "Backups",
  "data": {
    "items": [
      {
        "id": 1,
        "backup_type": "full",
        "status": "completed",
        "file_path": "/app/backups/full_backup_20260115.tar.gz",
        "file_size_bytes": 2048000,
        "created_at": "2026-01-15T02:00:00Z"
      }
    ]
  }
}
```

---

### `POST /api/backups/create`

Create a new backup (PostgreSQL dump + uploaded files archive).

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `system_admin`

**Response (200):**
```json
{
  "code": 200,
  "msg": "Backup created",
  "data": {
    "id": 2,
    "backup_type": "full",
    "status": "completed",
    "file_path": "/app/backups/full_backup_20260115143000.tar.gz"
  }
}
```

---

### `POST /api/backups/{backup_id}/recover`

Recover from a backup. Restores database and uploaded files.

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `system_admin`

**Safety:** Archive members are validated to reject absolute paths, traversal paths (`../`), and symlinks.

**Response (200):**
```json
{
  "code": 200,
  "msg": "Recovery completed",
  "data": { "backup_id": 2, "recovered": true }
}
```

---

## 12. Similarity (Reserved)

### `GET /api/similarity/check`

Check for similar materials by SHA-256 hash. **Interface is reserved but disabled by default.**

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `applicant`, `reviewer`, `system_admin`

**Query Parameters:**
| Parameter | Type | Required | Description |
|---|---|---|---|
| sha256_hash | string | Yes | File hash to check |

**Response (200):**
```json
{
  "code": 200,
  "msg": "Similarity check executed",
  "data": {
    "enabled": false,
    "matches": []
  }
}
```

> When `similarity_check_enabled = true` in configuration, this endpoint returns matching file records.

---

## 13. Admin

### `GET /api/admin/settings`

Get admin dashboard settings including whitelist policies.

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `system_admin`

**Response (200):**
```json
{
  "code": 200,
  "msg": "Admin settings",
  "data": {
    "backup": { "enabled": true },
    "whitelist_policies": [
      {
        "id": 1,
        "policy_name": "Default Policy",
        "scope_rule": "all_registrations",
        "is_active": true
      }
    ]
  }
}
```

---

### `POST /api/admin/whitelist-policies`

Create a new whitelist policy.

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `system_admin`

**Query Parameters:**
| Parameter | Type | Required | Description |
|---|---|---|---|
| policy_name | string | Yes | Policy name |
| scope_rule | string | Yes | Scope/rule definition |

**Response (200):**
```json
{
  "code": 200,
  "msg": "Whitelist policy created",
  "data": { "id": 2, "policy_name": "...", "scope_rule": "...", "is_active": true }
}
```

---

### `POST /api/admin/unlock-user`

Unlock a user account that was locked due to failed login attempts.

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `system_admin`

**Query Parameters:**
| Parameter | Type | Required | Description |
|---|---|---|---|
| username | string | Yes | Username to unlock |

**Response (200):**
```json
{
  "code": 200,
  "msg": "User unlocked",
  "data": { "username": "reviewer", "unlocked": true }
}
```

---

### `PUT /api/admin/secure-config/{config_key}`

Set an encrypted secure configuration value. Values are stored encrypted using Fernet symmetric encryption. Plaintext is never exposed via API.

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `system_admin`

**Request Body:**
```json
{
  "value": "sensitive-configuration-value"
}
```

**Response (200):**
```json
{
  "code": 200,
  "msg": "Secure configuration updated",
  "data": {
    "key": "sample_api_key",
    "is_set": true,
    "updated_by": 1,
    "updated_at": "2026-01-15T14:00:00Z"
  }
}
```

---

### `GET /api/admin/secure-config`

List secure configuration metadata. **Does not expose plaintext values.**

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `system_admin`

**Response (200):**
```json
{
  "code": 200,
  "msg": "Secure config metadata",
  "data": {
    "items": [
      {
        "key": "sample_api_key",
        "updated_at": "2026-01-15T14:00:00Z",
        "updated_by": 1
      }
    ]
  }
}
```

> **Security:** The `value` field is intentionally excluded from the response.

---

## 14. Audit Logs

### `GET /api/audit/logs`

List audit log entries (most recent 100).

**Headers:** `Authorization: Bearer <token>`  
**Roles:** `reviewer`, `system_admin`

**Response (200):**
```json
{
  "code": 200,
  "msg": "Audit logs",
  "data": {
    "items": [
      {
        "id": 1,
        "action": "registration.create",
        "target_type": "registration_form",
        "target_id": "5",
        "created_at": "2026-01-15T10:00:00Z"
      }
    ]
  }
}
```

---

## 15. Dashboard

### `GET /api/dashboard/summary`

Get a personalized dashboard summary.

**Headers:** `Authorization: Bearer <token>`  
**Roles:** Any authenticated user

**Response (200):**
```json
{
  "code": 200,
  "msg": "Dashboard summary",
  "data": {
    "welcome": "Welcome, System Admin",
    "role": "system_admin"
  }
}
```

---

## Appendix A: Role Permissions Matrix

| Endpoint | Applicant | Reviewer | Financial Admin | System Admin |
|---|---|---|---|---|
| `POST /api/auth/login` | ✅ | ✅ | ✅ | ✅ |
| `GET /api/auth/me` | ✅ | ✅ | ✅ | ✅ |
| `GET /api/registrations` | ✅ (own) | ✅ (all) | ❌ | ✅ (all) |
| `POST /api/registrations` | ✅ | ❌ | ❌ | ✅ |
| `POST /api/registrations/submit` | ✅ (own) | ❌ | ❌ | ✅ |
| `POST /api/registrations/supplementary` | ✅ (own) | ✅ | ❌ | ✅ |
| `GET /api/checklists` | ✅ | ✅ | ✅ | ✅ |
| `POST /api/materials/upload` | ✅ (own) | ❌ | ❌ | ✅ |
| `GET /api/materials/{id}` | ✅ (own) | ✅ | ❌ | ✅ |
| `PATCH /api/materials/status` | ❌ | ✅ | ❌ | ✅ |
| `GET /api/workflows/queue` | ❌ | ✅ | ❌ | ✅ |
| `POST /api/workflows/transition` | ❌ | ✅ | ❌ | ✅ |
| `POST /api/workflows/batch-transition` | ❌ | ✅ | ❌ | ✅ |
| `GET /api/workflows/{id}/history` | ✅ (own) | ✅ | ❌ | ✅ |
| `GET /api/finance/accounts` | ❌ | ❌ | ✅ | ✅ |
| `POST /api/finance/accounts` | ❌ | ❌ | ✅ | ✅ |
| `POST /api/finance/transactions` | ❌ | ❌ | ✅ | ✅ |
| `GET /api/finance/stats` | ❌ | ❌ | ✅ | ✅ |
| `POST /api/metrics/recompute` | ❌ | ✅ | ❌ | ✅ |
| `GET /api/alerts` | ❌ | ✅ | ✅ | ✅ |
| `POST /api/alerts/{id}/resolve` | ❌ | ❌ | ❌ | ✅ |
| `POST /api/reports/*` | ❌ | audit only | reconciliation | ✅ |
| `GET /api/backups` | ❌ | ❌ | ❌ | ✅ |
| `POST /api/backups/create` | ❌ | ❌ | ❌ | ✅ |
| `POST /api/backups/{id}/recover` | ❌ | ❌ | ❌ | ✅ |
| `GET /api/similarity/check` | ✅ | ✅ | ❌ | ✅ |
| `GET /api/admin/settings` | ❌ | ❌ | ❌ | ✅ |
| `POST /api/admin/whitelist-policies` | ❌ | ❌ | ❌ | ✅ |
| `POST /api/admin/unlock-user` | ❌ | ❌ | ❌ | ✅ |
| `PUT /api/admin/secure-config/{key}` | ❌ | ❌ | ❌ | ✅ |
| `GET /api/admin/secure-config` | ❌ | ❌ | ❌ | ✅ |
| `GET /api/audit/logs` | ❌ | ✅ | ❌ | ✅ |
| `GET /api/dashboard/summary` | ✅ | ✅ | ✅ | ✅ |

---

## Appendix B: Default Seed Accounts

| Username | Password | Role |
|---|---|---|
| `admin` | `Admin@123456` | system_admin |
| `reviewer` | `Reviewer@123456` | reviewer |
| `applicant` | `Applicant@123456` | applicant |
| `finance` | `Finance@123456` | financial_admin |
