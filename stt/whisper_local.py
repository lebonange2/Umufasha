"""Local Whisper STT using faster-whisper."""
from typing import Optional
import numpy as np
from stt.base import STTBackend
from utils.logging import get_logger

logger = get_logger('stt.whisper_local')


class WhisperLocalSTT(STTBackend):
    """Local Whisper STT using faster-whisper."""
    
    def __init__(self, model_size: str = "base", sample_rate: int = 16000, 
                 language: str = "en", device: str = "cpu"):
        """Initialize Whisper local STT.
        
        Args:
            model_size: Model size (tiny, base, small, medium, large)
            sample_rate: Audio sample rate
            language: Language code
            device: Device to use (cpu, cuda)
        """
        super().__init__(sample_rate, language)
        self.model_size = model_size
        self.device = device
        self.model = None
        
        self._load_model()
    
    def _load_model(self):
        """Load the Whisper model."""
        try:
            from faster_whisper import WhisperModel
            
            logger.info(f"Loading Whisper model: {self.model_size} on {self.device}")
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type="int8" if self.device == "cpu" else "float16"
            )
            logger.info("Whisper model loaded successfully")
        except ImportError:
            logger.error("faster-whisper not installed")
            self.model = None
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            self.model = None
    
    def is_available(self) -> bool:
        """Check if backend is available."""
        return self.model is not None
    
    def transcribe(self, audio_data: np.ndarray) -> Optional[str]:
        """Transcribe audio using Whisper.
        
        Args:
            audio_data: Audio data as numpy array
            
        Returns:
            Transcribed text or None
        """
        if not self.is_available():
            logger.error("Whisper model not available")
            return None
        
        try:
            # Preprocess audio
            audio_data = self.preprocess_audio(audio_data)
            
            # Transcribe
            segments, info = self.model.transcribe(
                audio_data,
                language=self.language,
                beam_size=5,
                vad_filter=False  # Disable VAD filter to avoid filtering out speech
            )
            
            # Collect segments
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text)
            
            text = " ".join(text_parts).strip()
            
            if text:
                logger.info(f"Transcribed: {text[:100]}...")
                return text
            else:
                logger.warning("No transcription produced")
                return None
                
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None
