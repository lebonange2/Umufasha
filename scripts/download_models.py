#!/usr/bin/env python3
"""Download STT models for offline use."""
import sys
import argparse
from pathlib import Path


def download_whisper(model_size="base"):
    """Download Whisper model."""
    print(f"Downloading Whisper model: {model_size}")
    
    try:
        from faster_whisper import WhisperModel
        
        print("This may take a few minutes...")
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        print(f"✓ Whisper {model_size} model downloaded successfully!")
        
        # Test it
        print("\nTesting model...")
        import numpy as np
        test_audio = np.zeros(16000, dtype=np.float32)  # 1 second of silence
        segments, info = model.transcribe(test_audio)
        print("✓ Model working correctly!")
        
    except ImportError:
        print("Error: faster-whisper not installed")
        print("Run: pip install faster-whisper")
        sys.exit(1)
    except Exception as e:
        print(f"Error downloading model: {e}")
        sys.exit(1)


def download_vosk():
    """Instructions for downloading Vosk model."""
    print("Vosk Model Download Instructions")
    print("=" * 60)
    print("\nVosk models must be downloaded manually:")
    print("\n1. Visit: https://alphacephei.com/vosk/models")
    print("\n2. Download a model (recommended for English):")
    print("   - Small: vosk-model-small-en-us-0.15 (~40MB)")
    print("   - Large: vosk-model-en-us-0.22 (~1.8GB)")
    print("\n3. Extract to the models/ directory:")
    print("   mkdir -p models")
    print("   unzip vosk-model-small-en-us-0.15.zip -d models/")
    print("\n4. Update .env file:")
    print("   VOSK_MODEL_PATH=models/vosk-model-small-en-us-0.15")
    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Download STT models")
    parser.add_argument(
        "backend",
        choices=["whisper", "vosk"],
        help="STT backend to download models for"
    )
    parser.add_argument(
        "--size",
        choices=["tiny", "base", "small", "medium", "large"],
        default="base",
        help="Whisper model size (default: base)"
    )
    
    args = parser.parse_args()
    
    if args.backend == "whisper":
        download_whisper(args.size)
    else:
        download_vosk()


if __name__ == "__main__":
    main()
