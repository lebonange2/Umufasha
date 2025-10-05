"""Autosave functionality for brainstorming sessions."""
import threading
import time
from pathlib import Path
from typing import Optional, Callable
from brain.model import BrainstormSession
from storage.files import FileStorage
from storage.exporters import MarkdownExporter
from utils.logging import get_logger

logger = get_logger('storage.autosave')


class AutoSaver:
    """Handles automatic saving of sessions."""
    
    def __init__(self, storage: FileStorage, interval: int = 30, 
                 export_markdown: bool = True, create_snapshots: bool = True):
        """Initialize autosaver.
        
        Args:
            storage: File storage instance
            interval: Save interval in seconds
            export_markdown: Also export to Markdown on save
            create_snapshots: Create version snapshots
        """
        self.storage = storage
        self.interval = interval
        self.export_markdown = export_markdown
        self.create_snapshots = create_snapshots
        
        self.session: Optional[BrainstormSession] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.last_save_time = 0.0
        self.save_callback: Optional[Callable] = None
        
        logger.info(f"AutoSaver initialized: interval={interval}s")
    
    def set_session(self, session: BrainstormSession):
        """Set the session to autosave.
        
        Args:
            session: Session to save
        """
        self.session = session
    
    def set_save_callback(self, callback: Callable):
        """Set callback to call after each save.
        
        Args:
            callback: Callback function
        """
        self.save_callback = callback
    
    def start(self):
        """Start autosaving."""
        if self.running:
            logger.warning("AutoSaver already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._autosave_loop, daemon=True)
        self.thread.start()
        logger.info("AutoSaver started")
    
    def stop(self):
        """Stop autosaving."""
        if not self.running:
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        logger.info("AutoSaver stopped")
    
    def save_now(self, create_snapshot: bool = False) -> bool:
        """Trigger an immediate save.
        
        Args:
            create_snapshot: Whether to create a snapshot
            
        Returns:
            True if successful
        """
        if not self.session:
            logger.warning("No session to save")
            return False
        
        try:
            # Save ledger
            success = self.storage.save_session(self.session)
            
            if success:
                self.last_save_time = time.time()
                
                # Export Markdown
                if self.export_markdown:
                    md_path = self.storage.get_file_path("notes.md")
                    MarkdownExporter.export(self.session, md_path)
                
                # Create snapshot if requested
                if create_snapshot and self.create_snapshots:
                    self.storage.create_snapshot(self.session)
                
                # Call callback
                if self.save_callback:
                    self.save_callback()
                
                logger.debug("Session saved successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Save failed: {e}")
            return False
    
    def _autosave_loop(self):
        """Main autosave loop."""
        while self.running:
            try:
                time.sleep(1)  # Check every second
                
                if not self.session:
                    continue
                
                # Check if it's time to save
                elapsed = time.time() - self.last_save_time
                if elapsed >= self.interval:
                    self.save_now()
                    
            except Exception as e:
                logger.error(f"AutoSave loop error: {e}")
    
    def get_time_since_last_save(self) -> float:
        """Get time since last save in seconds.
        
        Returns:
            Seconds since last save
        """
        if self.last_save_time == 0:
            return float('inf')
        return time.time() - self.last_save_time
    
    def get_time_until_next_save(self) -> float:
        """Get time until next save in seconds.
        
        Returns:
            Seconds until next save
        """
        elapsed = self.get_time_since_last_save()
        remaining = max(0, self.interval - elapsed)
        return remaining
