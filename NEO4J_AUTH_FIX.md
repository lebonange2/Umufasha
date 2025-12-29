# Neo4j Authentication Error Fix

## Errors You're Seeing

```
AuthError: The client is unauthorized due to authentication failure
ClientError: The client has provided incorrect authentication details too many times in a row
ExperimentalWarning: Unexpected config keys: timeout
```

## Root Causes

1. **Wrong Neo4j Password**: The password in `.env` doesn't match the Neo4j database password
2. **Driver Compatibility**: The `timeout` parameter in `verify_connectivity()` is not supported in neo4j-python driver 5.15.0

## Quick Fix (Choose One)

### Option 1: Reset Neo4j Password (RECOMMENDED)

Run our automated fix script:

```bash
cd /Umufasha
./scripts/fix_neo4j_password.sh
```

This will:
- Stop Neo4j
- Reset password to `neo4jpassword`
- Restart Neo4j
- Test the connection

### Option 2: Manual Password Reset

**If Neo4j is installed directly:**
```bash
# Stop Neo4j
neo4j stop

# Reset password (Neo4j 5+)
neo4j-admin dbms set-initial-password neo4jpassword --force

# Or for Neo4j 4:
neo4j-admin set-initial-password neo4jpassword

# Start Neo4j
neo4j start
```

**If using Docker:**
```bash
# Stop and remove the container
docker-compose down neo4j

# Remove the volume (this deletes data!)
docker volume rm umufasha_neo4j_data

# Start fresh
docker-compose up -d neo4j
```

### Option 3: Delete Auth File and Restart

```bash
# Stop Neo4j
neo4j stop

# Delete auth file
rm -f /var/lib/neo4j/data/dbms/auth
# Or: rm -f ~/neo4j/data/dbms/auth

# Start Neo4j
neo4j start

# Wait a few seconds, then set password
neo4j-admin dbms set-initial-password neo4jpassword

# Restart
neo4j restart
```

## Verify the Fix

### 1. Check Neo4j Status

```bash
neo4j status
```

Should show: `Neo4j is running`

### 2. Test with Browser

Open: http://localhost:7474

- Username: `neo4j`
- Password: `neo4jpassword`

### 3. Test with cypher-shell

```bash
cypher-shell -u neo4j -p neo4jpassword "RETURN 1;"
```

Should return: `1`

### 4. Check from Application

```bash
curl http://localhost:8000/api/graph/status
```

Should show:
```json
{
  "neo4j_available": true,
  "message": "Neo4j is connected and running"
}
```

## After Fixing

### Restart Your Application

```bash
./stop.sh
./start.sh
```

Or if using `uvicorn` directly:
```bash
# Press Ctrl+C to stop
# Then restart with:
./start.sh
```

## Understanding the Errors

### Error 1: Authentication Failure

```
AuthError: The client is unauthorized due to authentication failure
```

**Cause**: The password `neo4jpassword` in your `.env` doesn't match Neo4j's actual password

**Why it happens**:
- Neo4j was installed but password wasn't set correctly
- You changed Neo4j password manually
- Neo4j was reinstalled without clearing old auth data

### Error 2: Rate Limiting

```
AuthenticationRateLimit: The client has provided incorrect authentication details too many times in a row
```

**Cause**: After multiple failed authentication attempts, Neo4j temporarily blocks the client

**Solution**: 
1. Wait 30-60 seconds
2. Fix the password
3. Restart the application

### Error 3: Timeout Parameter

```
ExperimentalWarning: Unexpected config keys: timeout
```

**Cause**: The neo4j-python driver version 5.15.0 doesn't support the `timeout` parameter in `verify_connectivity()`

**Solution**: We removed the parameter (fixed in code)

## Code Changes Made

### 1. Removed `timeout` Parameter

**File**: `app/graph/connection.py`

```python
# Before
driver.verify_connectivity(timeout=5)

# After
driver.verify_connectivity()
```

### 2. Better Error Messages

**File**: `app/graph/connection.py`

Now detects authentication errors and provides actionable fix:
```python
elif "Unauthorized" in error_msg or "authentication" in error_msg.lower():
    raise ConnectionError(
        f"Neo4j authentication failed. "
        f"Wrong username or password. "
        f"Run: ./scripts/fix_neo4j_password.sh to reset password"
    )
```

### 3. Password Reset Script

**File**: `scripts/fix_neo4j_password.sh`

Automated script to reset Neo4j password to match `.env` configuration

## Prevention

### Always Check After Neo4j Install

After running `./setup.sh` or installing Neo4j:

```bash
# Check password works
cypher-shell -u neo4j -p neo4jpassword "RETURN 1;"

# If fails, reset it
./scripts/fix_neo4j_password.sh
```

### Verify .env Matches Neo4j

Your `.env` should have:
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4jpassword
```

## Troubleshooting

### "neo4j-admin: command not found"

**Solution**: Neo4j isn't in PATH or not installed

```bash
# Find neo4j-admin
which neo4j-admin
find / -name "neo4j-admin" 2>/dev/null

# Or reinstall Neo4j
./setup.sh
```

### "Could not determine runlevel" (in Docker/Container)

**Solution**: This is normal in containers, ignore it

### Password reset fails

**Solution**: Delete auth file manually

```bash
neo4j stop

# Find and delete auth files
find / -name "auth" -path "*/neo4j/data/dbms/*" 2>/dev/null
rm -f /var/lib/neo4j/data/dbms/auth

neo4j start
neo4j-admin dbms set-initial-password neo4jpassword
neo4j restart
```

### Still getting authentication errors after fix

**Solution**: Clear driver cache

```bash
# Stop app
./stop.sh

# Stop Neo4j
neo4j stop

# Wait 10 seconds
sleep 10

# Start Neo4j
neo4j start

# Wait for it to be ready
sleep 5

# Test connection
cypher-shell -u neo4j -p neo4jpassword "RETURN 1;"

# Start app
./start.sh
```

## Summary

| Error | Cause | Fix |
|-------|-------|-----|
| Authentication failure | Wrong password | `./scripts/fix_neo4j_password.sh` |
| Rate limiting | Too many failed attempts | Wait 60s, then fix password |
| Timeout parameter | Driver incompatibility | Fixed in code (update code) |

---

**Quick Fix Command**:
```bash
cd /Umufasha
git pull origin main  # Get latest fixes
./scripts/fix_neo4j_password.sh
./stop.sh && ./start.sh
```

**Status**: ✅ Fixed in code  
**Next**: Run the password fix script on your system
