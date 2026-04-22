"""
Scheduled cleanup service.
Deletes uploaded audio files older than FILE_CLEANUP_HOURS (default 24h).
Uses APScheduler to run in the background when the Flask app starts.
"""
import os
import time
import logging
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)


def delete_old_files(folder: str, max_age_hours: int = 24):
    """Remove files in `folder` that are older than `max_age_hours`."""
    if not os.path.isdir(folder):
        return

    cutoff = time.time() - (max_age_hours * 3600)
    removed = 0

    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)
        try:
            if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff:
                os.remove(filepath)
                removed += 1
        except OSError as e:
            logger.warning("Could not delete %s: %s", filepath, e)

    if removed:
        logger.info("Cleanup: removed %d old file(s) from %s", removed, folder)


def start_cleanup_scheduler(upload_folder: str, max_age_hours: int = 24):
    """
    Start a background scheduler that runs cleanup every hour.
    Call this once during app startup.
    """
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(
        func=delete_old_files,
        args=[upload_folder, max_age_hours],
        trigger="interval",
        hours=1,
        id="audio_cleanup",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Audio cleanup scheduler started (max age: %dh).", max_age_hours)
    return scheduler
