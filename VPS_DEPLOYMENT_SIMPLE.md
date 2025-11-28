# Simple Cambodia VPS Deployment (Direct KHQR)

This guide deploys `simple_khqr_bot.py` directly on your Cambodia VPS (Ubuntu) without a proxy layer. Bakong sees the VPS IP, satisfying the Cambodia IP restriction.

## 1. Prepare Environment (Ubuntu VPS)
```bash
sudo apt update
sudo apt install -y python3 python3-venv git
```

## 2. Copy Project to VPS
Option A (git clone):
```bash
cd ~
git clone https://github.com/Reachvip123/khqr-bot.git
cd khqr-bot
```
Option B (SCP from local if private repo):
```bash
scp -r "c:/Users/Reach/OneDrive/Documents/bot telegram" ubuntu@YOUR_VPS_IP:~/khqr-bot
cd ~/khqr-bot
```

## 3. Create .env
Create a `.env` file in the project root:
```
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
BAKONG_TOKEN=YOUR_BAKONG_API_TOKEN
BAKONG_ACCOUNT=NUMERIC_ACCOUNT_ID
MERCHANT_NAME=SOVANNAREACH VORN
CHECK_INTERVAL_SECONDS=10
MAX_WAIT_MINUTES=6
```

Ensure `BAKONG_ACCOUNT` is numeric (not alias). Example: `011442963`.

## 4. Install Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Test Run
```bash
source .venv/bin/activate
python simple_khqr_bot.py
```
Send an amount to the bot; you should see the QR and payment polling.

## 6. Systemd Service (Autostart)
Create a service file:
```bash
sudo tee /etc/systemd/system/khqr-bot.service > /dev/null <<'UNIT'
[Unit]
Description=KHQR Telegram Bot (Simple)
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/ubuntu/khqr-bot
Environment="PYTHONUNBUFFERED=1"
EnvironmentFile=/home/ubuntu/khqr-bot/.env
ExecStart=/home/ubuntu/khqr-bot/.venv/bin/python /home/ubuntu/khqr-bot/simple_khqr_bot.py
Restart=on-failure
RestartSec=5
User=ubuntu

[Install]
WantedBy=multi-user.target
UNIT
```
Reload + enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable khqr-bot
sudo systemctl start khqr-bot
sudo systemctl status khqr-bot -n 20
```

## 7. Logs
```bash
journalctl -u khqr-bot -f -n 50
```

## 8. Updating Code
```bash
cd ~/khqr-bot
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart khqr-bot
```

## 9. Common Issues
| Issue | Cause | Fix |
|-------|-------|-----|
| 409 Conflict | Another instance polling | Stop other instance (Railway) or disable systemd duplicate |
| QR fail | Bad Bakong token/account | Regenerate token / correct account id |
| Payment never confirms | Wrong amount or md5 mismatch | Ensure you pay exact amount; watch logs for status |
| Module not found (PIL) | Pillow not installed | Re-run requirements install |

## 10. Disable Old Deployments
Stop Railway bot to prevent conflicts:
- Remove project or set start command to a no-op.

---
You now have the simplest stable setup: single bot + direct KHQR on a Cambodia VPS.
