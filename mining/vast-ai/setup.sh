#!/bin/bash
# OpenSY GPU Mining Setup Script for Vast.ai
# Usage: curl -sSL https://raw.githubusercontent.com/opensy/OpenSY/main/mining/vast-ai/setup.sh | bash
#
# ═══════════════════════════════════════════════════════════════════════════
#  ⚠️  IMPORTANT: SET YOUR OWN MINING ADDRESS!
# ═══════════════════════════════════════════════════════════════════════════
#  
#  Before running this script, set your mining address:
#
#    export MINING_ADDRESS="syl1qYOUR_ADDRESS_HERE"
#    curl -sSL https://raw.githubusercontent.com/opensy/OpenSY/main/mining/vast-ai/setup.sh | bash
#
#  Or create a new address using:
#    ./build/bin/opensy-cli getnewaddress "" bech32
#
#  The default address below is for TESTING ONLY - rewards will go elsewhere!
# ═══════════════════════════════════════════════════════════════════════════

set -e

# Configuration - OVERRIDE THIS WITH YOUR OWN ADDRESS!
MINING_ADDRESS="${MINING_ADDRESS:-syl1q0y76xxxdfvhfad2sju4fymnsn8zs5lndpwhufw}"

# Warn if using default address
if [ "$MINING_ADDRESS" = "syl1q0y76xxxdfvhfad2sju4fymnsn8zs5lndpwhufw" ]; then
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  ⚠️  WARNING: Using default mining address!"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "  You are mining to the DEFAULT address. Your rewards will NOT"
    echo "  go to a wallet you control!"
    echo ""
    echo "  To use your own address, restart with:"
    echo ""
    echo "    export MINING_ADDRESS=\"syl1qYOUR_ADDRESS_HERE\""
    echo "    # then run this script again"
    echo ""
    echo "  Continuing in 10 seconds... (Ctrl+C to cancel)"
    echo ""
    sleep 10
fi

SEED_NODE="157.175.40.131:9633"
DNS_SEED="seed.opensyria.net:9633"

echo "=========================================="
echo "  OpenSY GPU Mining Setup"
echo "=========================================="
echo "Mining Address: $MINING_ADDRESS"
echo ""

# 1. Install dependencies
echo "[1/6] Installing dependencies..."
apt-get update -qq
apt-get install -y -qq git build-essential cmake libboost-all-dev \
  libevent-dev libssl-dev libsqlite3-dev jq screen curl > /dev/null 2>&1
echo "✓ Dependencies installed"

# 2. Clone OpenSY
echo "[2/6] Cloning OpenSY..."
cd /root
if [ -d "OpenSY" ]; then
    cd OpenSY && git pull -q
else
    git clone -q https://github.com/opensyria/OpenSY.git
    cd OpenSY
fi
echo "✓ Repository cloned"

# 3. Build
echo "[3/6] Building OpenSY (this takes 5-15 minutes)..."
cmake -B build -DBUILD_DAEMON=ON -DBUILD_CLI=ON -DBUILD_TESTS=OFF -DBUILD_GUI=OFF > /dev/null 2>&1
cmake --build build -j$(nproc) > /dev/null 2>&1
echo "✓ Build complete"

# 4. Configure
echo "[4/6] Configuring..."
mkdir -p ~/.opensy
# Generate secure random RPC password
RPC_PASS=$(openssl rand -hex 32)

cat > ~/.opensy/opensy.conf << EOF
# OpenSY Mining Configuration
server=1
daemon=0
printtoconsole=1
txindex=1

# Network
addnode=$SEED_NODE
addnode=$DNS_SEED
maxconnections=32

# RPC - Secure configuration
rpcuser=miner
rpcpassword=$RPC_PASS
rpcallowip=127.0.0.1
rpcbind=127.0.0.1
EOF

# Save password to file for reference
echo "$RPC_PASS" > ~/.opensy/rpc_password.txt
chmod 600 ~/.opensy/rpc_password.txt

echo "✓ Configuration created"
echo ""
echo "═══════════════════════════════════════════════════════"
echo "  RPC Password (save this!): $RPC_PASS"
echo "  Also saved to: ~/.opensy/rpc_password.txt"
echo "═══════════════════════════════════════════════════════"
echo ""

# 5. Start daemon
echo "[5/6] Starting daemon..."
pkill opensyd 2>/dev/null || true
sleep 2
screen -dmS opensyd ./build/bin/opensyd -printtoconsole

# Wait for daemon to start
echo "   Waiting for daemon to initialize..."
sleep 10

# Wait for sync
echo "   Syncing blockchain..."
for i in {1..60}; do
    BLOCKS=$(./build/bin/opensy-cli getblockcount 2>/dev/null || echo "0")
    if [ "$BLOCKS" != "0" ] && [ "$BLOCKS" != "" ]; then
        echo "   Current block: $BLOCKS"
        break
    fi
    sleep 5
done
echo "✓ Daemon running and synced"

# 6. Start mining
echo "[6/6] Starting mining..."
screen -dmS miner bash -c "
while true; do
    /root/OpenSY/build/bin/opensy-cli generatetoaddress 1 $MINING_ADDRESS 500000000 2>/dev/null || sleep 5
done
"
echo "✓ Mining started!"

echo ""
echo "=========================================="
echo "  SETUP COMPLETE!"
echo "=========================================="
echo ""
echo "Commands:"
echo "  screen -r miner      # View mining output"
echo "  screen -r opensyd # View daemon logs"
echo "  Ctrl+A, D            # Detach from screen"
echo ""
echo "Check status:"
echo "  ./build/bin/opensy-cli getmininginfo"
echo "  ./build/bin/opensy-cli getblockcount"
echo ""
echo "Mining to: $MINING_ADDRESS"
echo ""
