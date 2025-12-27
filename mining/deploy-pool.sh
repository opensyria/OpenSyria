#!/bin/bash
# OpenSY Mining Pool Production Deployment
# Deploys the Stratum pool with PostgreSQL, Redis, and monitoring

set -e

echo "⛏️  OpenSY Mining Pool Deployment"
echo "================================="

# Configuration
POOL_DOMAIN="${POOL_DOMAIN:-pool.opensyria.net}"
STRATUM_PORT="${STRATUM_PORT:-3333}"
API_PORT="${API_PORT:-8080}"
METRICS_PORT="${METRICS_PORT:-9090}"

# OpenSY node connection
NODE_RPC_URL="${NODE_RPC_URL:-http://127.0.0.1:9632}"
NODE_RPC_USER="${NODE_RPC_USER:-opensy}"
NODE_RPC_PASS="${NODE_RPC_PASS:-CHANGE_ME}"

# Pool wallet for coinbase rewards
POOL_WALLET="${POOL_WALLET:-YOUR_POOL_WALLET_ADDRESS}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "Configuration:"
echo "  Pool domain: $POOL_DOMAIN"
echo "  Stratum port: $STRATUM_PORT"
echo "  Node RPC: $NODE_RPC_URL"
echo "  Pool wallet: $POOL_WALLET"
echo ""

# Pre-flight checks
echo "[1/8] Pre-flight checks..."

if [ "$POOL_WALLET" == "YOUR_POOL_WALLET_ADDRESS" ]; then
    echo -e "${RED}ERROR: Set POOL_WALLET environment variable${NC}"
    echo "  export POOL_WALLET=Fxxxxxxxxxx..."
    exit 1
fi

if ! command -v go &> /dev/null; then
    echo -e "${RED}ERROR: Go not installed. Install Go 1.21+${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: Docker not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Pre-flight checks passed${NC}"

# Navigate to mining directory
cd "$(dirname "$0")/../mining/opensy-mining"

# Build RandomX library
echo "[2/8] Building RandomX library..."
cd common
make randomx
cd ..

# Start infrastructure
echo "[3/8] Starting PostgreSQL, Redis, Prometheus..."
cd docker
docker-compose up -d
sleep 5

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
until docker-compose exec -T postgres pg_isready -U opensy; do
    sleep 2
done
echo -e "${GREEN}✓ PostgreSQL ready${NC}"

# Wait for Redis
echo "Waiting for Redis..."
until docker-compose exec -T redis redis-cli ping | grep -q PONG; do
    sleep 2
done
echo -e "${GREEN}✓ Redis ready${NC}"

cd ..

# Create production config
echo "[4/8] Creating production configuration..."
mkdir -p /etc/opensy-pool
cat > /etc/opensy-pool/config.yaml << EOF
# OpenSY Mining Pool Production Configuration
# Generated: $(date -u)

pool:
  name: "OpenSY Pool | تجمع التعدين"
  fee: 1.0  # 1% pool fee
  wallet: "$POOL_WALLET"
  
node:
  rpc_url: "$NODE_RPC_URL"
  rpc_user: "$NODE_RPC_USER"
  rpc_password: "$NODE_RPC_PASS"
  timeout: 30s
  poll_interval: 500ms

stratum:
  host: "0.0.0.0"
  port: $STRATUM_PORT
  ssl_port: 3334
  ssl_cert: "/etc/letsencrypt/live/$POOL_DOMAIN/fullchain.pem"
  ssl_key: "/etc/letsencrypt/live/$POOL_DOMAIN/privkey.pem"
  max_connections: 50000
  max_connections_per_ip: 200
  read_timeout: 5m
  write_timeout: 30s

vardiff:
  enabled: true
  target_time: 30
  retarget_time: 120
  variance_percent: 30
  min_diff: 1000
  max_diff: 10000000000
  start_diff: 10000

shares:
  stale_grace_seconds: 5
  duplicate_check_height_range: 10

payout:
  scheme: "PPLNS"
  pplns_window: 10000
  min_payout: 100  # 100 SYL minimum
  payout_interval: "6h"
  
database:
  host: "127.0.0.1"
  port: 5432
  name: "opensy_pool"
  user: "opensy"
  password: "$(openssl rand -hex 16)"
  max_connections: 50

redis:
  host: "127.0.0.1"
  port: 6379
  db: 0

api:
  host: "127.0.0.1"
  port: $API_PORT
  cors_origins:
    - "https://$POOL_DOMAIN"
    - "https://pool.opensyria.net"

metrics:
  enabled: true
  port: $METRICS_PORT

logging:
  level: "info"
  format: "json"
EOF

echo -e "${GREEN}✓ Configuration created at /etc/opensy-pool/config.yaml${NC}"

# Build pool binary
echo "[5/8] Building pool server..."
go build -o /usr/local/bin/opensy-pool ./pool/cmd/server
echo -e "${GREEN}✓ Pool binary built${NC}"

# Create systemd service
echo "[6/8] Creating systemd service..."
cat > /etc/systemd/system/opensy-pool.service << EOF
[Unit]
Description=OpenSY Mining Pool
After=network.target postgresql.service redis.service opensyd.service
Wants=postgresql.service redis.service

[Service]
Type=simple
User=opensy
Group=opensy
ExecStart=/usr/local/bin/opensy-pool --config /etc/opensy-pool/config.yaml
Restart=always
RestartSec=5
LimitNOFILE=65535
StandardOutput=journal
StandardError=journal

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/opensy-pool

[Install]
WantedBy=multi-user.target
EOF

# Create nginx config for pool API/dashboard
echo "[7/8] Creating nginx configuration..."
cat > /etc/nginx/sites-available/opensy-pool << EOF
server {
    listen 80;
    server_name $POOL_DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $POOL_DOMAIN;
    
    ssl_certificate /etc/letsencrypt/live/$POOL_DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$POOL_DOMAIN/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Pool dashboard (static files - TODO: build dashboard)
    root /var/www/opensy-pool;
    index index.html;
    
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    
    # Pool API
    location /api/ {
        proxy_pass http://127.0.0.1:$API_PORT/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
    
    # Metrics (internal only - protect in production)
    location /metrics {
        allow 127.0.0.1;
        deny all;
        proxy_pass http://127.0.0.1:$METRICS_PORT/metrics;
    }
}

# Stratum SSL termination (optional - miners can connect directly)
stream {
    upstream stratum {
        server 127.0.0.1:$STRATUM_PORT;
    }
    
    server {
        listen 3334 ssl;
        proxy_pass stratum;
        
        ssl_certificate /etc/letsencrypt/live/$POOL_DOMAIN/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/$POOL_DOMAIN/privkey.pem;
    }
}
EOF

ln -sf /etc/nginx/sites-available/opensy-pool /etc/nginx/sites-enabled/

# Enable and start services
echo "[8/8] Starting services..."
systemctl daemon-reload
systemctl enable opensy-pool
systemctl start opensy-pool
nginx -t && systemctl reload nginx

echo ""
echo -e "${GREEN}✅ Mining Pool Deployment Complete!${NC}"
echo ""
echo "Services:"
echo "  - Pool server: systemctl status opensy-pool"
echo "  - PostgreSQL: docker-compose -f docker/docker-compose.yml ps"
echo "  - Redis: docker-compose -f docker/docker-compose.yml ps"
echo ""
echo "Endpoints:"
echo "  - Stratum: stratum+tcp://$POOL_DOMAIN:$STRATUM_PORT"
echo "  - Stratum SSL: stratum+ssl://$POOL_DOMAIN:3334"
echo "  - Dashboard: https://$POOL_DOMAIN"
echo "  - API: https://$POOL_DOMAIN/api/"
echo ""
echo "Test with XMRig:"
echo "  xmrig -o $POOL_DOMAIN:$STRATUM_PORT -u <your_wallet> -p worker1 -a rx/0"
echo ""
echo "Firewall rules needed:"
echo "  sudo ufw allow $STRATUM_PORT/tcp  # Stratum"
echo "  sudo ufw allow 3334/tcp           # Stratum SSL"
echo ""
echo "Next steps:"
echo "  1. Get SSL certificate: sudo certbot certonly --nginx -d $POOL_DOMAIN"
echo "  2. Build pool dashboard UI"
echo "  3. Announce to community!"
