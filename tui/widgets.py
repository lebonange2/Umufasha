"""Custom widgets for the TUI."""
from textual.widgets import Static, RichLog, Label
from textual.containers import Container, Vertical, Horizontal
from rich.text import Text
from rich.panel import Panel
from typing import List, Optional
from brain.model import Idea, ActionItem, Cluster


class AudioLevelMeter(Static):
    """Visual audio level meter."""
    
    def __init__(self, **kwargs):
        super().__init__("", **kwargs)
        self.level = 0.0
    
    def set_level(self, level: float):
        """Set audio level (0.0-1.0)."""
        self.level = max(0.0, min(1.0, level))
        self.update_display()
    
    def update_display(self):
        """Update the visual display."""
        width = 20
        filled = int(self.level * width)
        bar = "█" * filled + "░" * (width - filled)
        
        # Color based on level
        if self.level > 0.7:
            color = "red"
        elif self.level > 0.4:
            color = "yellow"
        else:
            color = "green"
        
        text = Text(f"[{bar}]", style=color)
        self.update(text)


class TranscriptPanel(Vertical):
    """Panel for displaying transcript."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rich_log: Optional[RichLog] = None
    
    def compose(self):
        """Compose the widget."""
        yield Static("📝 Transcript", classes="panel-title")
        self.rich_log = RichLog(highlight=True, markup=True)
        yield self.rich_log
    
    def add_entry(self, speaker: str, text: str, timestamp: str = ""):
        """Add a transcript entry."""
        if not self.rich_log:
            return
        
        if speaker == "user":
            icon = "👤"
            style = "cyan"
        else:
            icon = "🤖"
            style = "magenta"
        
        time_str = f"[dim]{timestamp}[/dim] " if timestamp else ""
        self.rich_log.write(f"{time_str}{icon} [bold {style}]{speaker.title()}:[/bold {style}] {text}")
    
    def clear(self):
        """Clear the transcript."""
        if self.rich_log:
            self.rich_log.clear()


class AssistantPanel(Vertical):
    """Panel for displaying assistant responses."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rich_log: Optional[RichLog] = None
    
    def compose(self):
        """Compose the widget."""
        yield Static("🤖 Assistant", classes="panel-title")
        self.rich_log = RichLog(highlight=True, markup=True)
        yield self.rich_log
    
    def add_response(self, text: str):
        """Add an assistant response."""
        if self.rich_log:
            self.rich_log.write(text)
    
    def clear(self):
        """Clear the panel."""
        if self.rich_log:
            self.rich_log.clear()


class OrganizerPanel(Vertical):
    """Panel for displaying organized ideas, clusters, and actions."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rich_log: Optional[RichLog] = None
    
    def compose(self):
        """Compose the widget."""
        yield Static("🗂️ Organizer", classes="panel-title")
        self.rich_log = RichLog(highlight=True, markup=True)
        yield self.rich_log
    
    def update_content(self, ideas: List[Idea], clusters: List[Cluster], 
                      actions: List[ActionItem]):
        """Update the organizer content."""
        if not self.rich_log:
            return
        
        self.rich_log.clear()
        
        # Key Ideas
        key_ideas = [i for i in ideas if i.promoted and i.merged_into is None]
        if key_ideas:
            self.rich_log.write("[bold yellow]🌟 Key Ideas[/bold yellow]")
            for idea in key_ideas[:5]:  # Show top 5
                tags_str = f" [dim]`{', '.join(idea.tags)}`[/dim]" if idea.tags else ""
                self.rich_log.write(f"  • {idea.text[:80]}{tags_str}")
            self.rich_log.write("")
        
        # Recent Ideas
        recent_ideas = [i for i in ideas if not i.promoted and i.merged_into is None][-5:]
        if recent_ideas:
            self.rich_log.write("[bold cyan]💡 Recent Ideas[/bold cyan]")
            for idea in recent_ideas:
                tags_str = f" [dim]`{', '.join(idea.tags)}`[/dim]" if idea.tags else ""
                icon = "🤖" if idea.source.value == "assistant" else "👤"
                self.rich_log.write(f"  {icon} {idea.text[:80]}{tags_str}")
            self.rich_log.write("")
        
        # Clusters
        if clusters:
            self.rich_log.write("[bold green]🗂️ Clusters[/bold green]")
            for cluster in clusters[-3:]:  # Show last 3
                self.rich_log.write(f"  📁 [bold]{cluster.name}[/bold] ({len(cluster.idea_ids)} ideas)")
            self.rich_log.write("")
        
        # Active Actions
        active_actions = [a for a in actions if not a.completed]
        if active_actions:
            self.rich_log.write("[bold magenta]✅ Action Items[/bold magenta]")
            for action in active_actions[:5]:  # Show top 5
                priority_emoji = {
                    "urgent": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(action.priority.value, "⚪")
                self.rich_log.write(f"  {priority_emoji} {action.text[:80]}")
    
    def clear(self):
        """Clear the panel."""
        if self.rich_log:
            self.rich_log.clear()


class StatusBar(Horizontal):
    """Status bar showing system state."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.project_label: Optional[Label] = None
        self.stt_label: Optional[Label] = None
        self.llm_label: Optional[Label] = None
        self.recording_label: Optional[Label] = None
        self.save_label: Optional[Label] = None
    
    def compose(self):
        """Compose the widget."""
        self.project_label = Label("Project: default")
        self.stt_label = Label("STT: whisper")
        self.llm_label = Label("LLM: openai")
        self.recording_label = Label("⏸️  Idle")
        self.save_label = Label("💾 Saved")
        
        yield self.project_label
        yield Static(" | ")
        yield self.stt_label
        yield Static(" | ")
        yield self.llm_label
        yield Static(" | ")
        yield self.recording_label
        yield Static(" | ")
        yield self.save_label
    
    def update_project(self, name: str):
        """Update project name."""
        if self.project_label:
            self.project_label.update(f"Project: {name}")
    
    def update_stt(self, backend: str):
        """Update STT backend."""
        if self.stt_label:
            self.stt_label.update(f"STT: {backend}")
    
    def update_llm(self, backend: str):
        """Update LLM backend."""
        if self.llm_label:
            self.llm_label.update(f"LLM: {backend}")
    
    def set_recording(self, recording: bool):
        """Set recording state."""
        if self.recording_label:
            if recording:
                self.recording_label.update("🔴 Recording")
            else:
                self.recording_label.update("⏸️  Idle")
    
    def set_save_status(self, saved: bool, time_until_next: Optional[float] = None):
        """Set save status."""
        if self.save_label:
            if saved:
                if time_until_next is not None:
                    self.save_label.update(f"💾 Saved ({int(time_until_next)}s)")
                else:
                    self.save_label.update("💾 Saved")
            else:
                self.save_label.update("💾 Saving...")


class HelpOverlay(Container):
    """Help overlay showing keybindings."""
    
    def compose(self):
        """Compose the widget."""
        help_text = """
[bold cyan]Brainstorming Assistant - Help[/bold cyan]

[bold yellow]Recording:[/bold yellow]
  [bold]Click Button[/bold] - Click 'Start Recording' button to record
  [bold]R[/bold]            - Toggle recording on/off
  [bold]Or[/bold]          - Click button again to stop

[bold yellow]Commands:[/bold yellow]
  [bold]:[/bold]         - Open command palette
  [bold]/[/bold]         - Search ideas
  [bold]?[/bold]         - Show this help
{{ ... }}

[bold yellow]Navigation:[/bold yellow]
  [bold]↑/↓[/bold]       - Scroll panels
  [bold]Tab[/bold]       - Switch focus
  [bold]E[/bold]         - Edit selected item

[bold yellow]Commands:[/bold yellow]
  :tag <id> <tags>      - Tag an idea
  :del <id>             - Delete an idea
  :promote <id>         - Promote to key idea
  :todo <text>          - Add action item
  :summarize [scope]    - Generate summary
  :search <query>       - Search ideas
  :export <format>      - Export (md|docx|csv)
  :config               - Show configuration
  :save                 - Save now

[bold]Press any key to close[/bold]
"""
        yield Static(help_text, classes="modal-dialog")
