# Docker-in-Docker Fix for RunPod

## Problem

When running `docker-compose up -d neo4j` in a RunPod container, you get this error:

```
docker.errors.DockerException: Error while fetching server API version: Not supported URL scheme http+docker
```

## Root Cause

RunPod containers don't have Docker daemon running by default. This is a Docker-in-Docker (DinD) limitation. The `docker-compose` command is installed, but it can't communicate with a Docker daemon.

## Quick Fix

Run our automated fix script:

```bash
cd /Umufasha  # or wherever your project is
./scripts/fix_docker_runpod.sh
```

This script will:
1. Try to start Docker daemon
2. If that fails, guide you to install services directly

## Solution Options

### Option 1: Install Services Directly (RECOMMENDED)

Instead of using Docker Compose, install Neo4j directly on the system:

```bash
./scripts/setup_runpod_services.sh
```

This will:
- Install Java
- Install Neo4j Community Edition
- Configure and start Neo4j
- Update your `.env` file automatically

**Advantages:**
- Works in any RunPod environment
- No Docker required
- Faster startup
- Simpler setup

### Option 2: Start Docker Daemon (if privileged)

If your container has privileged access:

```bash
# Try to start Docker
service docker start

# Or
systemctl start docker

# Verify it works
docker info

# Then use docker-compose
docker-compose up -d neo4j
```

**Requirements:**
- Container must be started with `--privileged` flag
- Or Docker socket must be mounted: `-v /var/run/docker.sock:/var/run/docker.sock`

### Option 3: Use Cloud Services

Use managed cloud databases instead:

**Neo4j Aura (Free Tier):**
1. Go to https://neo4j.com/cloud/aura/
2. Create free instance
3. Get connection details
4. Update `.env`:
   ```bash
   NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password
   ```

**Redis Cloud (Free Tier):**
1. Go to https://redis.com/try-free/
2. Create free database
3. Update `.env`:
   ```bash
   REDIS_URL=redis://default:password@redis-xxxxx.cloud.redislabs.com:12345
   ```

## Diagnostic Tools

### Check Docker Status

```bash
./scripts/check_docker_status.sh
```

This will show:
- Docker binary status
- Docker daemon status
- Container detection
- Recommendations

### Manual Diagnosis

```bash
# Check if Docker is installed
docker --version

# Check if Docker daemon is running
docker info

# Check if in a container
ls -la /.dockerenv

# Check Docker socket
ls -la /var/run/docker.sock
```

## Environment-Specific Instructions

### For RunPod Users

**Best Approach:** Use Option 1 (Install Directly)

```bash
# 1. Install services directly
./scripts/setup_runpod_services.sh

# 2. Start your application
./start.sh
```

### For Local Docker Users

```bash
# This should work normally
docker-compose up -d
```

### For Docker-in-Docker Scenarios

```bash
# Start container with privileged mode
docker run --privileged -it your-image

# Or mount Docker socket
docker run -v /var/run/docker.sock:/var/run/docker.sock -it your-image
```

## Understanding the Error

The error message breakdown:

```
urllib3.exceptions.URLSchemeUnknown: Not supported URL scheme http+docker
```

- **Cause**: The `requests` library used by `docker-compose` tries to connect to Docker daemon
- **Problem**: Docker daemon isn't running or accessible
- **URL Scheme**: `http+docker` is the protocol for Docker API communication
- **Impact**: `docker-compose` can't manage containers without daemon access

## What Gets Installed

### With Option 1 (Direct Installation)

- **Neo4j Community Edition**: Full graph database
  - HTTP: http://localhost:7474
  - Bolt: bolt://localhost:7687
  - User: neo4j
  - Pass: neo4jpassword

- **No Docker Required**: Services run as system services

### With Option 2 (Docker Compose)

All services run as Docker containers:
- Neo4j (port 7474, 7687)
- PostgreSQL (port 5432)
- Redis (port 6379)

## Testing After Fix

### Test Neo4j Connection

```bash
# If installed directly
curl http://localhost:7474

# If using Docker
docker-compose ps neo4j

# Test from Python
python3 -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'neo4jpassword')); driver.verify_connectivity(); print('✓ Neo4j connected!')"
```

### Test Your Application

```bash
# Start the app
./start.sh

# Check if it can connect to Neo4j
curl http://localhost:8000/health
```

## Troubleshooting

### "service docker start" fails

**Issue**: Permission denied or service not found

**Solution**:
```bash
# Try systemctl instead
systemctl start docker

# Or run dockerd directly
dockerd &

# Or use Option 1 (direct installation)
./scripts/setup_runpod_services.sh
```

### Neo4j installation fails

**Issue**: Can't install Neo4j package

**Solution**:
```bash
# Update package lists
apt-get update

# Install prerequisites
apt-get install -y openjdk-17-jdk wget gnupg

# Try manual installation
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | apt-key add -
echo 'deb https://debian.neo4j.com stable latest' > /etc/apt/sources.list.d/neo4j.list
apt-get update
apt-get install -y neo4j
```

### Can't connect to Neo4j after installation

**Issue**: Connection refused

**Solution**:
```bash
# Check if Neo4j is running
neo4j status

# Start it if not running
neo4j start

# Check logs
cat /var/log/neo4j/neo4j.log

# Verify it's listening
netstat -tulpn | grep 7474
```

## Quick Reference

| Command | Purpose |
|---------|---------|
| `./scripts/check_docker_status.sh` | Diagnose Docker issues |
| `./scripts/fix_docker_runpod.sh` | Automated fix attempt |
| `./scripts/setup_runpod_services.sh` | Install services directly |
| `service docker start` | Start Docker daemon |
| `docker-compose up -d neo4j` | Start Neo4j via Docker |
| `neo4j start` | Start Neo4j (direct install) |
| `neo4j status` | Check Neo4j status |

## Summary

- **Problem**: Docker daemon not running in RunPod container
- **Quick Fix**: Run `./scripts/fix_docker_runpod.sh`
- **Best Solution**: Run `./scripts/setup_runpod_services.sh` to install directly
- **Alternative**: Use cloud services (Neo4j Aura, Redis Cloud)

---

**Need help?** Check the logs:
- Docker: `/tmp/dockerd.log`
- Neo4j: `/var/log/neo4j/neo4j.log`
- Application: `logs/unified_app.log`
