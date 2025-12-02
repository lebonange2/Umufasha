#!/usr/bin/env python3
"""
Standalone test script for Bark TTS with PyTorch 2.6+ compatibility fix.
This script applies the necessary patches before using Bark.
"""
import sys
import os

# Disable hf_transfer requirement (optional, speeds up downloads but not required)
# This prevents errors if hf_transfer is not installed
if 'HF_HUB_ENABLE_HF_TRANSFER' not in os.environ:
    os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '0'
    print("✅ Disabled hf_transfer requirement (using standard download)")

# Apply PyTorch 2.6+ compatibility fix BEFORE importing Bark
try:
    import torch
    import numpy
    
    # Add safe globals for numpy objects
    if hasattr(torch.serialization, 'add_safe_globals'):
        # Handle numpy.core deprecation - try both old and new paths
        try:
            # Try new path first (numpy._core)
            scalar_class = numpy._core.multiarray.scalar
        except (AttributeError, ImportError):
            # Fallback to old path (numpy.core) for older numpy versions
            scalar_class = numpy.core.multiarray.scalar
        
        torch.serialization.add_safe_globals([scalar_class])
        print("✅ Added numpy multiarray.scalar to torch safe globals")
    
    # Patch torch.load to use weights_only=False for Bark compatibility
    original_load = torch.load
    def patched_load(*args, **kwargs):
        if 'weights_only' not in kwargs:
            kwargs['weights_only'] = False
        return original_load(*args, **kwargs)
    
    torch.load = patched_load
    print("✅ Patched torch.load for Bark compatibility")
    
except ImportError as e:
    print(f"❌ Error: {e}")
    print("Make sure torch and numpy are installed: pip install torch numpy")
    sys.exit(1)

# Now import Bark
try:
    from bark import generate_audio, preload_models, SAMPLE_RATE
    print("✅ Bark imported successfully")
except ImportError as e:
    print(f"❌ Bark not installed: {e}")
    print("Install with: pip install git+https://github.com/suno-ai/bark.git")
    sys.exit(1)

# Test preload_models
print("\n🔄 Preloading Bark models (this may take a while on first run)...")
try:
    preload_models()
    print("✅ Models preloaded successfully")
except Exception as e:
    print(f"❌ Model preloading failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test audio generation
print("\n🎵 Testing audio generation...")
test_text = "Hello, this is a test of the Bark text to speech system."
try:
    audio_array = generate_audio(test_text, silent=True)
    print(f"✅ Audio generated successfully!")
    print(f"   Audio length: {len(audio_array)} samples")
    print(f"   Duration: {len(audio_array) / SAMPLE_RATE:.2f} seconds")
    print(f"   Sample rate: {SAMPLE_RATE} Hz")
    
    # Save to file
    from scipy.io.wavfile import write as write_wav
    output_file = "test_bark_output.wav"
    write_wav(output_file, SAMPLE_RATE, audio_array)
    print(f"✅ Audio saved to: {output_file}")
    
except Exception as e:
    print(f"❌ Audio generation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n🎉 All tests passed! Bark TTS is working correctly!")

