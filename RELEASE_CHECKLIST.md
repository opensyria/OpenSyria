# OpenSY Release Checklist

This checklist must be completed before any mainnet release.

**Status: ✅ ALL BLOCKERS COMPLETE** (December 18, 2025)

## Pre-Launch Security Checklist

### Credentials Security

- [x] All example configs use placeholder passwords (not real defaults)
- [x] Explorer requires `RPC_PASSWORD` environment variable to start
- [x] Mining scripts generate random 32-character passwords
- [x] No hardcoded credentials in any committed files

### Verification

```bash
# Verify no hardcoded passwords in codebase
grep -r "rpcpassword=" . --include="*.sh" --include="*.conf" --include="*.js" | grep -v "YOUR_SECURE_PASSWORD" | grep -v '\$RPC_PASS' | grep -v '\${RPC_PASS}' | grep -v 'process.env'
# Expected: No results (or only template placeholders)
```

- [x] Above command returns no results

### Documentation

- [x] Mining setup warns about default address
- [x] README documents RPC password requirements
- [x] Explorer README explains RPC_PASSWORD environment variable

### Genesis Block

- [x] Genesis hash independently verified: `tools/verify_genesis.sh`
- [x] Genesis nonce: `48963683`
- [x] Genesis hash: `000000c4c94f54e5ae60a67df5c113dfbfd9ef872639e2359d15796f27920fd1`
- [x] Merkle root: `56f65e913353861d32d297c6bc87bbe81242b764d18b8634d75c5a0159c8859e`

### Cross-Platform Testing

- [x] Unit tests pass on macOS ARM64 (104 RandomX tests)
- [x] Unit tests pass on x86_64 Linux (Docker verified)
- [x] RandomX hashes identical - matches official test vectors
- [x] Results documented in `test/randomx_determinism_results.md`

### Concurrency Testing

- [x] ThreadSanitizer build completes without errors
- [x] TSAN test run shows zero data race warnings (8 threads, 0 races)
- [x] Test: `test/tsan_randomx_test.cpp`

### Multi-Node Testing

- [x] Multi-node sync test passes (`feature_randomx_pow.py`)
- [x] Reorg handling verified
- [x] Network partition recovery tested
- [x] Invalid block rejection verified (`feature_negative_pow_validation.py`)

### DNS Seeds

- [x] `seed.opensyria.net` resolves: `157.175.40.131`
- [x] Port 9633 (P2P) open and accepting connections

## Post-Launch Monitoring

- [ ] Monitor first 100 blocks for consensus issues
- [ ] Verify difficulty adjustment at first retarget
- [ ] Check peer connectivity and network health
- [ ] Update `nMinimumChainWork` after ~1000 blocks

## Contacts

- **Lead Developer**: [Add contact]
- **Security Team**: [Add contact]
- **Infrastructure**: [Add contact]

---

**Last Updated**: December 18, 2025
**Version**: 1.0.0 - Ready for Mainnet
