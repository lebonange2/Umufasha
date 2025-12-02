# Bark TTS Multi-GPU Optimization Guide

## Overview

The Bark TTS conversion has been optimized to leverage multiple GPUs for significantly faster processing of large documents.

## Performance Improvements

### Single GPU
- **Mode**: Sequential processing (one chunk at a time)
- **Speed**: Baseline (no change)
- **Memory**: ~4-6 GB VRAM per chunk

### Multiple GPUs
- **Mode**: Parallel processing (multiple chunks simultaneously)
- **Speed**: ~N× faster where N = number of GPUs
  - 2 GPUs: ~2× faster
  - 4 GPUs: ~4× faster
  - 8 GPUs: ~8× faster (up to MAX_PARALLEL_TTS_WORKERS limit)
- **Memory**: ~4-6 GB VRAM per GPU

### Example Performance
For a document with 20 chunks:
- **Single GPU**: ~6 minutes (sequential)
- **2 GPUs**: ~3 minutes (2 chunks in parallel)
- **4 GPUs**: ~1.5 minutes (4 chunks in parallel)
- **8 GPUs**: ~45 seconds (8 chunks in parallel, if configured)

## Configuration

### Environment Variables

1. **`ENABLE_PARALLEL_TTS`** (default: `true`)
   - Enable/disable parallel processing
   - Set to `false` to force sequential processing
   - Example: `export ENABLE_PARALLEL_TTS=false`

2. **`MAX_PARALLEL_TTS_WORKERS`** (default: `4`)
   - Maximum number of parallel workers (even if more GPUs are available)
   - Prevents memory exhaustion on systems with many GPUs
   - Example: `export MAX_PARALLEL_TTS_WORKERS=8`

### Example Configuration

```bash
# Enable parallel processing with up to 8 workers
export ENABLE_PARALLEL_TTS=true
export MAX_PARALLEL_TTS_WORKERS=8

# Start the server
./start.sh
```

## How It Works

1. **GPU Detection**: Automatically detects available GPUs at startup
2. **Chunk Distribution**: Distributes text chunks across GPUs using round-robin assignment
3. **Parallel Processing**: Each GPU processes its assigned chunks simultaneously
4. **Result Aggregation**: Results are collected and concatenated in the correct order

## GPU Memory Requirements

- **Per GPU**: ~4-6 GB VRAM for Bark models
- **Total**: N × 4-6 GB where N = number of GPUs used
- **Example**: 4 GPUs need ~16-24 GB total VRAM

## Troubleshooting

### Out of Memory Errors

If you encounter CUDA out-of-memory errors:

1. **Reduce parallel workers**:
   ```bash
   export MAX_PARALLEL_TTS_WORKERS=2
   ```

2. **Disable parallel processing**:
   ```bash
   export ENABLE_PARALLEL_TTS=false
   ```

3. **Use fewer GPUs**: The system will automatically use fewer workers if GPUs are unavailable

### Checking GPU Status

```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU count: {torch.cuda.device_count()}")
for i in range(torch.cuda.device_count()):
    print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
```

## Best Practices

1. **Large Documents**: Use multiple GPUs for documents with many chunks (>10 chunks)
2. **Small Documents**: Single GPU is sufficient for small documents (<5 chunks)
3. **Memory Management**: Monitor GPU memory usage and adjust `MAX_PARALLEL_TTS_WORKERS` accordingly
4. **System Resources**: Ensure sufficient system RAM for parallel processing

## Technical Details

- **Thread Safety**: Each GPU processes chunks in separate threads
- **Device Assignment**: Round-robin distribution ensures balanced workload
- **Error Handling**: Failed chunks on one GPU don't affect others
- **Order Preservation**: Results are sorted by chunk index to maintain text order

## Future Improvements

Potential optimizations for even faster processing:
- Batch processing multiple small chunks on single GPU
- Dynamic GPU memory allocation
- Model quantization for lower memory usage
- Streaming audio generation for very large documents

