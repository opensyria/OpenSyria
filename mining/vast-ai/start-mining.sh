#!/bin/bash
# OpenSyria Mining Script for Vast.ai
# This script runs on the rented GPU instance

set -e

# Configuration - YOUR MINING ADDRESS
MINING_ADDRESS="syl1q0y76xxxdfvhfad2sju4fymnsn8zs5lndpwhufw"

# Seed node to connect to
SEED_NODE="157.175.40.131:9633"

# Paths
OPENSYRIA_DIR="/home/opensyria/OpenSyria"
DATA_DIR="/home/opensyria/.opensyria"
CLI="${OPENSYRIA_DIR}/build/bin/opensyria-cli"
DAEMON="${OPENSYRIA_DIR}/build/bin/opensyriad"

echo "=========================================="
echo "  OpenSyria GPU Miner - Vast.ai Edition"
echo "=========================================="
echo "Mining Address: ${MINING_ADDRESS}"
echo "Seed Node: ${SEED_NODE}"
echo ""

# Create config
mkdir -p ${DATA_DIR}
cat > ${DATA_DIR}/opensyria.conf << EOF
# OpenSyria Miner Config
server=1
daemon=0
listen=1
txindex=0

# Connect to main node
addnode=${SEED_NODE}
connect=${SEED_NODE}

# RPC settings (local only)
rpcuser=miner
rpcpassword=minerpass123
rpcallowip=127.0.0.1

# Performance
dbcache=512
maxconnections=8
EOF

echo "[1/4] Starting OpenSyria daemon..."
${DAEMON} -datadir=${DATA_DIR} -printtoconsole &
DAEMON_PID=$!

echo "[2/4] Waiting for daemon to start..."
sleep 10

# Wait for sync
echo "[3/4] Waiting for blockchain sync..."
while true; do
    SYNC_INFO=$(${CLI} -datadir=${DATA_DIR} getblockchaininfo 2>/dev/null || echo "")
    if [ -n "$SYNC_INFO" ]; then
        BLOCKS=$(echo $SYNC_INFO | jq -r '.blocks')
        HEADERS=$(echo $SYNC_INFO | jq -r '.headers')
        PROGRESS=$(echo $SYNC_INFO | jq -r '.verificationprogress')
        
        if [ "$BLOCKS" = "$HEADERS" ] && [ "$HEADERS" != "null" ] && [ "$HEADERS" != "0" ]; then
            echo "Synced! Block height: $BLOCKS"
            break
        fi
        echo "Syncing: $BLOCKS / $HEADERS (${PROGRESS})"
    else
        echo "Waiting for daemon..."
    fi
    sleep 5
done

echo "[4/4] Starting mining to ${MINING_ADDRESS}..."
echo ""
echo "=========================================="
echo "  MINING STARTED!"
echo "=========================================="

# Get number of CPU cores for parallel mining
THREADS=$(nproc)
echo "Using ${THREADS} threads"

# Start multiple mining processes
for i in $(seq 1 $THREADS); do
    (
        while true; do
            ${CLI} -datadir=${DATA_DIR} generatetoaddress 1 ${MINING_ADDRESS} 500000000 2>/dev/null || sleep 1
        done
    ) &
done

# Monitor mining progress
while true; do
    BALANCE=$(${CLI} -datadir=${DATA_DIR} getblockchaininfo 2>/dev/null | jq -r '.blocks' || echo "?")
    PEERS=$(${CLI} -datadir=${DATA_DIR} getconnectioncount 2>/dev/null || echo "?")
    echo "[$(date '+%H:%M:%S')] Block: ${BALANCE} | Peers: ${PEERS} | Mining..."
    sleep 60
done
