"""Main application entry point."""
import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional
import numpy as np

from utils.config import Config
from utils.logging import setup_logging, get_logger
from brain.model import BrainstormSession, IdeaSource
from brain.organizer import Organizer
from brain.assistant import BrainstormAssistant
from audio.mic import MicrophoneRecorder
from audio.vad import SilenceDetector
from stt.base import STTBackend
from stt.whisper_local import WhisperLocalSTT
from stt.vosk_local import VoskSTT
from stt.whisper_cloud import WhisperAPISTT
from llm.base import LLMBackend
from llm.openai_client import OpenAIClient
from llm.http_client import HTTPClient
from storage.files import FileStorage
from storage.autosave import AutoSaver
from storage.exporters import export_session
from tui.main_view import BrainstormApp

logger = get_logger('app')


class BrainstormController:
    """Main controller coordinating all components."""
    
    def __init__(self, config: Config):
        """Initialize controller.
        
        Args:
            config: Configuration object
        """
        self.config = config
        
        # Initialize components
        self.session: Optional[BrainstormSession] = None
        self.organizer: Optional[Organizer] = None
        self.assistant: Optional[BrainstormAssistant] = None
        self.storage: Optional[FileStorage] = None
        self.autosaver: Optional[AutoSaver] = None
        self.mic: Optional[MicrophoneRecorder] = None
        self.vad: Optional[SilenceDetector] = None
        self.stt: Optional[STTBackend] = None
        self.llm: Optional[LLMBackend] = None
        self.tui: Optional[BrainstormApp] = None
        
        # State
        self.recording_audio: list = []
        
        logger.info("Controller initialized")
    
    def initialize(self):
        """Initialize all components."""
        # Storage
        self.storage = FileStorage(self.config.storage_base_dir)
        
        # Load or create session
        if self.storage.exists():
            logger.info("Loading existing session")
            self.session = self.storage.load_session()
        
        if not self.session:
            logger.info("Creating new session")
            self.session = BrainstormSession(project_name=self.config.project_name)
        
        # Organizer
        self.organizer = Organizer(self.session, self.config.dedupe_threshold)
        
        # Initialize STT
        self._init_stt()
        
        # Initialize LLM
        self._init_llm()
        
        # Assistant
        if self.llm:
            self.assistant = BrainstormAssistant(self.llm, self.organizer)
        
        # Audio
        self._init_audio()
        
        # Autosaver
        self.autosaver = AutoSaver(
            self.storage,
            interval=self.config.autosave_interval,
            export_markdown=True,
            create_snapshots=self.config.get('storage.version_snapshots', True)
        )
        self.autosaver.set_session(self.session)
        self.autosaver.start()
        
        logger.info("All components initialized")
    
    def _init_stt(self):
        """Initialize STT backend."""
        backend = self.config.stt_backend
        
        try:
            if backend == "whisper_local":
                self.stt = WhisperLocalSTT(
                    model_size=self.config.whisper_model_size,
                    sample_rate=self.config.sample_rate,
                    language=self.config.get('stt.language', 'en')
                )
            elif backend == "vosk":
                self.stt = VoskSTT(
                    model_path=self.config.vosk_model_path,
                    sample_rate=self.config.sample_rate
                )
            elif backend == "whisper_api":
                self.stt = WhisperAPISTT(
                    api_key=self.config.openai_api_key,
                    sample_rate=self.config.sample_rate,
                    language=self.config.get('stt.language', 'en'),
                    base_url=self.config.openai_base
                )
            else:
                logger.error(f"Unknown STT backend: {backend}")
                return
            
            if self.stt and self.stt.is_available():
                logger.info(f"STT backend initialized: {backend}")
            else:
                logger.error(f"STT backend not available: {backend}")
                self.stt = None
                
        except Exception as e:
            logger.error(f"Failed to initialize STT: {e}")
            self.stt = None
    
    def _init_llm(self):
        """Initialize LLM backend."""
        backend = self.config.llm_backend
        
        try:
            if backend == "openai":
                self.llm = OpenAIClient(
                    api_key=self.config.openai_api_key,
                    model=self.config.openai_model,
                    temperature=self.config.get('llm.temperature', 0.7),
                    max_tokens=self.config.get('llm.max_tokens', 1000),
                    base_url=self.config.openai_base if self.config.openai_base != "https://api.openai.com/v1" else None
                )
            elif backend == "http":
                self.llm = HTTPClient(
                    url=self.config.llm_http_url,
                    model=self.config.llm_http_model,
                    temperature=self.config.get('llm.temperature', 0.7),
                    max_tokens=self.config.get('llm.max_tokens', 1000)
                )
            else:
                logger.error(f"Unknown LLM backend: {backend}")
                return
            
            if self.llm and self.llm.is_available():
                logger.info(f"LLM backend initialized: {backend}")
            else:
                logger.warning(f"LLM backend not available: {backend}")
                
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            self.llm = None
    
    def _init_audio(self):
        """Initialize audio components."""
        try:
            self.mic = MicrophoneRecorder(
                sample_rate=self.config.sample_rate,
                channels=self.config.get('audio.channels', 1),
                chunk_size=self.config.get('audio.chunk_size', 1024)
            )
            
            if self.config.vad_enabled:
                self.vad = SilenceDetector(
                    sample_rate=self.config.sample_rate,
                    silence_duration=self.config.get('audio.silence_duration', 1.5),
                    aggressiveness=self.config.get('audio.vad_aggressiveness', 3)
                )
            
            logger.info("Audio components initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize audio: {e}")
            self.mic = None
            self.vad = None
    
    def start_recording(self):
        """Start recording audio."""
        if not self.mic:
            logger.error("Microphone not available")
            return
        
        try:
            self.recording_audio = []
            self.mic.start()
            logger.info("Recording started")
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
    
    def stop_recording(self):
        """Stop recording and process audio."""
        if not self.mic:
            return
        
        try:
            audio_data = self.mic.stop()
            
            if audio_data is None or len(audio_data) == 0:
                logger.warning("No audio data recorded")
                return
            
            # Process audio
            self._process_audio(audio_data)
            
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
    
    def _process_audio(self, audio_data: np.ndarray):
        """Process recorded audio.
        
        Args:
            audio_data: Audio data array
        """
        if not self.stt:
            logger.error("STT not available")
            if self.tui:
                self.tui.show_message("STT backend not available", "error")
            return
        
        # Transcribe
        logger.info("Transcribing audio...")
        if self.tui:
            self.tui.show_message("Transcribing...", "info")
        
        text = self.stt.transcribe(audio_data)
        
        if not text:
            logger.warning("Transcription failed or empty")
            if self.tui:
                self.tui.show_message("No speech detected", "error")
            return
        
        logger.info(f"Transcribed: {text}")
        
        # Add to transcript
        self.organizer.add_transcript(text, "user")
        
        # Add as idea
        idea = self.organizer.add_idea(text, source=IdeaSource.USER)
        
        # Update TUI
        if self.tui:
            self.tui.add_transcript("user", text)
            self.tui.update_organizer()
        
        # Get assistant response
        if self.assistant:
            self._get_assistant_response(text)
    
    def _get_assistant_response(self, user_text: str):
        """Get assistant response to user input.
        
        Args:
            user_text: User's input text
        """
        if not self.assistant:
            return
        
        logger.info("Getting assistant response...")
        if self.tui:
            self.tui.show_message("Assistant thinking...", "info")
        
        response = self.assistant.process_user_input(user_text)
        
        if response:
            # Add to transcript
            self.organizer.add_transcript(response, "assistant")
            
            # Update TUI
            if self.tui:
                self.tui.add_transcript("assistant", response)
                self.tui.add_assistant_response(response)
                self.tui.update_organizer()
            
            logger.info("Assistant response added")
        else:
            logger.warning("No assistant response")
            if self.tui:
                self.tui.show_message("Assistant unavailable", "error")
    
    def handle_command(self, command: str):
        """Handle a command.
        
        Args:
            command: Command string
        """
        logger.info(f"Command: {command}")
        
        parts = command.strip().split(maxsplit=1)
        if not parts:
            return
        
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        try:
            if cmd == "save":
                self._cmd_save()
            elif cmd == "tag":
                self._cmd_tag(args)
            elif cmd == "del" or cmd == "delete":
                self._cmd_delete(args)
            elif cmd == "promote":
                self._cmd_promote(args)
            elif cmd == "todo":
                self._cmd_todo(args)
            elif cmd == "summarize":
                self._cmd_summarize(args)
            elif cmd == "search":
                self._cmd_search(args)
            elif cmd == "export":
                self._cmd_export(args)
            elif cmd == "config":
                self._cmd_config()
            elif cmd == "help":
                self._cmd_help()
            elif cmd == "cluster":
                self._cmd_cluster()
            elif cmd == "dedupe":
                self._cmd_dedupe()
            else:
                if self.tui:
                    self.tui.show_message(f"Unknown command: {cmd}", "error")
        except Exception as e:
            logger.error(f"Command error: {e}")
            if self.tui:
                self.tui.show_message(f"Error: {e}", "error")
    
    def _cmd_save(self):
        """Save command."""
        if self.autosaver:
            self.autosaver.save_now(create_snapshot=True)
            if self.tui:
                self.tui.show_message("Session saved", "success")
    
    def _cmd_tag(self, args: str):
        """Tag command."""
        parts = args.split(maxsplit=1)
        if len(parts) < 2:
            if self.tui:
                self.tui.show_message("Usage: tag <id> <tag1,tag2,...>", "error")
            return
        
        idea_id = parts[0]
        tags = [t.strip() for t in parts[1].split(',')]
        
        if self.organizer.tag_idea(idea_id, tags):
            if self.tui:
                self.tui.show_message(f"Tagged idea {idea_id}", "success")
                self.tui.update_organizer()
        else:
            if self.tui:
                self.tui.show_message(f"Idea {idea_id} not found", "error")
    
    def _cmd_delete(self, args: str):
        """Delete command."""
        idea_id = args.strip()
        if not idea_id:
            if self.tui:
                self.tui.show_message("Usage: del <id>", "error")
            return
        
        if self.organizer.delete_idea(idea_id):
            if self.tui:
                self.tui.show_message(f"Deleted idea {idea_id}", "success")
                self.tui.update_organizer()
        else:
            if self.tui:
                self.tui.show_message(f"Idea {idea_id} not found", "error")
    
    def _cmd_promote(self, args: str):
        """Promote command."""
        idea_id = args.strip()
        if not idea_id:
            if self.tui:
                self.tui.show_message("Usage: promote <id>", "error")
            return
        
        if self.organizer.promote_idea(idea_id):
            if self.tui:
                self.tui.show_message(f"Promoted idea {idea_id}", "success")
                self.tui.update_organizer()
        else:
            if self.tui:
                self.tui.show_message(f"Idea {idea_id} not found", "error")
    
    def _cmd_todo(self, args: str):
        """Todo command."""
        if not args:
            if self.tui:
                self.tui.show_message("Usage: todo <text>", "error")
            return
        
        self.organizer.add_action(args)
        if self.tui:
            self.tui.show_message("Action item added", "success")
            self.tui.update_organizer()
    
    def _cmd_summarize(self, args: str):
        """Summarize command."""
        scope = args.strip() or "session"
        
        if not self.assistant:
            if self.tui:
                self.tui.show_message("Assistant not available", "error")
            return
        
        if self.tui:
            self.tui.show_message("Generating summary...", "info")
        
        summary = self.assistant.generate_summary(scope)
        
        if summary:
            if self.tui:
                self.tui.add_assistant_response(f"**Summary ({scope}):**\n\n{summary}")
                self.tui.show_message("Summary generated", "success")
        else:
            if self.tui:
                self.tui.show_message("Failed to generate summary", "error")
    
    def _cmd_search(self, args: str):
        """Search command."""
        query = args.strip()
        if not query:
            if self.tui:
                self.tui.show_message("Usage: search <query>", "error")
            return
        
        results = self.organizer.search_ideas(query, top_k=5)
        
        if results and self.tui:
            response = f"**Search results for '{query}':**\n\n"
            for i, (idea, similarity) in enumerate(results, 1):
                tags_str = f" [{', '.join(idea.tags)}]" if idea.tags else ""
                response += f"{i}. ({similarity:.2f}) {idea.text}{tags_str}\n"
            
            self.tui.add_assistant_response(response)
        elif self.tui:
            self.tui.show_message("No results found", "info")
    
    def _cmd_export(self, args: str):
        """Export command."""
        formats = args.strip().split(',') if args else ['md']
        formats = [f.strip() for f in formats]
        
        results = export_session(self.session, self.storage.base_dir, formats)
        
        if results and self.tui:
            msg = f"Exported: {', '.join(results.keys())}"
            self.tui.show_message(msg, "success")
        elif self.tui:
            self.tui.show_message("Export failed", "error")
    
    def _cmd_config(self):
        """Config command."""
        if self.tui:
            config_text = f"""**Configuration:**

Project: {self.config.project_name}
STT Backend: {self.config.stt_backend}
LLM Backend: {self.config.llm_backend}
Sample Rate: {self.config.sample_rate}Hz
VAD Enabled: {self.config.vad_enabled}
Autosave: {self.config.autosave_interval}s
Storage: {self.config.storage_base_dir}
"""
            self.tui.add_assistant_response(config_text)
    
    def _cmd_help(self):
        """Help command."""
        # Help is shown via the TUI help overlay
        pass
    
    def _cmd_cluster(self):
        """Cluster command."""
        if not self.assistant:
            if self.tui:
                self.tui.show_message("Assistant not available", "error")
            return
        
        if self.tui:
            self.tui.show_message("Generating clusters...", "info")
        
        response = self.assistant.generate_clusters()
        
        if response and self.tui:
            self.tui.add_assistant_response(f"**Clusters:**\n\n{response}")
            self.tui.show_message("Clusters generated", "success")
        elif self.tui:
            self.tui.show_message("Not enough ideas to cluster", "info")
    
    def _cmd_dedupe(self):
        """Dedupe command."""
        if not self.assistant:
            if self.tui:
                self.tui.show_message("Assistant not available", "error")
            return
        
        result = self.assistant.check_duplicates()
        
        if result['count'] > 0 and self.tui:
            response = f"**Found {result['count']} duplicate pairs:**\n\n"
            for pair in result['pairs'][:5]:
                response += f"- {pair['id1']}: {pair['text1'][:50]}...\n"
                response += f"  {pair['id2']}: {pair['text2'][:50]}...\n"
                response += f"  Similarity: {pair['similarity']:.2f}\n\n"
            
            self.tui.add_assistant_response(response)
        elif self.tui:
            self.tui.show_message("No duplicates found", "success")
    
    def run(self):
        """Run the application."""
        # Initialize TUI
        self.tui = BrainstormApp(self.session, self.config)
        
        # Set callbacks
        self.tui.set_record_callbacks(
            on_start=self.start_recording,
            on_stop=self.stop_recording
        )
        self.tui.set_command_callback(self.handle_command)
        
        # Run TUI
        try:
            self.tui.run()
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown the application."""
        logger.info("Shutting down...")
        
        # Stop autosaver
        if self.autosaver:
            self.autosaver.stop()
            # Final save
            self.autosaver.save_now(create_snapshot=True)
        
        # Stop mic
        if self.mic and self.mic.is_recording:
            self.mic.stop()
        
        logger.info("Shutdown complete")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Voice-Driven Brainstorming Assistant")
    parser.add_argument("--project", "-p", default="default", help="Project name")
    parser.add_argument("--config", "-c", type=Path, help="Config file path")
    parser.add_argument("--stt", choices=["whisper_local", "vosk", "whisper_api"], help="STT backend")
    parser.add_argument("--llm", choices=["openai", "http"], help="LLM backend")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = "DEBUG" if args.debug else "INFO"
    setup_logging(level=getattr(__import__('logging'), log_level))
    
    logger.info("Starting Brainstorming Assistant")
    logger.info(f"Project: {args.project}")
    
    # Load config
    config = Config(project_name=args.project, config_path=args.config)
    
    # Override with CLI args
    if args.stt:
        config.set('stt.backend', args.stt)
    if args.llm:
        config.set('llm.backend', args.llm)
    
    # Create controller
    controller = BrainstormController(config)
    
    try:
        controller.initialize()
        controller.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
