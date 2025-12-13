# OpenSyria Security Considerations

**Version:** 1.0  
**Date:** December 2025

---

## Overview

This document describes security considerations and known trade-offs in the OpenSyria implementation. It is intended for operators, auditors, and developers who need to understand the security properties of the system.

---

## RandomX Proof-of-Work

### Algorithm Selection

OpenSyria uses RandomX proof-of-work starting from block 1. RandomX is an ASIC-resistant, CPU-optimized mining algorithm that:

- Democratizes mining by making it accessible to commodity hardware
- Prevents hash power concentration in specialized ASICs
- Uses memory-hard computations that resist parallel attacks

### Key Rotation

RandomX keys are rotated every 32 blocks (mainnet) to prevent pre-computation attacks. The key for a block at height `h` is derived from the block at height:

```
keyHeight = floor(h / 32) * 32 - 32
```

### M-01: Early Key Block Sharing (Accepted Trade-off)

**Issue:** Blocks 1-63 all derive their RandomX key from the genesis block hash (block 0) due to the key rotation formula clamping negative heights to 0.

**Impact:** An attacker who knows the genesis hash before launch could pre-compute RandomX datasets and gain an unfair mining advantage for the first ~2 hours of network operation.

**Status:** **ACCEPTED TRADE-OFF**

This is a bootstrap security concession that cannot be changed without a hard fork. The trade-off is acceptable because:

1. **Historical:** For a launched mainnet, blocks 1-63 are already mined
2. **Time-limited:** Only affects the first 64 blocks (~2 hours)
3. **Self-correcting:** Difficulty adjusts to actual network hashrate
4. **Documented:** Users and operators are aware of this limitation

**Mitigations:**
- `nMinimumChainWork` is updated regularly in releases
- Block times are monitored for anomalies
- Future testnets will use improved key derivation

---

## Memory Management

### H-01: RandomX Context Pool

RandomX validation requires a ~256KB context per validation thread. To prevent memory exhaustion:

1. **Bounded Pool:** Maximum 8 contexts (2MB total) by default
2. **RAII Guards:** Automatic context return prevents leaks
3. **Key-aware Reuse:** Contexts are reused when keys match
4. **Timeout Protection:** Acquisition times out after 30 seconds

Configuration: The pool size can be tuned via `-randomxpoolsize` (default: 8).

---

## Header Synchronization

### H-02: Header Spam Protection

During sync, headers are checked for claimed work before full RandomX validation. Protections include:

1. **Tight Threshold:** Headers must claim work ≤ powLimit/4096
2. **Rate Limiting:** Maximum 2000 headers per minute per peer
3. **Graduated Scoring:** Excessive headers add to misbehavior score

---

## Peer Management

### M-04: Graduated Peer Scoring

Instead of immediate disconnection, misbehavior is scored:

| Offense Type | Score |
|--------------|-------|
| Consensus violation | 100 (immediate disconnect) |
| Invalid header | 50 |
| Protocol violation | 20 |
| Rate limiting exceeded | 10-20 |
| Minor quirk | 1 |

Peers are disconnected at score 100. This prevents eclipse attacks via false-positive misbehavior triggers.

---

## Wallet Security

### L-02: Key Derivation

New wallets use Argon2id key derivation (method 1) which provides:

- Memory-hard computation resistant to GPU/ASIC attacks
- Better protection against brute-force on weak passwords
- 64MB memory cost, 4 parallel lanes, 3 iterations by default

Legacy wallets using SHA512 (method 0) are still supported for backward compatibility. Users can upgrade via the `upgradewallet` RPC.

**Password Recommendations:**
- Use 12+ character passphrases
- Include mixed case, numbers, and symbols
- Consider using a password manager
- Never reuse passwords from other services

---

## Block Storage Integrity

### M-02: Corruption Detection

Block storage includes validation gates:

1. **Serve-time Validation:** Blocks are fully validated before relay
2. **Reindex Mode:** Use `-reindex` to fully re-validate chain

---

## Difficulty Adjustment

### M-03: Fork Height Reset

At the RandomX fork height, difficulty resets to minimum. This is necessary because:

1. SHA256d difficulty values are meaningless for RandomX
2. No pre-fork hashrate data exists
3. Difficulty self-corrects within ~2016 blocks

Operators should monitor block times during fork transitions.

---

## Reporting Security Issues

Please report security vulnerabilities responsibly via:

- Email: security@opensyria.org
- PGP Key: [Published on website]

Do not disclose vulnerabilities publicly until a fix is released.

---

*Document Version 1.0 — December 2025*
