"""APScheduler setup — background jobs for data sync."""
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.services.fetcher import fetch_all_active
from app.services.alerter import check_alerts

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def _fetch_and_alert_job():
    logger.info("Scheduled fetch + alert check started...")
    results = fetch_all_active()
    logger.info("Fetch done: %d snapshots stored.", len(results))
    check_alerts()
    logger.info("Alert check done.")


def start_scheduler(sync_interval_minutes: int = 60):
    scheduler.add_job(
        _fetch_and_alert_job,
        trigger=IntervalTrigger(minutes=sync_interval_minutes),
        id="fetch_and_alert",
        name="Fetch usage & check alerts",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started (sync+alert every %d minutes).", sync_interval_minutes)
