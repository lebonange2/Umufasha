# How to Push to GitHub

Your code has been committed successfully! Now you need to push it to GitHub.

## Option 1: Using SSH (Recommended)

If you have SSH keys set up with GitHub:

```bash
# Check if you have SSH remote
git remote -v

# If it shows HTTPS, change to SSH:
git remote set-url origin git@github.com:lebonange2/Umufasha.git

# Then push
git push origin main
```

## Option 2: Using Personal Access Token

1. **Create a Personal Access Token on GitHub**:
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Select scopes: `repo` (full control of private repositories)
   - Copy the token

2. **Push using the token**:
   ```bash
   git push https://<YOUR_TOKEN>@github.com/lebonange2/Umufasha.git main
   ```

   Or set it as credential helper:
   ```bash
   git config --global credential.helper store
   git push origin main
   # When prompted:
   # Username: lebonange2
   # Password: <paste your token>
   ```

## Option 3: Using GitHub CLI

If you have `gh` installed:

```bash
gh auth login
git push origin main
```

## Quick Push Command

If you have credentials configured:

```bash
cd /home/uwisiyose/ASSISTANT
git push origin main
```

## What Was Committed

✅ All Mindmapper files
✅ Local AI model support (Ollama/llama3.1)
✅ RunPod setup guides and scripts
✅ Database models and API routes
✅ Configuration updates

⚠️ Note: `node_modules` was included in the commit. For future commits, it's excluded via `.gitignore`.

## After Pushing

On your RunPod instance, you can now:

```bash
# Clone or pull the latest code
git clone https://github.com/lebonange2/Umufasha.git
# or if already cloned:
git pull origin main

# Then set up
cd Umufasha
./setup_ollama.sh
./start_server.sh
```

