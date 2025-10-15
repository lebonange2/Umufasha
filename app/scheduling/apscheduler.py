"""APScheduler implementation of notification scheduler."""
from datetime import datetime
from typing import Dict, Any, Optional
import structlog

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from app.scheduling.scheduler import NotificationScheduler
from app.scheduling.jobs import execute_notification_job

logger = structlog.get_logger(__name__)


class APSchedulerScheduler(NotificationScheduler):
    """APScheduler-based notification scheduler."""
    
    def __init__(self):
        # Configure job stores
        jobstores = {
            'default': MemoryJobStore()
        }
        
        # Configure executors
        executors = {
            'default': AsyncIOExecutor()
        }
        
        # Configure job defaults
        job_defaults = {
            'coalesce': True,
            'max_instances': 1,
            'misfire_grace_time': 300  # 5 minutes
        }
        
        # Create scheduler
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC'
        )
        
        # Add event listeners
        self.scheduler.add_listener(self._job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._job_error, EVENT_JOB_ERROR)
    
    def start(self) -> None:
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("APScheduler started")
    
    def stop(self) -> None:
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("APScheduler stopped")
    
    def schedule_notification(
        self,
        notification_id: str,
        execute_at: datetime,
        job_data: Dict[str, Any]
    ) -> bool:
        """Schedule a notification job."""
        try:
            # Check if job already exists
            if self.scheduler.get_job(notification_id):
                logger.warning("Job already exists", notification_id=notification_id)
                return False
            
            # Schedule the job
            self.scheduler.add_job(
                func=execute_notification_job,
                trigger='date',
                run_date=execute_at,
                args=[job_data],
                id=notification_id,
                replace_existing=True
            )
            
            logger.info(
                "Notification scheduled",
                notification_id=notification_id,
                execute_at=execute_at
            )
            return True
            
        except Exception as e:
            logger.error(
                "Failed to schedule notification",
                notification_id=notification_id,
                error=str(e)
            )
            return False
    
    def cancel_notification(self, notification_id: str) -> bool:
        """Cancel a scheduled notification."""
        try:
            job = self.scheduler.get_job(notification_id)
            if job:
                job.remove()
                logger.info("Notification cancelled", notification_id=notification_id)
                return True
            else:
                logger.warning("Job not found for cancellation", notification_id=notification_id)
                return False
                
        except Exception as e:
            logger.error(
                "Failed to cancel notification",
                notification_id=notification_id,
                error=str(e)
            )
            return False
    
    def reschedule_notification(
        self,
        notification_id: str,
        new_execute_at: datetime
    ) -> bool:
        """Reschedule a notification."""
        try:
            job = self.scheduler.get_job(notification_id)
            if job:
                job.reschedule(trigger='date', run_date=new_execute_at)
                logger.info(
                    "Notification rescheduled",
                    notification_id=notification_id,
                    new_execute_at=new_execute_at
                )
                return True
            else:
                logger.warning("Job not found for rescheduling", notification_id=notification_id)
                return False
                
        except Exception as e:
            logger.error(
                "Failed to reschedule notification",
                notification_id=notification_id,
                error=str(e)
            )
            return False
    
    def _job_executed(self, event):
        """Handle job execution event."""
        logger.info(
            "Job executed",
            job_id=event.job_id,
            return_value=event.return_value
        )
    
    def _job_error(self, event):
        """Handle job error event."""
        logger.error(
            "Job failed",
            job_id=event.job_id,
            exception=str(event.exception),
            traceback=event.traceback
        )
    
    def get_scheduled_jobs(self) -> list:
        """Get list of scheduled jobs."""
        return self.scheduler.get_jobs()
    
    def get_job_count(self) -> int:
        """Get number of scheduled jobs."""
        return len(self.scheduler.get_jobs())
