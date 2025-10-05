"""OpenAI Whisper API STT backend."""
from typing import Optional
import numpy as np
import io
import wave
from stt.base import STTBackend
from utils.logging import get_logger

logger = get_logger('stt.whisper_api')


class WhisperAPISTT(STTBackend):
    """OpenAI Whisper API STT backend."""
    
    def __init__(self, api_key: str, sample_rate: int = 16000, 
                 language: str = "en", base_url: Optional[str] = None):
        """Initialize Whisper API STT.
        
        Args:
            api_key: OpenAI API key
            sample_rate: Audio sample rate
            language: Language code
            base_url: Optional custom base URL
        """
        super().__init__(sample_rate, language)
        self.api_key = api_key
        self.base_url = base_url
        self.client = None
        
        self._init_client()
    
    def _init_client(self):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI
            
            kwargs = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            
            self.client = OpenAI(**kwargs)
            logger.info("OpenAI Whisper API client initialized")
            
        except ImportError:
            logger.error("openai package not installed")
            self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if backend is available."""
        return self.client is not None and bool(self.api_key)
    
    def _audio_to_wav_bytes(self, audio_data: np.ndarray) -> bytes:
        """Convert audio data to WAV bytes.
        
        Args:
            audio_data: Audio data as numpy array
            
        Returns:
            WAV file bytes
        """
        # Ensure int16 format
        if audio_data.dtype != np.int16:
            audio_data = (audio_data * 32768).astype(np.int16)
        
        # Flatten if needed
        if len(audio_data.shape) > 1:
            audio_data = audio_data.flatten()
        
        # Create WAV file in memory
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        return buffer.getvalue()
    
    def transcribe(self, audio_data: np.ndarray) -> Optional[str]:
        """Transcribe audio using OpenAI Whisper API.
        
        Args:
            audio_data: Audio data as numpy array
            
        Returns:
            Transcribed text or None
        """
        if not self.is_available():
            logger.error("Whisper API not available")
            return None
        
        try:
            # Convert to WAV
            wav_bytes = self._audio_to_wav_bytes(audio_data)
            
            # Create file-like object
            audio_file = io.BytesIO(wav_bytes)
            audio_file.name = "audio.wav"
            
            # Transcribe
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=self.language
            )
            
            text = response.text.strip()
            
            if text:
                logger.info(f"Transcribed: {text[:100]}...")
                return text
            else:
                logger.warning("No transcription produced")
                return None
                
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None
