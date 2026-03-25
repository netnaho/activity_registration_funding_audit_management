import pytest

from app.core.exceptions import APIError
from app.services.material_service import _check_file_constraints


def test_material_file_extension_validation():
    with pytest.raises(APIError):
        _check_file_constraints("invalid.exe", 100)


def test_material_single_file_size_validation():
    with pytest.raises(APIError):
        _check_file_constraints("sample.pdf", 21 * 1024 * 1024)


def test_material_valid_pdf_file():
    _check_file_constraints("sample.pdf", 1024)
