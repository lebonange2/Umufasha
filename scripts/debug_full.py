#!/usr/bin/env python3
"""Comprehensive debugging for recording issues."""
import sys
import time
import numpy as np
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_microphone():
    """Test basic microphone functionality."""
    print("\n" + "="*60)
    print("TEST 1: Microphone Capture")
    print("="*60)
    
    try:
        import sounddevice as sd
        
        # List devices
        print("\nAvailable devices:")
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                default = " [DEFAULT]" if i == sd.default.device[0] else ""
                print(f"  {i}: {dev['name']}{default}")
        
        # Get default input
        default_input = sd.default.device[0]
        print(f"\nUsing device: {default_input}")
        
        # Record 2 seconds
        print("\nRecording 2 seconds... SPEAK NOW!")
        duration = 2
        sample_rate = 16000
        
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype=np.int16,
            device=default_input
        )
        sd.wait()
        
        # Analyze
        audio = recording.flatten()
        print(f"\n✓ Recording complete")
        print(f"  Shape: {audio.shape}")
        print(f"  Min: {np.min(audio)}, Max: {np.max(audio)}")
        print(f"  RMS: {np.sqrt(np.mean(audio.astype(float)**2)):.2f}")
        
        max_val = np.max(np.abs(audio))
        if max_val < 100:
            print(f"\n❌ PROBLEM: Audio too quiet (max={max_val})")
            print(f"   Solutions:")
            print(f"   1. Increase mic volume: alsamixer (F4 for capture)")
            print(f"   2. Speak louder")
            print(f"   3. Move closer to mic")
            return None
        else:
            print(f"\n✓ Audio level OK (max={max_val})")
            return audio
            
    except Exception as e:
        print(f"\n❌ Microphone test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_mic_class():
    """Test MicrophoneRecorder class."""
    print("\n" + "="*60)
    print("TEST 2: MicrophoneRecorder Class")
    print("="*60)
    
    try:
        from audio.mic import MicrophoneRecorder
        
        mic = MicrophoneRecorder(sample_rate=16000, channels=1)
        print("\n✓ MicrophoneRecorder initialized")
        
        print("\nRecording 2 seconds... SPEAK NOW!")
        mic.start()
        time.sleep(2)
        audio_data = mic.stop()
        
        if audio_data is None:
            print("\n❌ PROBLEM: No audio data returned")
            return None
        
        print(f"\n✓ Recording complete")
        print(f"  Shape: {audio_data.shape}")
        print(f"  Min: {np.min(audio_data)}, Max: {np.max(audio_data)}")
        print(f"  RMS: {np.sqrt(np.mean(audio_data.astype(float)**2)):.2f}")
        
        return audio_data
        
    except Exception as e:
        print(f"\n❌ MicrophoneRecorder test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_stt(audio_data):
    """Test STT with audio data."""
    print("\n" + "="*60)
    print("TEST 3: Speech-to-Text")
    print("="*60)
    
    if audio_data is None:
        print("\n⏭️  Skipping (no audio data)")
        return
    
    try:
        from stt.whisper_local import WhisperLocalSTT
        
        print("\nLoading Whisper model...")
        stt = WhisperLocalSTT(model_size="base", sample_rate=16000)
        
        if not stt.is_available():
            print("\n❌ PROBLEM: Whisper model not available")
            return
        
        print("✓ Model loaded")
        
        print("\nTranscribing...")
        text = stt.transcribe(audio_data)
        
        if text:
            print(f"\n✅ SUCCESS!")
            print(f"   Transcription: '{text}'")
        else:
            print(f"\n❌ PROBLEM: No transcription produced")
            print(f"   Debugging info:")
            
            # Try with preprocessing
            from stt.base import STTBackend
            processed = STTBackend.preprocess_audio(None, audio_data)
            print(f"   Processed audio shape: {processed.shape}")
            print(f"   Processed audio dtype: {processed.dtype}")
            print(f"   Processed audio range: [{np.min(processed):.3f}, {np.max(processed):.3f}]")
            
            # Save for manual inspection
            np.save("/tmp/debug_audio.npy", audio_data)
            print(f"\n   Audio saved to: /tmp/debug_audio.npy")
            print(f"   You can load it with: np.load('/tmp/debug_audio.npy')")
            
    except Exception as e:
        print(f"\n❌ STT test failed: {e}")
        import traceback
        traceback.print_exc()

def test_whisper_directly():
    """Test Whisper with a simple audio signal."""
    print("\n" + "="*60)
    print("TEST 4: Whisper with Test Signal")
    print("="*60)
    
    try:
        from stt.whisper_local import WhisperLocalSTT
        
        # Create a simple test signal (silence)
        print("\nTesting with silence (should return empty)...")
        silence = np.zeros(16000, dtype=np.float32)  # 1 second of silence
        
        stt = WhisperLocalSTT(model_size="base", sample_rate=16000)
        result = stt.transcribe(silence)
        
        if result:
            print(f"  Result: '{result}'")
        else:
            print(f"  ✓ Correctly returned None for silence")
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

def main():
    print("\n" + "🔍 " + "="*58 + " 🔍")
    print("   COMPREHENSIVE RECORDING DEBUG")
    print("🔍 " + "="*58 + " 🔍")
    
    # Test 1: Basic microphone
    audio1 = test_microphone()
    
    # Test 2: MicrophoneRecorder class
    audio2 = test_mic_class()
    
    # Test 3: STT with recorded audio
    test_stt(audio2 if audio2 is not None else audio1)
    
    # Test 4: Whisper sanity check
    test_whisper_directly()
    
    print("\n" + "="*60)
    print("DEBUG COMPLETE")
    print("="*60)
    
    print("\nSummary:")
    print("  - If Test 1 fails: Microphone/system issue")
    print("  - If Test 2 fails: MicrophoneRecorder class issue")
    print("  - If Test 3 fails: STT/Whisper issue")
    print("\nNext steps:")
    print("  1. Check the output above for ❌ markers")
    print("  2. Follow the suggested solutions")
    print("  3. If audio is saved, inspect: /tmp/debug_audio.npy")

if __name__ == "__main__":
    main()
