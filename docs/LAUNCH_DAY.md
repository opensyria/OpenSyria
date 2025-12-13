# 🇸🇾 OpenSY Launch Day - December 8, 2025

> *"Dec 8 2024 - Syria Liberated from Assad / سوريا حرة"*
> — Genesis Block Message

## Network Launch Summary

**OpenSY** officially launched on **December 8, 2025** — exactly one year after Syria's liberation.

### Network Details

| Parameter | Value |
|-----------|-------|
| **Launch Date** | December 8, 2025 |
| **Genesis Timestamp** | 1733616000 (Dec 8, 2024 00:00:00 UTC) |
| **Currency** | SYL (Syrian Lira) |
| **Initial Block Reward** | 10,000 SYL |
| **Block Time** | 2 minutes |
| **Max Supply** | 21,000,000,000 SYL |
| **Halving Interval** | 1,050,000 blocks (~4 years) |

### First Seed Node

| Component | Details |
|-----------|---------|
| **IP Address** | 157.175.40.131 |
| **Hostname** | node1.opensy.net |
| **Region** | AWS Bahrain (me-south-1) |
| **P2P Port** | 9633 |
| **Version** | v30.99.0 |

### DNS Infrastructure

| Record | Target |
|--------|--------|
| `node1.opensy.net` | 157.175.40.131 |
| `ns1.opensy.net` | 157.175.40.131 |
| `seed.opensy.net` | NS → ns1.opensy.net |
| `explorer.opensy.net` | 157.175.40.131 |

### Block Explorer

🔍 **https://explorer.opensy.net**

- Full Arabic (RTL) and English support
- View blocks, transactions, addresses
- Network statistics dashboard
- Search by block height, hash, or transaction ID
- SSL secured with Let's Encrypt

### First Blocks

| Block | Hash | Timestamp |
|-------|------|-----------|
| Genesis (0) | `0000000727ee231c405685355f07629b06bfcb462cfa1ed7de868a6d9590ca8d` | Dec 8, 2024 |
| Block 1 | `0000001a06694a3c581ca3b3fad240676869336f04dccd42eccc72ffc988f526` | Dec 8, 2025 |

### First Address

```
syl1q0y76xxxdfvhfad2sju4fymnsn8zs5lndpwhufw
```

This bech32 address received the first block rewards.

## Connect to the Network

### Quick Start

```bash
# Clone and build
git clone https://github.com/opensy/OpenSY.git
cd OpenSY
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j$(nproc)

# Run node
./build/bin/opensyd -daemon

# Check status
./build/bin/opensy-cli getblockchaininfo
```

### Connect to Seed Node

```bash
./build/bin/opensyd -addnode=node1.opensy.net
```

## Services Running

| Service | Status | Port |
|---------|--------|------|
| opensyd | ✅ Active | 9633 (P2P), 9632 (RPC) |
| opensy-seeder | ✅ Active | 53/UDP (DNS) |
| opensy-miner | ✅ Active | N/A |

## How to Mine

### Solo Mining (CPU)

```bash
# Start your node
./build/bin/opensyd -daemon -addnode=node1.opensy.net

# Create a wallet
./build/bin/opensy-cli createwallet "mining-wallet"

# Get a mining address
./build/bin/opensy-cli -rpcwallet=mining-wallet getnewaddress "mining"

# Start mining (replace ADDRESS with your address)
./build/bin/opensy-cli generatetoaddress 100 ADDRESS 500000000
```

### Continuous Mining

```bash
# Run in a loop
while true; do 
  ./build/bin/opensy-cli generatetoaddress 10 YOUR_ADDRESS 500000000
done
```

> **Note:** Block rewards require 100 confirmations (~3.3 hours) before they can be spent.

## What's Next

- [ ] Deploy block explorer
- [ ] Create wallet releases (GUI)
- [ ] Add more seed nodes (geographic distribution)
- [ ] Community outreach
- [ ] Exchange listings

---

**سوريا حرة** 🇸🇾

*For the people of Syria, by the people of Syria.*
