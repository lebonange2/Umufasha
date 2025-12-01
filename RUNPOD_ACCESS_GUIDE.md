# Accessing the Application from Browser on RunPod

This guide explains how to access your FastAPI application running on a RunPod GPU instance from your local browser.

## Method 1: RunPod's Built-in Port Forwarding (Recommended)

RunPod provides built-in port forwarding through their web interface.

### Steps:

1. **Start your application on RunPod**:
   ```bash
   # SSH into your RunPod instance, then:
   cd /path/to/ASSISTANT
   python -m app.main
   # or
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. **In RunPod Web UI**:
   - Go to your pod's page
   - Look for "Connect" or "Ports" section
   - Click "Connect" or find the port forwarding option
   - RunPod will provide a public URL like: `https://xxxxx-8000.proxy.runpod.net`

3. **Access in browser**:
   - Use the provided RunPod URL
   - Navigate to: `https://xxxxx-8000.proxy.runpod.net/brainstorm/mindmapper`

## Method 2: SSH Tunneling (Alternative)

If RunPod's built-in forwarding isn't available, use SSH tunneling.

### Steps:

1. **On your local machine, create SSH tunnel**:
   ```bash
   ssh -L 8000:localhost:8000 root@<runpod-ip-or-hostname> -N
   ```
   
   Or if RunPod uses a different SSH setup:
   ```bash
   ssh -L 8000:localhost:8000 -p <port> root@<runpod-hostname> -N
   ```

2. **Keep the tunnel open** (leave this terminal running)

3. **Access in browser**:
   - Open: `http://localhost:8000/brainstorm/mindmapper`

## Method 3: Direct IP Access (If Public IP Available)

If your RunPod instance has a public IP:

1. **Start server bound to all interfaces**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. **Access via public IP**:
   - `http://<runpod-public-ip>:8000/brainstorm/mindmapper`

## Configuration Check

### Verify Server Binding

Make sure the server binds to `0.0.0.0` (all interfaces), not just `localhost`:

```python
# In app/main.py, the __main__ block already has:
uvicorn.run(
    "app.main:app",
    host="0.0.0.0",  # ✅ This allows external connections
    port=8000,
    reload=True,
    log_level="info"
)
```

If running with uvicorn directly:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### CORS Configuration

The app is already configured to allow all origins:
- `ALLOWED_HOSTS: List[str] = ["*"]` in `app/core/config.py`

This means CORS should work for any origin.

## Quick Start Script

Create a script to start the server with proper configuration:

```bash
#!/bin/bash
# start_server.sh

cd /path/to/ASSISTANT
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start server bound to all interfaces
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info
```

Make it executable:
```bash
chmod +x start_server.sh
./start_server.sh
```

## Troubleshooting

### Issue: Connection Refused

**Solution**: Make sure:
1. Server is bound to `0.0.0.0`, not `127.0.0.1`
2. Firewall allows port 8000 (RunPod usually handles this)
3. Server is actually running

### Issue: CORS Errors in Browser

**Solution**: The app already allows all origins, but if you see CORS errors:
1. Check browser console for specific error
2. Verify `ALLOWED_HOSTS` includes `["*"]`
3. Try accessing via the RunPod proxy URL

### Issue: Assets Not Loading

**Solution**: 
1. Check that static files are built: `ls app/static/mindmapper/`
2. Verify the static mount path in `app/main.py`
3. Check browser Network tab to see which assets fail to load

### Issue: Page Loads But API Calls Fail

**Solution**:
1. Check browser console for API errors
2. Verify API endpoints are accessible: `curl http://localhost:8000/api/mindmaps`
3. Check if API routes are registered in `app/main.py`

## Testing Connection

### From RunPod Instance:
```bash
# Test if server is listening
netstat -tuln | grep 8000
# or
ss -tuln | grep 8000

# Test locally
curl http://localhost:8000/health
```

### From Your Local Machine (via SSH tunnel):
```bash
curl http://localhost:8000/health
```

### From Browser:
- Open Developer Tools (F12)
- Check Console for errors
- Check Network tab to see which requests succeed/fail

## Security Considerations

⚠️ **Important**: When exposing your application:

1. **Change default admin credentials** in `.env`:
   ```
   ADMIN_USERNAME=your_secure_username
   ADMIN_PASSWORD=your_secure_password
   ```

2. **Use HTTPS** if possible (RunPod proxy usually provides this)

3. **Limit access** if you have sensitive data:
   - Use RunPod's access controls
   - Consider adding authentication middleware

4. **Monitor logs** for suspicious activity

## Example: Complete Setup

```bash
# 1. SSH into RunPod
ssh root@<runpod-hostname>

# 2. Navigate to project
cd /workspace/ASSISTANT  # or wherever your project is

# 3. Activate virtual environment (if using one)
source venv/bin/activate  # or your venv path

# 4. Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 5. In another terminal on your local machine, create SSH tunnel
ssh -L 8000:localhost:8000 root@<runpod-hostname> -N

# 6. Open browser
# Navigate to: http://localhost:8000/brainstorm/mindmapper
```

## RunPod-Specific Notes

- RunPod instances typically have port forwarding built-in
- Check RunPod dashboard for "Connect" or "Ports" section
- Some RunPod templates may have different SSH configurations
- RunPod may provide a direct web terminal you can use

## Next Steps

Once accessible:
1. Test the mindmapper at `/brainstorm/mindmapper`
2. Verify API endpoints work
3. Test creating/editing mind maps
4. Check that auto-save works

