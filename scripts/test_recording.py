#!/usr/bin/env python3
"""Test audio recording and STT."""
import sys
import time
import numpy as np
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from audio.mic import MicrophoneRecorder
from stt.whisper_local import WhisperLocalSTT

def main():
    print("🎤 Audio Recording & STT Test")
    print("=" * 60)
    
    # Initialize microphone
    print("\n1. Initializing microphone...")
    mic = MicrophoneRecorder(sample_rate=16000, channels=1)
    
    # Record audio
    print("\n2. Recording for 3 seconds...")
    print("   Please speak now!")
    print("   " + "=" * 50)
    
    mic.start()
    time.sleep(3)
    audio_data = mic.stop()
    
    if audio_data is None:
        print("❌ No audio data captured!")
        return 1
    
    # Analyze audio
    print(f"\n3. Audio captured:")
    print(f"   - Shape: {audio_data.shape}")
    print(f"   - Dtype: {audio_data.dtype}")
    print(f"   - Duration: {len(audio_data) / 16000:.2f}s")
    print(f"   - Min value: {np.min(audio_data)}")
    print(f"   - Max value: {np.max(audio_data)}")
    print(f"   - Mean: {np.mean(audio_data):.2f}")
    print(f"   - RMS: {np.sqrt(np.mean(audio_data**2)):.2f}")
    
    # Check if audio is too quiet
    rms = np.sqrt(np.mean(audio_data.astype(float)**2))
    max_val = np.max(np.abs(audio_data))
    
    if max_val < 100:
        print("\n⚠️  WARNING: Audio level very low!")
        print("   - Check microphone volume")
        print("   - Speak louder")
        print("   - Try a different microphone")
    elif rms < 10:
        print("\n⚠️  WARNING: Mostly silence detected!")
        print("   - Microphone might not be picking up sound")
        print("   - Check microphone permissions")
    else:
        print("\n✓ Audio levels look good")
    
    # Test STT
    print("\n4. Testing STT (Whisper)...")
    print("   Loading model (this may take a moment)...")
    
    try:
        stt = WhisperLocalSTT(model_size="base", sample_rate=16000)
        
        if not stt.is_available():
            print("❌ Whisper model not available!")
            return 1
        
        print("   Transcribing...")
        text = stt.transcribe(audio_data)
        
        if text:
            print(f"\n✅ Transcription successful!")
            print(f"   Text: '{text}'")
        else:
            print(f"\n❌ No transcription produced!")
            print(f"   Possible reasons:")
            print(f"   - Audio too quiet")
            print(f"   - No speech in audio")
            print(f"   - Background noise only")
            
            # Save audio for debugging
            print(f"\n   Saving audio for debugging...")
            np.save("/tmp/debug_audio.npy", audio_data)
            print(f"   Saved to: /tmp/debug_audio.npy")
            
    except Exception as e:
        print(f"❌ STT Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n" + "=" * 60)
    print("Test complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
