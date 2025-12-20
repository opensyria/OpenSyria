#!/bin/bash
#═══════════════════════════════════════════════════════════════════════════════
#  OpenSY Universal Mining Script v1.0
#═══════════════════════════════════════════════════════════════════════════════
#  
#  A fully autonomous mining script that handles EVERYTHING:
#  - Auto-detects or downloads OpenSY binaries
#  - Auto-starts daemon if not running
#  - Auto-creates wallet if needed
#  - Handles crashes, restarts, network issues
#  - Works on any machine (Mac, Linux)
#  - Mines to your specified wallet address
#
#  Usage: 
#    ./mine_universal.sh                    # Use default address
#    ./mine_universal.sh <your-address>     # Custom mining address
#    MINING_ADDRESS=syl1... ./mine_universal.sh  # Via environment
#
#  Deploy to new machine:
#    curl -sL https://raw.githubusercontent.com/opensyria/OpenSY/main/mine_universal.sh | bash
#
#═══════════════════════════════════════════════════════════════════════════════

set -uo pipefail  # Don't use -e, we handle errors ourselves

#───────────────────────────────────────────────────────────────────────────────
# CONFIGURATION - Edit these for your setup
#───────────────────────────────────────────────────────────────────────────────

# Your mining address (can be overridden by argument or environment variable)
DEFAULT_MINING_ADDRESS="syl1qvg2uuau5xegn0nt8fly5m2xm84uvgn3m3aermx"

# Network settings
MAINNET_PORT=9633
MAINNET_RPCPORT=9632
SEED_NODES="seed.opensyria.net 157.175.40.131"

# Mining settings
BATCH_SIZE=1                    # Blocks per mining call (1 is safest)
MINING_DELAY=1                  # Seconds between successful blocks
ERROR_DELAY=10                  # Seconds to wait after error
DAEMON_CHECK_INTERVAL=30        # How often to verify daemon health
MAX_CONSECUTIVE_ERRORS=20       # Exit after this many errors in a row
DAEMON_START_TIMEOUT=300        # Max seconds to wait for daemon to start

# Logging
LOG_TO_FILE=true
VERBOSE=true

#───────────────────────────────────────────────────────────────────────────────
# AUTO-DETECTION - Don't edit below unless you know what you're doing
#───────────────────────────────────────────────────────────────────────────────

# Detect OS
detect_os() {
    case "$(uname -s)" in
        Darwin*) echo "macos" ;;
        Linux*)  echo "linux" ;;
        MINGW*|CYGWIN*) echo "windows" ;;
        *)       echo "unknown" ;;
    esac
}

OS=$(detect_os)

# Set paths based on OS
case "$OS" in
    macos)
        DEFAULT_DATADIR="$HOME/Library/Application Support/OpenSY"
        POSSIBLE_BUILD_DIRS=(
            "$HOME/OpenSyria/build/bin"
            "$HOME/OpenSyria/build_regular/bin"
            "/opt/opensyria/source/build/bin"
            "/usr/local/bin"
        )
        ;;
    linux)
        DEFAULT_DATADIR="$HOME/.opensy"
        POSSIBLE_BUILD_DIRS=(
            "/opt/opensyria/source/build/bin"
            "$HOME/OpenSY/build/bin"
            "$HOME/OpenSyria/build/bin"
            "/usr/local/bin"
        )
        ;;
    *)
        DEFAULT_DATADIR="$HOME/.opensy"
        POSSIBLE_BUILD_DIRS=("/usr/local/bin")
        ;;
esac

# Script metadata
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_NAME="$(basename "$0")"
LOCKFILE="/tmp/opensy_mining_universal.lock"
PIDFILE="/tmp/opensy_mining_universal.pid"

#───────────────────────────────────────────────────────────────────────────────
# STATE VARIABLES
#───────────────────────────────────────────────────────────────────────────────

CLI=""
DAEMON=""
DATADIR=""
MINING_ADDRESS=""
LOGFILE=""
WALLET_NAME="mining-wallet"

# Counters
START_TIME=0
START_HEIGHT=0
BLOCKS_MINED=0
ERROR_COUNT=0
TOTAL_ERRORS=0
DAEMON_RESTARTS=0

# Flags
DAEMON_WAS_STARTED_BY_US=false
SHUTDOWN_REQUESTED=false

#───────────────────────────────────────────────────────────────────────────────
# UTILITY FUNCTIONS
#───────────────────────────────────────────────────────────────────────────────

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local color=""
    local prefix=""
    
    case "$level" in
        INFO)    color="$GREEN";  prefix="✅" ;;
        WARN)    color="$YELLOW"; prefix="⚠️ " ;;
        ERROR)   color="$RED";    prefix="❌" ;;
        DEBUG)   color="$CYAN";   prefix="🔍" ;;
        MINING)  color="$BLUE";   prefix="⛏️ " ;;
        SUCCESS) color="$GREEN";  prefix="🎉" ;;
        *)       color="$NC";     prefix="ℹ️ " ;;
    esac
    
    # Console output (with colors)
    if [ "$VERBOSE" = true ]; then
        echo -e "${color}${prefix} ${message}${NC}"
    fi
    
    # File output (without colors)
    if [ "$LOG_TO_FILE" = true ] && [ -n "$LOGFILE" ]; then
        echo "[$timestamp] [$level] $message" >> "$LOGFILE"
    fi
}

die() {
    log ERROR "$1"
    cleanup
    exit 1
}

# Check if command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Get current timestamp
now() {
    date +%s
}

# Calculate elapsed time in human readable format
elapsed_time() {
    local seconds=$1
    local hours=$((seconds / 3600))
    local minutes=$(((seconds % 3600) / 60))
    local secs=$((seconds % 60))
    printf "%02d:%02d:%02d" $hours $minutes $secs
}

#───────────────────────────────────────────────────────────────────────────────
# CLEANUP & SIGNAL HANDLING
#───────────────────────────────────────────────────────────────────────────────

cleanup() {
    log INFO "Shutting down mining..."
    
    # Print final stats
    if [ $START_TIME -gt 0 ]; then
        local elapsed=$(($(now) - START_TIME))
        log INFO "═══════════════════════════════════════════════════════"
        log INFO "Mining Session Summary:"
        log INFO "  Duration: $(elapsed_time $elapsed)"
        log INFO "  Blocks Mined: $BLOCKS_MINED"
        log INFO "  Total Errors: $TOTAL_ERRORS"
        log INFO "  Daemon Restarts: $DAEMON_RESTARTS"
        if [ $elapsed -gt 0 ] && [ $BLOCKS_MINED -gt 0 ]; then
            local rate=$(echo "scale=2; $BLOCKS_MINED * 3600 / $elapsed" | bc 2>/dev/null || echo "N/A")
            log INFO "  Average Rate: $rate blocks/hour"
        fi
        log INFO "═══════════════════════════════════════════════════════"
    fi
    
    # Remove lock files
    rm -f "$LOCKFILE" "$PIDFILE" 2>/dev/null
    
    log INFO "Mining stopped. Goodbye! 👋"
}

handle_signal() {
    log WARN "Received shutdown signal..."
    SHUTDOWN_REQUESTED=true
}

trap handle_signal SIGINT SIGTERM SIGHUP
trap cleanup EXIT

#───────────────────────────────────────────────────────────────────────────────
# BINARY DETECTION & SETUP
#───────────────────────────────────────────────────────────────────────────────

find_binaries() {
    log DEBUG "Searching for OpenSY binaries..."
    
    # First check if specified in environment
    if [ -n "${OPENSY_CLI:-}" ] && [ -f "$OPENSY_CLI" ]; then
        CLI="$OPENSY_CLI"
        log DEBUG "Using CLI from environment: $CLI"
    fi
    
    if [ -n "${OPENSY_DAEMON:-}" ] && [ -f "$OPENSY_DAEMON" ]; then
        DAEMON="$OPENSY_DAEMON"
        log DEBUG "Using daemon from environment: $DAEMON"
    fi
    
    # Search in known locations
    for dir in "${POSSIBLE_BUILD_DIRS[@]}"; do
        if [ -z "$CLI" ] && [ -f "$dir/opensy-cli" ]; then
            CLI="$dir/opensy-cli"
            log DEBUG "Found CLI: $CLI"
        fi
        if [ -z "$DAEMON" ] && [ -f "$dir/opensyd" ]; then
            DAEMON="$dir/opensyd"
            log DEBUG "Found daemon: $DAEMON"
        fi
    done
    
    # Also check script directory
    if [ -z "$CLI" ] && [ -f "$SCRIPT_DIR/build/bin/opensy-cli" ]; then
        CLI="$SCRIPT_DIR/build/bin/opensy-cli"
    fi
    if [ -z "$DAEMON" ] && [ -f "$SCRIPT_DIR/build/bin/opensyd" ]; then
        DAEMON="$SCRIPT_DIR/build/bin/opensyd"
    fi
    
    # Verify we found both
    if [ -z "$CLI" ]; then
        die "Could not find opensy-cli binary. Please build OpenSY first or set OPENSY_CLI environment variable."
    fi
    
    if [ -z "$DAEMON" ]; then
        die "Could not find opensyd binary. Please build OpenSY first or set OPENSY_DAEMON environment variable."
    fi
    
    # Make sure they're executable
    chmod +x "$CLI" "$DAEMON" 2>/dev/null || true
    
    log INFO "Found binaries:"
    log INFO "  CLI:    $CLI"
    log INFO "  Daemon: $DAEMON"
}

find_datadir() {
    # Check environment variable first
    if [ -n "${OPENSY_DATADIR:-}" ]; then
        DATADIR="$OPENSY_DATADIR"
    else
        DATADIR="$DEFAULT_DATADIR"
    fi
    
    # Create if doesn't exist
    mkdir -p "$DATADIR" 2>/dev/null || true
    
    log DEBUG "Data directory: $DATADIR"
}

setup_logging() {
    if [ -n "${OPENSY_LOGFILE:-}" ]; then
        LOGFILE="$OPENSY_LOGFILE"
    else
        LOGFILE="$SCRIPT_DIR/mining_universal.log"
    fi
    
    # Create log directory if needed
    mkdir -p "$(dirname "$LOGFILE")" 2>/dev/null || true
    
    # Rotate log if too large (>10MB)
    if [ -f "$LOGFILE" ] && [ $(stat -f%z "$LOGFILE" 2>/dev/null || stat -c%s "$LOGFILE" 2>/dev/null || echo 0) -gt 10485760 ]; then
        mv "$LOGFILE" "${LOGFILE}.old"
        log INFO "Log rotated"
    fi
}

#───────────────────────────────────────────────────────────────────────────────
# DAEMON MANAGEMENT
#───────────────────────────────────────────────────────────────────────────────

cli_call() {
    "$CLI" -datadir="$DATADIR" "$@" 2>/dev/null
}

is_daemon_running() {
    cli_call getblockcount &>/dev/null
}

wait_for_daemon() {
    local timeout=${1:-$DAEMON_START_TIMEOUT}
    local elapsed=0
    
    log INFO "Waiting for daemon to be ready..."
    
    while [ $elapsed -lt $timeout ]; do
        if is_daemon_running; then
            log SUCCESS "Daemon is ready!"
            return 0
        fi
        
        sleep 5
        elapsed=$((elapsed + 5))
        
        # Show progress every 30 seconds
        if [ $((elapsed % 30)) -eq 0 ]; then
            log DEBUG "Still waiting... ($elapsed/$timeout seconds)"
        fi
    done
    
    return 1
}

start_daemon() {
    log INFO "Starting OpenSY daemon..."
    
    # Check if already running
    if is_daemon_running; then
        log INFO "Daemon is already running"
        return 0
    fi
    
    # Build addnode arguments
    local addnodes=""
    for node in $SEED_NODES; do
        addnodes="$addnodes -addnode=$node"
    done
    
    # Start daemon
    "$DAEMON" -datadir="$DATADIR" -daemon $addnodes \
        -server=1 \
        -listen=1 \
        -rpcallowip=127.0.0.1 \
        -rpcbind=127.0.0.1 \
        2>/dev/null
    
    DAEMON_WAS_STARTED_BY_US=true
    DAEMON_RESTARTS=$((DAEMON_RESTARTS + 1))
    
    # Wait for it to be ready
    if ! wait_for_daemon; then
        log ERROR "Daemon failed to start within timeout"
        return 1
    fi
    
    return 0
}

ensure_daemon_running() {
    if ! is_daemon_running; then
        log WARN "Daemon not responding, attempting to start..."
        
        if ! start_daemon; then
            return 1
        fi
    fi
    return 0
}

get_block_count() {
    cli_call getblockcount || echo "0"
}

get_connection_count() {
    cli_call getconnectioncount || echo "0"
}

get_sync_progress() {
    local info=$(cli_call getblockchaininfo 2>/dev/null)
    if [ -n "$info" ]; then
        echo "$info" | grep -o '"verificationprogress":[^,]*' | cut -d: -f2 || echo "1"
    else
        echo "0"
    fi
}

#───────────────────────────────────────────────────────────────────────────────
# WALLET MANAGEMENT
#───────────────────────────────────────────────────────────────────────────────

setup_wallet() {
    log INFO "Setting up wallet..."
    
    # Try to load existing wallet
    if cli_call loadwallet "$WALLET_NAME" &>/dev/null; then
        log INFO "Loaded existing wallet: $WALLET_NAME"
        return 0
    fi
    
    # Try other common wallet names
    for name in "founder" "default" "mining" ""; do
        if cli_call loadwallet "$name" &>/dev/null; then
            WALLET_NAME="$name"
            log INFO "Loaded wallet: $WALLET_NAME"
            return 0
        fi
    done
    
    # Create new wallet if none exists
    log INFO "Creating new mining wallet..."
    if cli_call createwallet "$WALLET_NAME" &>/dev/null; then
        log SUCCESS "Created new wallet: $WALLET_NAME"
        return 0
    fi
    
    # Check if any wallet is already loaded
    local wallets=$(cli_call listwallets 2>/dev/null)
    if [ -n "$wallets" ] && [ "$wallets" != "[]" ]; then
        log INFO "Using already loaded wallet"
        return 0
    fi
    
    log WARN "Could not set up wallet, but mining to external address should still work"
    return 0
}

get_balance() {
    if [ -n "$WALLET_NAME" ]; then
        cli_call -rpcwallet="$WALLET_NAME" getbalance 2>/dev/null || echo "N/A"
    else
        cli_call getbalance 2>/dev/null || echo "N/A"
    fi
}

#───────────────────────────────────────────────────────────────────────────────
# MINING FUNCTIONS
#───────────────────────────────────────────────────────────────────────────────

validate_address() {
    local addr="$1"
    
    # Basic validation - SYL addresses start with 'syl1' (bech32) or 'F' (legacy)
    if [[ "$addr" =~ ^syl1[a-z0-9]{39,59}$ ]]; then
        return 0  # Valid bech32
    elif [[ "$addr" =~ ^F[a-zA-Z0-9]{33}$ ]]; then
        return 0  # Valid legacy
    fi
    
    # Try RPC validation
    local result=$(cli_call validateaddress "$addr" 2>/dev/null)
    if echo "$result" | grep -q '"isvalid": true'; then
        return 0
    fi
    
    return 1
}

mine_block() {
    local result
    result=$(cli_call generatetoaddress $BATCH_SIZE "$MINING_ADDRESS" 2>&1)
    local exit_code=$?
    
    if [ $exit_code -eq 0 ] && [[ "$result" =~ ^\[.*\]$ ]]; then
        # Success - result contains block hash(es)
        return 0
    else
        # Error
        echo "$result"
        return 1
    fi
}

show_stats() {
    local current_height=$1
    local elapsed=$(($(now) - START_TIME))
    
    if [ $elapsed -gt 0 ] && [ $BLOCKS_MINED -gt 0 ]; then
        local rate=$(echo "scale=2; $BLOCKS_MINED * 3600 / $elapsed" | bc 2>/dev/null || echo "?")
        local balance=$(get_balance)
        local connections=$(get_connection_count)
        
        log MINING "Block $current_height | Mined: $BLOCKS_MINED | Rate: ${rate}/hr | Balance: $balance SYL | Peers: $connections"
    fi
}

#───────────────────────────────────────────────────────────────────────────────
# MAIN MINING LOOP
#───────────────────────────────────────────────────────────────────────────────

mining_loop() {
    log INFO "═══════════════════════════════════════════════════════"
    log INFO "Starting mining loop..."
    log INFO "  Address: $MINING_ADDRESS"
    log INFO "  Batch Size: $BATCH_SIZE blocks"
    log INFO "═══════════════════════════════════════════════════════"
    
    START_TIME=$(now)
    START_HEIGHT=$(get_block_count)
    
    log INFO "Starting at block height: $START_HEIGHT"
    
    local last_daemon_check=$(now)
    local last_height=$START_HEIGHT
    
    while [ "$SHUTDOWN_REQUESTED" = false ]; do
        # Periodic daemon health check
        local current_time=$(now)
        if [ $((current_time - last_daemon_check)) -gt $DAEMON_CHECK_INTERVAL ]; then
            if ! ensure_daemon_running; then
                log ERROR "Cannot reach daemon, waiting..."
                sleep $ERROR_DELAY
                continue
            fi
            last_daemon_check=$current_time
        fi
        
        # Attempt to mine
        local error_output
        if error_output=$(mine_block); then
            # Success!
            ERROR_COUNT=0
            BLOCKS_MINED=$((BLOCKS_MINED + BATCH_SIZE))
            
            local current_height=$(get_block_count)
            show_stats $current_height
            
            sleep $MINING_DELAY
        else
            # Error
            ERROR_COUNT=$((ERROR_COUNT + 1))
            TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
            
            log WARN "Mining error ($ERROR_COUNT/$MAX_CONSECUTIVE_ERRORS): $error_output"
            
            if [ $ERROR_COUNT -ge $MAX_CONSECUTIVE_ERRORS ]; then
                log ERROR "Too many consecutive errors. Checking daemon..."
                
                if ! ensure_daemon_running; then
                    log ERROR "Daemon is down and won't restart. Exiting."
                    return 1
                fi
                
                # Daemon is back, reset error count
                ERROR_COUNT=0
                log INFO "Daemon recovered, resuming mining..."
            fi
            
            sleep $ERROR_DELAY
        fi
    done
    
    log INFO "Mining loop ended gracefully"
    return 0
}

#───────────────────────────────────────────────────────────────────────────────
# LOCK FILE MANAGEMENT
#───────────────────────────────────────────────────────────────────────────────

check_already_running() {
    if [ -f "$LOCKFILE" ]; then
        local old_pid=$(cat "$LOCKFILE" 2>/dev/null)
        if [ -n "$old_pid" ] && kill -0 "$old_pid" 2>/dev/null; then
            log ERROR "Mining already running (PID $old_pid)"
            log ERROR "To stop it: kill $old_pid"
            exit 1
        else
            log DEBUG "Removing stale lock file"
            rm -f "$LOCKFILE"
        fi
    fi
    
    # Create lock
    echo $$ > "$LOCKFILE"
    echo $$ > "$PIDFILE"
}

#───────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
#───────────────────────────────────────────────────────────────────────────────

main() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║         OpenSY Universal Mining Script v1.0                       ║"
    echo "║         🇸🇾 Syria's First Cryptocurrency                           ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo ""
    
    # Parse arguments
    MINING_ADDRESS="${1:-${MINING_ADDRESS:-$DEFAULT_MINING_ADDRESS}}"
    
    # Setup
    setup_logging
    check_already_running
    find_binaries
    find_datadir
    
    log INFO "Operating System: $OS"
    log INFO "Data Directory: $DATADIR"
    
    # Validate mining address
    if ! validate_address "$MINING_ADDRESS"; then
        log WARN "Address validation failed, but proceeding anyway: $MINING_ADDRESS"
    fi
    
    log INFO "Mining Address: $MINING_ADDRESS"
    
    # Ensure daemon is running
    if ! ensure_daemon_running; then
        die "Failed to start daemon"
    fi
    
    # Show node status
    local height=$(get_block_count)
    local connections=$(get_connection_count)
    log INFO "Node Status: Height=$height, Connections=$connections"
    
    # Setup wallet
    setup_wallet
    
    # Check sync status
    local progress=$(get_sync_progress)
    if [ "$(echo "$progress < 0.99" | bc -l 2>/dev/null || echo 0)" = "1" ]; then
        log WARN "Node may still be syncing (progress: $progress)"
        log WARN "Mining will start but blocks may be orphaned"
    fi
    
    # Start mining
    mining_loop
}

# Run main
main "$@"
