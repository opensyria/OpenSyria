# OpenSY Emergency PoW Fallback: Argon2id

**Version:** 1.0  
**Date:** December 21, 2025  
**Status:** Dormant (Emergency Only)

---

## Overview

OpenSY includes a dormant emergency fallback proof-of-work algorithm: **Argon2id**.

This mechanism is designed to protect the network if RandomX is ever compromised (cryptographic break, critical implementation vulnerability, or novel attack vector). The fallback is **not active by default** and can only be activated via a consensus hard fork.

---

## Why Argon2id?

| Criteria | Argon2id | Alternative Considered |
|----------|----------|------------------------|
| **ASIC Resistance** | ✅ Memory-hard | SHA256d has ASICs |
| **CPU Friendly** | ✅ Designed for CPUs | scrypt has GPU ASICs |
| **Audit Quality** | ✅ PHC Winner 2015 | yespower less reviewed |
| **Side-Channel Resistance** | ✅ id variant | CryptoNight deprecated |
| **Library Support** | ✅ libsodium, widespread | Custom implementations risky |
| **Complexity** | ✅ Simpler than RandomX | Fewer attack surfaces |

### Argon2id Properties

- **Memory**: Configurable (default 2GB, matching RandomX)
- **Time Cost**: 1 iteration (tuned for ~100ms per hash)
- **Parallelism**: 1 (prevents GPU optimization)
- **Output**: 256-bit hash

---

## Activation Mechanism

### Default State: DORMANT

```cpp
consensus.nArgon2EmergencyHeight = -1;  // Never active
```

The fallback is dormant by default. RandomX remains the active PoW algorithm.

### Emergency Activation

If RandomX is compromised, the OpenSY developers would:

1. **Assess the threat** (cryptographic break, CVE, etc.)
2. **Coordinate with miners** via announcement channels
3. **Set activation height** in new release:
   ```cpp
   consensus.nArgon2EmergencyHeight = <BLOCK_HEIGHT>;
   ```
4. **Release emergency update** with mandatory upgrade notice
5. **Hard fork activates** at specified height

### Algorithm Selection Logic

```
height == 0                              → SHA256d (genesis)
height >= 1 && nArgon2EmergencyHeight < 0  → RandomX
height >= 1 && height >= nArgon2EmergencyHeight → Argon2id
```

---

## Technical Implementation

### Files

| File | Purpose |
|------|---------|
| [src/crypto/argon2_context.h](../../src/crypto/argon2_context.h) | Argon2 context header |
| [src/crypto/argon2_context.cpp](../../src/crypto/argon2_context.cpp) | Argon2 implementation |
| [src/consensus/params.h](../../src/consensus/params.h) | Algorithm selection |
| [src/pow.cpp](../../src/pow.cpp) | PoW validation integration |
| [src/test/argon2_fallback_tests.cpp](../../src/test/argon2_fallback_tests.cpp) | Unit tests |

### Consensus Parameters

```cpp
// In Consensus::Params
int nArgon2EmergencyHeight{-1};       // Height for activation (-1 = never)
uint32_t nArgon2MemoryCost{1 << 21};  // Memory in KiB (2GB)
uint32_t nArgon2TimeCost{1};          // Iterations
uint32_t nArgon2Parallelism{1};       // Threads
uint256 powLimitArgon2;               // Minimum difficulty
```

### Algorithm Enum

```cpp
enum class PowAlgorithm {
    SHA256D,    // Genesis block
    RANDOMX,    // Primary algorithm (block 1+)
    ARGON2ID    // Emergency fallback
};
```

---

## Security Considerations

### Why Not Pre-Announce the Fallback Height?

Pre-announcing an activation height would:
- Allow attackers to prepare optimized hardware
- Create uncertainty about which chain is canonical
- Enable manipulation of the transition

The fallback is intentionally **dormant** until needed.

### What Triggers Activation?

| Scenario | Response |
|----------|----------|
| RandomX cryptographic break | Immediate emergency fork |
| Critical CVE in RandomX implementation | Emergency fork within days |
| Theoretical weakness discovered | Planned upgrade with lead time |
| 51% attack (not algo-related) | No algo change needed |

### Difficulty Reset

At emergency activation, difficulty resets to `powLimitArgon2` to allow miners to immediately participate with the new algorithm.

---

## Dependencies

### libsodium (Recommended)

For production deployments, link against libsodium for optimized Argon2id:

```bash
# macOS
brew install libsodium

# Ubuntu/Debian
apt install libsodium-dev

# Build with libsodium
cmake -B build -DCMAKE_BUILD_TYPE=Release
# libsodium is auto-detected via pkg-config
```

If libsodium is not available, a reference implementation stub is used (suitable for testing, not production).

---

## Testing

### Unit Tests

```bash
# Run Argon2 fallback tests
./build/bin/test_opensy --run_test=argon2_fallback_tests

# Run all tests
./build/bin/test_opensy
```

### Regtest Testing

Test emergency activation on regtest:

```bash
# Start regtest with emergency activation at height 100
./opensyd -regtest -randomxforkheight=1 -argon2emergencyheight=100

# Mine past activation height
./opensy-cli -regtest generatetoaddress 150 <address>

# Verify Argon2id is active
./opensy-cli -regtest getblockchaininfo
```

---

## Emergency Hard Fork Operations Runbook

This section provides step-by-step procedures for activating the Argon2id emergency fallback.

### Pre-Requisites

Before initiating an emergency hard fork:

- [ ] Confirm the threat to RandomX (cryptographic break, critical CVE, active attack)
- [ ] Core development team consensus (minimum 3 maintainers)
- [ ] Security assessment documented
- [ ] Test build verified on testnet/regtest

### Phase 1: Assessment & Decision (0-4 hours)

```
┌─────────────────────────────────────────────────────────────────┐
│  INCIDENT DETECTED                                               │
│  • Hashrate monitor alert (>30% drop)                           │
│  • Block time anomalies (>3x target)                            │
│  • Security researcher disclosure                               │
│  • CVE published for RandomX                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. ASSESS SEVERITY                                              │
│  • Is RandomX fundamentally broken?                             │
│  • Is this a temporary mining pool issue?                       │
│  • Can a patch fix the issue without algorithm change?          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. CORE TEAM DECISION                                          │
│  • Emergency meeting (Signal/Matrix)                            │
│  • Vote on emergency activation                                 │
│  • Set target activation height                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Phase 2: Development & Testing (4-12 hours)

#### Step 2.1: Update Consensus Parameters

Edit `src/kernel/chainparams.cpp`:

```cpp
// In CMainParams constructor:
consensus.nArgon2EmergencyHeight = <ACTIVATION_HEIGHT>;
// Choose height ~24-48 hours in the future to allow upgrade time
// Example: current_height + 144 (for ~24h) or + 288 (for ~48h)
```

#### Step 2.2: Create Emergency Release Branch

```bash
git checkout -b emergency/argon2-activation-v<VERSION>
# Make changes
git commit -m "EMERGENCY: Activate Argon2id fallback at height <HEIGHT>"
git push origin emergency/argon2-activation-v<VERSION>
```

#### Step 2.3: Test on Regtest

```bash
# Build emergency release
cmake -B build_emergency -DCMAKE_BUILD_TYPE=Release
cmake --build build_emergency -j$(nproc)

# Test activation
./build_emergency/bin/opensyd -regtest -argon2emergencyheight=10
./build_emergency/bin/opensy-cli -regtest generatetoaddress 15 <address>
# Verify blocks 10+ use Argon2id
```

#### Step 2.4: Run Full Test Suite

```bash
# Unit tests
./build_emergency/bin/test_opensy --run_test=argon2_fallback_tests
./build_emergency/bin/test_opensy --run_test=pow_tests

# Functional tests
./test/functional/feature_argon2_fallback.py
./test/functional/feature_argon2_stress.py
```

### Phase 3: Release & Communication (12-24 hours)

#### Step 3.1: Build Release Binaries

```bash
# macOS
cmake -B build_release_mac --preset=mac-release
cmake --build build_release_mac

# Linux
cmake -B build_release_linux --preset=linux-release  
cmake --build build_release_linux

# Windows (cross-compile)
cmake -B build_release_win --preset=win-release
cmake --build build_release_win
```

#### Step 3.2: Create Release Artifacts

```bash
# Create release tag
git tag -s v<VERSION>-emergency -m "Emergency Argon2id activation"
git push origin v<VERSION>-emergency

# Build checksums
sha256sum opensyd-* > SHA256SUMS
gpg --detach-sign --armor SHA256SUMS
```

#### Step 3.3: Communication Plan

**Immediate (Hour 0-1):**
- [ ] Post to GitHub Releases with CRITICAL label
- [ ] Tweet from @OpenSYcoin: "EMERGENCY UPDATE: Please upgrade immediately"
- [ ] Discord announcement with @everyone
- [ ] Telegram broadcast

**Template Announcement:**
```
🚨 EMERGENCY SECURITY UPDATE 🚨

OpenSY v<VERSION> is a MANDATORY upgrade that activates the Argon2id 
proof-of-work fallback at block height <HEIGHT> (~<DATE/TIME> UTC).

This upgrade is required due to [brief reason - e.g., "critical 
vulnerability in RandomX discovered"].

⏰ DEADLINE: Block <HEIGHT> (~<HOURS> hours from now)

📥 DOWNLOAD: https://github.com/OpenSyria/OpenSyria/releases/v<VERSION>

All nodes MUST upgrade before the activation height. Nodes running 
older versions will fork off the network.

Miners: Your mining software will automatically switch to Argon2id 
after the upgrade.

Questions? Join #emergency-support on Discord.
```

**Ongoing (Hour 1-24):**
- [ ] Monitor upgrade adoption via node version tracking
- [ ] Direct outreach to known pool operators
- [ ] Exchange notifications (if applicable)
- [ ] Update documentation and website

### Phase 4: Activation & Monitoring

#### Step 4.1: Pre-Activation Checklist (T-1 hour)

- [ ] >50% of known nodes on new version
- [ ] Major mining pools confirmed upgraded
- [ ] Monitoring dashboards active:
  - `hashrate_monitor.py --drop-threshold 0.20`
  - `blocktime_monitor.py --slow-threshold 2.0`
- [ ] Core team on standby

#### Step 4.2: Activation Block

At activation height, the network will:
1. Reset difficulty to `powLimitArgon2`
2. Switch PoW validation to Argon2id
3. Reject RandomX blocks from non-upgraded nodes

**Monitor for:**
- Hashrate recovery (Argon2id miners joining)
- Block time normalization (~10 min target)
- Any chain splits (old nodes forking)

#### Step 4.3: Post-Activation (First 24 hours)

- [ ] Verify chain is progressing normally
- [ ] Monitor for orphan rate changes
- [ ] Track difficulty adjustments
- [ ] Respond to community questions

### Rollback Procedure

If the emergency activation causes unexpected issues:

**Option A: Continue with Argon2id**
- Most likely path; Argon2id is production-ready
- Address any issues with follow-up patches

**Option B: Emergency Rollback (last resort)**
- Only if Argon2id itself has critical issues
- Requires another hard fork back to RandomX (or new algorithm)
- Extremely unlikely given Argon2id's maturity

```bash
# Rollback would require:
consensus.nArgon2EmergencyHeight = -1;  // Deactivate
# Plus height-based logic to switch back after the rollback height
```

### Emergency Contacts

| Role | Contact | Backup |
|------|---------|--------|
| Lead Developer | [REDACTED] | [REDACTED] |
| Security Lead | [REDACTED] | [REDACTED] |
| Infrastructure | [REDACTED] | [REDACTED] |
| Communications | [REDACTED] | [REDACTED] |

---

## Monitoring Tools

The following tools are available in `contrib/monitoring/`:

| Tool | Purpose |
|------|---------|
| `hashrate_monitor.py` | Alerts on hashrate drops >30% |
| `blocktime_monitor.py` | Alerts on abnormal block times |
| `peer_monitor.py` | Monitors peer connections and bans |
| `distribution_analyzer.py` | Analyzes mining centralization |

### Quick Start

```bash
# Monitor hashrate with Slack alerts
python3 contrib/monitoring/hashrate_monitor.py \
    --rpc-user YOUR_USER \
    --rpc-password YOUR_PASSWORD \
    --webhook-url https://hooks.slack.com/services/XXX \
    --drop-threshold 0.30

# Monitor block times
python3 contrib/monitoring/blocktime_monitor.py \
    --rpc-user YOUR_USER \
    --rpc-password YOUR_PASSWORD \
    --slow-threshold 3.0
```

---

## FAQ

### Q: Is Argon2id currently active?

**No.** It is dormant. RandomX is the active PoW algorithm. Argon2id only activates in an emergency.

### Q: Will my miner work with Argon2id?

If Argon2id is activated, miners will need to update their software. The new version will include Argon2id mining support.

### Q: Why not use multiple algorithms like DigiByte?

Multi-algo introduces complexity and potential attack vectors (algo-hopping, difficulty manipulation). A single primary algorithm with a dormant fallback is simpler and more secure.

### Q: What if Argon2id is also compromised?

If both RandomX and Argon2id were compromised simultaneously (extremely unlikely), the network would need a more fundamental upgrade. The fallback buys time for such a response.

### Q: How much notice will we have before activation?

The target is 24-48 hours between release and activation. This balances urgency (if RandomX is actively being exploited) with giving node operators time to upgrade.

### Q: What happens to old nodes?

Nodes that don't upgrade will fork off onto their own chain after the activation height. They will reject Argon2id blocks as invalid. This is intentional - it's a hard fork.

---

## References

- [Argon2 Specification (RFC 9106)](https://datatracker.ietf.org/doc/html/rfc9106)
- [Password Hashing Competition](https://password-hashing.net/)
- [libsodium Documentation](https://doc.libsodium.org/)
- [RandomX Specification](https://github.com/tevador/RandomX)

---

*سوريا حرة* 🇸🇾
