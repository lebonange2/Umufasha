# Multi-GPU Parallel Processing for Exam Generation

## Overview

The exam generator now supports automatic multi-GPU parallel processing, specifically optimized for RunPod cloud GPU instances. The system automatically detects available GPUs and distributes workload across them for faster exam generation.

## How It Works

### GPU Detection

The system uses multiple methods to detect available GPUs on RunPod:

1. **nvidia-smi** (Primary method)
   - Queries `nvidia-smi --list-gpus` to count GPUs
   - Works reliably on RunPod instances with NVIDIA GPUs

2. **nvidia-smi query** (Alternative)
   - Uses `nvidia-smi --query-gpu=count` as fallback

3. **CUDA_VISIBLE_DEVICES** (Environment variable)
   - Checks RunPod's GPU visibility settings
   - Parses comma-separated GPU indices

4. **PyTorch CUDA** (If available)
   - Uses `torch.cuda.device_count()` as additional check

5. **Device files** (Fallback)
   - Checks `/dev/nvidia*` device files

6. **Default assumption**
   - If detection fails, assumes 2 GPUs (common RunPod setup)

### Client Pool Creation

- **Multiple GPUs detected**: Creates one LLM client per GPU
  - Example: 2 GPUs → 2 clients
  - All clients connect to the same Ollama instance
  - Ollama automatically distributes concurrent requests across GPUs

- **Single GPU**: Creates multiple clients (up to 4) for better concurrency
  - Even with one GPU, parallel requests improve throughput

### Parallel Processing

1. **Problem Generation**
   - All learning objectives are processed in parallel
   - Each objective is assigned to a client using round-robin distribution
   - Concurrent requests are sent to Ollama, which distributes them across GPUs

2. **Validation**
   - All problems are validated in parallel
   - Validation tasks are distributed across the client pool
   - Multiple GPUs process validations simultaneously

3. **Review and Fix Loop**
   - Uses the same client pool for all LLM operations
   - Ensures consistent GPU utilization throughout the process

## RunPod Configuration

### Automatic Detection

The system automatically detects RunPod GPUs. No manual configuration needed.

### Verifying GPU Detection

Check the application logs for messages like:
```
Detected 2 GPU(s) via nvidia-smi
Multi-GPU setup: 2 GPUs detected, 2 clients created
Ollama will automatically distribute concurrent requests across all GPUs
```

### Manual Verification

You can verify GPU detection on your RunPod instance:

```bash
# Check GPU count
nvidia-smi --list-gpus

# Check CUDA devices
echo $CUDA_VISIBLE_DEVICES

# Test Ollama with multiple concurrent requests
# (The system does this automatically)
```

## Performance Benefits

### Before (Single GPU)
- Sequential processing: ~150 problems in ~30-45 minutes
- One GPU utilized at a time

### After (Multi-GPU)
- Parallel processing: ~150 problems in ~15-20 minutes (estimated 2x speedup)
- All GPUs utilized simultaneously
- Better resource utilization

## Technical Details

### Ollama Multi-GPU Support

Ollama automatically uses all available GPUs when:
- Multiple GPUs are detected
- Multiple concurrent requests are made
- The model fits across GPUs (or uses model parallelism)

### Client Pool Architecture

```
ExamGeneratorCompany
├── GPU Detection (nvidia-smi, CUDA, etc.)
├── Client Pool Creation (1 client per GPU)
│   ├── Client 1 → Ollama (distributes to GPU 0)
│   ├── Client 2 → Ollama (distributes to GPU 1)
│   └── ...
└── Parallel Task Distribution
    ├── Objective 1 → Client 1 → GPU 0
    ├── Objective 2 → Client 2 → GPU 1
    ├── Objective 3 → Client 1 → GPU 0
    └── ...
```

### Round-Robin Distribution

Tasks are distributed using round-robin to ensure even load:
- Objective 1 → Client 0 (GPU 0)
- Objective 2 → Client 1 (GPU 1)
- Objective 3 → Client 0 (GPU 0)
- Objective 4 → Client 1 (GPU 1)
- ...

## Troubleshooting

### GPUs Not Detected

If the system defaults to 2 GPUs but you have a different number:

1. **Check nvidia-smi**:
   ```bash
   nvidia-smi --list-gpus
   ```

2. **Check environment variables**:
   ```bash
   echo $CUDA_VISIBLE_DEVICES
   ```

3. **Check logs**: Look for GPU detection messages in application logs

### Only One GPU Working

If only one GPU is being used:

1. **Verify Ollama is using all GPUs**:
   - Ollama should automatically use all available GPUs
   - Check Ollama logs: `tail -f /tmp/ollama.log`

2. **Check concurrent requests**:
   - The system creates multiple clients for parallel requests
   - Verify multiple objectives are being processed simultaneously

3. **Model size**: Very large models might not fit across multiple GPUs
   - Check model size vs. GPU memory

### Performance Not Improved

If you don't see performance improvements:

1. **Verify parallel processing**: Check logs for "parallel" messages
2. **Check GPU utilization**: Use `nvidia-smi` to monitor GPU usage
3. **Verify Ollama configuration**: Ensure Ollama is running and accessible
4. **Model limitations**: Some models may not support multi-GPU efficiently

## Future Enhancements

Potential improvements:
- GPU-specific model loading
- Dynamic client pool sizing based on workload
- GPU memory monitoring and load balancing
- Support for model sharding across GPUs
