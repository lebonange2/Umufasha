"""Vosk STT backend for offline recognition."""
from typing import Optional
import json
import numpy as np
from pathlib import Path
from stt.base import STTBackend
from utils.logging import get_logger

logger = get_logger('stt.vosk')


class VoskSTT(STTBackend):
    """Vosk STT backend."""
    
    def __init__(self, model_path: str, sample_rate: int = 16000, language: str = "en"):
        """Initialize Vosk STT.
        
        Args:
            model_path: Path to Vosk model directory
            sample_rate: Audio sample rate
            language: Language code (not used by Vosk directly)
        """
        super().__init__(sample_rate, language)
        self.model_path = Path(model_path)
        self.model = None
        self.recognizer = None
        
        self._load_model()
    
    def _load_model(self):
        """Load the Vosk model."""
        try:
            from vosk import Model, KaldiRecognizer
            
            if not self.model_path.exists():
                logger.error(f"Vosk model not found at {self.model_path}")
                return
            
            logger.info(f"Loading Vosk model from {self.model_path}")
            self.model = Model(str(self.model_path))
            logger.info("Vosk model loaded successfully")
            
        except ImportError:
            logger.error("vosk not installed")
            self.model = None
        except Exception as e:
            logger.error(f"Failed to load Vosk model: {e}")
            self.model = None
    
    def is_available(self) -> bool:
        """Check if backend is available."""
        return self.model is not None
    
    def transcribe(self, audio_data: np.ndarray) -> Optional[str]:
        """Transcribe audio using Vosk.
        
        Args:
            audio_data: Audio data as numpy array
            
        Returns:
            Transcribed text or None
        """
        if not self.is_available():
            logger.error("Vosk model not available")
            return None
        
        try:
            from vosk import KaldiRecognizer
            
            # Create recognizer
            recognizer = KaldiRecognizer(self.model, self.sample_rate)
            recognizer.SetWords(True)
            
            # Ensure int16 format
            if audio_data.dtype != np.int16:
                audio_data = (audio_data * 32768).astype(np.int16)
            
            # Flatten if needed
            if len(audio_data.shape) > 1:
                audio_data = audio_data.flatten()
            
            # Process audio
            audio_bytes = audio_data.tobytes()
            
            if recognizer.AcceptWaveform(audio_bytes):
                result = json.loads(recognizer.Result())
            else:
                result = json.loads(recognizer.FinalResult())
            
            text = result.get('text', '').strip()
            
            if text:
                logger.info(f"Transcribed: {text[:100]}...")
                return text
            else:
                logger.warning("No transcription produced")
                return None
                
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None
