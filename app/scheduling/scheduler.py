"""Notification scheduler interface."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime


class NotificationScheduler(ABC):
    """Abstract base class for notification schedulers."""
    
    @abstractmethod
    def start(self) -> None:
        """Start the scheduler."""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop the scheduler."""
        pass
    
    @abstractmethod
    def schedule_notification(
        self,
        notification_id: str,
        execute_at: datetime,
        job_data: Dict[str, Any]
    ) -> bool:
        """Schedule a notification job.
        
        Args:
            notification_id: Unique notification ID
            execute_at: When to execute the job
            job_data: Job data including user_id, event_id, channel, etc.
            
        Returns:
            True if scheduled successfully
        """
        pass
    
    @abstractmethod
    def cancel_notification(self, notification_id: str) -> bool:
        """Cancel a scheduled notification.
        
        Args:
            notification_id: Notification ID to cancel
            
        Returns:
            True if cancelled successfully
        """
        pass
    
    @abstractmethod
    def reschedule_notification(
        self,
        notification_id: str,
        new_execute_at: datetime
    ) -> bool:
        """Reschedule a notification.
        
        Args:
            notification_id: Notification ID to reschedule
            new_execute_at: New execution time
            
        Returns:
            True if rescheduled successfully
        """
        pass
