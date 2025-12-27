# OpenSY Deployment Day - Action Checklist

**Date**: December 27, 2025  
**Goal**: Deploy web wallet and mining pool to production

---

## Pre-Deployment Verification

### Node Health Check
```bash
# SSH to your server
ssh user@node.opensyria.net

# Verify node is synced
./opensy-cli getblockchaininfo | jq '.blocks, .headers'

# Check peer connections
./opensy-cli getconnectioncount

# Verify RPC is working
./opensy-cli getmininginfo
```

### Server Requirements

| Service | Min RAM | Min Disk | Ports |
|---------|---------|----------|-------|
| OpenSY Node | 4 GB | 50 GB SSD | 9633 (P2P), 9632 (RPC local) |
| Web Wallet API | 512 MB | 1 GB | 8080 (local) |
| Mining Pool | 4 GB | 50 GB | 3333, 3334, 8080 |
| PostgreSQL | 1 GB | 20 GB | 5432 (local) |
| Redis | 256 MB | 1 GB | 6379 (local) |

---

## Deployment Order

### 1️⃣ Web Wallet (30 minutes)

```bash
# On your server
cd /path/to/OpenSY

# Review and run deployment script
chmod +x contrib/web-wallet/deploy.sh
sudo ./contrib/web-wallet/deploy.sh

# Verify it's running
curl http://127.0.0.1:8080/api/blockchain
```

**DNS**: Point `wallet.opensyria.net` to your server IP

**SSL**:
```bash
sudo certbot --nginx -d wallet.opensyria.net
```

**Test**: Open https://wallet.opensyria.net in browser

---

### 2️⃣ Mining Pool (45 minutes)

```bash
# Set required environment variables
export POOL_WALLET="F..."  # Your pool fee wallet address
export NODE_RPC_USER="opensy"
export NODE_RPC_PASS="your_password"
export POOL_DOMAIN="pool.opensyria.net"

# Run deployment
chmod +x mining/deploy-pool.sh
sudo ./mining/deploy-pool.sh
```

**DNS**: Point `pool.opensyria.net` to your server IP

**SSL**:
```bash
sudo certbot certonly --nginx -d pool.opensyria.net
```

**Test mining**:
```bash
# From any machine with XMRig
xmrig -o pool.opensyria.net:3333 -u YOUR_WALLET -p worker1 -a rx/0
```

**Verify**:
```bash
# Check pool is finding blocks
curl https://pool.opensyria.net/api/pool/stats
```

---

### 3️⃣ Upstream Sync Automation (5 minutes)

```bash
# Commit the new GitHub Action
cd OpenSY
git add .github/workflows/upstream-sync-check.yml
git add doc/upstream-sync-strategy.md
git commit -m "Add upstream Bitcoin Core sync monitoring"
git push

# Manually trigger first run
gh workflow run upstream-sync-check.yml
```

---

## Post-Deployment Verification

### Checklist

- [ ] Explorer still working: https://explorer.opensyria.net
- [ ] Wallet loading: https://wallet.opensyria.net  
- [ ] Wallet API responding: https://wallet.opensyria.net/api/blockchain
- [ ] Pool Stratum accepting connections: `nc -zv pool.opensyria.net 3333`
- [ ] Pool dashboard loading: https://pool.opensyria.net
- [ ] XMRig can connect and submit shares

### Monitoring Setup

```bash
# Add to your monitoring (UptimeRobot, Pingdom, etc.)
- https://explorer.opensyria.net (HTTP 200)
- https://wallet.opensyria.net (HTTP 200)
- https://wallet.opensyria.net/api/blockchain (JSON response)
- https://pool.opensyria.net (HTTP 200)
- pool.opensyria.net:3333 (TCP connect)
```

---

## Announcement Template

### Arabic
```
🚀 إطلاق خدمات جديدة لشبكة OpenSY!

محفظة الويب 💰
https://wallet.opensyria.net
راقب رصيدك بأمان - لا نحتفظ بمفاتيحك

تجمع التعدين ⛏️
stratum+tcp://pool.opensyria.net:3333
- رسوم 1% فقط
- دفعات PPLNS عادلة
- متوافق مع XMRig

عدّن بجهازك الآن!
```

### English
```
🚀 New OpenSY Services Launched!

Web Wallet 💰
https://wallet.opensyria.net
Monitor your balance securely - we never hold your keys

Mining Pool ⛏️
stratum+tcp://pool.opensyria.net:3333
- Only 1% fee
- Fair PPLNS payouts
- XMRig compatible

Start mining with your CPU today!
```

---

## Rollback Plan

### If Web Wallet Fails
```bash
sudo systemctl stop opensy-wallet-api
# Check logs
sudo journalctl -u opensy-wallet-api -n 100
# Revert nginx
sudo rm /etc/nginx/sites-enabled/opensy-wallet
sudo systemctl reload nginx
```

### If Mining Pool Fails
```bash
sudo systemctl stop opensy-pool
# Check logs
sudo journalctl -u opensy-pool -n 100
# Stop infrastructure
cd mining/opensy-mining/docker && docker-compose down
# Close firewall
sudo ufw delete allow 3333/tcp
```

---

## Tomorrow's Tasks

1. **Monitor** - Watch logs for first 24 hours
2. **Pool Dashboard** - Build/deploy the frontend UI
3. **Mobile Wallet** - Start Rust core development
4. **Electrum Server** - Required for mobile wallet

---

## Files Created Today

| File | Purpose |
|------|---------|
| `.github/workflows/upstream-sync-check.yml` | Weekly Bitcoin Core change monitoring |
| `doc/upstream-sync-strategy.md` | Merge strategy documentation |
| `contrib/web-wallet/deploy.sh` | Web wallet deployment script |
| `doc/mobile-wallet-architecture.md` | Native mobile wallet design |
| `mining/deploy-pool.sh` | Mining pool deployment script |
| `doc/deployment-day-checklist.md` | This file |
