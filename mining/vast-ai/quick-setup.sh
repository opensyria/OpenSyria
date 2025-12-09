#!/bin/bash
# PASTE THIS ENTIRE SCRIPT INTO YOUR VAST.AI INSTANCE
# One-liner mining setup for OpenSyria

MINING_ADDRESS="syl1q0y76xxxdfvhfad2sju4fymnsn8zs5lndpwhufw"
SEED_NODE="157.175.40.131"

echo "=== OpenSyria Miner Setup ==="

# Install deps
apt-get update && apt-get install -y git build-essential cmake libboost-all-dev libevent-dev libssl-dev libsqlite3-dev pkg-config jq screen

# Clone repo
cd /root
git clone https://github.com/opensyria/OpenSyria.git
cd OpenSyria

# Build (this takes ~10-15 minutes)
echo "Building OpenSyria... (this takes ~10-15 min)"
cmake -B build -DBUILD_DAEMON=ON -DBUILD_CLI=ON -DBUILD_TESTS=OFF -DBUILD_GUI=OFF -DBUILD_UTIL=OFF
cmake --build build -j$(nproc)

# Create config
mkdir -p /root/.opensyria
cat > /root/.opensyria/opensyria.conf << EOF
server=1
daemon=1
listen=1
addnode=${SEED_NODE}:9633
connect=${SEED_NODE}:9633
rpcuser=miner
rpcpassword=minerpass123
rpcallowip=127.0.0.1
dbcache=1024
EOF

# Start daemon
echo "Starting OpenSyria daemon..."
./build/bin/opensyriad -daemon
sleep 10

# Wait for sync
echo "Waiting for sync..."
while true; do
    INFO=$(./build/bin/opensyria-cli getblockchaininfo 2>/dev/null)
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
screen -dmS miner bash -c "while true; do /root/OpenSyria/build/bin/opensyria-cli generatetoaddress 1 $MINING_ADDRESS 500000000 2>/dev/null || sleep 1; done"

echo ""
echo "=========================================="
echo "  MINING STARTED!"
echo "=========================================="
echo "Address: $MINING_ADDRESS"
echo ""
echo "Monitor with: screen -r miner"
echo "Check sync:   /root/OpenSyria/build/bin/opensyria-cli getblockchaininfo"
echo ""
