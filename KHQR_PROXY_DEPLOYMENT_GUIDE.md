# KHQR Proxy Deployment Guide (Cambodia VPS)

This guide walks you through deploying the Bun + Hono KHQR proxy on a Cambodia VPS and configuring your Telegram bot to use it.

## What You'll Need

1. **A Cambodia VPS** (with Docker installed)
   - Recommended: 512MB-1GB RAM, 10GB disk (minimal)
   - Providers: CamNet, Kingdom Internet, or similar Cambodia-based ISPs
   - Estimated cost: $3–$10 USD/month

2. **A domain name** (optional, but recommended for HTTPS)
   - You already have one from Hostinger, so you can use that
   - Or use your VPS's static IP directly

3. **The proxy project** (already created in `khqr-proxy/`)

## Step 1: Get a Cambodia VPS

### Quick Options:
- **CamNet** (Cambodia): https://www.camnet.com.kh/
- **Kingdom Internet** (Cambodia): https://www.kingdominternet.com/
- **Other regional providers** (Singapore, Thailand) — NOT recommended as they won't satisfy Bakong's requirement

### What to ask for:
- "Ubuntu 22.04 or 20.04 with Docker pre-installed"
- "Static public IP address"
- "Root or sudo access"

Once you have SSH access, proceed to Step 2.

## Step 2: Prepare Your VPS

SSH into your VPS:
```bash
ssh root@YOUR_VPS_IP
# or: ssh username@YOUR_VPS_IP (then use sudo for commands below)
```

Update the system:
```bash
apt update && apt upgrade -y
```

Install Docker and docker-compose (if not already installed):
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
apt install docker-compose -y
docker --version
docker-compose --version
```

## Step 3: Upload & Deploy the Proxy

From your local machine, copy the `khqr-proxy` folder to your VPS:

```powershell
# Windows PowerShell
scp -r "C:\Users\Reach\OneDrive\Documents\bot telegram\khqr-proxy" root@YOUR_VPS_IP:/opt/
```

Or if you have SSH key, add `-i path\to\key.pem`.

On the VPS, navigate to the proxy directory:
```bash
cd /opt/khqr-proxy
```

Create a `.env` file with your secret API key:
```bash
cat > .env << 'EOF'
PROXY_API_KEY=your-super-secret-api-key-here-change-this
PORT=3000
NODE_ENV=production
EOF
```

Choose a **strong random secret** for `PROXY_API_KEY` (e.g., `openssl rand -hex 32`). Use the same value in your bot's `.env` later.

## Step 4: Start the Proxy with Docker

Start the proxy:
```bash
docker-compose up -d
```

Verify it's running:
```bash
docker-compose logs -f
```

You should see:
```
khqr-proxy  | KHQR Proxy listening on port 3000
```

Stop log monitoring with `Ctrl+C`.

## Step 5: (Optional) Set Up HTTPS with Let's Encrypt

If you want to use a domain name (recommended for production):

Install Certbot:
```bash
apt install certbot python3-certbot-nginx -y
```

Install Nginx as a reverse proxy:
```bash
apt install nginx -y
```

Create Nginx config at `/etc/nginx/sites-available/khqr-proxy`:
```nginx
server {
    listen 80;
    server_name your-domain.example;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:
```bash
ln -s /etc/nginx/sites-available/khqr-proxy /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

Get SSL certificate:
```bash
certbot --nginx -d your-domain.example
```

After this, your proxy will be accessible at `https://your-domain.example`.

## Step 6: Test the Proxy

From your VPS:
```bash
curl -X GET \
  -H "X-API-KEY: your-super-secret-api-key-here-change-this" \
  http://127.0.0.1:3000/v1/khqr/check?md5=test-md5
```

Expected response:
```json
{"paid": false, "md5": "test-md5"}
```

Or from your local machine (if using domain):
```powershell
$headers = @{ "X-API-KEY" = "your-super-secret-api-key-here-change-this" }
Invoke-RestMethod -Uri "https://your-domain.example/v1/khqr/check?md5=test-md5" -Headers $headers
```

## Step 7: Configure Your Bot

Edit your bot's `.env` file on your local machine:

```
BOT_TOKEN=your_telegram_bot_token
BAKONG_TOKEN=your_bakong_api_token
BAKONG_ACCOUNT=your_bakong_account_id
MERCHANT_NAME=Your Merchant Name
BAKONG_PROXY_URL=https://your-domain.example
PROXY_API_KEY=your-super-secret-api-key-here-change-this
```

Or if using IP instead of domain:
```
BAKONG_PROXY_URL=https://YOUR_VPS_IP:3000
```

Note: If using IP with HTTPS, you'll get SSL warnings. For production, use a domain + Let's Encrypt (Step 5).

## Step 8: Restart Your Bot

Restart your bot locally to pick up the new `.env` settings:

```powershell
# Stop the bot (Ctrl+C in the terminal where it's running)
# Then restart it:
python storebot.py
# or with venv:
.\venv\Scripts\python.exe khqrbot.txt
```

Watch the logs for:
```
Bot is running with KHQR PROXY enabled!
Proxy URL: https://your-domain.example
```

## Step 9: Test End-to-End

1. Send a message to your Telegram bot: `2.50`
2. The bot should generate a QR and log:
   ```
   [BOT] Using proxy for QR creation
   [PROXY] Creating QR via proxy...
   ```
3. Watch your proxy logs:
   ```bash
   docker-compose logs -f
   ```
   You should see requests forwarded to `https://api-bakong.nbc.gov.kh`.

4. Scan the QR with a Bakong app and make a test payment.

5. The bot should detect the payment and auto-deliver accounts.

## Troubleshooting

### Proxy not starting
```bash
docker-compose logs
```
Check for port conflicts or missing `.env` variables.

### "Invalid API key" errors
Ensure `PROXY_API_KEY` matches in both:
- `/opt/khqr-proxy/.env` on the VPS
- `PROXY_API_KEY` in your bot's `.env`

### Bakong API errors
The proxy forwards requests as-is. If Bakong rejects the request:
- Verify your `BAKONG_TOKEN` is valid
- Check proxy logs for the exact Bakong error response
- Ensure the VPS IP is actually in Cambodia (use a tool like ipinfo.io)

### SSL certificate errors (if using domain)
```bash
certbot renew --dry-run
```

Auto-renewal is set up by default; certbot will renew 30 days before expiry.

## Maintenance

### View proxy logs
```bash
docker-compose logs -f
```

### Restart the proxy
```bash
cd /opt/khqr-proxy
docker-compose restart
```

### Stop the proxy
```bash
docker-compose down
```

### Update the proxy code
If you make changes locally:
```powershell
# Copy updated files to VPS
scp -r "C:\Users\Reach\OneDrive\Documents\bot telegram\khqr-proxy\src" root@YOUR_VPS_IP:/opt/khqr-proxy/
```

On the VPS:
```bash
cd /opt/khqr-proxy
docker-compose up -d --build
```

## Next Steps

- Monitor bot logs and proxy logs together during testing
- Once QR payment works, test with real accounts and stock
- Set up monitoring (optional: add Prometheus/Grafana to track proxy uptime)
- Keep your API key secure; rotate it periodically

Enjoy your Cambodia-hosted KHQR proxy!
