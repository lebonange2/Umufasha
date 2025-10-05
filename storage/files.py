"""File storage for brainstorming sessions."""
import json
from pathlib import Path
from typing import Optional
from datetime import datetime
from brain.model import BrainstormSession
from utils.logging import get_logger

logger = get_logger('storage.files')


class FileStorage:
    """Handles file-based storage for sessions."""
    
    def __init__(self, base_dir: Path):
        """Initialize file storage.
        
        Args:
            base_dir: Base directory for storage
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.versions_dir = self.base_dir / "versions"
        self.versions_dir.mkdir(exist_ok=True)
        
        logger.info(f"File storage initialized: {self.base_dir}")
    
    def save_session(self, session: BrainstormSession, filename: str = "ledger.json") -> bool:
        """Save session to JSON file.
        
        Args:
            session: Session to save
            filename: Filename for the ledger
            
        Returns:
            True if successful
        """
        try:
            filepath = self.base_dir / filename
            
            # Update timestamp
            session.updated_at = datetime.now()
            
            # Convert to dict
            data = session.to_dict()
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Session saved to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            return False
    
    def load_session(self, filename: str = "ledger.json") -> Optional[BrainstormSession]:
        """Load session from JSON file.
        
        Args:
            filename: Filename of the ledger
            
        Returns:
            Loaded session or None
        """
        try:
            filepath = self.base_dir / filename
            
            if not filepath.exists():
                logger.warning(f"Session file not found: {filepath}")
                return None
            
            # Read file
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert from dict
            session = BrainstormSession.from_dict(data)
            
            logger.info(f"Session loaded from {filepath}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return None
    
    def create_snapshot(self, session: BrainstormSession) -> bool:
        """Create a versioned snapshot of the session.
        
        Args:
            session: Session to snapshot
            
        Returns:
            True if successful
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"snapshot_{timestamp}.json"
            filepath = self.versions_dir / filename
            
            # Save snapshot
            data = session.to_dict()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Snapshot created: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create snapshot: {e}")
            return False
    
    def list_snapshots(self) -> list:
        """List all available snapshots.
        
        Returns:
            List of snapshot filenames
        """
        try:
            snapshots = sorted(self.versions_dir.glob("snapshot_*.json"))
            return [s.name for s in snapshots]
        except Exception as e:
            logger.error(f"Failed to list snapshots: {e}")
            return []
    
    def load_snapshot(self, filename: str) -> Optional[BrainstormSession]:
        """Load a specific snapshot.
        
        Args:
            filename: Snapshot filename
            
        Returns:
            Loaded session or None
        """
        try:
            filepath = self.versions_dir / filename
            
            if not filepath.exists():
                logger.warning(f"Snapshot not found: {filepath}")
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            session = BrainstormSession.from_dict(data)
            logger.info(f"Snapshot loaded: {filename}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to load snapshot: {e}")
            return None
    
    def get_file_path(self, filename: str) -> Path:
        """Get full path for a file.
        
        Args:
            filename: Filename
            
        Returns:
            Full path
        """
        return self.base_dir / filename
    
    def exists(self, filename: str = "ledger.json") -> bool:
        """Check if a file exists.
        
        Args:
            filename: Filename to check
            
        Returns:
            True if exists
        """
        return (self.base_dir / filename).exists()
