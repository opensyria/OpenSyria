#!/bin/bash
# OpenSY Web Wallet Deployment Script
# Run on the same server as your OpenSY node

set -e

echo "🔐 OpenSY Watch-Only Web Wallet Deployment"
echo "==========================================="

# Configuration - EDIT THESE
DEPLOY_DIR="/opt/opensy/web-wallet"
DOMAIN="wallet.opensyria.net"
RPC_USER="${OPENSY_RPC_USER:-opensy}"
RPC_PASSWORD="${OPENSY_RPC_PASSWORD:-CHANGE_ME}"
RPC_HOST="127.0.0.1"
RPC_PORT="9632"
API_PORT="8080"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo ""
echo "Configuration:"
echo "  Deploy dir: $DEPLOY_DIR"
echo "  Domain: $DOMAIN"
echo "  RPC: $RPC_HOST:$RPC_PORT"
echo ""

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Please run with sudo${NC}"
  exit 1
fi

# 1. Create deployment directory
echo "[1/7] Creating deployment directory..."
mkdir -p "$DEPLOY_DIR"
cp -r contrib/web-wallet/* "$DEPLOY_DIR/"

# 2. Install Python dependencies
echo "[2/7] Installing Python dependencies..."
pip3 install flask flask-cors flask-limiter gunicorn requests cachetools

# 3. Create systemd service for API
echo "[3/7] Creating systemd service..."
cat > /etc/systemd/system/opensy-wallet-api.service << EOF
[Unit]
Description=OpenSY Web Wallet API
After=network.target opensyd.service

[Service]
Type=simple
User=opensy
Group=opensy
WorkingDirectory=$DEPLOY_DIR/api
Environment="OPENSY_RPC_HOST=$RPC_HOST"
Environment="OPENSY_RPC_PORT=$RPC_PORT"
Environment="OPENSY_RPC_USER=$RPC_USER"
Environment="OPENSY_RPC_PASSWORD=$RPC_PASSWORD"
Environment="API_PORT=$API_PORT"
Environment="ALLOWED_ORIGINS=https://$DOMAIN,https://wallet.opensyria.net"
ExecStart=/usr/bin/gunicorn -w 2 -b 127.0.0.1:$API_PORT server:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 4. Create nginx configuration
echo "[4/7] Creating nginx configuration..."
cat > /etc/nginx/sites-available/opensy-wallet << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    # Redirect to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;
    
    # SSL - update paths after running certbot
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' https://$DOMAIN;" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=wallet_api:10m rate=10r/s;
    
    # Static frontend
    root $DEPLOY_DIR;
    index index.html;
    
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    
    # API proxy
    location /api/ {
        limit_req zone=wallet_api burst=20 nodelay;
        
        proxy_pass http://127.0.0.1:$API_PORT/api/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts
        proxy_connect_timeout 10s;
        proxy_read_timeout 30s;
    }
}
EOF

# 5. Enable nginx site
echo "[5/7] Enabling nginx site..."
ln -sf /etc/nginx/sites-available/opensy-wallet /etc/nginx/sites-enabled/
nginx -t

# 6. SSL Certificate
echo "[6/7] SSL Certificate..."
echo "Run this command to get SSL certificate:"
echo "  sudo certbot --nginx -d $DOMAIN"
echo ""
echo "Or if DNS is not ready yet, skip for now and run later."

# 7. Start services
echo "[7/7] Starting services..."
systemctl daemon-reload
systemctl enable opensy-wallet-api
systemctl start opensy-wallet-api
systemctl reload nginx

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Update DNS: Point $DOMAIN to this server"
echo "  2. Get SSL: sudo certbot --nginx -d $DOMAIN"
echo "  3. Test: https://$DOMAIN"
echo ""
echo "Service status:"
systemctl status opensy-wallet-api --no-pager
