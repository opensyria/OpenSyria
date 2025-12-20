#!/bin/bash
#═══════════════════════════════════════════════════════════════════════════════
#  OpenSY One-Click Installer & Miner
#═══════════════════════════════════════════════════════════════════════════════
#
#  This script will:
#  1. Install all dependencies (git, cmake, etc.)
#  2. Clone and build OpenSY
#  3. Start the daemon
#  4. Begin mining to your address
#
#  Usage:
#    curl -sL https://raw.githubusercontent.com/opensyria/OpenSY/main/install_and_mine.sh | bash
#    curl -sL https://raw.githubusercontent.com/opensyria/OpenSY/main/install_and_mine.sh | bash -s YOUR_ADDRESS
#
#═══════════════════════════════════════════════════════════════════════════════

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[OpenSY]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[OpenSY]${NC} $1"
}

error() {
    echo -e "${RED}[OpenSY]${NC} $1"
    exit 1
}

# Detect OS
detect_os() {
    case "$(uname -s)" in
        Darwin*) echo "macos" ;;
        Linux*)  echo "linux" ;;
        *)       echo "unknown" ;;
    esac
}

OS=$(detect_os)
MINING_ADDRESS="${1:-syl1qvg2uuau5xegn0nt8fly5m2xm84uvgn3m3aermx}"

echo ""
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║         OpenSY One-Click Installer & Miner                        ║"
echo "║         🇸🇾 Syria's First Cryptocurrency                           ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

log "Detected OS: $OS"
log "Mining Address: $MINING_ADDRESS"

#───────────────────────────────────────────────────────────────────────────────
# STEP 1: Install Dependencies
#───────────────────────────────────────────────────────────────────────────────

log "Step 1: Installing dependencies..."

case "$OS" in
    macos)
        # Check for Homebrew
        if ! command -v brew &> /dev/null; then
            log "Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        
        log "Installing build dependencies via Homebrew..."
        brew install --quiet cmake boost libevent berkeley-db@4 miniupnpc zeromq qt@5 qrencode || true
        ;;
        
    linux)
        # Check for package manager
        if command -v apt-get &> /dev/null; then
            log "Installing build dependencies via apt..."
            sudo apt-get update
            sudo apt-get install -y \
                build-essential libtool autotools-dev automake pkg-config bsdmainutils python3 \
                libevent-dev libboost-dev libboost-system-dev libboost-filesystem-dev \
                libboost-thread-dev libsqlite3-dev libminiupnpc-dev libnatpmp-dev \
                libzmq3-dev cmake git || error "Failed to install dependencies"
        elif command -v yum &> /dev/null; then
            log "Installing build dependencies via yum..."
            sudo yum groupinstall -y "Development Tools"
            sudo yum install -y cmake boost-devel libevent-devel miniupnpc-devel zeromq-devel || true
        else
            warn "Unknown package manager. Please install: cmake, boost, libevent, miniupnpc, zeromq"
        fi
        ;;
        
    *)
        error "Unsupported OS: $OS"
        ;;
esac

#───────────────────────────────────────────────────────────────────────────────
# STEP 2: Clone Repository
#───────────────────────────────────────────────────────────────────────────────

INSTALL_DIR="$HOME/OpenSY"

if [ -d "$INSTALL_DIR" ]; then
    log "Step 2: Updating existing OpenSY installation..."
    cd "$INSTALL_DIR"
    git pull origin main || warn "Could not pull latest changes"
else
    log "Step 2: Cloning OpenSY repository..."
    git clone https://github.com/opensyria/OpenSY.git "$INSTALL_DIR" || error "Failed to clone repository"
    cd "$INSTALL_DIR"
fi

#───────────────────────────────────────────────────────────────────────────────
# STEP 3: Build
#───────────────────────────────────────────────────────────────────────────────

log "Step 3: Building OpenSY (this may take 10-30 minutes)..."

BUILD_DIR="$INSTALL_DIR/build"
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Configure
log "Configuring build..."
cmake .. \
    -DBUILD_TESTS=OFF \
    -DENABLE_GUI=OFF \
    -DWITH_MINIUPNPC=ON \
    -DWITH_ZMQ=ON \
    2>&1 | tail -5

# Build (use half of available cores to not overwhelm the system)
CORES=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 2)
JOBS=$((CORES / 2 + 1))

log "Building with $JOBS parallel jobs..."
cmake --build . -j$JOBS 2>&1 | tail -20

# Verify binaries
if [ ! -f "$BUILD_DIR/bin/opensyd" ] || [ ! -f "$BUILD_DIR/bin/opensy-cli" ]; then
    error "Build failed - binaries not found"
fi

log "Build complete! ✅"

#───────────────────────────────────────────────────────────────────────────────
# STEP 4: Install (optional - add to PATH)
#───────────────────────────────────────────────────────────────────────────────

log "Step 4: Setting up environment..."

# Add to PATH if not already there
EXPORT_LINE="export PATH=\"$BUILD_DIR/bin:\$PATH\""
SHELL_RC=""

if [ -n "$ZSH_VERSION" ] || [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ] || [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
fi

if [ -n "$SHELL_RC" ] && ! grep -q "OpenSY" "$SHELL_RC" 2>/dev/null; then
    echo "" >> "$SHELL_RC"
    echo "# OpenSY binaries" >> "$SHELL_RC"
    echo "$EXPORT_LINE" >> "$SHELL_RC"
    log "Added OpenSY to PATH in $SHELL_RC"
fi

# Export for current session
export PATH="$BUILD_DIR/bin:$PATH"

#───────────────────────────────────────────────────────────────────────────────
# STEP 5: Start Mining!
#───────────────────────────────────────────────────────────────────────────────

log "Step 5: Starting mining..."

# Make mining script executable
chmod +x "$INSTALL_DIR/mine_universal.sh"

# Set environment variables
export OPENSY_CLI="$BUILD_DIR/bin/opensy-cli"
export OPENSY_DAEMON="$BUILD_DIR/bin/opensyd"

# Run mining script
exec "$INSTALL_DIR/mine_universal.sh" "$MINING_ADDRESS"
