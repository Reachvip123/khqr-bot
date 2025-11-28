# KHQR Proxy README

A lightweight proxy for routing Bakong KHQR API requests through a Cambodia-hosted server. This allows your Telegram bot (running anywhere) to make KHQR payment requests that Bakong will accept.

## What It Does

- Proxies all requests to `https://api-bakong.nbc.gov.kh` from a Cambodia IP address.
- Protects the proxy with an `X-API-KEY` header to prevent misuse.
- Logs all requests for debugging.

## Quick Start (Local Development)

Requires Bun (install from https://bun.sh):

```bash
# Install dependencies
bun install

# Run in development mode (watches for changes)
bun run dev

# In another terminal, test:
curl -H "X-API-KEY: your-secret-key" \
  http://localhost:3000/v1/khqr/create?amount=0.01
```

## Deployment (Docker)

### Option 1: Using docker-compose (recommended)

```bash
# Create .env file
cp .env.example .env
# Edit .env and set PROXY_API_KEY to a strong secret

# Start the proxy
docker compose up -d

# View logs
docker compose logs -f

# Stop the proxy
docker compose down
```

### Option 2: Manual Docker build

```bash
docker build -t khqr-proxy .
docker run -p 3000:3000 -e PROXY_API_KEY=your-secret khqr-proxy
```

## Using the Proxy from Your Bot

### Update your bot's .env:

```
BAKONG_PROXY_URL=https://your-proxy-domain-or-ip:3000
PROXY_API_KEY=your-secret
```

### Update your bot code to use the proxy:

```python
import requests

def create_qr_via_proxy(amount):
    url = f"{BAKONG_PROXY_URL}/v1/khqr/create"
    headers = {"X-API-KEY": PROXY_API_KEY}
    params = {"amount": amount}
    res = requests.get(url, headers=headers, params=params, timeout=10)
    res.raise_for_status()
    return res.json()

def check_payment_via_proxy(md5):
    url = f"{BAKONG_PROXY_URL}/v1/khqr/check"
    headers = {"X-API-KEY": PROXY_API_KEY}
    params = {"md5": md5}
    res = requests.get(url, headers=headers, params=params, timeout=10)
    res.raise_for_status()
    return res.json()
```

## Environment Variables

- `PROXY_API_KEY` — API key header value (required for security)
- `PORT` — Port to listen on (default: 3000)
- `NODE_ENV` — Set to `production` for deployment

## Troubleshooting

- **"Invalid API key"** — Make sure you're sending the correct `X-API-KEY` header.
- **Connection refused** — Ensure the proxy is running and the domain/port are correct.
- **Bakong API errors** — Check proxy logs (`docker compose logs`) to see Bakong's response.

## Security Notes

- Change `PROXY_API_KEY` in production. Use a strong, random secret.
- Only expose the proxy to your bot server (consider using a private network or VPN).
- The proxy forwards all requests; do not expose it publicly without authentication.
- For production, consider adding rate limiting and request logging.

## License

MIT
