#!/bin/bash
# PASTE THIS ENTIRE SCRIPT INTO YOUR VAST.AI INSTANCE
# One-liner mining setup for OpenSY
#
# ⚠️  IMPORTANT: Change MINING_ADDRESS to your own wallet address!
#     Generate one with: opensy-cli getnewaddress "" bech32

MINING_ADDRESS="${MINING_ADDRESS:-syl1q0y76xxxdfvhfad2sju4fymnsn8zs5lndpwhufw}"
SEED_NODE="157.175.40.131"

# Warn if using default address
if [ "$MINING_ADDRESS" = "syl1q0y76xxxdfvhfad2sju4fymnsn8zs5lndpwhufw" ]; then
    echo ""
    echo "⚠️  WARNING: Using default mining address!"
    echo "   Set your own: export MINING_ADDRESS='syl1qYOUR_ADDRESS'"
    echo "   Continuing in 5 seconds..."
    echo ""
    sleep 5
fi

echo "=== OpenSY Miner Setup ==="

# Install deps
apt-get update && apt-get install -y git build-essential cmake libboost-all-dev libevent-dev libssl-dev libsqlite3-dev pkg-config jq screen

# Clone repo
cd /root
git clone https://github.com/opensyria/OpenSY.git
cd OpenSY

# Build (this takes ~10-15 minutes)
echo "Building OpenSY... (this takes ~10-15 min)"
cmake -B build -DBUILD_DAEMON=ON -DBUILD_CLI=ON -DBUILD_TESTS=OFF -DBUILD_GUI=OFF -DBUILD_UTIL=OFF
cmake --build build -j$(nproc)

# Generate secure RPC password
RPC_PASS=$(openssl rand -hex 32)

# Create config
mkdir -p /root/.opensy
cat > /root/.opensy/opensy.conf << EOF
server=1
daemon=1
listen=1
addnode=${SEED_NODE}:9633
connect=${SEED_NODE}:9633
rpcuser=miner
rpcpassword=${RPC_PASS}
rpcallowip=127.0.0.1
dbcache=1024
EOF

# Save password for reference
echo "${RPC_PASS}" > /root/.opensy/rpc_password.txt
chmod 600 /root/.opensy/rpc_password.txt
echo "RPC password saved to: /root/.opensy/rpc_password.txt"

# Start daemon
echo "Starting OpenSY daemon..."
./build/bin/opensyd -daemon
sleep 10

# Wait for sync
echo "Waiting for sync..."
while true; do
    INFO=$(./build/bin/opensy-cli getblockchaininfo 2>/dev/null)
    if [ $? -eq 0 ]; then
        BLOCKS=$(echo $INFO | jq -r '.blocks')
        HEADERS=$(echo $INFO | jq -r '.headers')
        if [ "$BLOCKS" = "$HEADERS" ] && [ "$HEADERS" != "0" ]; then
            echo "Synced at block $BLOCKS!"
            break
        fi
        echo "Syncing: $BLOCKS / $HEADERS"
    fi
    sleep 5
done

# Start mining in screen
echo "Starting mining to $MINING_ADDRESS"
screen -dmS miner bash -c "while true; do /root/OpenSY/build/bin/opensy-cli generatetoaddress 1 $MINING_ADDRESS 500000000 2>/dev/null || sleep 1; done"

echo ""
echo "=========================================="
echo "  MINING STARTED!"
echo "=========================================="
echo "Address: $MINING_ADDRESS"
echo ""
echo "Monitor with: screen -r miner"
echo "Check sync:   /root/OpenSY/build/bin/opensy-cli getblockchaininfo"
echo ""
