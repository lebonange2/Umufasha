"""Main TUI application using Textual."""
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Input, Button
from textual.binding import Binding
from textual.reactive import reactive
from typing import Optional, Callable
from datetime import datetime

from tui.widgets import (
    TranscriptPanel, AssistantPanel, OrganizerPanel,
    StatusBar, AudioLevelMeter, HelpOverlay
)
from brain.model import BrainstormSession
from utils.logging import get_logger

logger = get_logger('tui')


class BrainstormApp(App):
    """Main brainstorming TUI application."""
    
    CSS_PATH = "app.tcss"
    
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("?", "help", "Help", show=True),
        Binding("r", "toggle_recording", "Record", show=True),
        Binding("colon", "command", "Command", show=True),
        Binding("slash", "search", "Search", show=True),
        Binding("ctrl+s", "save", "Save", show=True),
        Binding("f2", "config", "Config", show=False),
    ]
    
    TITLE = "🧠 Brainstorming Assistant"
    
    # Reactive state
    is_recording = reactive(False)
    audio_level = reactive(0.0)
    
    def __init__(self, session: BrainstormSession, config, **kwargs):
        """Initialize the app.
        
        Args:
            session: Brainstorming session
            config: Configuration object
            **kwargs: Additional arguments
        """
        super().__init__(**kwargs)
        self.session = session
        self.config = config
        
        # Widgets
        self.transcript_panel: Optional[TranscriptPanel] = None
        self.assistant_panel: Optional[AssistantPanel] = None
        self.organizer_panel: Optional[OrganizerPanel] = None
        self.status_bar: Optional[StatusBar] = None
        self.audio_meter: Optional[AudioLevelMeter] = None
        self.command_input: Optional[Input] = None
        self.record_button: Optional[Button] = None
        
        # Callbacks
        self.on_record_start: Optional[Callable] = None
        self.on_record_stop: Optional[Callable] = None
        self.on_command: Optional[Callable[[str], None]] = None
        self.on_search: Optional[Callable[[str], None]] = None
        
        # State
        self.show_help_overlay = False
        self.command_mode = False
        
        logger.info("TUI app initialized")
    
    def compose(self) -> ComposeResult:
        """Compose the UI."""
        yield Header()
        
        # Main container
        with Container(id="main-container"):
            # Left panel (transcript + assistant)
            with Vertical(id="left-panel"):
                self.transcript_panel = TranscriptPanel(id="transcript-panel")
                yield self.transcript_panel
                
                self.assistant_panel = AssistantPanel(id="assistant-panel")
                yield self.assistant_panel
            
            # Right panel (organizer)
            with Vertical(id="right-panel"):
                self.organizer_panel = OrganizerPanel(id="organizer-panel")
                yield self.organizer_panel
        
        # Control bar with record button
        with Horizontal(id="control-bar"):
            self.record_button = Button("🎤 Start Recording", id="record-button", variant="success")
            yield self.record_button
            
            yield Static(" ", classes="spacer")
            
            self.audio_meter = AudioLevelMeter(id="audio-level")
            yield self.audio_meter
        
        # Status bar
        with Horizontal(id="status-bar"):
            self.status_bar = StatusBar()
            yield self.status_bar
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when app is mounted."""
        # Update status bar
        if self.status_bar:
            self.status_bar.update_project(self.session.project_name)
            self.status_bar.update_stt(self.config.stt_backend)
            self.status_bar.update_llm(self.config.llm_backend)
        
        # Initial organizer update
        self.update_organizer()
        
        logger.info("TUI mounted")
    
    def action_quit(self) -> None:
        """Quit the application."""
        logger.info("Quit requested")
        self.exit()
    
    def action_help(self) -> None:
        """Show help overlay."""
        self.show_help_overlay = not self.show_help_overlay
        if self.show_help_overlay:
            self.push_screen(HelpOverlay())
    
    def action_toggle_recording(self) -> None:
        """Toggle recording on/off."""
        if not self.is_recording:
            self._start_recording()
        else:
            self._stop_recording()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "record-button":
            self.action_toggle_recording()
    
    def _start_recording(self) -> None:
        """Start recording."""
        if self.is_recording:
            return
        
        self.is_recording = True
        
        # Update button
        if self.record_button:
            self.record_button.label = "⏹️ Stop Recording"
            self.record_button.variant = "error"
        
        # Update status bar
        if self.status_bar:
            self.status_bar.set_recording(True)
        
        if self.on_record_start:
            self.on_record_start()
        
        logger.info("Recording started")
    
    def _stop_recording(self) -> None:
        """Stop recording."""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        # Update button
        if self.record_button:
            self.record_button.label = "🎤 Start Recording"
            self.record_button.variant = "success"
        
        # Update status bar
        if self.status_bar:
            self.status_bar.set_recording(False)
        
        if self.on_record_stop:
            self.on_record_stop()
        
        logger.info("Recording stopped")
    
    def action_command(self) -> None:
        """Open command input."""
        self.command_mode = True
        
        # Create command input
        if not self.command_input:
            self.command_input = Input(placeholder="Enter command...", classes="command-input")
            self.command_input.focus()
        
        # Show command input (would need modal implementation)
        logger.info("Command mode activated")
    
    def action_search(self) -> None:
        """Open search input."""
        logger.info("Search mode activated")
    
    def action_save(self) -> None:
        """Trigger manual save."""
        if self.on_command:
            self.on_command("save")
        logger.info("Manual save triggered")
    
    def action_config(self) -> None:
        """Show configuration."""
        if self.on_command:
            self.on_command("config")
    
    # Public methods for updating UI
    
    def add_transcript(self, speaker: str, text: str):
        """Add a transcript entry.
        
        Args:
            speaker: "user" or "assistant"
            text: Transcript text
        """
        if self.transcript_panel:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.transcript_panel.add_entry(speaker, text, timestamp)
    
    def add_assistant_response(self, text: str):
        """Add an assistant response.
        
        Args:
            text: Response text
        """
        if self.assistant_panel:
            self.assistant_panel.add_response(text)
    
    def update_organizer(self):
        """Update the organizer panel."""
        if self.organizer_panel:
            self.organizer_panel.update_content(
                self.session.ideas,
                self.session.clusters,
                self.session.actions
            )
    
    def set_audio_level(self, level: float):
        """Set audio level meter.
        
        Args:
            level: Audio level (0.0-1.0)
        """
        self.audio_level = level
        if self.audio_meter:
            self.audio_meter.set_level(level)
    
    def update_save_status(self, time_until_next: Optional[float] = None):
        """Update save status.
        
        Args:
            time_until_next: Seconds until next autosave
        """
        if self.status_bar:
            self.status_bar.set_save_status(True, time_until_next)
    
    def show_message(self, message: str, message_type: str = "info"):
        """Show a status message.
        
        Args:
            message: Message text
            message_type: "info", "success", "error"
        """
        # Would display in a notification area
        logger.info(f"Message ({message_type}): {message}")
        
        # For now, add to assistant panel
        if self.assistant_panel:
            if message_type == "error":
                styled = f"[bold red]❌ {message}[/bold red]"
            elif message_type == "success":
                styled = f"[bold green]✅ {message}[/bold green]"
            else:
                styled = f"[bold cyan]ℹ️  {message}[/bold cyan]"
            
            self.assistant_panel.add_response(styled)
    
    def execute_command(self, command: str):
        """Execute a command.
        
        Args:
            command: Command string
        """
        if self.on_command:
            self.on_command(command)
        
        self.command_mode = False
    
    # Callback setters
    
    def set_record_callbacks(self, on_start: Callable, on_stop: Callable):
        """Set recording callbacks.
        
        Args:
            on_start: Callback for recording start
            on_stop: Callback for recording stop
        """
        self.on_record_start = on_start
        self.on_record_stop = on_stop
    
    def set_command_callback(self, callback: Callable[[str], None]):
        """Set command callback.
        
        Args:
            callback: Callback for commands
        """
        self.on_command = callback
    
    def set_search_callback(self, callback: Callable[[str], None]):
        """Set search callback.
        
        Args:
            callback: Callback for search
        """
        self.on_search = callback
