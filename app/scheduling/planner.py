"""Notification planner using LLM policy."""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import structlog

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models import User, Event, Notification, Rule
from app.llm.policy import PolicyAgent
from app.llm.client import LLMClient
from app.schemas import PolicyRequest

logger = structlog.get_logger(__name__)


class NotificationPlanner:
    """Plans notifications using LLM policy agent."""
    
    def __init__(self, llm_client: LLMClient):
        self.policy_agent = PolicyAgent(llm_client)
    
    async def plan_user_notifications(
        self,
        db: AsyncSession,
        user_id: str,
        event_id: Optional[str] = None,
        force_replan: bool = False
    ) -> Dict[str, Any]:
        """Plan notifications for a user's events.
        
        Args:
            db: Database session
            user_id: User ID
            event_id: Optional specific event ID
            force_replan: Force replanning even if notifications exist
            
        Returns:
            Planning result
        """
        try:
            # Get user
            user_result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                return {"error": "User not found"}
            
            # Get events to plan for
            if event_id:
                # Plan for specific event
                event_result = await db.execute(
                    select(Event).where(
                        and_(Event.id == event_id, Event.user_id == user_id)
                    )
                )
                events = [event_result.scalar_one_or_none()] if event_result.scalar_one_or_none() else []
            else:
                # Plan for all upcoming events
                now = datetime.utcnow()
                future_cutoff = now + timedelta(days=30)
                
                events_result = await db.execute(
                    select(Event).where(
                        and_(
                            Event.user_id == user_id,
                            Event.start_ts > now,
                            Event.start_ts <= future_cutoff,
                            Event.status == "confirmed"
                        )
                    )
                )
                events = events_result.scalars().all()
            
            # Filter out events that already have notifications (unless force_replan)
            events_to_plan = []
            for event in events:
                if not event:
                    continue
                
                if force_replan:
                    events_to_plan.append(event)
                else:
                    # Check if notifications already exist
                    existing_result = await db.execute(
                        select(Notification).where(
                            and_(
                                Notification.user_id == user_id,
                                Notification.event_id == event.id
                            )
                        )
                    )
                    existing_notifications = existing_result.scalars().all()
                    
                    if not existing_notifications:
                        events_to_plan.append(event)
            
            # Plan notifications for each event
            total_planned = 0
            planning_results = []
            
            for event in events_to_plan:
                result = await self._plan_event_notifications(db, user, event)
                planning_results.append(result)
                total_planned += result.get("notifications_planned", 0)
            
            return {
                "user_id": user_id,
                "events_processed": len(events_to_plan),
                "notifications_planned": total_planned,
                "results": planning_results
            }
            
        except Exception as e:
            logger.error("Notification planning failed", user_id=user_id, error=str(e))
            return {"error": str(e)}
    
    async def _plan_event_notifications(
        self,
        db: AsyncSession,
        user: User,
        event: Event
    ) -> Dict[str, Any]:
        """Plan notifications for a specific event."""
        try:
            # Get user rules
            rules_result = await db.execute(
                select(Rule).where(
                    and_(Rule.user_id == user.id, Rule.enabled == True)
                ).order_by(Rule.priority.desc())
            )
            rules = rules_result.scalars().all()
            
            # Build user preferences
            user_prefs = {
                "channel_pref": user.channel_pref,
                "quiet_start": user.quiet_start,
                "quiet_end": user.quiet_end,
                "max_call_attempts": user.max_call_attempts,
                "weekend_policy": user.weekend_policy,
                "escalation_threshold": user.escalation_threshold,
                "timezone": user.timezone,
                "rules": [{"type": rule.rule_type, "config": rule.rule_json} for rule in rules]
            }
            
            # Build event data
            event_data = {
                "id": str(event.id),
                "title": event.title,
                "start_ts": event.start_ts.isoformat(),
                "end_ts": event.end_ts.isoformat(),
                "location": event.location,
                "conf_link": event.conf_link,
                "organizer": event.organizer,
                "attendees": event.attendees or [],
                "description": event.description,
                "status": event.status
            }
            
            # Get notification history for this event
            history_result = await db.execute(
                select(Notification).where(
                    and_(
                        Notification.user_id == user.id,
                        Notification.event_id == event.id
                    )
                ).order_by(Notification.created_at.desc())
            )
            history = history_result.scalars().all()
            
            history_data = []
            for notif in history:
                history_data.append({
                    "channel": notif.channel,
                    "status": notif.status,
                    "sent_time": notif.sent_time.isoformat() if notif.sent_time else None,
                    "created_at": notif.created_at.isoformat()
                })
            
            # Create policy request
            policy_request = PolicyRequest(
                event=event_data,
                user_preferences=user_prefs,
                history=history_data,
                timezone=user.timezone
            )
            
            # Get policy decision
            policy_response = await self.policy_agent.plan_notifications(policy_request)
            
            if not policy_response.plan:
                return {
                    "event_id": str(event.id),
                    "notifications_planned": 0,
                    "reasoning": policy_response.reasoning
                }
            
            # Create notification records
            notifications_created = 0
            for plan_item in policy_response.plan:
                # Calculate execution time
                event_start = event.start_ts
                offset_minutes = plan_item["offset_minutes"]
                execute_at = event_start + timedelta(minutes=offset_minutes)
                
                # Skip if execution time is in the past
                if execute_at <= datetime.utcnow():
                    continue
                
                # Create notification record
                notification = Notification(
                    user_id=user.id,
                    event_id=event.id,
                    channel=plan_item["channel"],
                    plan_time=execute_at,
                    payload=plan_item,
                    status="planned"
                )
                
                db.add(notification)
                notifications_created += 1
            
            await db.commit()
            
            return {
                "event_id": str(event.id),
                "notifications_planned": notifications_created,
                "reasoning": policy_response.reasoning
            }
            
        except Exception as e:
            logger.error(
                "Event notification planning failed",
                user_id=user.id,
                event_id=event.id,
                error=str(e)
            )
            return {
                "event_id": str(event.id),
                "notifications_planned": 0,
                "error": str(e)
            }
    
    async def replan_event_notifications(
        self,
        db: AsyncSession,
        user_id: str,
        event_id: str
    ) -> Dict[str, Any]:
        """Replan notifications for a specific event (delete existing and create new)."""
        try:
            # Delete existing notifications for this event
            existing_result = await db.execute(
                select(Notification).where(
                    and_(
                        Notification.user_id == user_id,
                        Notification.event_id == event_id,
                        Notification.status == "planned"
                    )
                )
            )
            existing_notifications = existing_result.scalars().all()
            
            for notification in existing_notifications:
                await db.delete(notification)
            
            await db.commit()
            
            # Plan new notifications
            return await self.plan_user_notifications(
                db=db,
                user_id=user_id,
                event_id=event_id,
                force_replan=True
            )
            
        except Exception as e:
            logger.error(
                "Event notification replanning failed",
                user_id=user_id,
                event_id=event_id,
                error=str(e)
            )
            return {"error": str(e)}
