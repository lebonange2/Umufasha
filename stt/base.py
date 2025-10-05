"""Base class for speech-to-text backends."""
from abc import ABC, abstractmethod
from typing import Optional
import numpy as np


class STTBackend(ABC):
    """Abstract base class for STT backends."""
    
    def __init__(self, sample_rate: int = 16000, language: str = "en"):
        """Initialize STT backend.
        
        Args:
            sample_rate: Audio sample rate
            language: Language code
        """
        self.sample_rate = sample_rate
        self.language = language
    
    @abstractmethod
    def transcribe(self, audio_data: np.ndarray) -> Optional[str]:
        """Transcribe audio data to text.
        
        Args:
            audio_data: Audio data as numpy array (int16)
            
        Returns:
            Transcribed text or None if failed
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if backend is available and ready.
        
        Returns:
            True if backend is ready to use
        """
        pass
    
    def preprocess_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """Preprocess audio data before transcription.
        
        Args:
            audio_data: Raw audio data
            
        Returns:
            Preprocessed audio data
        """
        # Ensure correct shape
        if len(audio_data.shape) > 1:
            audio_data = audio_data.flatten()
        
        # Convert to float32 if needed
        if audio_data.dtype == np.int16:
            audio_data = audio_data.astype(np.float32) / 32768.0
        
        return audio_data
