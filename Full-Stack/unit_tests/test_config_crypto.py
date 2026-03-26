from app.security.config_crypto import decrypt_config_value, encrypt_config_value


def test_secure_config_encryption_roundtrip():
    plain = "my-sensitive-value"
    cipher = encrypt_config_value(plain)
    assert cipher != plain
    assert decrypt_config_value(cipher) == plain
