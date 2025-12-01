"""Background worker for notification processing."""
import asyncio
import structlog
from datetime import datetime, timedelta

from app.database import AsyncSessionLocal
from app.scheduling.planner import NotificationPlanner
from app.scheduling.jobs import execute_notification_job
from app.llm.client import LLMClient
from app.core.config import settings

logger = structlog.get_logger(__name__)


class NotificationWorker:
    """Background worker for processing notifications."""
    
    def __init__(self):
        # Use local LLM (Ollama) - no API key needed
        local_url = getattr(settings, 'LLM_LOCAL_URL', 'http://localhost:11434/v1')
        self.llm_client = LLMClient(
            api_key=None,  # No API key needed for local
            base_url=local_url,
            model=settings.LLM_MODEL,
            provider="local"
        )
        self.planner = NotificationPlanner(self.llm_client)
        self.running = False
    
    async def start(self):
        """Start the worker."""
        self.running = True
        logger.info("Notification worker started")
        
        while self.running:
            try:
                await self._process_pending_notifications()
                await self._plan_new_notifications()
                await asyncio.sleep(60)  # Run every minute
            except Exception as e:
                logger.error("Worker error", error=str(e))
                await asyncio.sleep(30)  # Wait before retrying
    
    async def stop(self):
        """Stop the worker."""
        self.running = False
        logger.info("Notification worker stopped")
    
    async def _process_pending_notifications(self):
        """Process notifications that are due to be sent."""
        async with AsyncSessionLocal() as db:
            from app.models import Notification, User, Event
            from sqlalchemy import select, and_
            
            # Get notifications that are due
            now = datetime.utcnow()
            due_notifications = await db.execute(
                select(Notification)
                .join(User)
                .join(Event)
                .where(
                    and_(
                        Notification.status == "planned",
                        Notification.plan_time <= now
                    )
                )
            )
            
            notifications = due_notifications.scalars().all()
            
            for notification in notifications:
                try:
                    # Get user and event data
                    user_result = await db.execute(
                        select(User).where(User.id == notification.user_id)
                    )
                    user = user_result.scalar_one_or_none()
                    
                    event_result = await db.execute(
                        select(Event).where(Event.id == notification.event_id)
                    )
                    event = event_result.scalar_one_or_none()
                    
                    if not user or not event:
                        logger.warning(
                            "Missing user or event for notification",
                            notification_id=notification.id
                        )
                        continue
                    
                    # Prepare job data
                    job_data = {
                        "notification_id": str(notification.id),
                        "user_id": str(user.id),
                        "event_id": str(event.id),
                        "channel": notification.channel,
                        "event": {
                            "id": str(event.id),
                            "title": event.title,
                            "start_ts": event.start_ts.isoformat(),
                            "end_ts": event.end_ts.isoformat(),
                            "location": event.location,
                            "conf_link": event.conf_link,
                            "organizer": event.organizer,
                            "attendees": event.attendees or [],
                            "description": event.description
                        },
                        "user": {
                            "id": str(user.id),
                            "name": user.name,
                            "email": user.email,
                            "phone_e164": user.phone_e164,
                            "timezone": user.timezone
                        },
                        "notification": notification.payload or {}
                    }
                    
                    # Execute the notification
                    result = await execute_notification_job(job_data)
                    
                    # Update notification status
                    notification.status = result.get("status", "failed")
                    notification.sent_time = datetime.utcnow()
                    notification.result = result
                    notification.attempts += 1
                    
                    if result.get("status") == "failed":
                        notification.error = result.get("error", "Unknown error")
                    
                    await db.commit()
                    
                    logger.info(
                        "Notification processed",
                        notification_id=notification.id,
                        status=notification.status
                    )
                    
                except Exception as e:
                    logger.error(
                        "Failed to process notification",
                        notification_id=notification.id,
                        error=str(e)
                    )
                    
                    # Update notification with error
                    notification.status = "failed"
                    notification.error = str(e)
                    notification.attempts += 1
                    await db.commit()
    
    async def _plan_new_notifications(self):
        """Plan notifications for new events."""
        async with AsyncSessionLocal() as db:
            from app.models import User, Event
            from sqlalchemy import select, and_
            
            # Get users with recent events that might need planning
            recent_cutoff = datetime.utcnow() - timedelta(hours=1)
            
            users_result = await db.execute(
                select(User).where(
                    User.updated_at >= recent_cutoff
                )
            )
            users = users_result.scalars().all()
            
            for user in users:
                try:
                    # Plan notifications for this user
                    result = await self.planner.plan_user_notifications(
                        db=db,
                        user_id=str(user.id)
                    )
                    
                    if result.get("notifications_planned", 0) > 0:
                        logger.info(
                            "Planned notifications for user",
                            user_id=user.id,
                            notifications_planned=result["notifications_planned"]
                        )
                        
                except Exception as e:
                    logger.error(
                        "Failed to plan notifications for user",
                        user_id=user.id,
                        error=str(e)
                    )


async def main():
    """Main worker entry point."""
    worker = NotificationWorker()
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
