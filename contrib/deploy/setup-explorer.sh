#!/bin/bash
# =============================================================================
# OpenSY Block Explorer Setup Script
# =============================================================================
# Deploys btc-rpc-explorer for OpenSY blockchain.
# Requires Docker and an OpenSY node with txindex=1.
#
# Usage:
#   sudo ./setup-explorer.sh
# =============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
EXPLORER_DIR="/opt/opensy/explorer"
DOCKER_COMPOSE_VERSION="2.24.0"

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

install_docker() {
    log_info "Installing Docker..."
    
    if command -v docker &> /dev/null; then
        log_warn "Docker already installed"
        docker --version
    else
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        rm get-docker.sh
        
        # Start Docker
        systemctl enable docker
        systemctl start docker
        
        log_success "Docker installed"
    fi
    
    # Install Docker Compose plugin
    if ! docker compose version &> /dev/null; then
        log_info "Installing Docker Compose..."
        apt-get install -y docker-compose-plugin
    fi
    
    log_success "Docker ready"
}

install_nginx() {
    log_info "Installing Nginx..."
    
    apt-get update
    apt-get install -y nginx certbot python3-certbot-nginx
    
    systemctl enable nginx
    systemctl start nginx
    
    log_success "Nginx installed"
}

get_rpc_credentials() {
    log_info "Getting RPC credentials..."
    
    CRED_FILE="/home/opensy/.opensy/.rpc_credentials"
    
    if [[ -f "$CRED_FILE" ]]; then
        source "$CRED_FILE"
        log_success "Found RPC credentials"
    else
        log_warn "RPC credentials file not found"
        read -p "Enter RPC username: " RPC_USER
        read -sp "Enter RPC password: " RPC_PASS
        echo ""
    fi
    
    # Verify RPC connection
    read -p "Enter OpenSY node IP [127.0.0.1]: " NODE_IP
    NODE_IP=${NODE_IP:-"127.0.0.1"}
    
    read -p "Enter RPC port [9632]: " RPC_PORT
    RPC_PORT=${RPC_PORT:-"9632"}
}

setup_explorer() {
    log_info "Setting up block explorer..."
    
    mkdir -p "$EXPLORER_DIR"
    cd "$EXPLORER_DIR"
    
    # Prompt for domain
    read -p "Enter explorer domain (e.g., explore.opensyria.net): " EXPLORER_DOMAIN
    EXPLORER_DOMAIN=${EXPLORER_DOMAIN:-"explore.opensyria.net"}
    
    # Create docker-compose.yml
    cat > docker-compose.yml << EOF
version: '3.8'

services:
  explorer:
    image: btcpayserver/btc-rpc-explorer:latest
    container_name: opensy-explorer
    restart: unless-stopped
    ports:
      - "127.0.0.1:3002:3002"
    environment:
      # Basic Configuration
      BTCEXP_HOST: "0.0.0.0"
      BTCEXP_PORT: "3002"
      
      # Bitcoin RPC Connection (OpenSY)
      BTCEXP_BITCOIND_HOST: "${NODE_IP}"
      BTCEXP_BITCOIND_PORT: "${RPC_PORT}"
      BTCEXP_BITCOIND_USER: "${RPC_USER}"
      BTCEXP_BITCOIND_PASS: "${RPC_PASS}"
      
      # Branding
      BTCEXP_SITE_TITLE: "OpenSY Explorer"
      BTCEXP_SITE_DESC: "OpenSY Blockchain Explorer - Syria's First Blockchain"
      BTCEXP_SITE_SUBTITLE: "SYL"
      
      # Display Options
      BTCEXP_NO_RATES: "true"
      BTCEXP_PRIVACY_MODE: "false"
      BTCEXP_UI_SHOW_TOOLS_SUBHEADER: "true"
      BTCEXP_DEMO: "false"
      
      # Currency Display
      BTCEXP_DISPLAY_CURRENCY: "syl"
      
      # Performance
      BTCEXP_SLOW_DEVICE_MODE: "false"
      
    extra_hosts:
      - "host.docker.internal:host-gateway"
    
    networks:
      - opensy-net
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3002/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

networks:
  opensy-net:
    driver: bridge
EOF
    
    # Save configuration
    cat > .env << EOF
NODE_IP=${NODE_IP}
RPC_PORT=${RPC_PORT}
RPC_USER=${RPC_USER}
RPC_PASS=${RPC_PASS}
EXPLORER_DOMAIN=${EXPLORER_DOMAIN}
EOF
    chmod 600 .env
    
    log_success "Docker configuration created"
}

configure_nginx() {
    log_info "Configuring Nginx reverse proxy..."
    
    source "${EXPLORER_DIR}/.env"
    
    cat > /etc/nginx/sites-available/opensy-explorer << EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${EXPLORER_DOMAIN};

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    location / {
        proxy_pass http://127.0.0.1:3002;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 90;
    }

    # API endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:3002/api/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    
    # Enable site
    ln -sf /etc/nginx/sites-available/opensy-explorer /etc/nginx/sites-enabled/
    
    # Test and reload
    nginx -t
    systemctl reload nginx
    
    log_success "Nginx configured"
}

setup_ssl() {
    log_info "Setting up SSL certificate..."
    
    source "${EXPLORER_DIR}/.env"
    
    echo ""
    log_warn "SSL setup requires DNS to be pointing to this server."
    read -p "Is DNS configured for ${EXPLORER_DOMAIN}? [y/N] " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter email for SSL certificate: " SSL_EMAIL
        SSL_EMAIL=${SSL_EMAIL:-"admin@opensyria.net"}
        
        certbot --nginx -d "${EXPLORER_DOMAIN}" --email "${SSL_EMAIL}" --agree-tos --non-interactive
        
        log_success "SSL certificate installed"
    else
        log_warn "Skipping SSL. Run later with: certbot --nginx -d ${EXPLORER_DOMAIN}"
    fi
}

open_firewall() {
    log_info "Opening firewall ports..."
    
    ufw allow 80/tcp comment 'HTTP'
    ufw allow 443/tcp comment 'HTTPS'
    
    log_success "Firewall updated"
}

start_explorer() {
    log_info "Starting block explorer..."
    
    cd "$EXPLORER_DIR"
    docker compose up -d
    
    # Wait for container to start
    log_info "Waiting for explorer to start..."
    sleep 10
    
    if docker compose ps | grep -q "running"; then
        log_success "Block explorer started"
    else
        log_error "Failed to start explorer"
        docker compose logs
        exit 1
    fi
}

print_summary() {
    source "${EXPLORER_DIR}/.env"
    PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "<YOUR_SERVER_IP>")
    
    echo ""
    echo "============================================================================="
    echo -e "${GREEN}OpenSY Block Explorer Setup Complete!${NC}"
    echo "============================================================================="
    echo ""
    echo "Explorer URL: http://${EXPLORER_DOMAIN}"
    echo "Local URL: http://127.0.0.1:3002"
    echo ""
    echo "Docker Commands:"
    echo "  - View logs:      cd ${EXPLORER_DIR} && docker compose logs -f"
    echo "  - Restart:        cd ${EXPLORER_DIR} && docker compose restart"
    echo "  - Stop:           cd ${EXPLORER_DIR} && docker compose down"
    echo "  - Update:         cd ${EXPLORER_DIR} && docker compose pull && docker compose up -d"
    echo ""
    echo "DNS Configuration Required:"
    echo "  Add A record: ${EXPLORER_DOMAIN} -> ${PUBLIC_IP}"
    echo ""
    if [[ ! -f /etc/letsencrypt/live/${EXPLORER_DOMAIN}/fullchain.pem ]]; then
        echo "SSL Setup:"
        echo "  After DNS is configured, run:"
        echo "  certbot --nginx -d ${EXPLORER_DOMAIN}"
    fi
    echo ""
    echo "============================================================================="
}

# =============================================================================
# Main
# =============================================================================

main() {
    echo ""
    echo "============================================================================="
    echo "  OpenSY Block Explorer Setup Script"
    echo "============================================================================="
    echo ""
    
    check_root
    
    read -p "This will set up the block explorer. Continue? [y/N] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Installation cancelled"
        exit 0
    fi
    
    install_docker
    install_nginx
    get_rpc_credentials
    setup_explorer
    configure_nginx
    open_firewall
    start_explorer
    setup_ssl
    print_summary
}

main "$@"
