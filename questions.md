# Business Logic Questions Log

## 1. Supplementary Submission Trigger and Scope

**Question:** The Prompt states "a one-time supplementary submission process (within 72 hours) can still be initiated," but does not specify *who* initiates it (applicant or reviewer), *what status* the registration must be in, or whether the 72-hour clock starts from the rejection/supplementation time or from the original submission time.

**My Understanding:** Only registrations in a correction-related status (`rejected` or `supplemented`) should allow a supplementary window. The 72h clock should start from the most recent reviewer action that triggered the correction (i.e., the `created_at` of the latest workflow record transitioning to `supplemented` or `rejected`). Both the applicant (owner) and reviewer/admin should be able to open it, since reviewers request corrections but applicants need to act on them.

**Solution:** Implemented in `registration_service.py:136-173`. The supplementary window checks: (1) status must be `rejected` or `supplemented`, (2) looks up the latest `ReviewWorkflowRecord` with `to_status` in `[supplemented, rejected]` and uses its `created_at` as the trigger time, (3) enforces `datetime.now(UTC) <= trigger_time + 72h`, (4) checks for existing `SupplementarySubmissionRecord` to enforce one-time usage. Roles `APPLICANT`, `REVIEWER`, and `SYSTEM_ADMIN` are allowed to open it.

---

## 2. Material Lock Behavior After Deadline vs. After Supplementary

**Question:** The Prompt says "automatically locks materials after the deadline" and also allows a supplementary submission window. It is unclear whether opening a supplementary window *unlocks* previously locked materials, and whether the supplementary window has its own independent lock deadline.

**My Understanding:** When a reviewer transitions a registration to `supplemented`, the lock should be released so the applicant can re-upload corrected materials. The supplementary window has its own `expires_at` (72h from opening), but the generic deadline-based auto-lock mechanism (`maybe_lock_registration`) still applies on each access.

**Solution:** In `workflow_service.py:61-63`, transitioning to `supplemented` sets `registration.is_locked = False` and marks latest material versions as `needs_correction`. In `registration_service.py:169`, opening a supplementary window also sets `is_locked = False`. The `maybe_lock_registration` function (`registration_service.py:129-133`) re-locks on access if the original `deadline_at` has passed. The supplementary window's `expires_at` is stored but the lock mechanism still relies on the original deadline field — a potential gap if the original deadline has already passed before supplementary opens.

---

## 3. Overspend Threshold Scope: Per-Transaction or Cumulative

**Question:** The Prompt states "if expenses exceed the budget by 10%, a frontend pop-up warning is triggered." It is ambiguous whether the 10% threshold applies to a single transaction exceeding the budget by 10%, or to the *cumulative* total expenses exceeding the budget by 10%.

**My Understanding:** The 10% threshold should apply cumulatively — the system should warn when the total projected expenses (existing expenses + new transaction amount) exceed 110% of the account's budget.

**Solution:** Implemented in `finance_service.py:77-89`. The check calculates `current_expense = _account_expense_total(db, account_id)` (sum of all existing expenses), then `projected = current_expense + amount`. Warning triggers when `projected > budget_amount * 1.1`. This is a cumulative check, not per-transaction.

---

## 4. Correction Reason Recording: Where and How

**Question:** The Prompt mentions "reasons for correction recorded" but does not specify whether correction reasons are stored as part of the material version, as a separate workflow comment, or as an audit log entry.

**My Understanding:** Correction reasons are best captured as the `comment` field on the `ReviewWorkflowRecord` when a reviewer transitions a registration to `supplemented` or `rejected`. This ties the reason to the workflow timeline for traceability.

**Solution:** In `workflow_service.py:57-58`, a comment is *required* for transitions to `rejected`, `supplemented`, or `canceled`. The comment is stored in `ReviewWorkflowRecord.comment` and displayed in the workflow timeline drawer (`ReviewerQueueView.vue:69`). Additionally, the supplementary window itself records a `reason` field (`SupplementarySubmissionRecord.reason`).

---

## 5. State Machine: "Promoted from Waitlist" Entry Conditions

**Question:** The Prompt lists `promoted_from_waitlist` as a valid status but does not specify which statuses can transition *to* it, or what a "waitlist" means in this context. There is no explicit "waitlisted" status.

**My Understanding:** "Promoted from waitlist" is a terminal-like recovery action for registrations that were previously `rejected` or put into a holding pattern via `supplemented`. It represents a second-chance approval and can be reached from `supplemented` or `rejected`.

**Solution:** Implemented in `workflow_service.py:21-27`:
- `supplemented → promoted_from_waitlist` (allowed)
- `rejected → promoted_from_waitlist` (allowed)
- `promoted_from_waitlist` is a terminal state (no outgoing transitions).

---

## 6. Mandatory Checklist Items and Submission Gating

**Question:** The Prompt says applicants "upload materials item by item according to the checklist" but does not specify whether *all* checklist items must have uploads before submission, or only those marked as required.

**My Understanding:** Only checklist items marked as `required=True` should gate submission. Optional checklist items can be skipped.

**Solution:** In `registration_service.py:85-101`, submission calls `_required_item_ids(db)` to get all checklist items where `required=True`, then `_submitted_item_ids(db, registration_id)` to get items with at least one uploaded version. If `required - submitted` is non-empty, submission is blocked with "Checklist mandatory materials are incomplete."

---

## 7. Sensitive Field Masking: Which Roles See What

**Question:** The Prompt states "sensitive fields (e.g., ID numbers, contact information) are displayed with role-based masking" but does not define the exact masking rules per role — e.g., does a reviewer see masked data? Does the applicant see their own data unmasked?

**My Understanding:** The applicant should see their own unmasked data (they provided it). System admins see all data unmasked (full access for management). Reviewers and financial admins should see masked versions to limit exposure.

**Solution:** Implemented in `registration_service.py:177-186`:
- Applicant viewing *own* registration: unmasked.
- System admin: unmasked.
- All other roles (reviewer, financial_admin): `id_number` → `mask_id_number()`, `contact_phone` → `mask_contact()`.
Masking functions in `utils/masking.py` replace middle characters (e.g., `AB****12`, `123*****90`).

---

## 8. Batch Review Comment: Shared or Per-Item

**Question:** The Prompt allows "batch review (≤50 entries per batch)" with "filling in review comments." It is unclear whether a single comment applies to the entire batch or if each registration in the batch gets its own individual comment.

**My Understanding:** For batch operations, a single shared comment is practical and standard. Reviewers provide one comment that applies to all selected registrations in the batch.

**Solution:** `workflow_service.py:80-102` — `apply_batch_transition` accepts a single `comment` string and a single `target_status`, then iterates over `registration_ids` calling `apply_transition` with the same comment for each. A `batch_ref` identifier groups them in the workflow history.

---

## 9. Data Deletion Strategy: Physical or Logical

**Question:** The Prompt does not specify whether records (users, registrations, materials, transactions) should be physically deleted or logically soft-deleted when removed.

**My Understanding:** Given the auditing and compliance focus of the platform (audit logs, compliance reports, backup/recovery), logical deletion is the appropriate approach. However, the Prompt does not describe any explicit "delete" operations for business entities.

**Solution:** The project does not implement any delete endpoints for core business entities (registrations, materials, transactions, funding accounts). Users have an `is_active` flag (`user.py`) that serves as a soft-disable mechanism. `audit_log` records are never deleted. This is consistent with the compliance-oriented nature of the platform — no data destruction, full traceability.

---

## 10. JWT Secret Management in Offline/Containerized Deployment

**Question:** The Prompt requires "encryption of sensitive configurations" and "pure offline deployment." It does not specify how JWT secrets should be managed when no external secret manager is available and the environment variable may not be set.

**My Understanding:** In an offline Docker deployment, the backend should auto-generate a strong JWT secret on first startup and persist it locally so it survives container restarts. Weak or default secrets should be rejected to prevent accidental insecure deployments.

**Solution:** Implemented in `core/secrets.py:24-48`:
1. If `JWT_SECRET_KEY` env var is provided and strong (≥32 chars, not in weak list), use it.
2. If weak/default, raise RuntimeError at startup.
3. If not provided, check for persisted secret at `/app/backups/security/jwt_secret.key`.
4. If no persisted secret, generate `secrets.token_urlsafe(64)`, write it with `chmod 0600`, and cache it.

---

## 11. Finance Statistics: Aggregation by Income vs. Expense

**Question:** The Prompt says "generate statistics by category and time" for financial data, but does not specify whether statistics should be broken down by income vs. expense separately, or aggregated together.

**My Understanding:** The current implementation aggregates all transaction amounts by category and by day regardless of type. A more useful breakdown would separate income and expense totals.

**Solution:** Implemented in `finance_service.py:132-153` as a combined aggregation (`by_category` and `by_day` summing all transaction amounts). This is a simplified approach. Enhancement would add `by_type` breakdown or separate income/expense subtotals per category.

---

## 12. Similarity/Duplicate Check: Scope and Activation

**Question:** The Prompt says "a 'similarity/duplicate check' interface is reserved but disabled by default and does not rely on external services." It is unclear what exactly the interface should return when called while disabled, and what constitutes "similarity" vs. SHA-256 duplicate detection.

**My Understanding:** Two distinct concepts: (1) SHA-256 exact duplicate detection is *always active* during upload (comparing file hashes), and (2) the "similarity" interface is an *advanced* feature placeholder that could do content-level fuzzy comparison but is explicitly disabled. When called while disabled, it should return a safe response indicating the feature is not active.

**Solution:** SHA-256 duplicate detection is active in `material_service.py:102` — checked during every upload and returned as `duplicate_detected` boolean. The similarity endpoint (`routers/similarity.py`) is a separate reserved interface controlled by `config.py:21` (`similarity_check_enabled: bool = False`). When called, it returns a 200 response without performing external calls. The API functional test verifies it responds successfully (`test_api_functional.py:269-270`).

---

## 13. Backup Recovery: Scope and Safety

**Question:** The Prompt requires "one-click recovery" but does not specify whether recovery should be a full state replacement (destructive overwrite) or a merge operation. It also doesn't address security risks like tar path traversal in backup archives.

**My Understanding:** Recovery should be a full restore from a backup archive (DB dump + uploaded files). Since this is destructive, safety validation of archive contents is critical to prevent path traversal attacks.

**Solution:** Implemented in `backup_service.py`:
- `create_local_backup` creates a `tar.gz` containing a PostgreSQL SQL dump + uploaded files archive.
- `recover_backup` extracts and applies the archive.
- `_validate_tar_members` (tested in `test_backup_tar_safety.py:16-30`) rejects absolute paths, traversal paths (`../`), and symlink members before extraction.
- `README.md:196-198` documents these hardening measures.

---

## 14. Access Frequency Control: Account-Level vs. IP-Level

**Question:** The Prompt specifies "account locked for 30 minutes after ≥10 failed attempts within 5 minutes" but does not clarify whether the rate limit is per-account (username-based), per-IP, or a combination.

**My Understanding:** Per-account lockout is the standard approach for this requirement. IP-based rate limiting would require additional infrastructure (reverse proxy, Redis) that conflicts with the offline/simple deployment model.

**Solution:** Implemented as per-account lockout in `auth_service.py:11-89`. The `User` model tracks `failed_attempt_count`, `first_failed_attempt_at`, and `locked_until`. Each `LoginAttemptLog` records `ip_address` and `user_agent` for audit purposes, but the lockout decision is username-based. An admin unlock endpoint (`/api/admin/unlock-user`) allows recovery.

---

## 15. Report Export Format and Delivery

**Question:** The Prompt requires "exporting reconciliation, audit, compliance reports, and whitelist policies" but does not specify the file format, whether reports are downloaded directly by the client, or stored server-side.

**My Understanding:** CSV is the standard format for tabular report exports in offline enterprise systems. Reports should be generated and stored server-side (for backup/audit trail purposes), with the file path returned to the client.

**Solution:** All four report endpoints (`reports.py:20-53`) generate CSV files via `report_service.py` and store them under the reports backup directory. The API returns `{"file_path": path}` so the client knows the export succeeded. The files are included in backup archives for long-term retention.
