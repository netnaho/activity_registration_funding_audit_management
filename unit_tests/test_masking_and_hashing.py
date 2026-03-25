from app.storage.hashing import sha256_bytes
from app.utils.masking import mask_contact, mask_id_number


def test_mask_id_number_hides_middle_characters():
    assert mask_id_number("ABCDEF12") == "AB****12"


def test_mask_contact_hides_middle_digits():
    assert mask_contact("1234567890") == "123*****90"


def test_sha256_hash_consistency():
    payload = b"same-data"
    assert sha256_bytes(payload) == sha256_bytes(payload)
