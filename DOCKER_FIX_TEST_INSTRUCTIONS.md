# Docker Fix - Testing Instructions

## Issue Fixed
**Error**: `docker.errors.DockerException: Error while fetching server API version: Not supported URL scheme http+docker`

**Cause**: Docker daemon not running in RunPod container (Docker-in-Docker limitation)

## Solution Deployed

Created 3 automated scripts + comprehensive documentation:

1. **check_docker_status.sh** - Diagnoses Docker issues
2. **fix_docker_runpod.sh** - Attempts automated fixes
3. **setup_runpod_services.sh** - Installs Neo4j directly (no Docker needed)
4. **RUNPOD_DOCKER_FIX.md** - Full troubleshooting guide

## Testing on RunPod

### Step 1: Pull Latest Code

```bash
cd /Umufasha
git pull origin main
```

### Step 2: Run Diagnostic

```bash
./scripts/check_docker_status.sh
```

This will show:
- Docker installation status
- Docker daemon status
- Container environment detection
- Recommended solutions

### Step 3: Apply Fix

Choose one of these options:

#### Option A: Automated Fix (Recommended)

```bash
./scripts/fix_docker_runpod.sh
```

This will:
- Try to start Docker daemon
- If that fails, provide instructions for direct installation

#### Option B: Install Services Directly

```bash
./scripts/setup_runpod_services.sh
```

This will:
- Install Java + Neo4j directly
- Configure Neo4j
- Start Neo4j service
- Update .env file automatically

#### Option C: Manual Docker Start

```bash
# Try to start Docker daemon
service docker start

# Verify
docker info

# If successful, use docker-compose
docker-compose up -d neo4j
```

### Step 4: Verify Installation

After running the fix:

```bash
# Check Neo4j status
curl http://localhost:7474

# Or if Neo4j was installed directly
neo4j status

# Check if app can connect
python3 -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'neo4jpassword')); driver.verify_connectivity(); print('✓ Connected!')"
```

### Step 5: Start Application

```bash
# Start the app
./start.sh

# Or
python3 unified_app.py --host 0.0.0.0 --port 8000
```

### Step 6: Test in Browser

Open: http://localhost:8000

Test these features:
- Dashboard loads
- Brainstorming mode works
- Neo4j graph connections work

## Expected Outcomes

### If Option A (Automated Fix) Succeeds

```
✓ Docker daemon started successfully!

You can now use docker-compose:
  docker-compose up -d neo4j
```

### If Option B (Direct Installation) Succeeds

```
✓ Neo4j installed and running!

Connection details:
  URI: bolt://localhost:7687
  Browser: http://localhost:7474
  Username: neo4j
  Password: neo4jpassword
```

### If Docker Can't Start

```
Alternative Solutions:
Option A: Install services directly (RECOMMENDED for RunPod)
  ./scripts/setup_runpod_services.sh

Option B: Use cloud services
  - Neo4j Aura: https://neo4j.com/cloud/aura/
```

## Troubleshooting

### Issue: Scripts are not executable

```bash
chmod +x scripts/*.sh
```

### Issue: Neo4j installation fails

```bash
# Check logs
tail -f /var/log/neo4j/neo4j.log

# Try manual start
neo4j start

# Check if port is already in use
netstat -tulpn | grep 7474
```

### Issue: Can't connect to Neo4j

```bash
# Check if Neo4j is running
ps aux | grep neo4j

# Check Neo4j status
neo4j status

# Restart Neo4j
neo4j restart
```

### Issue: Application can't connect to Neo4j

**Check .env file**:
```bash
cat .env | grep NEO4J
```

Should show:
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4jpassword
```

## Documentation

Full documentation available in:
- **RUNPOD_DOCKER_FIX.md** - Comprehensive troubleshooting guide
- **RUNPOD_GPU_SETUP.md** - RunPod setup instructions
- **DEBUG_DOCKER_COMPOSE_FIX.md** - Docker Compose detection fix

## Files Changed

- ✅ `scripts/check_docker_status.sh` (new)
- ✅ `scripts/fix_docker_runpod.sh` (new)
- ✅ `scripts/setup_runpod_services.sh` (new)
- ✅ `RUNPOD_DOCKER_FIX.md` (new)

All scripts are:
- Syntax validated ✓
- Executable permissions set ✓
- Committed and pushed ✓

## Quick Test Command

Run this single command to diagnose and fix:

```bash
cd /Umufasha && git pull && ./scripts/fix_docker_runpod.sh
```

## Success Criteria

- [ ] Scripts execute without errors
- [ ] Neo4j is accessible at http://localhost:7474
- [ ] Application starts successfully
- [ ] No Docker-related errors in logs
- [ ] Brainstorming mode works with graph features

---

**Commit**: `893c690`  
**Status**: Ready for testing  
**Tested**: Syntax validated ✓  
**Next**: Test on RunPod container
