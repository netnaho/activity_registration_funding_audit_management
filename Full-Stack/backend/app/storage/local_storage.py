from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.core.config import settings
from app.storage.hashing import sha256_bytes


class LocalStorageService:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_path = Path(base_dir or settings.uploads_dir)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def build_safe_path(self, namespace: str, filename: str) -> Path:
        extension = Path(filename).suffix.lower()
        date_bucket = datetime.utcnow().strftime("%Y/%m/%d")
        safe_name = f"{uuid4().hex}{extension}"
        target_dir = self.base_path / namespace / date_bucket
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir / safe_name

    def save_bytes(self, namespace: str, original_filename: str, payload: bytes) -> dict[str, str | int]:
        target_path = self.build_safe_path(namespace, original_filename)
        target_path.write_bytes(payload)
        digest = sha256_bytes(payload)
        return {
            "stored_path": str(target_path),
            "stored_filename": target_path.name,
            "sha256": digest,
            "size_bytes": len(payload),
        }
