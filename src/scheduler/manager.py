# src/scheduler/manager.py
"""APScheduler configuration and management."""
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.triggers.date import DateTrigger
from loguru import logger

from src.core.config import settings


class SchedulerManager:
    """Manages APScheduler lifecycle and job operations."""

    _instance: "SchedulerManager | None" = None

    def __init__(self):
        self.scheduler: AsyncIOScheduler | None = None

    @classmethod
    def get_instance(cls) -> "SchedulerManager":
        """Singleton access."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def setup(self) -> AsyncIOScheduler:
        """Initialize scheduler with job store."""
        jobstores = {
            "default": SQLAlchemyJobStore(url=settings.jobstore_url)
        }
        executors = {
            "default": ThreadPoolExecutor(10)
        }
        job_defaults = {
            "coalesce": True,  # Combine missed runs
            "max_instances": 1,
            "misfire_grace_time": 300  # 5 min grace
        }

        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults
        )
        return self.scheduler

    def start(self):
        """Start scheduler."""
        if self.scheduler:
            self.scheduler.start()
            logger.info("Scheduler started")

    def shutdown(self, wait: bool = True):
        """Shutdown scheduler."""
        if self.scheduler:
            self.scheduler.shutdown(wait=wait)
            logger.info("Scheduler shutdown")

    def add_reminder(
        self,
        job_id: str,
        run_at: datetime,
        user_id: int,
        task_id: int
    ):
        """Schedule a one-time reminder."""
        if not self.scheduler:
            raise RuntimeError("Scheduler not initialized")

        from src.scheduler.jobs.notify import send_reminder_job

        self.scheduler.add_job(
            send_reminder_job,
            trigger=DateTrigger(run_date=run_at),
            id=job_id,
            replace_existing=True,
            kwargs={"user_id": user_id, "task_id": task_id}
        )
        logger.info(f"Added reminder job {job_id} for {run_at}")

    def remove_job(self, job_id: str):
        """Remove scheduled job."""
        if self.scheduler:
            try:
                self.scheduler.remove_job(job_id)
                logger.info(f"Removed job {job_id}")
            except Exception:
                pass  # Job may not exist


def get_scheduler() -> SchedulerManager:
    """Get scheduler manager instance."""
    return SchedulerManager.get_instance()
