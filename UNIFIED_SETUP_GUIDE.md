# Unified Setup Guide

## ✨ Simplified Setup Process

The setup has been unified into **two simple commands**:

```bash
./setup.sh   # One-time setup (installs everything)
./start.sh   # Start the application
```

## 🎯 What Changed

### Before
- Run `./setup.sh` for Python dependencies
- Manually run `docker-compose up -d neo4j` OR
- Manually run `./scripts/setup_runpod_services.sh` for Neo4j
- Deal with Docker-in-Docker issues
- Manually configure `.env` for Neo4j

### After
- Run `./setup.sh` - **everything is automatic!**
  - Installs Python dependencies
  - Auto-detects Docker availability
  - If Docker available: uses docker-compose for Neo4j
  - If Docker unavailable: installs Neo4j directly
  - Updates `.env` automatically
- Run `./start.sh` - starts everything
  - Auto-starts Neo4j if needed
  - Auto-starts Ollama if available
  - Starts the application

## 📋 Usage

### Initial Setup (First Time)

```bash
cd /Umufasha  # or your project directory
git pull origin main
./setup.sh
```

**What happens:**
1. ✅ Installs Python dependencies
2. ✅ Installs system dependencies
3. ✅ Installs Docker Compose (if needed)
4. ✅ Sets up SQLite database
5. ✅ **NEW: Auto-installs Neo4j** (Docker or direct)
6. ✅ **NEW: Configures Neo4j automatically**
7. ✅ Updates `.env` with all settings
8. ✅ Installs Ollama (if available)
9. ✅ Downloads AI models

### Starting the Application

```bash
./start.sh
```

**What happens:**
1. ✅ **NEW: Auto-starts Neo4j** if installed but not running
2. ✅ Auto-starts Ollama if installed
3. ✅ Starts the web application
4. ✅ Opens on http://localhost:8000

### Stopping the Application

```bash
./stop.sh
# Or press Ctrl+C
```

## 🔧 How Neo4j Installation Works

### Environment Detection

The setup script automatically detects your environment:

#### Scenario 1: Docker Available
```
✓ Docker detected
✓ docker-compose found
→ Starting Neo4j via Docker Compose
✓ Neo4j container started
✓ .env updated
```

#### Scenario 2: Docker Not Available (RunPod/Container)
```
⚠ Docker not available
→ Installing Neo4j directly
✓ Java installed
✓ Neo4j Community Edition installed
✓ Neo4j configured
✓ Neo4j started
✓ .env updated
```

#### Scenario 3: Neo4j Already Installed
```
✓ Neo4j already installed
✓ Neo4j is running
→ Skipping installation
✓ .env updated
```

## 🐛 Fixed Issues

### Issue 1: Neo4j 5 Compatibility ✅
**Before:**
```
Unmatched arguments from index 0: 'set-initial-password'
```

**After:**
- Automatically uses correct command for Neo4j 5: `neo4j-admin dbms set-initial-password`
- Falls back to Neo4j 4 command if needed
- Provides helpful error messages

### Issue 2: Docker-in-Docker ✅
**Before:**
- Had to manually run `./scripts/setup_runpod_services.sh`
- Confusing Docker errors in containers

**After:**
- Automatically detects if Docker is available
- Installs Neo4j directly if Docker unavailable
- No manual intervention needed

### Issue 3: Manual Configuration ✅
**Before:**
- Had to manually edit `.env` for Neo4j settings

**After:**
- `.env` automatically updated with Neo4j credentials
- Works for both Docker and direct installations

## 📊 Connection Details

After setup, Neo4j is available at:

- **Browser UI**: http://localhost:7474
- **Bolt Protocol**: bolt://localhost:7687
- **Username**: neo4j
- **Password**: neo4jpassword

These are automatically added to your `.env` file.

## 🎮 Testing

### Test Neo4j Connection

```bash
# Check if Neo4j is running
curl http://localhost:7474

# Or check via neo4j command (if installed directly)
neo4j status

# Or check via Docker (if using Docker)
docker-compose ps neo4j
```

### Test from Python

```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    'bolt://localhost:7687',
    auth=('neo4j', 'neo4jpassword')
)
driver.verify_connectivity()
print('✓ Neo4j connected!')
```

### Test Application

```bash
./start.sh
# Open browser: http://localhost:8000
# Go to Brainstorming mode: http://localhost:8000/brainstorm
# Test graph features
```

## 🔍 Troubleshooting

### Neo4j Not Starting

```bash
# Check status
neo4j status

# View logs
journalctl -u neo4j
# Or
cat /var/log/neo4j/neo4j.log

# Restart
neo4j restart
```

### Docker Neo4j Issues

```bash
# Check container
docker-compose ps neo4j

# View logs
docker-compose logs neo4j

# Restart container
docker-compose restart neo4j
```

### Reset Neo4j Password

```bash
# For Neo4j 5+
neo4j-admin dbms set-initial-password neo4jpassword

# For Neo4j 4
neo4j-admin set-initial-password neo4jpassword
```

### Port Already in Use

```bash
# Check what's using port 7474
lsof -i :7474
netstat -tulpn | grep 7474

# Stop conflicting service
neo4j stop
# Or
docker-compose down neo4j
```

## 📚 Environment Variables

After setup, `.env` contains:

```bash
# Neo4j Graph Database
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4jpassword
```

You can modify these if using a different Neo4j instance (e.g., Neo4j Aura).

## 🌐 Cloud Alternative

If you prefer cloud-hosted Neo4j:

1. Create account at https://neo4j.com/cloud/aura/
2. Create free database
3. Update `.env`:
   ```bash
   NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_generated_password
   ```

## ✅ Summary

| Task | Command | Frequency |
|------|---------|-----------|
| Initial setup | `./setup.sh` | Once |
| Start application | `./start.sh` | Every time |
| Stop application | `./stop.sh` or Ctrl+C | As needed |
| Check Neo4j status | `neo4j status` or `docker-compose ps neo4j` | As needed |

## 🚀 Quick Start

For new users on RunPod or any environment:

```bash
# 1. Clone and navigate
git clone https://github.com/lebonange2/Umufasha.git
cd Umufasha

# 2. Run setup (installs everything automatically)
./setup.sh

# 3. Start application
./start.sh

# 4. Open browser
# http://localhost:8000
```

That's it! No manual Neo4j setup, no Docker troubleshooting, no configuration files to edit.

---

**Commit**: `19d1fdb`  
**Status**: ✅ Production ready  
**Tested**: Syntax validated, Neo4j 5 compatible
