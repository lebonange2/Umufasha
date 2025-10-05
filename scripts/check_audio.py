#!/usr/bin/env python3
"""Check audio devices and test microphone."""
import sys
import numpy as np

try:
    import sounddevice as sd
except ImportError:
    print("Error: sounddevice not installed")
    print("Run: pip install sounddevice")
    sys.exit(1)


def main():
    print("🎤 Audio Device Check\n")
    
    # List all devices
    print("Available audio devices:")
    print("=" * 60)
    devices = sd.query_devices()
    print(devices)
    print()
    
    # Get default input device
    default_input = sd.default.device[0]
    print(f"Default input device: {default_input}")
    
    # Test recording
    print("\n" + "=" * 60)
    print("Testing microphone...")
    print("Recording 3 seconds of audio...")
    print("Please speak into your microphone!")
    print("=" * 60)
    
    try:
        duration = 3  # seconds
        sample_rate = 16000
        
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype=np.int16
        )
        sd.wait()
        
        # Analyze recording
        audio_data = recording.flatten()
        max_amplitude = np.max(np.abs(audio_data))
        rms = np.sqrt(np.mean(audio_data.astype(float)**2))
        
        print("\n✓ Recording successful!")
        print(f"  Max amplitude: {max_amplitude}")
        print(f"  RMS level: {rms:.2f}")
        
        if max_amplitude < 100:
            print("\n⚠️  Warning: Very low audio level detected")
            print("   Check microphone volume or try speaking louder")
        elif max_amplitude > 30000:
            print("\n⚠️  Warning: Audio level very high (possible clipping)")
            print("   Consider reducing microphone gain")
        else:
            print("\n✓ Audio levels look good!")
        
        # Check for silence
        if rms < 10:
            print("\n❌ No audio detected!")
            print("   Possible issues:")
            print("   - Microphone not connected")
            print("   - Wrong input device selected")
            print("   - Microphone muted")
            print("   - Permissions not granted")
        
    except Exception as e:
        print(f"\n❌ Recording failed: {e}")
        print("\nPossible solutions:")
        print("- Check microphone permissions")
        print("- Try a different device index")
        print("- Ensure microphone is not in use by another app")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("Audio check complete!")
    print("\nTo use a specific device, set in .env:")
    print("  AUDIO_DEVICE=<device_index>")


if __name__ == "__main__":
    main()
