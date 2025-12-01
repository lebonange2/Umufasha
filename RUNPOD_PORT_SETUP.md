# RunPod Port Configuration Guide

## Problem: RunPod Only Shows Jupyter (Port 8888)

RunPod automatically detects and exposes Jupyter Lab on port 8888, but your FastAPI app on port 8000 may not be automatically detected.

## Solution 1: Use RunPod's Custom Port Configuration

### Step 1: Check Current Port Status

On your RunPod instance, check what's running:
```bash
# Check if your app is running
ps aux | grep uvicorn
# or
netstat -tuln | grep 8000
```

### Step 2: Start Your Application

Make sure your app is running on port 8000:
```bash
cd /path/to/ASSISTANT
./start_server.sh
# or
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Step 3: Configure Port in RunPod UI

1. **Go to your RunPod pod page**
2. **Look for "Ports" or "Network" section** (may be under Settings/Advanced)
3. **Add a custom port mapping**:
   - Port: `8000`
   - Protocol: `HTTP`
   - Name: `FastAPI App` (optional)

4. **Save the configuration**

5. **RunPod should now show a new port forwarding link** for port 8000

## Solution 2: Use RunPod's Terminal to Create Port Forward

Some RunPod setups allow you to create port forwards via terminal:

```bash
# Check if RunPod CLI is available
which runpod

# Or check for port forwarding scripts
ls -la /workspace/.runpod/
```

## Solution 3: Use ngrok or Similar Tunnel (Alternative)

If RunPod's port forwarding doesn't work, use a tunnel service:

### Option A: Using ngrok

```bash
# Install ngrok (if not already installed)
# Download from https://ngrok.com/download

# Start your FastAPI app
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# In another terminal, start ngrok
ngrok http 8000

# ngrok will provide a public URL like: https://xxxxx.ngrok.io
# Use this URL in your browser
```

### Option B: Using Cloudflare Tunnel (free)

```bash
# Install cloudflared
# Then create tunnel
cloudflared tunnel --url http://localhost:8000
```

## Solution 4: Change to a Port RunPod Recognizes

Some RunPod setups auto-detect common ports. Try using port 8080 or 5000:

### Modify to use port 8080:

```bash
# Edit start_server.sh or run directly:
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Then access via: `https://xxxxx-8080.proxy.runpod.net`

## Solution 5: SSH Tunnel from Your Local Machine

This is the most reliable method:

### On Your Local Machine:

```bash
# Create SSH tunnel
ssh -L 8000:localhost:8000 root@<runpod-ip> -N

# Keep this terminal open, then in browser:
# http://localhost:8000/brainstorm/mindmapper
```

### Get RunPod Connection Info:

1. In RunPod dashboard, find your pod's **SSH connection details**
2. Look for:
   - SSH Host
   - SSH Port (usually 22 or a custom port)
   - Username (usually `root`)

3. Use the connection string provided by RunPod

## Solution 6: Use RunPod's Jupyter Terminal

Since Jupyter is already accessible:

1. **Open Jupyter Lab** (the link that works)
2. **Open a Terminal** in Jupyter
3. **Start your FastAPI app** in that terminal:
   ```bash
   cd /workspace/ASSISTANT  # or your project path
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
4. **Then use SSH tunnel** from your local machine to access it

## Solution 7: Check RunPod Template/Container Settings

Some RunPod templates have port configuration in:

1. **Container Environment Variables**:
   ```bash
   # Check environment variables
   env | grep PORT
   ```

2. **Dockerfile or startup scripts**:
   ```bash
   # Look for port exposure
   cat Dockerfile | grep EXPOSE
   ```

3. **RunPod YAML/Config files**:
   ```bash
   # Check for RunPod config
   find . -name "*.yaml" -o -name "*.yml" | xargs grep -l "port\|PORT"
   ```

## Quick Diagnostic Commands

Run these on your RunPod instance to diagnose:

```bash
# 1. Check if app is running
ps aux | grep -E "uvicorn|python.*main"

# 2. Check what's listening on ports
netstat -tuln | grep -E "8000|8888"

# 3. Test if port 8000 is accessible locally
curl http://localhost:8000/health

# 4. Check RunPod-specific port forwarding
cat /etc/runpod/ports.conf 2>/dev/null || echo "No RunPod ports config found"

# 5. Check for RunPod environment
env | grep -i runpod
```

## Recommended Approach

**For immediate access, use SSH Tunnel (Solution 5)**:

1. Get SSH connection info from RunPod dashboard
2. On your local machine:
   ```bash
   ssh -L 8000:localhost:8000 -p <ssh-port> root@<runpod-host> -N
   ```
3. On RunPod, start your app:
   ```bash
   ./start_server.sh
   ```
4. Access via: `http://localhost:8000/brainstorm/mindmapper`

**For permanent solution, configure port in RunPod UI (Solution 1)**

## Troubleshooting the "@https://xxxxx-8000.proxy.runpod.net" Link

If you see a link like `@https://xxxxx-8000.proxy.runpod.net` but it doesn't work:

1. **Check if the app is actually running**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Try accessing the health endpoint directly**:
   - `https://xxxxx-8000.proxy.runpod.net/health`
   - Should return: `{"status":"healthy","version":"1.0.0"}`

3. **Check browser console** (F12) for errors

4. **Try different endpoints**:
   - `https://xxxxx-8000.proxy.runpod.net/`
   - `https://xxxxx-8000.proxy.runpod.net/brainstorm`
   - `https://xxxxx-8000.proxy.runpod.net/brainstorm/mindmapper`

5. **Verify the port number in the URL matches your app port**

## Contact RunPod Support

If none of these work, RunPod support can help:
- They can manually configure port forwarding
- They can check if there are restrictions on your account
- They can verify the pod's network configuration

