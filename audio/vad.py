"""Voice Activity Detection using webrtcvad."""
import collections
from typing import Optional
import webrtcvad
from utils.logging import get_logger

logger = get_logger('vad')


class VAD:
    """Voice Activity Detector wrapper."""
    
    def __init__(self, sample_rate: int = 16000, aggressiveness: int = 3, 
                 frame_duration_ms: int = 30):
        """Initialize VAD.
        
        Args:
            sample_rate: Audio sample rate (8000, 16000, 32000, or 48000)
            aggressiveness: VAD aggressiveness (0-3, higher = more aggressive)
            frame_duration_ms: Frame duration in milliseconds (10, 20, or 30)
        """
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)
        
        self.vad = webrtcvad.Vad(aggressiveness)
        logger.info(f"Initialized VAD with aggressiveness={aggressiveness}, rate={sample_rate}")
    
    def is_speech(self, audio_frame: bytes) -> bool:
        """Check if audio frame contains speech.
        
        Args:
            audio_frame: Raw audio bytes (16-bit PCM)
            
        Returns:
            True if speech detected
        """
        try:
            return self.vad.is_speech(audio_frame, self.sample_rate)
        except Exception as e:
            logger.error(f"VAD error: {e}")
            return False


class SilenceDetector:
    """Detects silence periods for auto-stop recording."""
    
    def __init__(self, sample_rate: int = 16000, silence_duration: float = 1.5,
                 aggressiveness: int = 3, frame_duration_ms: int = 30):
        """Initialize silence detector.
        
        Args:
            sample_rate: Audio sample rate
            silence_duration: Duration of silence (seconds) to trigger stop
            aggressiveness: VAD aggressiveness
            frame_duration_ms: Frame duration in milliseconds
        """
        self.vad = VAD(sample_rate, aggressiveness, frame_duration_ms)
        self.silence_duration = silence_duration
        self.frame_duration_ms = frame_duration_ms
        
        # Calculate number of silent frames needed
        self.num_silent_frames = int(silence_duration * 1000 / frame_duration_ms)
        
        # Ring buffer for tracking recent speech activity
        self.ring_buffer = collections.deque(maxlen=self.num_silent_frames)
        self.triggered = False
        
        logger.info(f"Silence detector: {silence_duration}s = {self.num_silent_frames} frames")
    
    def process_frame(self, audio_frame: bytes) -> tuple[bool, bool]:
        """Process an audio frame.
        
        Args:
            audio_frame: Raw audio bytes
            
        Returns:
            Tuple of (is_speech, should_stop)
            - is_speech: True if current frame contains speech
            - should_stop: True if silence period exceeded
        """
        is_speech = self.vad.is_speech(audio_frame)
        
        # Add to ring buffer
        self.ring_buffer.append(is_speech)
        
        # Check if we should trigger (start of speech)
        if not self.triggered:
            num_voiced = sum(self.ring_buffer)
            if num_voiced > 0.5 * self.ring_buffer.maxlen:
                self.triggered = True
                logger.debug("Speech triggered")
            return is_speech, False
        
        # Check if we should stop (end of speech)
        num_unvoiced = sum(1 for x in self.ring_buffer if not x)
        should_stop = num_unvoiced >= self.ring_buffer.maxlen * 0.9
        
        if should_stop:
            logger.debug("Silence detected, stopping")
            self.reset()
        
        return is_speech, should_stop
    
    def reset(self):
        """Reset the detector state."""
        self.ring_buffer.clear()
        self.triggered = False
