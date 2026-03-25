from __future__ import annotations

import json
import logging
import sys
import uuid
from typing import Any, Mapping
from datetime import datetime, timezone

from app.logging.redaction import redact_mapping


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "channel": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        category = getattr(record, "category", None)
        if category:
            payload["category"] = category
        event = getattr(record, "event", None)
        if event:
            payload["event"] = event
        request_id = getattr(record, "request_id", None)
        if request_id:
            payload["request_id"] = request_id
        context = getattr(record, "context", None)
        if isinstance(context, Mapping):
            payload["context"] = redact_mapping(dict(context))
        return json.dumps(payload, ensure_ascii=True)


def configure_logging() -> None:
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)

    for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = True


def app_logger(name: str = "app") -> logging.Logger:
    return logging.getLogger(name)


def new_request_id() -> str:
    return uuid.uuid4().hex


def log_info(logger: logging.Logger, event: str, category: str, context: dict | None = None, request_id: str | None = None) -> None:
    logger.info(event, extra={"event": event, "category": category, "context": context or {}, "request_id": request_id})


def log_warning(
    logger: logging.Logger,
    event: str,
    category: str,
    context: dict | None = None,
    request_id: str | None = None,
) -> None:
    logger.warning(event, extra={"event": event, "category": category, "context": context or {}, "request_id": request_id})


def log_error(logger: logging.Logger, event: str, category: str, context: dict | None = None, request_id: str | None = None) -> None:
    logger.error(event, extra={"event": event, "category": category, "context": context or {}, "request_id": request_id})
