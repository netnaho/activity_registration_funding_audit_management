from __future__ import annotations

import time
from collections.abc import Callable

from fastapi import Request, Response

from app.logging.logger import app_logger, log_error, log_info, log_warning, new_request_id


logger = app_logger("app.request")


async def request_logging_middleware(request: Request, call_next: Callable) -> Response:
    request_id = request.headers.get("x-request-id") or new_request_id()
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        log_error(
            logger,
            event="request_failed",
            category="operational",
            request_id=request_id,
            context={
                "method": request.method,
                "path": request.url.path,
                "elapsed_ms": elapsed_ms,
                "client": request.client.host if request.client else None,
            },
        )
        raise

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    context = {
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "elapsed_ms": elapsed_ms,
        "client": request.client.host if request.client else None,
    }

    if response.status_code >= 500:
        log_error(logger, event="request_completed", category="operational", request_id=request_id, context=context)
    elif response.status_code >= 400 or elapsed_ms >= 2000:
        log_warning(logger, event="request_completed", category="operational", request_id=request_id, context=context)
    else:
        log_info(logger, event="request_completed", category="operational", request_id=request_id, context=context)

    response.headers["x-request-id"] = request_id
    return response
