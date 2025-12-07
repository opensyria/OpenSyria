# OpenSyria Infrastructure Deployment Guide

## Complete Setup: Oracle Cloud (Free) + Hetzner (Budget) + Cloudflare (Free)

**Total Monthly Cost: ~$7-10/month**

This guide will walk you through deploying a production-ready OpenSyria blockchain infrastructure using the most cost-effective approach.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Prerequisites](#2-prerequisites)
3. [Phase 1: Domain & Cloudflare Setup](#3-phase-1-domain--cloudflare-setup)
4. [Phase 2: Oracle Cloud Free Tier Setup](#4-phase-2-oracle-cloud-free-tier-setup)
5. [Phase 3: Hetzner Budget Nodes](#5-phase-3-hetzner-budget-nodes)
6. [Phase 4: DNS Seeder Configuration](#6-phase-4-dns-seeder-configuration)
7. [Phase 5: Block Explorer Deployment](#7-phase-5-block-explorer-deployment)
8. [Phase 6: Monitoring Setup](#8-phase-6-monitoring-setup)
9. [Phase 7: Final Integration](#9-phase-7-final-integration)
10. [AWS Enterprise Upgrade Path](#10-aws-enterprise-upgrade-path)
11. [Maintenance Procedures](#11-maintenance-procedures)

---

## 1. Architecture Overview

```
                                    INTERNET
                                        │
                                        ▼
                    ┌───────────────────────────────────────┐
                    │           CLOUDFLARE (FREE)           │
                    │  • DNS Hosting                        │
                    │  • DDoS Protection                    │
                    │  • CDN for static assets              │
                    │  • SSL/TLS Termination                │
                    └───────────────────────────────────────┘
                                        │
            ┌───────────────────────────┼───────────────────────────┐
            │                           │                           │
            ▼                           ▼                           ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│  ORACLE CLOUD FREE  │   │  ORACLE CLOUD FREE  │   │   HETZNER (€6.58)   │
│     SINGAPORE       │   │     FRANKFURT       │   │      GERMANY        │
│                     │   │                     │   │                     │
│  ┌───────────────┐  │   │  ┌───────────────┐  │   │  ┌───────────────┐  │
│  │  Seed Node 1  │  │   │  │  Seed Node 2  │  │   │  │  Seed Node 3  │  │
│  │  2 OCPU       │  │   │  │  2 OCPU       │  │   │  │  2 vCPU       │  │
│  │  12GB RAM     │  │   │  │  12GB RAM     │  │   │  │  4GB RAM      │  │
│  │  100GB SSD    │  │   │  │  100GB SSD    │  │   │  │  40GB SSD     │  │
│  └───────────────┘  │   │  └───────────────┘  │   │  └───────────────┘  │
│                     │   │                     │   │                     │
│  ┌───────────────┐  │   │                     │   │  ┌───────────────┐  │
│  │  DNS Seeder   │  │   │                     │   │  │Block Explorer │  │
│  │  (shared)     │  │   │                     │   │  │  (CX22)       │  │
│  └───────────────┘  │   │                     │   │  └───────────────┘  │
└─────────────────────┘   └─────────────────────┘   └─────────────────────┘

Cost Breakdown:
├── Oracle Cloud Singapore:  $0/month (Free Forever)
├── Oracle Cloud Frankfurt:  $0/month (Free Forever)
├── Hetzner CX22 (Node):     €3.29/month (~$3.50)
├── Hetzner CX22 (Explorer): €3.29/month (~$3.50)
├── Cloudflare:              $0/month (Free)
├── Domain (opensyria.net):  ~$12/year (~$1/month)
└── TOTAL:                   ~$8/month
```

---

## 2. Prerequisites

### 2.1 Accounts Required

| Service | URL | Credit Card Required? |
|---------|-----|----------------------|
| Oracle Cloud | https://cloud.oracle.com | Yes (for verification, not charged) |
| Hetzner Cloud | https://console.hetzner.cloud | Yes |
| Cloudflare | https://cloudflare.com | No |
| Domain Registrar | Namecheap, Porkbun, etc. | Yes |

### 2.2 Local Requirements

```bash
# Required on your local machine
brew install ssh-keygen  # or use existing SSH keys
ssh-keygen -t ed25519 -C "opensyria-deploy"
cat ~/.ssh/id_ed25519.pub  # Save this for later
```

### 2.3 Domain Registration

Register `opensyria.net` (or your chosen domain) at:
- **Porkbun** (~$9/year) - Recommended, cheapest
- **Namecheap** (~$12/year) - Good support
- **Cloudflare Registrar** (~$10/year) - Direct integration

---

## 3. Phase 1: Domain & Cloudflare Setup

### 3.1 Create Cloudflare Account

1. Go to https://cloudflare.com
2. Sign up for free account
3. Verify email

### 3.2 Add Your Domain to Cloudflare

1. Click "Add a Site"
2. Enter `opensyria.net`
3. Select **Free Plan**
4. Cloudflare will scan existing DNS records
5. Note the Cloudflare nameservers:
   ```
   Example:
   - aria.ns.cloudflare.com
   - ben.ns.cloudflare.com
   ```

### 3.3 Update Domain Nameservers

At your domain registrar:
1. Find "Nameservers" settings
2. Change to Custom/Cloudflare nameservers
3. Enter both Cloudflare nameservers
4. Save and wait 24-48 hours for propagation

### 3.4 Initial DNS Records (Placeholder)

In Cloudflare DNS dashboard, add these placeholder records:

| Type | Name | Content | Proxy | TTL |
|------|------|---------|-------|-----|
| A | @ | 1.2.3.4 | Yes | Auto |
| A | www | 1.2.3.4 | Yes | Auto |
| A | seed | 1.2.3.4 | No | Auto |
| A | seed2 | 1.2.3.4 | No | Auto |
| A | seed3 | 1.2.3.4 | No | Auto |
| A | explore | 1.2.3.4 | Yes | Auto |
| A | api | 1.2.3.4 | Yes | Auto |
| A | stats | 1.2.3.4 | Yes | Auto |

> **Note:** We'll update these IPs after deploying servers. Seed nodes must have Proxy OFF (gray cloud) for P2P to work.

### 3.5 Cloudflare SSL/TLS Settings

1. Go to SSL/TLS → Overview
2. Set mode to **Full (strict)**
3. Go to Edge Certificates
4. Enable **Always Use HTTPS**
5. Enable **Automatic HTTPS Rewrites**

---

## 4. Phase 2: Oracle Cloud Free Tier Setup

### 4.1 Create Oracle Cloud Account

1. Go to https://cloud.oracle.com
2. Click "Start for free"
3. Fill in details (use real info - they verify)
4. Add credit card (verification only, won't be charged for free tier)
5. Select home region: **Choose Frankfurt (eu-frankfurt-1)**

> ⚠️ **Important:** Your home region cannot be changed. Frankfurt is recommended for European presence.

### 4.2 Understanding Oracle Cloud Free Tier

**Always Free Resources:**
- 4 Ampere A1 (ARM) OCPUs + 24GB RAM total
- 200GB block storage
- 10TB outbound data/month
- 2 AMD micro instances (1GB RAM each) - less useful
- 1 Load Balancer

**Our Allocation:**
- Seed Node 1: 2 OCPU, 12GB RAM (Singapore)
- Seed Node 2: 2 OCPU, 12GB RAM (Frankfurt)

### 4.3 Create Virtual Cloud Network (VCN)

1. Go to **Networking → Virtual Cloud Networks**
2. Click **Start VCN Wizard**
3. Select **Create VCN with Internet Connectivity**
4. Configure:
   ```
   VCN Name: opensyria-vcn
   VCN CIDR: 10.0.0.0/16
   Public Subnet CIDR: 10.0.0.0/24
   Private Subnet CIDR: 10.0.1.0/24
   ```
5. Click **Create**

### 4.4 Configure Security List (Firewall)

1. Go to **Networking → Virtual Cloud Networks**
2. Click on `opensyria-vcn`
3. Click on **Security Lists** → **Default Security List**
4. Add **Ingress Rules**:

| Source CIDR | Protocol | Dest Port | Description |
|-------------|----------|-----------|-------------|
| 0.0.0.0/0 | TCP | 22 | SSH |
| 0.0.0.0/0 | TCP | 9633 | OpenSyria P2P |
| 0.0.0.0/0 | TCP | 19633 | OpenSyria Testnet |
| 0.0.0.0/0 | UDP | 53 | DNS Seeder |
| 0.0.0.0/0 | TCP | 53 | DNS Seeder |
| 0.0.0.0/0 | TCP | 8332 | RPC (optional) |

### 4.5 Create Seed Node 1 (Frankfurt)

1. Go to **Compute → Instances**
2. Click **Create Instance**
3. Configure:
   ```
   Name: opensyria-seed-1
   Compartment: (root)
   
   Placement:
     Availability Domain: AD-1 (or any available)
   
   Image: 
     - Click "Change Image"
     - Select "Ubuntu"
     - Version: 22.04 (Canonical Ubuntu)
     - Image type: Platform image
   
   Shape:
     - Click "Change Shape"
     - Select "Ampere" (ARM)
     - Series: VM.Standard.A1.Flex
     - OCPUs: 2
     - Memory: 12 GB
   
   Networking:
     - VCN: opensyria-vcn
     - Subnet: Public Subnet
     - Public IP: Assign IPv4
   
   SSH Keys:
     - Paste your public key from: cat ~/.ssh/id_ed25519.pub
   
   Boot Volume:
     - Size: 100 GB
     - VPU: 10 (Balanced)
   ```
4. Click **Create**
5. Note the **Public IP** when assigned

### 4.6 Create Seed Node 2 (Singapore - Different Region)

1. Change region selector (top right) to **Singapore (ap-singapore-1)**
2. You need to set up a new VCN in this region (repeat 4.3 and 4.4)
3. Create instance with same specs as Seed Node 1
4. Note the **Public IP**

### 4.7 Initial Server Setup (Both Nodes)

SSH into each node:

```bash
ssh -i ~/.ssh/id_ed25519 ubuntu@<PUBLIC_IP>
```

Run initial setup:

```bash
#!/bin/bash
# Run on BOTH Oracle Cloud instances

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y \
    build-essential \
    cmake \
    pkg-config \
    libevent-dev \
    libboost-dev \
    libboost-system-dev \
    libboost-filesystem-dev \
    libboost-test-dev \
    libsqlite3-dev \
    libzmq3-dev \
    libssl-dev \
    git \
    ufw \
    fail2ban \
    htop \
    tmux

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 9633/tcp    # OpenSyria P2P
sudo ufw allow 53/udp      # DNS (only on seed1)
sudo ufw allow 53/tcp      # DNS (only on seed1)
sudo ufw --force enable

# Configure fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Create opensyria user
sudo useradd -m -s /bin/bash opensyria
sudo usermod -aG sudo opensyria

# Create data directory
sudo mkdir -p /opt/opensyria
sudo chown opensyria:opensyria /opt/opensyria
```

### 4.8 Build OpenSyria on ARM

```bash
# Switch to opensyria user
sudo su - opensyria

# Clone repository
cd /opt/opensyria
git clone https://github.com/opensyria/OpenSyria.git source
cd source

# Build for ARM64
cmake -B build \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_GUI=OFF \
    -DBUILD_TESTS=OFF

cmake --build build -j$(nproc)

# Verify build
./build/bin/opensyriad --version
```

### 4.9 Configure OpenSyria Node

```bash
# Create config directory
mkdir -p ~/.opensyria

# Generate RPC credentials
RPC_USER="opensyriarpc"
RPC_PASS=$(openssl rand -hex 32)

# Create configuration
cat > ~/.opensyria/opensyria.conf << EOF
# OpenSyria Seed Node Configuration
# Node: seed1.opensyria.net (or seed2)

# Network
server=1
daemon=1
listen=1
port=9633
bind=0.0.0.0

# Peer connections
maxconnections=256
maxuploadtarget=5000  # MB per day

# Index (required for explorer API)
txindex=1

# RPC
rpcuser=${RPC_USER}
rpcpassword=${RPC_PASS}
rpcbind=127.0.0.1
rpcallowip=127.0.0.1
rpcport=9632

# Logging
debug=net
logips=1
logtimestamps=1
shrinkdebugfile=1

# Performance
dbcache=1000  # MB - adjust based on available RAM
par=2         # Parallel script verification threads

# Seed node specific
seednode=seed2.opensyria.net:9633
seednode=seed3.opensyria.net:9633
# Add more seeds as they come online
EOF

# Save credentials for later
echo "RPC_USER=${RPC_USER}" > ~/.opensyria/.rpc_credentials
echo "RPC_PASS=${RPC_PASS}" >> ~/.opensyria/.rpc_credentials
chmod 600 ~/.opensyria/.rpc_credentials
```

### 4.10 Create Systemd Service

```bash
sudo tee /etc/systemd/system/opensyriad.service << EOF
[Unit]
Description=OpenSyria daemon
Documentation=https://opensyria.net/
After=network-online.target
Wants=network-online.target

[Service]
Type=forking
User=opensyria
Group=opensyria

ExecStart=/opt/opensyria/source/build/bin/opensyriad -daemon -conf=/home/opensyria/.opensyria/opensyria.conf -datadir=/home/opensyria/.opensyria
ExecStop=/opt/opensyria/source/build/bin/opensyria-cli stop

Restart=on-failure
RestartSec=30
TimeoutStartSec=infinity
TimeoutStopSec=600

# Hardening
PrivateTmp=true
ProtectSystem=full
NoNewPrivileges=true
PrivateDevices=true
MemoryDenyWriteExecute=true

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable opensyriad
sudo systemctl start opensyriad

# Check status
sudo systemctl status opensyriad
```

### 4.11 Verify Node Operation

```bash
# Check if daemon is running
/opt/opensyria/source/build/bin/opensyria-cli getblockchaininfo

# Check peer connections
/opt/opensyria/source/build/bin/opensyria-cli getpeerinfo

# Check network info
/opt/opensyria/source/build/bin/opensyria-cli getnetworkinfo
```

---

## 5. Phase 3: Hetzner Budget Nodes

### 5.1 Create Hetzner Account

1. Go to https://console.hetzner.cloud
2. Create account
3. Add payment method
4. Create new project: `opensyria`

### 5.2 Create Seed Node 3

1. Click **Add Server**
2. Configure:
   ```
   Location: Falkenstein (fsn1) or Nuremberg (nbg1)
   Image: Ubuntu 22.04
   Type: CX22 (2 vCPU, 4GB RAM, 40GB SSD) - €3.29/mo
   
   SSH Key: Add your public key
   
   Name: opensyria-seed-3
   ```
3. Click **Create & Buy**
4. Note the IP address

### 5.3 Create Block Explorer Server

1. Click **Add Server**
2. Configure:
   ```
   Location: Same as Seed Node 3
   Image: Ubuntu 22.04
   Type: CX22 (2 vCPU, 4GB RAM, 40GB SSD) - €3.29/mo
   
   SSH Key: Add your public key
   
   Name: opensyria-explorer
   ```
3. Click **Create & Buy**
4. Note the IP address

### 5.4 Configure Hetzner Firewall

1. Go to **Firewalls** → **Create Firewall**
2. Name: `opensyria-fw`
3. Inbound Rules:

| Protocol | Port | Source | Description |
|----------|------|--------|-------------|
| TCP | 22 | Any | SSH |
| TCP | 9633 | Any | P2P |
| TCP | 80 | Any | HTTP |
| TCP | 443 | Any | HTTPS |

4. Apply to both servers

### 5.5 Setup Seed Node 3

SSH in and run the same setup as Oracle nodes (Section 4.7 - 4.11), with these adjustments:

```bash
# opensyria.conf for seed3
cat > ~/.opensyria/opensyria.conf << EOF
# OpenSyria Seed Node 3 Configuration

server=1
daemon=1
listen=1
port=9633
bind=0.0.0.0

maxconnections=125  # Lower due to less RAM
txindex=1

rpcuser=opensyriarpc
rpcpassword=$(openssl rand -hex 32)
rpcbind=127.0.0.1
rpcallowip=127.0.0.1

dbcache=512  # Lower due to less RAM
par=2

seednode=seed.opensyria.net:9633
seednode=seed2.opensyria.net:9633
EOF
```

---

## 6. Phase 4: DNS Seeder Configuration

### 6.1 Build DNS Seeder (On Seed Node 1)

```bash
# SSH into seed1 (Oracle Singapore)
ssh ubuntu@<SEED1_IP>
sudo su - opensyria

# Clone bitcoin-seeder
cd /opt/opensyria
git clone https://github.com/sipa/bitcoin-seeder.git
cd bitcoin-seeder

# Modify for OpenSyria
# Edit main.cpp to change:
#   - pchMessageStart to OpenSyria's magic bytes
#   - nDefaultPort to 9633
#   - strDNSHost
```

### 6.2 Create OpenSyria Seeder Patch

```bash
cat > opensyria-seeder.patch << 'EOF'
--- a/main.cpp
+++ b/main.cpp
@@ -15,9 +15,9 @@ using namespace std;
 
 class CAddrDbStats {
 public:
-  int nBanned;
-  int nAvail;
-  int nTracked;
+  int nBanned = 0;
+  int nAvail = 0;
+  int nTracked = 0;
 };
 
-static const unsigned char pchMessageStart[4] = {0xf9, 0xbe, 0xb4, 0xd9};
+static const unsigned char pchMessageStart[4] = {0x53, 0x59, 0x4c, 0x4d}; // SYLM
-static const int nDefaultPort = 8333;
+static const int nDefaultPort = 9633;
 
 class CDnsSeedOpts {
 public:
-  string host = "seed.bitcoin.sipa.be";
-  string ns = "vps.bitcoin.sipa.be";
-  string mbox = "sipa.bitcoin.sipa.be";
+  string host = "seed.opensyria.net";
+  string ns = "ns1.opensyria.net";
+  string mbox = "admin.opensyria.net";
EOF

# Apply patch (manual edits may be needed)
# Then build
make
```

### 6.3 Run DNS Seeder

```bash
# Create systemd service
sudo tee /etc/systemd/system/opensyria-seeder.service << EOF
[Unit]
Description=OpenSyria DNS Seeder
After=network.target opensyriad.service

[Service]
Type=simple
User=opensyria
WorkingDirectory=/opt/opensyria/bitcoin-seeder
ExecStart=/opt/opensyria/bitcoin-seeder/dnsseed -h seed.opensyria.net -n ns1.opensyria.net -m admin.opensyria.net
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable opensyria-seeder
sudo systemctl start opensyria-seeder
```

### 6.4 Configure Cloudflare DNS for Seeder

In Cloudflare DNS settings, update:

| Type | Name | Content | Proxy | TTL |
|------|------|---------|-------|-----|
| A | ns1 | \<SEED1_IP\> | OFF | Auto |
| NS | seed | ns1.opensyria.net | - | Auto |

This delegates `seed.opensyria.net` to your seeder.

---

## 7. Phase 5: Block Explorer Deployment

### 7.1 Setup Explorer Server

```bash
# SSH into explorer server (Hetzner)
ssh root@<EXPLORER_IP>

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install -y docker-compose-plugin

# Create explorer directory
mkdir -p /opt/explorer
cd /opt/explorer
```

### 7.2 Option A: BTC RPC Explorer (Lightweight)

```bash
# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3'
services:
  explorer:
    image: btcpayserver/btc-rpc-explorer:latest
    container_name: opensyria-explorer
    restart: always
    ports:
      - "3002:3002"
    environment:
      BTCEXP_HOST: "0.0.0.0"
      BTCEXP_PORT: "3002"
      BTCEXP_BITCOIND_HOST: "host.docker.internal"
      BTCEXP_BITCOIND_PORT: "9632"
      BTCEXP_BITCOIND_USER: "opensyriarpc"
      BTCEXP_BITCOIND_PASS: "<RPC_PASSWORD>"
      BTCEXP_BITCOIND_COOKIE: ""
      BTCEXP_SITE_TITLE: "OpenSyria Explorer"
      BTCEXP_SITE_DESC: "OpenSyria Blockchain Explorer"
      BTCEXP_NO_RATES: "true"
      BTCEXP_PRIVACY_MODE: "false"
    extra_hosts:
      - "host.docker.internal:host-gateway"
EOF

# Start explorer
docker compose up -d
```

### 7.3 Option B: Mempool.space (Full-Featured)

```bash
# Clone mempool
git clone https://github.com/mempool/mempool.git
cd mempool/docker

# Configure for OpenSyria
cp docker-compose.yml docker-compose.yml.bak

# Edit configuration (create .env file)
cat > .env << EOF
MEMPOOL_BACKEND=electrs
CORE_RPC_HOST=<SEED_NODE_IP>
CORE_RPC_PORT=9632
CORE_RPC_USERNAME=opensyriarpc
CORE_RPC_PASSWORD=<RPC_PASSWORD>
DATABASE_HOST=mariadb
DATABASE_USER=mempool
DATABASE_PASSWORD=$(openssl rand -hex 16)
DATABASE_NAME=mempool
EOF

# Start mempool stack
docker compose up -d
```

### 7.4 Setup Nginx Reverse Proxy

```bash
# Install Nginx
sudo apt install -y nginx certbot python3-certbot-nginx

# Create Nginx config
sudo tee /etc/nginx/sites-available/explorer << 'EOF'
server {
    listen 80;
    server_name explore.opensyria.net;

    location / {
        proxy_pass http://127.0.0.1:3002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/explorer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Get SSL certificate (after DNS is pointed)
sudo certbot --nginx -d explore.opensyria.net
```

---

## 8. Phase 6: Monitoring Setup

### 8.1 Grafana Cloud (Free Tier)

1. Go to https://grafana.com/products/cloud/
2. Create free account (50GB free)
3. Note your Grafana Cloud credentials

### 8.2 Install Prometheus Node Exporter (All Nodes)

```bash
# Download and install
wget https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-arm64.tar.gz
tar xvfz node_exporter-*.tar.gz
sudo mv node_exporter-*/node_exporter /usr/local/bin/

# Create systemd service
sudo tee /etc/systemd/system/node_exporter.service << EOF
[Unit]
Description=Node Exporter
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/node_exporter
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable node_exporter
sudo systemctl start node_exporter
```

### 8.3 Install Grafana Agent (All Nodes)

```bash
# Download Grafana Agent
wget https://github.com/grafana/agent/releases/download/v0.40.0/grafana-agent-linux-arm64.zip
unzip grafana-agent-*.zip
sudo mv grafana-agent-linux-arm64 /usr/local/bin/grafana-agent

# Create config
sudo mkdir -p /etc/grafana-agent
sudo tee /etc/grafana-agent/agent.yaml << EOF
server:
  log_level: info

metrics:
  global:
    scrape_interval: 60s
    remote_write:
      - url: https://prometheus-prod-10-prod-us-central-0.grafana.net/api/prom/push
        basic_auth:
          username: <GRAFANA_CLOUD_USER>
          password: <GRAFANA_CLOUD_API_KEY>

  configs:
    - name: opensyria
      scrape_configs:
        - job_name: 'node'
          static_configs:
            - targets: ['localhost:9100']
              labels:
                instance: 'seed1.opensyria.net'
                network: 'mainnet'
EOF

# Create service and start
sudo systemctl enable grafana-agent
sudo systemctl start grafana-agent
```

### 8.4 Create Monitoring Dashboard

Import the Bitcoin Core Grafana dashboard and modify for OpenSyria metrics.

---

## 9. Phase 7: Final Integration

### 9.1 Update Cloudflare DNS Records

Now that all servers are deployed, update DNS:

| Type | Name | Content | Proxy |
|------|------|---------|-------|
| A | @ | \<EXPLORER_IP\> | ON |
| A | www | \<EXPLORER_IP\> | ON |
| A | seed | (NS record) | OFF |
| A | seed2 | \<SEED2_IP\> | OFF |
| A | seed3 | \<SEED3_IP\> | OFF |
| A | explore | \<EXPLORER_IP\> | ON |
| A | ns1 | \<SEED1_IP\> | OFF |
| NS | seed | ns1.opensyria.net | - |

### 9.2 Update OpenSyria Source Code

After deploying infrastructure, update `chainparams.cpp` with real seeds:

```cpp
// In src/kernel/chainparams.cpp
vSeeds.emplace_back("seed.opensyria.net");
vSeeds.emplace_back("seed2.opensyria.net");
vSeeds.emplace_back("seed3.opensyria.net");
```

Also populate `contrib/seeds/nodes_main.txt`:

```
<SEED1_IP>:9633
<SEED2_IP>:9633
<SEED3_IP>:9633
```

### 9.3 Verification Checklist

```bash
# Test DNS seeder
dig seed.opensyria.net

# Test node connectivity
nc -zv seed.opensyria.net 9633
nc -zv seed2.opensyria.net 9633
nc -zv seed3.opensyria.net 9633

# Test explorer
curl -I https://explore.opensyria.net

# Test RPC (locally on node)
opensyria-cli getblockchaininfo
```

---

## 10. AWS Enterprise Upgrade Path

When OpenSyria grows and requires enterprise-grade infrastructure, follow this migration plan.

### 10.1 When to Migrate to AWS

**Trigger Conditions:**
- Daily active users > 10,000
- Node count > 100
- Transaction volume > 10,000/day
- Enterprise/government partnerships requiring SLAs
- Geographic expansion to 5+ regions
- Need for compliance certifications (SOC2, ISO27001)

### 10.2 AWS Architecture (Target State)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AWS GLOBAL                                      │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         ROUTE 53 (DNS)                               │   │
│  │  • Latency-based routing                                            │   │
│  │  • Health checks                                                     │   │
│  │  • Failover                                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│         ┌──────────────────────────┼──────────────────────────┐            │
│         │                          │                          │            │
│         ▼                          ▼                          ▼            │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐      │
│  │   US-EAST-1     │     │   EU-WEST-1     │     │  AP-SOUTHEAST-1 │      │
│  │   (Virginia)    │     │   (Ireland)     │     │   (Singapore)   │      │
│  │                 │     │                 │     │                 │      │
│  │  ┌───────────┐  │     │  ┌───────────┐  │     │  ┌───────────┐  │      │
│  │  │    ALB    │  │     │  │    ALB    │  │     │  │    ALB    │  │      │
│  │  └─────┬─────┘  │     │  └─────┬─────┘  │     │  └─────┬─────┘  │      │
│  │        │        │     │        │        │     │        │        │      │
│  │  ┌─────┴─────┐  │     │  ┌─────┴─────┐  │     │  ┌─────┴─────┐  │      │
│  │  │  ECS/EKS  │  │     │  │  ECS/EKS  │  │     │  │  ECS/EKS  │  │      │
│  │  │ Fargate   │  │     │  │ Fargate   │  │     │  │ Fargate   │  │      │
│  │  └─────┬─────┘  │     │  └─────┬─────┘  │     │  └─────┬─────┘  │      │
│  │        │        │     │        │        │     │        │        │      │
│  │  ┌─────┴─────┐  │     │  ┌─────┴─────┐  │     │  ┌─────┴─────┐  │      │
│  │  │ EC2 Nodes │  │     │  │ EC2 Nodes │  │     │  │ EC2 Nodes │  │      │
│  │  │ (3x m6i)  │  │     │  │ (3x m6i)  │  │     │  │ (3x m6i)  │  │      │
│  │  └───────────┘  │     │  └───────────┘  │     │  └───────────┘  │      │
│  │                 │     │                 │     │                 │      │
│  │  ┌───────────┐  │     │  ┌───────────┐  │     │  ┌───────────┐  │      │
│  │  │  Aurora   │  │     │  │  Aurora   │  │     │  │  Aurora   │  │      │
│  │  │  (Read)   │  │     │  │ (Primary) │  │     │  │  (Read)   │  │      │
│  │  └───────────┘  │     │  └───────────┘  │     │  └───────────┘  │      │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘      │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      SHARED SERVICES                                 │   │
│  │  • S3 (Backups, chain data snapshots)                               │   │
│  │  • CloudWatch (Logging, metrics, alarms)                            │   │
│  │  • Secrets Manager (RPC credentials)                                │   │
│  │  • WAF (API protection)                                              │   │
│  │  • Shield Advanced (DDoS protection)                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 10.3 AWS Migration Steps

#### Step 1: Set Up AWS Organization (Week 1)

```bash
# Create AWS accounts structure
opensyria-org/
├── opensyria-prod/      # Production workloads
├── opensyria-staging/   # Staging environment
├── opensyria-security/  # Security & logging
└── opensyria-shared/    # Shared services (S3, ECR)
```

#### Step 2: Infrastructure as Code (Week 1-2)

Create Terraform/CloudFormation templates:

```hcl
# terraform/main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

module "vpc" {
  source = "./modules/vpc"
  
  name = "opensyria-vpc"
  cidr = "10.0.0.0/16"
  
  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  
  enable_nat_gateway = true
  single_nat_gateway = false
  
  tags = {
    Project = "OpenSyria"
    Environment = "Production"
  }
}

module "ecs_cluster" {
  source = "./modules/ecs"
  
  cluster_name = "opensyria-cluster"
  vpc_id       = module.vpc.vpc_id
  subnet_ids   = module.vpc.private_subnets
}

module "opensyria_nodes" {
  source = "./modules/ec2-nodes"
  
  instance_count = 3
  instance_type  = "m6i.large"
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  
  root_volume_size = 500  # GB for full node
}
```

#### Step 3: Container Registry Setup (Week 2)

```bash
# Create ECR repository
aws ecr create-repository \
    --repository-name opensyria/node \
    --image-scanning-configuration scanOnPush=true

# Build and push Docker image
docker build -t opensyria-node .
docker tag opensyria-node:latest <account>.dkr.ecr.us-east-1.amazonaws.com/opensyria/node:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/opensyria/node:latest
```

#### Step 4: ECS Task Definition (Week 2)

```json
{
  "family": "opensyria-node",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "8192",
  "containerDefinitions": [
    {
      "name": "opensyriad",
      "image": "<account>.dkr.ecr.us-east-1.amazonaws.com/opensyria/node:latest",
      "essential": true,
      "portMappings": [
        {"containerPort": 9633, "protocol": "tcp"},
        {"containerPort": 9632, "protocol": "tcp"}
      ],
      "mountPoints": [
        {
          "sourceVolume": "opensyria-data",
          "containerPath": "/home/opensyria/.opensyria"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/opensyria-node",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "secrets": [
        {
          "name": "RPC_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<account>:secret:opensyria/rpc"
        }
      ]
    }
  ],
  "volumes": [
    {
      "name": "opensyria-data",
      "efsVolumeConfiguration": {
        "fileSystemId": "fs-xxxxx",
        "transitEncryption": "ENABLED"
      }
    }
  ]
}
```

#### Step 5: Route 53 DNS Migration (Week 3)

```bash
# Create hosted zone
aws route53 create-hosted-zone \
    --name opensyria.net \
    --caller-reference $(date +%s)

# Create health checks
aws route53 create-health-check \
    --caller-reference $(date +%s) \
    --health-check-config '{
        "IPAddress": "<NODE_IP>",
        "Port": 9633,
        "Type": "TCP",
        "RequestInterval": 30,
        "FailureThreshold": 3
    }'

# Create latency-based routing records
aws route53 change-resource-record-sets \
    --hosted-zone-id Z1234567890 \
    --change-batch '{
        "Changes": [{
            "Action": "CREATE",
            "ResourceRecordSet": {
                "Name": "seed.opensyria.net",
                "Type": "A",
                "SetIdentifier": "us-east-1",
                "Region": "us-east-1",
                "TTL": 60,
                "ResourceRecords": [{"Value": "<US_NODE_IP>"}],
                "HealthCheckId": "<HEALTH_CHECK_ID>"
            }
        }]
    }'
```

#### Step 6: Monitoring & Alerting (Week 3)

```bash
# Create CloudWatch dashboard
aws cloudwatch put-dashboard \
    --dashboard-name OpenSyria-Network \
    --dashboard-body file://dashboard.json

# Create alarms
aws cloudwatch put-metric-alarm \
    --alarm-name "OpenSyria-HighCPU" \
    --alarm-description "Alert when CPU exceeds 80%" \
    --metric-name CPUUtilization \
    --namespace AWS/EC2 \
    --statistic Average \
    --period 300 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2 \
    --alarm-actions arn:aws:sns:us-east-1:<account>:opensyria-alerts
```

### 10.4 AWS Cost Estimation (Monthly)

| Service | Configuration | Est. Cost |
|---------|--------------|-----------|
| EC2 (9 nodes) | 3x m6i.large per region × 3 regions | $550 |
| EBS Storage | 500GB gp3 × 9 | $225 |
| NAT Gateway | 3 regions | $100 |
| ALB | 3 regions | $60 |
| Route 53 | Hosted zone + health checks | $20 |
| CloudWatch | Logs + metrics | $50 |
| S3 | Backups + snapshots | $30 |
| Data Transfer | ~2TB/month | $180 |
| WAF | Basic protection | $25 |
| Secrets Manager | 10 secrets | $5 |
| **Total** | | **~$1,250/month** |

**With Reserved Instances (1-year):** ~$800/month (35% savings)

### 10.5 Migration Timeline

```
MIGRATION TIMELINE (8 WEEKS)
═══════════════════════════════════════════════════════════════

Week 1-2: PREPARATION
├── Set up AWS Organization & accounts
├── Create IAM roles & policies
├── Deploy VPC in all regions
└── Create Terraform modules

Week 3-4: PARALLEL DEPLOYMENT
├── Deploy EC2 nodes in AWS (alongside existing)
├── Configure ECS clusters
├── Set up Aurora for explorer
└── Migrate container images to ECR

Week 5-6: TESTING
├── Sync AWS nodes with network
├── Test failover scenarios
├── Verify latency & performance
└── Security audit

Week 7: DNS MIGRATION
├── Add AWS nodes to DNS rotation
├── Configure health checks
├── Gradually shift traffic (10% → 50% → 100%)
└── Monitor for issues

Week 8: CLEANUP
├── Decommission Oracle/Hetzner nodes
├── Final verification
├── Documentation update
└── Post-migration review
```

---

## 11. Maintenance Procedures

### 11.1 Regular Maintenance Tasks

```bash
# Weekly: Update node software
cd /opt/opensyria/source
git pull origin main
cmake --build build -j$(nproc)
sudo systemctl restart opensyriad

# Monthly: System updates
sudo apt update && sudo apt upgrade -y
sudo reboot

# Monthly: Check disk usage
df -h
# Prune if needed:
opensyria-cli pruneblockchain 1000

# Quarterly: Rotate RPC credentials
NEW_PASS=$(openssl rand -hex 32)
sed -i "s/rpcpassword=.*/rpcpassword=${NEW_PASS}/" ~/.opensyria/opensyria.conf
sudo systemctl restart opensyriad
```

### 11.2 Backup Procedures

```bash
# Daily: Backup wallet (if enabled)
opensyria-cli backupwallet /opt/opensyria/backups/wallet-$(date +%Y%m%d).dat

# Weekly: Backup chainstate (optional, large)
tar -czf /opt/opensyria/backups/chainstate-$(date +%Y%m%d).tar.gz ~/.opensyria/chainstate/

# Upload to remote storage
aws s3 sync /opt/opensyria/backups/ s3://opensyria-backups/node1/
# OR
rclone sync /opt/opensyria/backups/ gdrive:opensyria-backups/
```

### 11.3 Emergency Procedures

```bash
# Node won't start - check logs
journalctl -u opensyriad -f

# Chain fork detected - resync
opensyria-cli stop
rm -rf ~/.opensyria/chainstate ~/.opensyria/blocks
systemctl start opensyriad

# Network partition - force reconnect
opensyria-cli addnode seed.opensyria.net onetry
opensyria-cli addnode seed2.opensyria.net onetry
```

---

## Quick Reference

### Service URLs
- **Main Site:** https://opensyria.net
- **Block Explorer:** https://explore.opensyria.net
- **Network Stats:** https://stats.opensyria.net
- **API Docs:** https://api.opensyria.net/docs

### Port Reference
| Port | Protocol | Service |
|------|----------|---------|
| 9633 | TCP | P2P Mainnet |
| 9632 | TCP | RPC |
| 19633 | TCP | P2P Testnet |
| 53 | UDP/TCP | DNS Seeder |

### Support Contacts
- **Technical Issues:** admin@opensyria.net
- **Security Reports:** security@opensyria.net
- **GitHub:** https://github.com/opensyria/OpenSyria

---

*Last Updated: December 2025*
*Version: 1.0*
