# OpenSY Mobile Wallet Architecture

**Version:** 1.0  
**Date:** December 21, 2025  
**Status:** Planning

---

## Executive Summary

Syria has **95%+ mobile internet usage**. Without mobile wallets, mass adoption of OpenSY is impossible. This document outlines the architecture options for implementing mobile wallet support.

---

## Current Infrastructure

OpenSY already has the server-side infrastructure for light clients:

| Component | Status | Details |
|-----------|--------|---------|
| **BIP 157/158 Block Filters** | ✅ Enabled by default | Full nodes index and serve compact block filters |
| **P2P Filter Protocol** | ✅ Implemented | `getcfilters`, `getcfheaders`, `getcfcheckpt` messages |
| **NODE_COMPACT_FILTERS** | ✅ Advertised | Nodes signal light client support in service flags |
| **AssumeUTXO** | ✅ Configured | Fast sync for semi-light setups |

**What's Missing:** A mobile client application to consume these services.

---

## Architecture Options

### Option A: Neutrino-Style Light Client (BIP 157/158)

```
┌─────────────────────────────────────────────────────────────────┐
│                     MOBILE DEVICE                                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  OpenSY Mobile Wallet                      │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │  │
│  │  │   Wallet    │  │   Neutrino  │  │    P2P Layer    │   │  │
│  │  │   Manager   │  │   Client    │  │  (Light Mode)   │   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘   │  │
│  │         │                │                  │             │  │
│  │         └────────────────┴──────────────────┘             │  │
│  │                          │                                 │  │
│  │  ┌───────────────────────┴───────────────────────────┐   │  │
│  │  │              Local SQLite Database                 │   │  │
│  │  │  • Wallet keys (encrypted)                         │   │  │
│  │  │  • Block headers                                   │   │  │
│  │  │  • Relevant filters                                │   │  │
│  │  │  • Transaction history                             │   │  │
│  │  └───────────────────────────────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ P2P Protocol (BIP 157/158)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     OPENSY FULL NODES                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Node 1    │  │   Node 2    │  │        Node N           │  │
│  │ (Mainnet)   │  │ (Mainnet)   │  │      (Mainnet)          │  │
│  │             │  │             │  │                         │  │
│  │ Filters: ✓  │  │ Filters: ✓  │  │      Filters: ✓         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**How It Works:**
1. Mobile wallet connects to multiple OpenSY full nodes
2. Downloads block headers (80 bytes each, ~50 MB for full chain)
3. Downloads compact block filters (BIP 158) for relevant blocks
4. Filters match wallet addresses → download full block for those matches
5. Extracts relevant transactions locally

**Pros:**
- Pure P2P - no server infrastructure needed
- Maximum decentralization and privacy
- Works offline after initial sync
- Bitcoin Core-compatible protocol

**Cons:**
- More complex client implementation
- Higher bandwidth for initial sync (~50-100 MB)
- Requires connecting to multiple peers

**Estimated Development Time:** 3-4 months

**Technology Stack:**
- React Native (iOS + Android)
- rust-bitcoin or bitcoinjs-lib for cryptography
- Custom P2P networking layer

---

### Option B: Electrum Protocol

```
┌─────────────────────────────────────────────────────────────────┐
│                     MOBILE DEVICE                                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  OpenSY Mobile Wallet                      │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │  │
│  │  │   Wallet    │  │  Electrum   │  │   SSL/TCP       │   │  │
│  │  │   Manager   │  │   Client    │  │   Connection    │   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Electrum Protocol (JSON-RPC over SSL)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  ELECTRUM SERVER CLUSTER                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Fulcrum 1   │  │ Fulcrum 2   │  │      Fulcrum N          │  │
│  │  (Europe)   │  │  (Americas) │  │     (Asia-Pacific)      │  │
│  │             │  │             │  │                         │  │
│  │ Index: ✓    │  │ Index: ✓    │  │       Index: ✓          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│         │                │                      │                │
│         └────────────────┴──────────────────────┘                │
│                          │                                       │
│                          ▼                                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    OpenSY Full Node                        │  │
│  │                   (Backend for Fulcrum)                    │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**How It Works:**
1. Deploy Fulcrum/ElectrumX servers connected to OpenSY nodes
2. Servers index all addresses and maintain UTXO index
3. Mobile wallet queries server for address history
4. Server returns transaction data, balance, etc.

**Pros:**
- Proven technology (millions of Electrum users)
- Instant sync (no headers download)
- Many existing client libraries
- Lower bandwidth usage

**Cons:**
- Requires server infrastructure
- Less privacy (servers see addresses)
- Single point of failure (mitigated by multiple servers)

**Estimated Development Time:** 2-3 months

**Technology Stack:**
- Fulcrum (high-performance Electrum server)
- React Native with electrum-client library
- Or adapt existing Electrum mobile (Android)

---

### Option C: Hybrid Approach (RECOMMENDED)

```
Phase 1 (MVP - 6 weeks):
├── Deploy Electrum infrastructure for quick mobile wallet
├── Use existing Electrum client as base
└── Fast time-to-market for Syrian users

Phase 2 (Long-term - 3 months):
├── Develop native Neutrino client
├── Add P2P mode to mobile wallet
└── Users can choose: Electrum (fast) or Neutrino (private)
```

**Recommended because:**
- Gets mobile wallet to Syrian users FAST
- Electrum infrastructure is simpler to deploy
- Neutrino adds privacy option for power users
- Both use existing OpenSY P2P/filter infrastructure

---

## Implementation Roadmap

### Phase 1: Electrum Infrastructure (Weeks 1-2)

```bash
# 1. Deploy Fulcrum server
git clone https://github.com/cculianu/Fulcrum
# Configure for OpenSY:
# - Point to opensyd RPC
# - Set network magic
# - Configure ports

# 2. Start Fulcrum
./Fulcrum -D datadir -c opensy-fulcrum.conf

# 3. SSL certificate setup
certbot certonly --standalone -d electrum.opensyria.net
```

**Fulcrum Configuration:**
```conf
# opensy-fulcrum.conf
datadir = /data/fulcrum
opensyd = 127.0.0.1:9632
rpcuser = fulcrum
rpcpassword = <secure_password>

# OpenSY-specific
coin = OpenSY
# Network magic: 0x53 0x59 0x4c 0x4d

tcp = 0.0.0.0:50001
ssl = 0.0.0.0:50002
cert = /etc/letsencrypt/live/electrum.opensyria.net/fullchain.pem
key = /etc/letsencrypt/live/electrum.opensyria.net/privkey.pem
```

### Phase 2: Mobile Wallet MVP (Weeks 3-6)

**React Native Structure:**
```
opensy-mobile/
├── src/
│   ├── wallet/
│   │   ├── keys.ts          # BIP39/BIP44 key derivation
│   │   ├── addresses.ts     # OpenSY address generation (syl1...)
│   │   └── transactions.ts  # TX building and signing
│   ├── electrum/
│   │   ├── client.ts        # Electrum protocol client
│   │   ├── connection.ts    # Server connection management
│   │   └── subscriptions.ts # Address notifications
│   ├── ui/
│   │   ├── screens/
│   │   │   ├── Home.tsx
│   │   │   ├── Send.tsx
│   │   │   ├── Receive.tsx
│   │   │   └── History.tsx
│   │   └── components/
│   └── storage/
│       └── secure.ts        # Encrypted key storage
├── ios/
├── android/
└── package.json
```

**Key Dependencies:**
```json
{
  "dependencies": {
    "react-native": "^0.72.0",
    "bip39": "^3.1.0",
    "bip32": "^4.0.0",
    "bitcoinjs-lib": "^6.1.0",
    "electrum-client": "^0.1.0",
    "@react-native-async-storage/async-storage": "^1.19.0",
    "react-native-keychain": "^8.1.0"
  }
}
```

### Phase 3: Neutrino Integration (Months 3-4)

Add P2P light client mode using BIP 157/158:

```typescript
// src/neutrino/client.ts
class NeutrinoClient {
  private peers: Peer[] = [];
  private headerChain: BlockHeader[] = [];
  private filters: Map<number, CompactFilter> = new Map();
  
  async sync() {
    // 1. Connect to OpenSY peers
    await this.connectToPeers();
    
    // 2. Download headers
    await this.syncHeaders();
    
    // 3. Download filters for wallet birthday to tip
    await this.syncFilters(this.walletBirthday);
    
    // 4. Scan filters for matches
    const matches = await this.scanFilters(this.addresses);
    
    // 5. Download matching blocks
    for (const height of matches) {
      await this.downloadBlock(height);
    }
  }
}
```

---

## Security Considerations

### Key Storage

```typescript
// Use secure enclave/keychain for private keys
import * as Keychain from 'react-native-keychain';

async function storeWalletSeed(seed: string) {
  await Keychain.setGenericPassword(
    'opensy_wallet',
    seed,
    {
      accessControl: Keychain.ACCESS_CONTROL.BIOMETRY_ANY_OR_DEVICE_PASSCODE,
      accessible: Keychain.ACCESSIBLE.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
    }
  );
}
```

### Server Trust (Electrum Mode)

- Connect to multiple Electrum servers
- Verify transaction proofs (SPV)
- Cross-check balances between servers
- Warn if servers disagree

### P2P Trust (Neutrino Mode)

- Connect to 8+ peers
- Verify filter headers chain
- Download filters from multiple peers
- Ban peers that send invalid data

---

## OpenSY-Specific Considerations

### Address Format

OpenSY uses `syl1...` Bech32 addresses (HRP = 'syl' for Syrian Lira):

```typescript
// Address generation
import * as bitcoin from 'bitcoinjs-lib';

const OPENSY_MAINNET = {
  bech32: 'sy',
  bip32: { public: 0x53594d50, private: 0x53594d56 },
  pubKeyHash: 0x3f,
  scriptHash: 0x40,
  wif: 0x80,
};

function generateAddress(publicKey: Buffer): string {
  const { address } = bitcoin.payments.p2wpkh({
    pubkey: publicKey,
    network: OPENSY_MAINNET,
  });
  return address; // syl1q...
}
```

### RandomX Considerations

Light clients don't validate PoW directly, but should:
- Verify block headers form valid chain
- Trust that connected full nodes validated RandomX
- For high-value transactions, wait for more confirmations

### Transaction Fees

- OpenSY uses similar fee structure to Bitcoin
- Recommend 1-2 sat/vbyte for normal transactions
- Implement fee estimation from Electrum server

---

## Testing Strategy

### Unit Tests
- Key derivation (BIP39/44)
- Address generation
- Transaction signing
- Electrum protocol parsing

### Integration Tests
- Connect to testnet Electrum server
- Send/receive on testnet
- Multi-device sync

### Regtest Testing
```bash
# Start regtest with Electrum
./opensyd -regtest -electrumserver=1

# Or use functional test
./test/functional/feature_electrum.py
```

---

## Deployment Checklist

### Electrum Infrastructure
- [ ] Deploy Fulcrum servers (3 regions minimum)
- [ ] SSL certificates configured
- [ ] Load balancing configured
- [ ] Monitoring and alerting
- [ ] Backup/redundancy plan

### Mobile App
- [ ] iOS App Store submission
- [ ] Google Play Store submission
- [ ] APK direct download (for regions with Play Store issues)
- [ ] F-Droid submission (open source Android)

### Documentation
- [ ] User guide (Arabic + English)
- [ ] Video tutorials
- [ ] FAQ

---

## Resources

### Existing Implementations to Study

| Project | Language | Notes |
|---------|----------|-------|
| [Electrum](https://github.com/spesmilo/electrum) | Python | Reference Electrum client |
| [BlueWallet](https://github.com/BlueWallet/BlueWallet) | React Native | Popular mobile wallet |
| [Neutrino](https://github.com/lightninglabs/neutrino) | Go | LND's light client |
| [BDK](https://github.com/bitcoindevkit/bdk) | Rust | Bitcoin Dev Kit (recommended) |

### BIP References
- [BIP 157: Client Side Block Filtering](https://github.com/bitcoin/bips/blob/master/bip-0157.mediawiki)
- [BIP 158: Compact Block Filters](https://github.com/bitcoin/bips/blob/master/bip-0158.mediawiki)
- [Electrum Protocol](https://electrumx.readthedocs.io/en/latest/protocol.html)

---

## Timeline Summary

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Electrum Infrastructure | 2 weeks | Fulcrum servers operational |
| Mobile MVP (Electrum) | 4 weeks | Basic send/receive wallet |
| App Store Submission | 2 weeks | iOS + Android published |
| Neutrino Integration | 8 weeks | P2P light client mode |
| **Total to MVP** | **6 weeks** | **Mobile wallet live** |
| **Total to Full** | **16 weeks** | **Both modes available** |

---

*سوريا حرة* 🇸🇾
