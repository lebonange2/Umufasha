# Rebuild Frontend to See Graph Fix

## Why You Need to Rebuild

The graph rendering fix I made is in **React/TypeScript code** (`EmbeddedGraph.tsx`), which needs to be compiled/built before the browser can see the changes.

The old compiled JavaScript is still being served, which is why you're still seeing the blank graph.

## Quick Fix

### Option 1: Full Rebuild (Recommended)

```bash
cd /Umufasha/writer

# Install dependencies (if not already installed)
npm install

# Build the production bundle
npm run build

# The built files go to: app/static/writer/
# The backend serves them from there
```

### Option 2: Development Mode (Hot Reload)

If you're actively developing, use dev mode for automatic rebuilds:

```bash
cd /Umufasha/writer

# Start dev server with hot reload
npm run dev
```

Then in a **separate terminal**, start the backend:

```bash
cd /Umufasha
./start.sh
```

## After Rebuilding

1. **Hard refresh** your browser: `Ctrl + Shift + R` (or `Cmd + Shift + R` on Mac)
2. **Clear cache** if needed: `Ctrl + Shift + Delete`
3. **Reload the page**: http://localhost:8000/writer/ferrari-company
4. **Check browser console** (F12) for debug logs

You should see:
```
Graph data received: {nodes: Array(1), edges: Array(0)}
Transformed graph data: {nodeCount: 1, linkCount: 0, nodes: [...], links: []}
Updating graph with data
```

## What You'll See After Fix

- **A visible gray sphere** representing the Project node
- **Dark background** (`#1a1a1a`) instead of black
- **Interactive 3D view** - you can:
  - Rotate by dragging
  - Zoom with mouse wheel
  - See node label on hover

## Troubleshooting

### Issue: npm not found

Install Node.js:
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### Issue: Build fails

```bash
cd /Umufasha/writer

# Clean and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Issue: Still blank after rebuild

**Check browser console** (F12 → Console tab):
- Look for errors in red
- Check for WebGL errors
- Verify console logs show up

**Test WebGL support**:
Visit: https://get.webgl.org/
- If it says WebGL not supported, the 3D graph won't work
- Try a different browser (Chrome/Firefox recommended)

**Force clear cache**:
```bash
# In browser dev tools (F12)
Application tab → Clear storage → Clear site data
```

### Issue: Module not found errors

The project uses Vite + React. Check `package.json`:
```bash
cd /Umufasha/writer
cat package.json
```

Should have:
```json
{
  "dependencies": {
    "3d-force-graph": "^1.x.x",
    "react": "^18.x.x",
    ...
  }
}
```

If missing:
```bash
npm install 3d-force-graph react react-dom
npm run build
```

## Verification

After rebuild, check these files exist:

```bash
ls -la /Umufasha/app/static/writer/assets/

# Should see compiled JS/CSS files with hashes like:
# index-DgK2Djbw.js
# index-CjwYQEtz.css
```

## Complete Rebuild Steps

```bash
# 1. Navigate to project
cd /Umufasha

# 2. Pull latest code
git pull origin main

# 3. Navigate to React app
cd writer

# 4. Install dependencies
npm install

# 5. Build production bundle
npm run build

# 6. Restart backend (to serve new files)
cd ..
./stop.sh
./start.sh

# 7. Hard refresh browser
# Press Ctrl+Shift+R in browser
```

## Expected Timeline

- `npm install`: 1-2 minutes (first time), seconds (subsequent)
- `npm run build`: 10-30 seconds
- Backend restart: 5-10 seconds
- **Total**: ~2-3 minutes for first build

## Success Indicators

✅ Build completes without errors  
✅ Files appear in `app/static/writer/assets/`  
✅ Browser console shows debug logs  
✅ Gray sphere visible in graph area  
✅ Can interact with 3D view  

---

**Current Status**: Code is fixed and pushed ✅  
**Next Step**: Rebuild frontend to apply changes  
**Command**: `cd /Umufasha/writer && npm run build`
