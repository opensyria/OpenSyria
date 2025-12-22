# OpenSY Web Watch-Only Wallet

A production-ready, mobile-friendly web interface for monitoring OpenSY addresses without exposing private keys.

## 🔒 Security

**This is a WATCH-ONLY wallet**:
- ✅ View balances and UTXOs
- ✅ Monitor multiple addresses
- ✅ Works on mobile browsers
- ❌ Cannot send transactions
- ❌ Never handles private keys

## 📁 Project Structure

```
contrib/web-wallet/
├── index.html           # Frontend web application
├── api/
│   └── server.py        # Backend API server
└── README.md            # This documentation
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Users' Browsers                       │
│               (Mobile / Desktop / Tablet)                │
└─────────────────────────────────────────────────────────┘
                          │
                          │ HTTPS
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    Nginx / Reverse Proxy                 │
│              (SSL termination, Rate limiting)            │
└─────────────────────────────────────────────────────────┘
         │                                    │
         │ Static Files                       │ /api/* 
         ▼                                    ▼
┌─────────────────────────┐       ┌─────────────────────────┐
│    index.html           │       │  API Server (Flask)     │
│   (Static CDN)          │       │  - Rate limiting        │
│                         │       │  - Response caching     │
└─────────────────────────┘       │  - CORS handling        │
                                  └─────────────────────────┘
                                              │
                                              │ RPC (localhost)
                                              ▼
                                  ┌─────────────────────────┐
                                  │    OpenSY Full Node     │
                                  │    (opensyd on 9632)    │
                                  └─────────────────────────┘
```

## 🚀 Quick Start (Development)

### 1. Start OpenSY Node

Ensure your node is running with RPC enabled:

```bash
# ~/.opensy/opensy.conf  (or ~/Library/Application Support/OpenSY/opensy.conf on macOS)
server=1
rpcuser=opensy
rpcpassword=your_password
rpcallowip=127.0.0.1
rpcbind=127.0.0.1
txindex=1
```

### 2. Install API Dependencies

```bash
cd contrib/web-wallet/api
pip install flask flask-cors flask-limiter cachetools requests
```

### 3. Run API Server

```bash
# Set environment variables
export OPENSY_RPC_USER=opensy
export OPENSY_RPC_PASSWORD=your_password
export OPENSY_RPC_HOST=127.0.0.1
export OPENSY_RPC_PORT=9632

python server.py
```

### 4. Access Web Wallet

Open http://127.0.0.1:8080 in your browser.

Or serve the frontend separately:

```bash
# In another terminal
cd contrib/web-wallet
python3 -m http.server 3000
```

Then open http://localhost:3000?api=http://127.0.0.1:8080/api

## 🌐 Production Deployment

### Option A: Docker Compose (Recommended)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  opensy-node:
    image: opensy/core:latest
    volumes:
      - opensy-data:/root/.opensy
    networks:
      - opensy-internal
    restart: unless-stopped

  api:
    build: ./api
    environment:
      - OPENSY_RPC_HOST=opensy-node
      - OPENSY_RPC_PORT=9632
      - OPENSY_RPC_USER=${RPC_USER}
      - OPENSY_RPC_PASSWORD=${RPC_PASSWORD}
      - RATE_LIMIT_PER_MINUTE=100
    depends_on:
      - opensy-node
    networks:
      - opensy-internal
      - public
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./index.html:/usr/share/nginx/html/index.html:ro
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/letsencrypt:ro
    depends_on:
      - api
    networks:
      - public
    restart: unless-stopped

volumes:
  opensy-data:

networks:
  opensy-internal:
    internal: true
  public:
```

Create `api/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    flask \
    flask-cors \
    flask-limiter \
    cachetools \
    requests \
    gunicorn

COPY server.py .

EXPOSE 8080

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "server:app"]
```

Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    include       mime.types;
    default_type  application/octet-stream;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    upstream api_backend {
        server api:8080;
    }
    
    server {
        listen 80;
        server_name wallet.opensy.org;
        return 301 https://$host$request_uri;
    }
    
    server {
        listen 443 ssl http2;
        server_name wallet.opensy.org;
        
        ssl_certificate /etc/letsencrypt/live/wallet.opensy.org/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/wallet.opensy.org/privkey.pem;
        
        # Security headers
        add_header X-Content-Type-Options nosniff;
        add_header X-Frame-Options DENY;
        add_header X-XSS-Protection "1; mode=block";
        add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';";
        
        # Static frontend
        location / {
            root /usr/share/nginx/html;
            index index.html;
            try_files $uri $uri/ /index.html;
        }
        
        # API proxy
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://api_backend/api/;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

Deploy:

```bash
# Get SSL certificate
certbot certonly --standalone -d wallet.opensy.org

# Start services
docker-compose up -d
```

### Option B: Manual Deployment

#### 1. Server Setup

```bash
# Install dependencies
sudo apt update
sudo apt install nginx python3-pip certbot python3-certbot-nginx

# Create user
sudo useradd -r -s /bin/false opensy-wallet
```

#### 2. Install API Service

```bash
# Create directory
sudo mkdir -p /opt/opensy-wallet/api
sudo cp api/server.py /opt/opensy-wallet/api/

# Install Python packages
pip3 install flask flask-cors flask-limiter cachetools requests gunicorn

# Create config
sudo tee /opt/opensy-wallet/api/.env << EOF
OPENSY_RPC_HOST=127.0.0.1
OPENSY_RPC_PORT=9632
OPENSY_RPC_USER=opensy
OPENSY_RPC_PASSWORD=your_secure_password
API_HOST=127.0.0.1
API_PORT=8080
RATE_LIMIT_PER_MINUTE=100
EOF
```

#### 3. Systemd Service

```bash
sudo tee /etc/systemd/system/opensy-wallet-api.service << EOF
[Unit]
Description=OpenSY Wallet API Server
After=network.target opensyd.service

[Service]
Type=simple
User=opensy-wallet
WorkingDirectory=/opt/opensy-wallet/api
EnvironmentFile=/opt/opensy-wallet/api/.env
ExecStart=/usr/local/bin/gunicorn -w 4 -b 127.0.0.1:8080 server:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable opensy-wallet-api
sudo systemctl start opensy-wallet-api
```

#### 4. Nginx Configuration

```bash
sudo tee /etc/nginx/sites-available/opensy-wallet << 'EOF'
server {
    listen 80;
    server_name wallet.opensy.org;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name wallet.opensy.org;
    
    ssl_certificate /etc/letsencrypt/live/wallet.opensy.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/wallet.opensy.org/privkey.pem;
    
    root /var/www/opensy-wallet;
    index index.html;
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:8080/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/opensy-wallet /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

#### 5. Deploy Frontend

```bash
sudo mkdir -p /var/www/opensy-wallet
sudo cp index.html /var/www/opensy-wallet/
sudo chown -R www-data:www-data /var/www/opensy-wallet
```

#### 6. Get SSL Certificate

```bash
sudo certbot --nginx -d wallet.opensy.org
```

## ⚙️ API Configuration

Environment variables for the API server:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENSY_RPC_HOST` | `127.0.0.1` | RPC host |
| `OPENSY_RPC_PORT` | `9632` | RPC port (mainnet) |
| `OPENSY_RPC_USER` | `opensy` | RPC username |
| `OPENSY_RPC_PASSWORD` | `password` | RPC password |
| `API_HOST` | `127.0.0.1` | API bind address |
| `API_PORT` | `8080` | API port |
| `RATE_LIMIT_PER_MINUTE` | `100` | Rate limit per IP |
| `CACHE_TTL_BLOCKCHAIN` | `10` | Cache TTL for blockchain info |
| `CACHE_TTL_ADDRESS` | `30` | Cache TTL for address queries |
| `CACHE_TTL_TX` | `300` | Cache TTL for transaction data |

## 📚 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Health check |
| `GET /api/info` | Blockchain info (height, difficulty, etc.) |
| `GET /api/address/<addr>` | Address balance and UTXOs |
| `GET /api/address/<addr>/txs` | Address transaction history |
| `GET /api/tx/<txid>` | Transaction details |
| `GET /api/block/<hash\|height>` | Block details |
| `GET /api/blocks/recent` | Recent blocks (last 10) |
| `GET /api/mempool` | Mempool statistics |
| `GET /api/estimate-fee` | Fee estimation |

## 🔐 Security Considerations

### What This Wallet Does NOT Do
- Generate or store private keys
- Sign transactions
- Access your funds directly

### Production Security Checklist

- [x] RPC credentials never exposed to frontend
- [x] API server rate-limited
- [x] Response caching to reduce node load
- [x] Read-only operations only
- [ ] Enable HTTPS (required for production)
- [ ] Configure firewall (block direct RPC access)
- [ ] Use strong RPC password
- [ ] Monitor API for abuse

### Privacy
- Addresses saved in browser localStorage only
- No server-side tracking of addresses
- Clear browser data to remove all stored info

## 📱 Features

### Address Watching
- Add multiple OpenSY addresses
- Custom labels for organization
- Persistent storage (localStorage)
- Balance auto-refresh

### Network Status
- Live block height
- Network hashrate
- Difficulty
- Mempool size

### Mobile Optimized
- Responsive design
- Touch-friendly UI
- Works on all modern browsers

## 🔄 Roadmap

### v2.1
- [ ] QR code scanning for addresses
- [ ] Export address list (CSV)
- [ ] Transaction history view
- [ ] Push notifications (PWA)

### v2.2
- [ ] Multiple currency display (USD/EUR rates)
- [ ] Address book import/export
- [ ] Block explorer integration
- [ ] WebSocket for live updates

### v3.0
- [ ] PSBT viewing (unsigned transactions)
- [ ] Hardware wallet integration (watch-only)
- [ ] Multi-sig address watching

## 🤝 Contributing

1. Edit files in `contrib/web-wallet/`
2. Test locally with dev setup
3. Submit PR

## 📄 License

MIT License - Same as OpenSY Core

---

**سوريا حرة** 🇸🇾 - Built for the people of Syria
