"""Session storage for debate sessions."""
import json
from pathlib import Path
from typing import Optional
from app.product_debate.models import DebateSession
import structlog

logger = structlog.get_logger(__name__)


class SessionStorage:
    """Manages storage of debate sessions."""
    
    def __init__(self, base_dir: str = "sessions"):
        """Initialize storage.
        
        Args:
            base_dir: Base directory for session storage
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def save_session(self, session: DebateSession) -> None:
        """Save a debate session.
        
        Args:
            session: Debate session to save
        """
        session_dir = self.base_dir / session.session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Save main session file
        session_file = session_dir / "session.json"
        with open(session_file, "w") as f:
            json.dump(session.to_dict(), f, indent=2)
        
        logger.info("Session saved", session_id=session.session_id, path=str(session_file))
    
    def load_session(self, session_id: str) -> Optional[DebateSession]:
        """Load a debate session.
        
        Args:
            session_id: Session ID to load
            
        Returns:
            DebateSession or None if not found
        """
        session_file = self.base_dir / session_id / "session.json"
        
        if not session_file.exists():
            return None
        
        try:
            with open(session_file, "r") as f:
                data = json.load(f)
            return DebateSession.from_dict(data)
        except Exception as e:
            logger.error("Failed to load session", session_id=session_id, error=str(e))
            return None
    
    def list_sessions(self) -> list[str]:
        """List all session IDs.
        
        Returns:
            List of session IDs
        """
        sessions = []
        for session_dir in self.base_dir.iterdir():
            if session_dir.is_dir() and (session_dir / "session.json").exists():
                sessions.append(session_dir.name)
        return sorted(sessions, reverse=True)  # Most recent first
    
    def get_session_path(self, session_id: str) -> Path:
        """Get the directory path for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Path to session directory
        """
        return self.base_dir / session_id

