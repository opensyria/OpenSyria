# OpenSY Native Mobile Wallet Architecture

## Overview

Native iOS (Swift) and Android (Kotlin) wallets for the OpenSY blockchain, providing the best user experience with full platform integration.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Mobile Applications                              │
├────────────────────────────────┬────────────────────────────────────────┤
│     iOS (Swift/SwiftUI)        │      Android (Kotlin/Compose)          │
│  ┌──────────────────────────┐  │  ┌──────────────────────────────────┐  │
│  │ UI Layer                 │  │  │ UI Layer                         │  │
│  │ - SwiftUI Views          │  │  │ - Jetpack Compose                │  │
│  │ - Arabic RTL native      │  │  │ - Arabic RTL native              │  │
│  │ - System dark mode       │  │  │ - Material You theming           │  │
│  └──────────────────────────┘  │  └──────────────────────────────────┘  │
│  ┌──────────────────────────┐  │  ┌──────────────────────────────────┐  │
│  │ ViewModel / State        │  │  │ ViewModel / State                │  │
│  │ - @Observable            │  │  │ - StateFlow                      │  │
│  │ - Combine publishers     │  │  │ - Kotlin Coroutines              │  │
│  └──────────────────────────┘  │  └──────────────────────────────────┘  │
│  ┌──────────────────────────┐  │  ┌──────────────────────────────────┐  │
│  │ Core Wallet Library      │  │  │ Core Wallet Library              │  │
│  │ (Shared Rust via FFI)    │  │  │ (Shared Rust via JNI)            │  │
│  └──────────────────────────┘  │  └──────────────────────────────────┘  │
└────────────────────────────────┴────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    opensy-wallet-core (Rust)                            │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────────────┐│
│  │ Key Management  │ │ Transaction     │ │ Network                     ││
│  │ - BIP39 mnemonic│ │ - PSBT building │ │ - Electrum client           ││
│  │ - BIP32 HD keys │ │ - Signing       │ │ - P2P light client (future) ││
│  │ - BIP44/84 paths│ │ - Fee estimation│ │ - Block headers             ││
│  │ - Encryption    │ │ - Coin selection│ │ - SPV proofs                ││
│  └─────────────────┘ └─────────────────┘ └─────────────────────────────┘│
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────────────┐│
│  │ Address         │ │ UTXO Management │ │ Persistence                 ││
│  │ - F... (legacy) │ │ - UTXO tracking │ │ - SQLite                    ││
│  │ - syl1... (SW)  │ │ - Balance calc  │ │ - Encrypted storage         ││
│  │ - Validation    │ │ - History       │ │ - Backup/restore            ││
│  └─────────────────┘ └─────────────────┘ └─────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ Electrum Protocol (TCP/SSL)
┌─────────────────────────────────────────────────────────────────────────┐
│                     Electrum Server Cluster                              │
│  electrum1.opensyria.net:50002 (SSL)                                    │
│  electrum2.opensyria.net:50002 (SSL)                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     OpenSY Full Nodes                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

## Shared Rust Core

Using Rust for crypto/wallet logic provides:
- **Single codebase** for iOS/Android
- **Memory safety** for key handling
- **Performance** for crypto operations
- **Auditable** single security-critical module

### Build Targets

```bash
# iOS
cargo build --target aarch64-apple-ios
cargo build --target aarch64-apple-ios-sim

# Android  
cargo build --target aarch64-linux-android
cargo build --target armv7-linux-androideabi
cargo build --target x86_64-linux-android
```

## Key Features

### Security
- [ ] Biometric authentication (Face ID / Fingerprint)
- [ ] Secure Enclave key storage (iOS) / Android Keystore
- [ ] BIP39 mnemonic with optional passphrase
- [ ] Encrypted local database
- [ ] No plaintext keys ever in memory (Rust zeroing)

### UX
- [ ] Arabic-first design with full RTL
- [ ] One-tap receive (QR code display)
- [ ] QR scanning for send
- [ ] Transaction history with Arabic date formatting
- [ ] Push notifications for incoming transactions
- [ ] Offline transaction signing (air-gapped)
- [ ] iCloud/Google Drive encrypted backup

### Network Resilience
- [ ] Multiple Electrum server fallback
- [ ] Offline queue for transactions
- [ ] Background sync
- [ ] Low-bandwidth mode (header-only sync)

## Directory Structure

```
mobile/
├── opensy-wallet-core/          # Rust shared library
│   ├── Cargo.toml
│   ├── src/
│   │   ├── lib.rs
│   │   ├── keys.rs              # BIP32/39/44
│   │   ├── address.rs           # OpenSY address encoding
│   │   ├── transaction.rs       # Tx building & signing
│   │   ├── electrum.rs          # Electrum protocol client
│   │   ├── storage.rs           # Encrypted SQLite
│   │   └── ffi/
│   │       ├── ios.rs           # Swift FFI bindings
│   │       └── android.rs       # JNI bindings
│   └── tests/
├── ios/
│   ├── OpenSY.xcodeproj
│   ├── OpenSY/
│   │   ├── App.swift
│   │   ├── Views/
│   │   ├── ViewModels/
│   │   ├── Services/
│   │   └── Localization/
│   │       ├── ar.lproj/
│   │       └── en.lproj/
│   └── OpenSYTests/
├── android/
│   ├── app/
│   │   ├── src/main/
│   │   │   ├── java/.../opensy/
│   │   │   │   ├── MainActivity.kt
│   │   │   │   ├── ui/
│   │   │   │   ├── viewmodel/
│   │   │   │   └── data/
│   │   │   └── res/
│   │   │       ├── values/
│   │   │       └── values-ar/
│   │   └── build.gradle.kts
│   └── build.gradle.kts
└── docs/
    ├── security-model.md
    └── electrum-protocol.md
```

## Development Phases

### Phase 1: Core Library (4-6 weeks)
- [ ] BIP39 mnemonic generation/recovery
- [ ] BIP32/44/84 key derivation for OpenSY paths
- [ ] Address generation (F..., syl1...)
- [ ] Transaction building and signing
- [ ] Electrum client (balance, UTXO, broadcast)
- [ ] Unit tests with test vectors

### Phase 2: iOS App (4-6 weeks)
- [ ] SwiftUI shell with navigation
- [ ] Wallet creation/recovery flow
- [ ] Receive screen with QR
- [ ] Send flow with QR scanner
- [ ] Transaction history
- [ ] Settings & backup
- [ ] Arabic localization

### Phase 3: Android App (4-6 weeks)
- [ ] Compose UI matching iOS
- [ ] JNI integration with Rust core
- [ ] Full feature parity
- [ ] Arabic localization

### Phase 4: Polish & Audit (2-4 weeks)
- [ ] Security audit of Rust core
- [ ] Penetration testing
- [ ] Beta testing program
- [ ] App Store / Play Store submission

## Dependencies

### Rust Core
```toml
[dependencies]
bip39 = "2.0"                    # Mnemonic handling
bitcoin = "0.32"                 # Primitives (fork for OpenSY params)
secp256k1 = "0.29"              # Signing
electrum-client = "0.19"         # Electrum protocol
rusqlite = { version = "0.31", features = ["bundled"] }
chacha20poly1305 = "0.10"        # Encryption
zeroize = "1.7"                  # Secure memory wiping
uniffi = "0.27"                  # FFI bindings generator
```

### iOS
- Minimum iOS 15.0
- Swift 5.9+
- SwiftUI
- Swift Package Manager

### Android
- Minimum SDK 26 (Android 8.0)
- Kotlin 1.9+
- Jetpack Compose
- Gradle 8.x

## Electrum Server Requirements

Before mobile launch, deploy:

1. **Fulcrum** (recommended) or ElectrumX
2. Minimum 2 servers for redundancy
3. SSL certificates for secure connections
4. WebSocket support for real-time updates

```bash
# Fulcrum config for OpenSY
datadir = /data/fulcrum
bitcoind = 127.0.0.1:9632
rpcuser = fulcrum
rpcpassword = <password>
tcp = 0.0.0.0:50001
ssl = 0.0.0.0:50002
cert = /etc/ssl/certs/electrum.crt
key = /etc/ssl/private/electrum.key
```

## Security Considerations

1. **Key material never leaves Rust core** - Swift/Kotlin only see addresses and signed txs
2. **Mnemonic displayed once** during creation, then only encrypted
3. **Biometric required** for signing, optional for balance view
4. **No analytics/tracking** - privacy first
5. **Reproducible builds** for verification

## Next Immediate Steps

1. Set up `mobile/` directory structure
2. Initialize Rust workspace with UniFFI
3. Implement BIP39 with OpenSY word list (standard English for now)
4. Create OpenSY address derivation (m/44'/9633'/0'/...)
5. Set up Electrum server on your infrastructure
