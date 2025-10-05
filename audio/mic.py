"""Microphone capture using sounddevice."""
import queue
import threading
from typing import Optional, Callable
import numpy as np
import sounddevice as sd
from utils.logging import get_logger

logger = get_logger('mic')


class MicrophoneRecorder:
    """Records audio from microphone."""
    
    def __init__(self, sample_rate: int = 16000, channels: int = 1, 
                 chunk_size: int = 1024, device: Optional[int] = None):
        """Initialize microphone recorder.
        
        Args:
            sample_rate: Sample rate in Hz
            channels: Number of audio channels
            chunk_size: Size of audio chunks
            device: Device index (None = default)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.device = device
        
        self.audio_queue: queue.Queue = queue.Queue()
        self.stream: Optional[sd.InputStream] = None
        self.is_recording = False
        
        # Audio level tracking
        self.current_level = 0.0
        self.level_callback: Optional[Callable[[float], None]] = None
        
        logger.info(f"Initialized mic recorder: {sample_rate}Hz, {channels}ch")
    
    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
        """Callback for audio stream."""
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        # Calculate audio level (RMS)
        level = np.sqrt(np.mean(indata.astype(float)**2))
        self.current_level = float(level)
        
        if self.level_callback:
            self.level_callback(self.current_level)
        
        # Add to queue
        if self.is_recording:
            self.audio_queue.put(indata.copy())
    
    def start(self):
        """Start recording."""
        if self.is_recording:
            logger.warning("Already recording")
            return
        
        self.is_recording = True
        self.audio_queue = queue.Queue()
        
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.int16,
                blocksize=self.chunk_size,
                device=self.device,
                callback=self._audio_callback
            )
            self.stream.start()
            logger.info("Started recording")
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            self.is_recording = False
            raise
    
    def stop(self) -> Optional[np.ndarray]:
        """Stop recording and return audio data.
        
        Returns:
            Recorded audio as numpy array, or None if no data
        """
        if not self.is_recording:
            logger.warning("Not recording")
            return None
        
        self.is_recording = False
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        # Collect all audio chunks
        chunks = []
        while not self.audio_queue.empty():
            try:
                chunk = self.audio_queue.get_nowait()
                chunks.append(chunk)
            except queue.Empty:
                break
        
        if not chunks:
            logger.warning("No audio data recorded")
            return None
        
        # Concatenate chunks
        audio_data = np.concatenate(chunks, axis=0)
        duration = len(audio_data) / self.sample_rate
        
        logger.info(f"Stopped recording: {duration:.2f}s, {len(audio_data)} samples")
        return audio_data
    
    def get_audio_level(self) -> float:
        """Get current audio level (0.0-1.0).
        
        Returns:
            Current audio level
        """
        return min(self.current_level * 10, 1.0)  # Scale and clamp
    
    def set_level_callback(self, callback: Callable[[float], None]):
        """Set callback for audio level updates.
        
        Args:
            callback: Function to call with audio level
        """
        self.level_callback = callback
    
    @staticmethod
    def list_devices():
        """List available audio devices."""
        devices = sd.query_devices()
        logger.info(f"Available audio devices:\n{devices}")
        return devices
    
    @staticmethod
    def get_default_device() -> int:
        """Get default input device index."""
        return sd.default.device[0]


class AudioBuffer:
    """Thread-safe circular audio buffer."""
    
    def __init__(self, max_duration: float = 10.0, sample_rate: int = 16000):
        """Initialize audio buffer.
        
        Args:
            max_duration: Maximum buffer duration in seconds
            sample_rate: Sample rate
        """
        self.max_samples = int(max_duration * sample_rate)
        self.sample_rate = sample_rate
        self.buffer: list = []
        self.lock = threading.Lock()
    
    def add(self, audio_data: np.ndarray):
        """Add audio data to buffer.
        
        Args:
            audio_data: Audio data to add
        """
        with self.lock:
            self.buffer.append(audio_data)
            
            # Trim if too large
            total_samples = sum(len(chunk) for chunk in self.buffer)
            while total_samples > self.max_samples and len(self.buffer) > 1:
                removed = self.buffer.pop(0)
                total_samples -= len(removed)
    
    def get_all(self) -> Optional[np.ndarray]:
        """Get all audio data from buffer.
        
        Returns:
            Concatenated audio data or None if empty
        """
        with self.lock:
            if not self.buffer:
                return None
            return np.concatenate(self.buffer, axis=0)
    
    def clear(self):
        """Clear the buffer."""
        with self.lock:
            self.buffer.clear()
    
    def duration(self) -> float:
        """Get current buffer duration in seconds.
        
        Returns:
            Duration in seconds
        """
        with self.lock:
            total_samples = sum(len(chunk) for chunk in self.buffer)
            return total_samples / self.sample_rate
