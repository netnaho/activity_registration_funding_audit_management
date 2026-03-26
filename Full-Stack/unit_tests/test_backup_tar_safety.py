import tarfile
from pathlib import Path

import pytest

from app.core.exceptions import APIError
from app.services.backup_service import _validate_tar_members


def _tar_member(name: str) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name=name)
    info.size = 0
    return info


def test_validate_tar_members_rejects_absolute_path(tmp_path: Path):
    members = [_tar_member("/etc/passwd")]
    with pytest.raises(APIError):
        _validate_tar_members(members, tmp_path)


def test_validate_tar_members_rejects_traversal(tmp_path: Path):
    members = [_tar_member("../../escape.txt")]
    with pytest.raises(APIError):
        _validate_tar_members(members, tmp_path)


def test_validate_tar_members_accepts_safe_paths(tmp_path: Path):
    members = [_tar_member("database.sql"), _tar_member("uploads/file.pdf")]
    _validate_tar_members(members, tmp_path)
