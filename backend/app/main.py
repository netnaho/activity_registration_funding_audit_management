from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.responses import error_response
from app.api.routers import (
    admin,
    alerts,
    audit,
    auth,
    backups,
    checklists,
    dashboard,
    finance,
    health,
    materials,
    metrics,
    registrations,
    reports,
    similarity,
    workflows,
)
from app.core.config import settings
from app.core.exceptions import APIError
from app.core.middleware import request_logging_middleware
from app.db.init_seed import seed_initial_data
from app.db.session import SessionLocal
from app.jobs.scheduler import start_scheduler, stop_scheduler
from app.logging.logger import app_logger, configure_logging, log_error, log_info


app = FastAPI(title=settings.app_name)
configure_logging()
logger = app_logger("app.main")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Path(settings.uploads_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.backups_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.reports_dir).mkdir(parents=True, exist_ok=True)
    db = SessionLocal()
    try:
        seed_initial_data(db)
    finally:
        db.close()
    start_scheduler()
    log_info(logger, event="application_started", category="operational", context={"env": settings.app_env})


@app.on_event("shutdown")
def on_shutdown() -> None:
    stop_scheduler()
    log_info(logger, event="application_stopped", category="operational", context={"env": settings.app_env})


app.middleware("http")(request_logging_middleware)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(registrations.router)
app.include_router(checklists.router)
app.include_router(materials.router)
app.include_router(workflows.router)
app.include_router(finance.router)
app.include_router(metrics.router)
app.include_router(alerts.router)
app.include_router(reports.router)
app.include_router(backups.router)
app.include_router(similarity.router)
app.include_router(admin.router)
app.include_router(audit.router)


@app.exception_handler(APIError)
async def handle_api_error(_: Request, exc: APIError):
    return JSONResponse(status_code=exc.status_code, content=error_response(code=exc.code, msg=exc.message, data=None))


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=error_response(code=422, msg="Validation error", data={"errors": exc.errors()}),
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(_: Request, exc: Exception):
    log_error(logger, event="unhandled_exception", category="operational", context={"error": str(exc)})
    return JSONResponse(status_code=500, content=error_response(code=500, msg="Internal server error", data=None))
