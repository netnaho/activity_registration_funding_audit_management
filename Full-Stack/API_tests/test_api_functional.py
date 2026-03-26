import json
import time
import urllib.error
import urllib.parse
import urllib.request


BASE_URL = "http://localhost:8000"


def request_json(method: str, path: str, payload: dict | None = None, token: str | None = None, content_type: str = "application/json"):
    url = f"{BASE_URL}{path}"
    data = None
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    if payload is not None:
        if content_type == "application/json":
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        else:
            encoded = urllib.parse.urlencode(payload).encode("utf-8")
            data = encoded
            headers["Content-Type"] = content_type

    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {"raw": body}
        return exc.code, parsed


def login(username: str, password: str) -> tuple[int, dict]:
    return request_json("POST", "/api/auth/login", {"username": username, "password": password})


def assert_true(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)


def run():
    status, health = request_json("GET", "/api/health")
    assert_true(status == 200, "health endpoint failed")
    assert_true(health.get("data", {}).get("status") == "healthy", "health payload mismatch")

    status, admin_login = login("admin", "Admin@123456")
    assert_true(status == 200, "admin login failed")
    admin_token = admin_login["data"]["access_token"]

    # Ensure repeatable runs even if previous execution locked accounts.
    for username in ["reviewer", "applicant", "finance"]:
        unlock_status, _unlock_payload = request_json("POST", f"/api/admin/unlock-user?username={username}", token=admin_token)
        assert_true(unlock_status == 200, f"failed to unlock user {username} for deterministic test run")

    status, bad_login = login("admin", "WrongPassword123")
    assert_true(status == 401, "invalid login should fail")

    status, applicant_login = login("applicant", "Applicant@123456")
    assert_true(status == 200, "applicant login failed")
    applicant_token = applicant_login["data"]["access_token"]

    status, reviewer_login = login("reviewer", "Reviewer@123456")
    assert_true(status == 200, "reviewer login failed")
    reviewer_token = reviewer_login["data"]["access_token"]

    status, finance_login = login("finance", "Finance@123456")
    assert_true(status == 200, "finance login failed")
    finance_token = finance_login["data"]["access_token"]

    status, checklists = request_json("GET", "/api/checklists", token=applicant_token)
    assert_true(status == 200, "checklist fetch failed")
    checklist_items = checklists.get("data", {}).get("items", [])[0]["items"]
    assert_true(len(checklist_items) >= 3, "checklist items missing")

    reg_payload = {
        "title": f"API Test Registration {int(time.time())}",
        "description": "API functional test registration for acceptance hardening.",
        "contact_phone": "5550001111",
        "id_number": "ID55667788",
        "deadline_at": "2030-12-31T10:00:00Z",
    }
    status, reg_create = request_json("POST", "/api/registrations", payload=reg_payload, token=applicant_token)
    assert_true(status == 200, "registration create failed")
    registration_id = reg_create["data"]["id"]

    status, _missing_fields = request_json("POST", "/api/registrations", payload={"title": "x"}, token=applicant_token)
    assert_true(status in (400, 422), "invalid registration payload should fail")

    status, _forbidden_reg_create = request_json("POST", "/api/registrations", payload=reg_payload, token=reviewer_token)
    assert_true(status == 403, "reviewer should not create registration")

    # object-level authorization: applicant cannot access others' registration resources
    status, applicant_regs = request_json("GET", "/api/registrations", token=applicant_token)
    assert_true(status == 200, "applicant registrations list failed")
    own_ids = {item["id"] for item in applicant_regs.get("data", {}).get("items", [])}
    candidate_forbidden_id = 1
    if candidate_forbidden_id in own_ids:
        candidate_forbidden_id = registration_id + 9999

    status, _forbidden_materials = request_json("GET", f"/api/materials/{candidate_forbidden_id}", token=applicant_token)
    assert_true(status in (403, 404), "applicant should not access foreign materials")

    status, _forbidden_history = request_json("GET", f"/api/workflows/{candidate_forbidden_id}/history", token=applicant_token)
    assert_true(status in (403, 404), "applicant should not access foreign workflow history")

    status, _forbidden_supplementary = request_json(
        "POST",
        "/api/registrations/supplementary",
        payload={"registration_id": candidate_forbidden_id, "reason": "not owner"},
        token=applicant_token,
    )
    assert_true(status in (403, 404), "applicant should not open supplementary on foreign registration")

    file_boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    file_content = b"%PDF-1.4\napi-test-content\n"
    def multipart_body(reg_id: int, item_id: int, filename: str, content: bytes, content_type: str = "application/pdf"):
        lines = []
        lines.append(f"--{file_boundary}\r\n".encode())
        lines.append(b'Content-Disposition: form-data; name="registration_id"\r\n\r\n')
        lines.append(f"{reg_id}\r\n".encode())
        lines.append(f"--{file_boundary}\r\n".encode())
        lines.append(b'Content-Disposition: form-data; name="checklist_item_id"\r\n\r\n')
        lines.append(f"{item_id}\r\n".encode())
        lines.append(f"--{file_boundary}\r\n".encode())
        lines.append(
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\nContent-Type: {content_type}\r\n\r\n'.encode()
        )
        lines.append(content)
        lines.append(b"\r\n")
        lines.append(f"--{file_boundary}--\r\n".encode())
        return b"".join(lines)

    def upload(reg_id: int, item_id: int, filename: str, content: bytes, content_type: str = "application/pdf"):
        body = multipart_body(reg_id, item_id, filename, content, content_type)
        req = urllib.request.Request(
            f"{BASE_URL}/api/materials/upload",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {applicant_token}",
                "Content-Type": f"multipart/form-data; boundary={file_boundary}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.status, json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode())

    status, upload1 = upload(registration_id, checklist_items[0]["id"], "item1.pdf", file_content)
    assert_true(status == 200, "valid file upload failed")
    assert_true(upload1.get("data", {}).get("status") == "pending_submission", "new upload should start as pending_submission")

    status, upload_bad_ext = upload(registration_id, checklist_items[1]["id"], "item2.exe", b"binary", "application/octet-stream")
    assert_true(status == 400, "invalid extension upload should fail")

    status, upload2 = upload(registration_id, checklist_items[1]["id"], "item2.pdf", file_content)
    assert_true(status == 200, "second valid upload failed")

    status, upload3 = upload(registration_id, checklist_items[2]["id"], "item3.pdf", b"%PDF-1.4\nthird\n")
    assert_true(status == 200, "third valid upload failed")

    # max 3 versions per material: 4th upload to same checklist item must fail
    status, _v2 = upload(registration_id, checklist_items[0]["id"], "item1_v2.pdf", b"%PDF-1.4\nver2\n")
    assert_true(status == 200, "second version upload failed")
    status, _v3 = upload(registration_id, checklist_items[0]["id"], "item1_v3.pdf", b"%PDF-1.4\nver3\n")
    assert_true(status == 200, "third version upload failed")
    status, _v4 = upload(registration_id, checklist_items[0]["id"], "item1_v4.pdf", b"%PDF-1.4\nver4\n")
    assert_true(status == 400, "fourth version upload should fail due to max 3 versions")

    status, reg_submit = request_json("POST", "/api/registrations/submit", payload={"registration_id": registration_id}, token=applicant_token)
    assert_true(status == 200, "registration submit failed")

    status, submit_again = request_json("POST", "/api/registrations/submit", payload={"registration_id": registration_id}, token=applicant_token)
    assert_true(status == 400, "re-submitting already submitted registration should fail")
    assert_true("cannot be submitted" in submit_again.get("msg", ""), "re-submit failure reason mismatch")

    status, materials_after_submit = request_json("GET", f"/api/materials/{registration_id}", token=applicant_token)
    assert_true(status == 200, "materials read after submit failed")
    flattened = [v for s in materials_after_submit.get("data", {}).get("items", []) for v in s.get("versions", [])]
    assert_true(any(v.get("status") == "submitted" for v in flattened), "pending versions should become submitted on submit")

    status, transition_invalid = request_json(
        "POST",
        "/api/workflows/transition",
        payload={"registration_id": registration_id, "target_status": "draft", "comment": "invalid"},
        token=reviewer_token,
    )
    assert_true(status in (400, 422), "invalid transition should fail")

    status, transition_valid = request_json(
        "POST",
        "/api/workflows/transition",
        payload={"registration_id": registration_id, "target_status": "supplemented", "comment": "Need correction"},
        token=reviewer_token,
    )
    assert_true(status == 200, "valid transition failed")

    status, materials_after_correction = request_json("GET", f"/api/materials/{registration_id}", token=reviewer_token)
    assert_true(status == 200, "materials read after correction failed")
    flattened_correction = [v for s in materials_after_correction.get("data", {}).get("items", []) for v in s.get("versions", [])]
    assert_true(any(v.get("status") == "needs_correction" for v in flattened_correction), "correction should mark versions needs_correction")

    target_version = flattened_correction[0]["material_version_id"]
    status, _invalid_material_status = request_json(
        "PATCH",
        "/api/materials/status",
        payload={"material_version_id": target_version, "status": "submitted"},
        token=reviewer_token,
    )
    assert_true(status in (400, 422), "invalid material transition should fail")

    status, history = request_json("GET", f"/api/workflows/{registration_id}/history", token=reviewer_token)
    assert_true(status == 200 and len(history.get("data", {}).get("items", [])) >= 1, "workflow history missing")

    status, batch_too_large = request_json(
        "POST",
        "/api/workflows/batch-transition",
        payload={"registration_ids": list(range(1, 52)), "target_status": "approved", "comment": "batch"},
        token=reviewer_token,
    )
    assert_true(status in (400, 422), "batch > 50 should fail")

    status, batch_ok = request_json(
        "POST",
        "/api/workflows/batch-transition",
        payload={"registration_ids": [registration_id], "target_status": "approved", "comment": "batch ok"},
        token=reviewer_token,
    )
    assert_true(status == 200, "batch <= 50 should pass")

    account_payload = {
        "account_name": f"API Account {int(time.time())}",
        "category": "ops",
        "period": "2026Q3",
        "budget_amount": 100,
    }
    status, account_create = request_json("POST", "/api/finance/accounts", payload=account_payload, token=finance_token)
    assert_true(status == 200, "finance account create failed")
    account_id = account_create["data"]["id"]

    tx_payload = {
        "funding_account_id": account_id,
        "transaction_type": "expense",
        "amount": 120,
        "transaction_time": "2030-01-01T10:00:00Z",
        "category": "ops",
        "note": "overspend check",
        "overspend_confirmed": "false",
    }
    status, overspend_no_confirm = request_json(
        "POST", "/api/finance/transactions", payload=tx_payload, token=finance_token, content_type="application/x-www-form-urlencoded"
    )
    assert_true(status == 409, "overspend without confirmation should fail")

    tx_payload["overspend_confirmed"] = "true"
    status, overspend_confirm = request_json(
        "POST", "/api/finance/transactions", payload=tx_payload, token=finance_token, content_type="application/x-www-form-urlencoded"
    )
    assert_true(status == 200, "overspend with confirmation should pass")

    status, _stats = request_json("GET", "/api/finance/stats", token=finance_token)
    assert_true(status == 200, "finance stats failed")
    stats_data = _stats.get("data", {})
    assert_true("total_transactions" in stats_data, "finance stats missing total_transactions")
    assert_true("by_category" in stats_data and isinstance(stats_data["by_category"], dict), "finance stats missing by_category")
    assert_true("by_day" in stats_data and isinstance(stats_data["by_day"], dict), "finance stats missing by_day")
    assert_true(stats_data.get("total_transactions", 0) >= 1, "finance stats should include at least one transaction")
    assert_true("ops" in stats_data.get("by_category", {}), "finance stats should aggregate ops category")

    for path in ["/api/reports/reconciliation", "/api/reports/audit", "/api/reports/compliance", "/api/reports/whitelist"]:
        status, _report = request_json("POST", path, token=admin_token)
        assert_true(status == 200, f"report export failed for {path}")

    status, _alerts = request_json("GET", "/api/alerts", token=admin_token)
    assert_true(status == 200, "alerts list failed")

    status, _similarity = request_json("GET", "/api/similarity/check?sha256_hash=testhash", token=admin_token)
    assert_true(status == 200, "similarity endpoint failed")

    # secure config (write-only metadata listing)
    status, secure_set = request_json(
        "PUT",
        "/api/admin/secure-config/sample_api_key",
        payload={"value": "top-secret"},
        token=admin_token,
    )
    assert_true(status == 200, "secure config set failed")
    assert_true(secure_set.get("data", {}).get("is_set") is True, "secure config set flag missing")

    status, secure_list = request_json("GET", "/api/admin/secure-config", token=admin_token)
    assert_true(status == 200, "secure config metadata list failed")
    first_meta = secure_list.get("data", {}).get("items", [])[0]
    assert_true("key" in first_meta and "updated_at" in first_meta, "secure config metadata missing")
    assert_true("value" not in first_meta, "secure config must not expose plaintext value")

    status, _secure_forbidden = request_json(
        "PUT",
        "/api/admin/secure-config/forbidden_test",
        payload={"value": "not-allowed"},
        token=applicant_token,
    )
    assert_true(status == 403, "non-admin must not set secure config")

    # lockout behavior using a dedicated username (seeded reviewer account)
    for _ in range(10):
        status, _ = login("reviewer", "wrong-pass")
    status, locked = login("reviewer", "Reviewer@123456")
    assert_true(status == 401, "account should be locked after repeated failures")
    assert_true("locked" in locked.get("msg", "").lower(), "lockout message missing")

    # Restore reviewer account state for repeatable future runs.
    unlock_status, _unlock_payload = request_json("POST", "/api/admin/unlock-user?username=reviewer", token=admin_token)
    assert_true(unlock_status == 200, "failed to unlock reviewer after lockout test")

    print("API functional checks completed successfully")


if __name__ == "__main__":
    run()
