# Railway Deployment Guide

## Prerequisites
- Git installed locally
- Railway account and project created
- This folder connected to a GitHub repository
- Variables set in Railway dashboard:
  - BOT_TOKEN
  - BAKONG_ACCOUNT
  - MERCHANT_NAME
  - BAKONG_PROXY_URL (e.g. http://157.10.73.90:3000) if using proxy
  - PROXY_API_KEY if using proxy
  - BAKONG_TOKEN only if NOT using proxy (direct Bakong API calls)

## Files
- khqrbot.txt: main bot runner (uses python-telegram-bot polling)
- requirements.txt: Python dependencies
- .gitignore: excludes .env

## First-Time Git Setup (if .git not present)
```powershell
cd "c:\Users\Reach\OneDrive\Documents\bot telegram"
git init
git add khqrbot.txt requirements.txt .gitignore RAILWAY_DEPLOYMENT.md
git commit -m "Initial KHQR bot commit"
git branch -M main
git remote add origin https://github.com/YOUR_USER/YOUR_REPO.git
git push -u origin main
```
Replace YOUR_USER/YOUR_REPO with your GitHub path.

## Subsequent Updates / Redeploy
```powershell
cd "c:\Users\Reach\OneDrive\Documents\bot telegram"
# Make code changes first
python -m py_compile khqrbot.txt  # optional syntax check
git add khqrbot.txt RAILWAY_DEPLOYMENT.md
git commit -m "Redeploy: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
git push origin main
```
Railway will auto-build and start. Logs should show the Startup diagnostics block.

## Manual Redeploy Without Code Change
```powershell
cd "c:\Users\Reach\OneDrive\Documents\bot telegram"
git commit --allow-empty -m "Trigger redeploy $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
git push origin main
```

## Start Command in Railway
Set service start command to:
```
python khqrbot.txt
```

## Verifying Deployment
1. Open Logs: Look for `[Startup] Environment configuration:` block.
2. Confirm `USE_PROXY: True` if proxy vars provided.
3. Send amount to the bot to generate a QR.
4. Pay and watch logs for `[PROXY CHECK]` and success message.

## Common Issues
| Symptom | Cause | Fix |
|---------|-------|-----|
| Missing env error | Variable not set | Add in Railway Variables panel |
| ImportError | Package missing | Add to requirements.txt and redeploy |
| Proxy timeout | VPS port blocked | Ensure firewall allows inbound 3000 |
| Payment never detected | MD5 mismatch or proxy not forwarding | Check VPS proxy logs |

## Rotating PROXY_API_KEY
1. On VPS: generate new key `openssl rand -hex 32` and update proxy `.env`.
2. Restart proxy container (`docker compose restart`).
3. Update Railway `PROXY_API_KEY` variable.
4. Commit empty change to trigger redeploy.

## Safe Local Testing
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python khqrbot.txt
```

## Health Check (Optional)
You can add a simple HTTP health endpoint by creating a small separate process or switching to a webhook architecture. For polling bots, Railway considers the container healthy if the process stays running.

---
Keep secrets out of commits. `.env` is ignored; use Railway Variables.
