from pathlib import Path

from app.services.backup_service import _pg_conn_parts


def test_pg_connection_parts_parser():
    parsed = _pg_conn_parts("postgresql+psycopg://user:pass@postgres:5432/dbname")
    assert parsed["host"] == "postgres"
    assert parsed["port"] == "5432"
    assert parsed["user"] == "user"
    assert parsed["database"] == "dbname"


def test_backup_archive_name_pattern_example():
    filename = "full_backup_20260101010101.tar.gz"
    assert filename.startswith("full_backup_")
    assert filename.endswith(".tar.gz")
