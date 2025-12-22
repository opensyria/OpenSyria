# OpenSY Wallet Infrastructure Guide

**Version:** 1.0  
**Date:** December 21, 2025

---

## Overview

OpenSY provides multiple wallet options for different use cases:

| Wallet Type | Platform | Use Case | Status |
|-------------|----------|----------|--------|
| **opensy-qt** | Desktop (Win/Mac/Linux) | Full GUI wallet | ✅ Available |
| **opensy-cli** | Command Line | Power users, servers | ✅ Available |
| **Watch-Only** | Any | Cold storage monitoring | ✅ Supported |
| **Web Interface** | Browser | Quick balance checking | ✅ Included |
| **Mobile Wallet** | iOS/Android | Mass adoption | 🚧 In Development |

---

## Desktop GUI Wallet (opensy-qt)

### Building the GUI

The GUI is built with Qt6. To enable:

#### macOS
```bash
# Install dependencies
brew install qt@6 qrencode

# Configure with GUI
cmake -B build -DBUILD_GUI=ON

# Build
cmake --build build -j$(sysctl -n hw.ncpu)

# Run
./build/bin/opensy-qt
```

#### Ubuntu/Debian
```bash
# Install dependencies
sudo apt-get install qt6-base-dev qt6-tools-dev libqrencode-dev

# Configure with GUI
cmake -B build -DBUILD_GUI=ON

# Build
cmake --build build -j$(nproc)

# Run
./build/bin/opensy-qt
```

#### Windows (MSVC)
```powershell
# Install Qt6 via vcpkg or official installer
# See doc/build-windows-msvc.md for details

cmake -B build -DBUILD_GUI=ON -DQt6_DIR="C:\Qt\6.x.x\msvc2022_64\lib\cmake\Qt6"
cmake --build build --config Release
```

### GUI Features

- **Send/Receive**: Easy transaction creation
- **Address Book**: Save frequently used addresses
- **Transaction History**: View all wallet activity
- **QR Codes**: Generate payment requests
- **Coin Control**: Advanced UTXO management
- **PSBT Support**: Partially Signed Bitcoin Transactions
- **Watch-Only Wallets**: Monitor cold storage

---

## Command-Line Wallet (opensy-cli)

### Basic Operations

```bash
# Create new wallet
opensy-cli createwallet "mywallet"

# Get new address
opensy-cli -rpcwallet=mywallet getnewaddress

# Check balance
opensy-cli -rpcwallet=mywallet getbalance

# Send coins
opensy-cli -rpcwallet=mywallet sendtoaddress "syl1q..." 10.0

# List transactions
opensy-cli -rpcwallet=mywallet listtransactions
```

### Wallet Backup

```bash
# Backup wallet
opensy-cli -rpcwallet=mywallet backupwallet "/path/to/backup.dat"

# Dump all private keys (for paper backup)
opensy-cli -rpcwallet=mywallet dumpwallet "/path/to/keys.txt"
```

---

## Watch-Only Wallets

Watch-only wallets allow you to monitor balances and transactions without having private keys. This is essential for:

- **Cold storage monitoring**: Watch your hardware wallet addresses
- **Business accounting**: Monitor customer payments
- **Audit**: Track addresses without signing capability

### Creating a Watch-Only Wallet

```bash
# Create descriptor-based watch-only wallet
opensy-cli createwallet "watchonly" false true false false true

# Parameters:
#   "watchonly"          - Wallet name
#   false                - avoid_reuse
#   true                 - descriptors (required for modern wallets)
#   false                - load_on_startup
#   false                - external_signer
#   true                 - disable_private_keys (makes it watch-only)
```

### Importing Addresses

#### Import a Single Address
```bash
# Import address for watching
opensy-cli -rpcwallet=watchonly importaddress "syl1q..." "label" true

# Parameters:
#   "syl1q..."    - Address to watch
#   "label"      - Optional label
#   true         - Rescan blockchain (slow, but finds historical tx)
```

#### Import Extended Public Key (xpub/zpub)
```bash
# Import descriptor for HD watching
opensy-cli -rpcwallet=watchonly importdescriptors '[{
  "desc": "wpkh([fingerprint/84h/0h/0h]zpub...)/*",
  "timestamp": "now",
  "range": [0, 1000],
  "watchonly": true,
  "label": "hardware_wallet"
}]'
```

#### Import from Hardware Wallet

If using a hardware wallet with HWI (Hardware Wallet Interface):

```bash
# List connected devices
hwi enumerate

# Get xpub from device
hwi -d "device_path" getxpub "m/84h/0h/0h"

# Import the xpub as watch-only
opensy-cli -rpcwallet=watchonly importdescriptors '[{
  "desc": "wpkh([FINGERPRINT/84h/0h/0h]XPUB/0/*)#checksum",
  "timestamp": "now",
  "range": [0, 100],
  "watchonly": true
}]'
```

### Monitoring Watch-Only Wallet

```bash
# Check balance
opensy-cli -rpcwallet=watchonly getbalance

# List recent transactions
opensy-cli -rpcwallet=watchonly listtransactions "*" 10

# Get address info
opensy-cli -rpcwallet=watchonly getaddressinfo "syl1q..."
```

### Creating Unsigned Transactions (for Cold Storage)

```bash
# Create PSBT (Partially Signed Bitcoin Transaction)
opensy-cli -rpcwallet=watchonly walletcreatefundedpsbt \
  '[]' \
  '[{"syl1q...": 10.0}]' \
  0 \
  '{"fee_rate": 2}'

# The output is a base64 PSBT that can be signed offline
```

Then sign with cold wallet:
```bash
# On cold/offline machine with full wallet
opensy-cli -rpcwallet=cold_wallet walletprocesspsbt "base64_psbt"

# Finalize and broadcast
opensy-cli finalizepsbt "signed_psbt"
opensy-cli sendrawtransaction "final_hex"
```

---

## Web Watch-Only Interface

For quick balance checking without running a full node, use the included web interface:

```bash
# Start the web interface
cd contrib/web-wallet
python3 -m http.server 8080

# Open browser to http://localhost:8080
```

The web interface connects to Electrum servers (when deployed) for lightweight balance checking.

See: `contrib/web-wallet/README.md`

---

## Mobile Wallet (Coming Soon)

A mobile wallet is in development. See [MOBILE_WALLET_ARCHITECTURE.md](architecture/MOBILE_WALLET_ARCHITECTURE.md) for details.

### Current Options for Mobile Users

Until the native mobile wallet is ready:

1. **Web Interface**: Use the web watch-only interface on mobile browser
2. **Watch-Only via CLI**: Set up watch-only on a server, query via API
3. **Remote opensy-qt**: Run GUI on desktop, access via VNC/remote desktop

---

## Security Best Practices

### Wallet Encryption

```bash
# Encrypt wallet (required for mainnet!)
opensy-cli -rpcwallet=mywallet encryptwallet "strong_passphrase"

# Unlock for sending (2 minutes)
opensy-cli -rpcwallet=mywallet walletpassphrase "passphrase" 120

# Lock immediately
opensy-cli -rpcwallet=mywallet walletlock
```

### Cold Storage Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│  HOT MACHINE (Online)                                            │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Watch-Only Wallet                                          │ │
│  │  • Can view balance                                         │ │
│  │  • Can create unsigned transactions (PSBT)                  │ │
│  │  • CANNOT sign or spend                                     │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ USB drive with unsigned PSBT
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  COLD MACHINE (Offline - air-gapped)                            │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Full Wallet with Private Keys                              │ │
│  │  • Signs PSBT                                               │ │
│  │  • Never connected to internet                              │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ USB drive with signed PSBT
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  HOT MACHINE (Online)                                            │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Broadcast signed transaction to network                    │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Backup Checklist

- [ ] Wallet file backed up: `~/.opensy/wallets/*/wallet.dat`
- [ ] Seed phrase (if HD wallet) written on paper
- [ ] Backup stored in secure location (safe, safety deposit box)
- [ ] Test restore from backup periodically

---

## Wallet Types Comparison

| Feature | opensy-qt | opensy-cli | Watch-Only | Web |
|---------|-----------|------------|------------|-----|
| View Balance | ✅ | ✅ | ✅ | ✅ |
| Send Transactions | ✅ | ✅ | ❌ (PSBT only) | ❌ |
| Create Addresses | ✅ | ✅ | ❌ | ❌ |
| QR Codes | ✅ | ❌ | ❌ | ✅ |
| Coin Control | ✅ | ✅ | ✅ | ❌ |
| Multi-Wallet | ✅ | ✅ | ✅ | ✅ |
| Encryption | ✅ | ✅ | N/A | N/A |
| HW Wallet | ✅ | ✅ | ✅ | ❌ |

---

## Troubleshooting

### "Wallet file not found"
```bash
# List available wallets
opensy-cli listwalletdir

# Load specific wallet
opensy-cli loadwallet "wallet_name"
```

### "Insufficient funds"
- Check if wallet is fully synced: `opensy-cli getblockchaininfo`
- For watch-only, ensure addresses were imported with rescan

### "Error: Please enter the wallet passphrase"
```bash
# Unlock wallet first
opensy-cli -rpcwallet=mywallet walletpassphrase "passphrase" 60
```

### GUI won't start
- Ensure Qt6 is installed: `brew info qt@6` or `apt show qt6-base-dev`
- Check if built with GUI: Rebuild with `-DBUILD_GUI=ON`

---

## API Access

For programmatic wallet access:

```bash
# Enable server mode
opensyd -server -rpcuser=user -rpcpassword=pass

# Query via curl
curl --user user:pass --data-binary \
  '{"jsonrpc": "1.0", "method": "getbalance", "params": []}' \
  -H 'content-type: text/plain;' http://127.0.0.1:9632/wallet/mywallet
```

See [REST interface](rest-interface.md) for additional API options.

---

*سوريا حرة* 🇸🇾
