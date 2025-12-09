# OpenSyria Mining on Vast.ai - Quick Start Guide

## Step 1: Sign Up for Vast.ai
1. Go to https://vast.ai
2. Create account
3. Add credits ($20-50 recommended)

## Step 2: Find a Machine
1. Click "Search" or "Create"
2. Filter by:
   - **GPU**: RTX 4090, RTX 3090, or A100
   - **Price**: $0.30-0.80/hr
   - **Disk**: At least 50GB
   - **Docker**: Enabled

3. Look for machines with:
   - Low price per hour
   - Good reliability score
   - Fast internet speed

## Step 3: Launch Instance

### Option A: Use Docker Image (Easiest)
```bash
# On the Vast.ai instance, run:
docker run -d --name opensyria-miner \
  -e MINING_ADDRESS="syl1q0y76xxxdfvhfad2sju4fymnsn8zs5lndpwhufw" \
  -p 9633:9633 \
  opensyria/miner:latest
```

### Option B: Manual Setup (If Docker image not available)

SSH into your Vast.ai instance and run:

```bash
# 1. Install dependencies
apt-get update && apt-get install -y git build-essential cmake libboost-all-dev libevent-dev libssl-dev libsqlite3-dev jq

# 2. Clone and build OpenSyria
git clone https://github.com/opensyria/OpenSyria.git
cd OpenSyria
cmake -B build -DBUILD_DAEMON=ON -DBUILD_CLI=ON -DBUILD_TESTS=OFF -DBUILD_GUI=OFF
cmake --build build -j$(nproc)

# 3. Create config
mkdir -p ~/.opensyria
cat > ~/.opensyria/opensyria.conf << 'EOF'
server=1
daemon=1
addnode=157.175.40.131:9633
connect=157.175.40.131:9633
rpcuser=miner
rpcpassword=minerpass123
EOF

# 4. Start daemon
./build/bin/opensyriad -daemon

# 5. Wait for sync (check with)
./build/bin/opensyria-cli getblockchaininfo

# 6. Start mining (run in screen/tmux)
while true; do
  ./build/bin/opensyria-cli generatetoaddress 1 syl1q0y76xxxdfvhfad2sju4fymnsn8zs5lndpwhufw 500000000
done
```

## Step 4: Monitor Mining

Check if you're winning blocks:
```bash
# On your main node (AWS)
opensyria-cli -rpcwallet=founders-wallet getbalance
```

## Tips for Maximum Hashpower

1. **Rent multiple instances** - Each one adds to your hashrate
2. **Choose machines with many CPU cores** - More cores = more hashing
3. **Keep instances running** - Don't stop/start frequently
4. **Check spot prices** - Interruptible instances are cheaper

## Your Mining Address
```
syl1q0y76xxxdfvhfad2sju4fymnsn8zs5lndpwhufw
```

## Your Seed Node
```
157.175.40.131:9633
```

## Expected Results
- 1x RTX 4090 instance: ~50-100 MH/s
- With 3 instances: ~150-300 MH/s (should beat other miner!)
- Cost: ~$1-2/hour total
- Expected earnings: ~300,000-500,000 SYL/hour
