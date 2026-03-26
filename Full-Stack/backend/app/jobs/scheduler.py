from apscheduler.schedulers.background import BackgroundScheduler

from app.db.session import SessionLocal
from app.services.backup_service import create_local_backup
from app.services.metrics_service import compute_and_store_metrics


scheduler = BackgroundScheduler(timezone="UTC")


def run_daily_backup() -> None:
    db = SessionLocal()
    try:
        create_local_backup(db, triggered_by=None)
    finally:
        db.close()


def run_metrics_job() -> None:
    db = SessionLocal()
    try:
        compute_and_store_metrics(db)
    finally:
        db.close()


def start_scheduler() -> None:
    if not scheduler.running:
        scheduler.add_job(run_daily_backup, "interval", hours=24, id="daily_backup", replace_existing=True)
        scheduler.add_job(run_metrics_job, "interval", hours=1, id="metrics_job", replace_existing=True)
        scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
