import os
import shutil
import subprocess
import tarfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import APIError
from app.models.backup_record import BackupRecord
from app.storage.hashing import sha256_bytes


def _pg_conn_parts(database_url: str) -> dict[str, str]:
    # expected: postgresql+psycopg://user:pass@host:port/db
    normalized = database_url.replace("postgresql+psycopg://", "postgresql://")
    parsed = urlparse(normalized)
    return {
        "host": parsed.hostname or "postgres",
        "port": str(parsed.port or 5432),
        "user": parsed.username or "activity_user",
        "password": parsed.password or "activity_password",
        "database": (parsed.path or "/activity_audit").lstrip("/"),
    }


def create_local_backup(db: Session, triggered_by: int | None = None) -> BackupRecord:
    backups_dir = Path(settings.backups_dir)
    uploads_dir = Path(settings.uploads_dir)
    backups_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    archive_path = backups_dir / f"full_backup_{ts}.tar.gz"
    tmp_dir = backups_dir / f"tmp_{ts}"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    db_dump_path = tmp_dir / "database.sql"
    conn = _pg_conn_parts(os.getenv("DATABASE_URL", "postgresql://activity_user:activity_password@postgres:5432/activity_audit"))
    env = os.environ.copy()
    env["PGPASSWORD"] = conn["password"]
    dump_cmd = [
        "pg_dump",
        "-h",
        conn["host"],
        "-p",
        conn["port"],
        "-U",
        conn["user"],
        "-d",
        conn["database"],
        "-f",
        str(db_dump_path),
    ]
    result = subprocess.run(dump_cmd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise APIError(500, f"Database backup failed: {result.stderr.strip()}")

    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(db_dump_path, arcname="database.sql")
        if uploads_dir.exists():
            tar.add(uploads_dir, arcname="uploads")

    shutil.rmtree(tmp_dir, ignore_errors=True)

    payload = archive_path.read_bytes()
    record = BackupRecord(
        backup_type="full",
        file_path=str(archive_path),
        file_sha256=sha256_bytes(payload),
        file_size_bytes=len(payload),
        status="completed",
        triggered_by=triggered_by,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_backups(db: Session) -> list[BackupRecord]:
    return db.query(BackupRecord).order_by(BackupRecord.created_at.desc()).all()


def recover_backup(db: Session, backup_id: int) -> str:
    record = db.query(BackupRecord).filter(BackupRecord.id == backup_id).first()
    if not record:
        raise APIError(404, "Backup record not found")

    archive = Path(record.file_path)
    if not archive.exists():
        raise APIError(404, "Backup file does not exist on disk")

    tmp_restore = Path(settings.backups_dir) / f"restore_{backup_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    tmp_restore.mkdir(parents=True, exist_ok=True)

    with tarfile.open(archive, "r:gz") as tar:
        tar.extractall(path=tmp_restore)

    db_dump = tmp_restore / "database.sql"
    restored_uploads = tmp_restore / "uploads"

    if restored_uploads.exists():
        target_uploads = Path(settings.uploads_dir)
        target_uploads.parent.mkdir(parents=True, exist_ok=True)
        if target_uploads.exists():
            shutil.rmtree(target_uploads)
        shutil.move(str(restored_uploads), str(target_uploads))

    if db_dump.exists():
        conn = _pg_conn_parts(os.getenv("DATABASE_URL", "postgresql://activity_user:activity_password@postgres:5432/activity_audit"))
        env = os.environ.copy()
        env["PGPASSWORD"] = conn["password"]
        restore_cmd = [
            "psql",
            "-h",
            conn["host"],
            "-p",
            conn["port"],
            "-U",
            conn["user"],
            "-d",
            conn["database"],
            "-f",
            str(db_dump),
        ]
        result = subprocess.run(restore_cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            shutil.rmtree(tmp_restore, ignore_errors=True)
            raise APIError(500, f"Database restore failed: {result.stderr.strip()}")

    shutil.rmtree(tmp_restore, ignore_errors=True)

    return "Recovery completed"
