from app.logging.redaction import redact_mapping


def test_redact_sensitive_keys():
    data = {
        "username": "demo",
        "password": "secret",
        "token": "abc",
        "nested": {
            "id_number": "ID1234",
            "contact_phone": "5551112222",
        },
    }
    redacted = redact_mapping(data)
    assert redacted["username"] == "demo"
    assert redacted["password"] == "***REDACTED***"
    assert redacted["token"] == "***REDACTED***"
    assert redacted["nested"]["id_number"] == "***REDACTED***"
    assert redacted["nested"]["contact_phone"] == "***REDACTED***"
