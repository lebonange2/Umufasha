#!/usr/bin/env python3
"""Seed script to create demo data for testing."""
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal
from app.models import User, Event, Rule
from app.core.config import settings


async def create_demo_user():
    """Create a demo user with sample data."""
    async with AsyncSessionLocal() as db:
        # Create demo user
        user = User(
            name="Demo User",
            email="demo@example.com",
            phone_e164="+1234567890",
            timezone="America/New_York",
            channel_pref="both",
            quiet_start="21:00",
            quiet_end="07:00",
            max_call_attempts=3,
            weekend_policy="email",
            escalation_threshold=60,
            locale="en",
            voice="Polly.Joanna"
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        print(f"Created demo user: {user.name} ({user.email})")
        
        # Create sample events
        now = datetime.utcnow()
        
        # Event 1: Tomorrow morning
        event1 = Event(
            user_id=user.id,
            provider="google",
            provider_event_id="demo-event-1",
            title="Team Standup",
            start_ts=now + timedelta(days=1, hours=9),
            end_ts=now + timedelta(days=1, hours=9, minutes=30),
            location="Conference Room A",
            conf_link="https://meet.google.com/demo-standup",
            organizer="manager@company.com",
            attendees=[
                {"email": "demo@example.com", "name": "Demo User", "responseStatus": "accepted"},
                {"email": "colleague@company.com", "name": "Colleague", "responseStatus": "accepted"}
            ],
            description="Daily team standup meeting",
            status="confirmed",
            etag="demo-etag-1",
            hash="demo-hash-1"
        )
        
        # Event 2: This afternoon (urgent)
        event2 = Event(
            user_id=user.id,
            provider="google",
            provider_event_id="demo-event-2",
            title="Client Call",
            start_ts=now + timedelta(hours=2),
            end_ts=now + timedelta(hours=2, minutes=30),
            location="Virtual",
            conf_link="https://meet.google.com/demo-client",
            organizer="client@company.com",
            attendees=[
                {"email": "demo@example.com", "name": "Demo User", "responseStatus": "accepted"},
                {"email": "client@company.com", "name": "Client", "responseStatus": "accepted"}
            ],
            description="Important client call",
            status="confirmed",
            etag="demo-etag-2",
            hash="demo-hash-2"
        )
        
        # Event 3: Next week
        event3 = Event(
            user_id=user.id,
            provider="google",
            provider_event_id="demo-event-3",
            title="Project Review",
            start_ts=now + timedelta(days=7, hours=14),
            end_ts=now + timedelta(days=7, hours=15),
            location="Board Room",
            organizer="director@company.com",
            attendees=[
                {"email": "demo@example.com", "name": "Demo User", "responseStatus": "accepted"},
                {"email": "director@company.com", "name": "Director", "responseStatus": "accepted"}
            ],
            description="Monthly project review meeting",
            status="confirmed",
            etag="demo-etag-3",
            hash="demo-hash-3"
        )
        
        db.add_all([event1, event2, event3])
        await db.commit()
        
        print(f"Created {3} demo events")
        
        # Create sample rules
        rule1 = Rule(
            user_id=user.id,
            rule_type="vip_organizer",
            rule_json={
                "organizers": ["director@company.com", "ceo@company.com"],
                "action": "always_call"
            },
            enabled=True,
            priority=10
        )
        
        rule2 = Rule(
            user_id=user.id,
            rule_type="internal_meeting",
            rule_json={
                "keywords": ["standup", "team", "internal"],
                "action": "email_only"
            },
            enabled=True,
            priority=5
        )
        
        rule3 = Rule(
            user_id=user.id,
            rule_type="travel_buffer",
            rule_json={
                "buffer_minutes": 20,
                "action": "add_travel_time"
            },
            enabled=True,
            priority=1
        )
        
        db.add_all([rule1, rule2, rule3])
        await db.commit()
        
        print(f"Created {3} demo rules")
        
        return user


async def main():
    """Main function to seed demo data."""
    print("Seeding demo data...")
    
    try:
        user = await create_demo_user()
        print(f"\nDemo data created successfully!")
        print(f"User ID: {user.id}")
        print(f"Email: {user.email}")
        print(f"Phone: {user.phone_e164}")
        print(f"\nYou can now:")
        print(f"1. Go to http://localhost:8000/admin")
        print(f"2. Login with admin:admin123")
        print(f"3. View the demo user and events")
        print(f"4. Test notifications")
        
    except Exception as e:
        print(f"Error creating demo data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
