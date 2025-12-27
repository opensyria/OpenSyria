# OpenSY Upstream Sync Strategy

## Overview

OpenSY is forked from Bitcoin Core with RandomX proof-of-work integration. This document outlines the strategy for maintaining compatibility with upstream security fixes while preserving OpenSY-specific modifications.

## Divergence Points

### Critical Files Modified by OpenSY

These files contain OpenSY-specific logic and require manual review when upstream changes:

| File | Modification | Merge Strategy |
|------|--------------|----------------|
| `src/pow.cpp` | RandomX/Argon2id PoW | **Manual merge** - core divergence |
| `src/pow.h` | RandomX function signatures | **Manual merge** |
| `src/crypto/randomx_*` | **New files** - RandomX integration | N/A (OpenSY only) |
| `src/crypto/argon2_*` | **New files** - Argon2 fallback | N/A (OpenSY only) |
| `src/kernel/chainparams.cpp` | OpenSY chain params | **Manual merge** - parameters differ |
| `src/consensus/params.h` | RandomX consensus params | **Manual merge** |
| `src/validation.cpp` | RandomX validation calls | **Careful merge** - isolated changes |
| `src/chainparamsseeds.h` | OpenSY seed nodes | **Replace** - completely different |
| `src/qt/*` | Branding changes | **Easy merge** - mostly cosmetic |

### Files Safe to Sync

These can generally be merged from upstream with minimal conflicts:

- `src/wallet/*` - Wallet functionality (no PoW interaction)
- `src/rpc/*` - RPC handlers (except mining RPCs)
- `src/net.cpp`, `src/net_processing.cpp` - P2P networking
- `src/script/*` - Script validation
- `src/index/*` - Indexes
- `src/util/*` - Utilities
- `test/*` - Tests (may need adaptation)
- `doc/*` - Documentation

## Automated Monitoring

### GitHub Action

A weekly GitHub Action (`.github/workflows/upstream-sync-check.yml`) monitors upstream Bitcoin Core for:

1. **Security-critical changes** in consensus, crypto, and validation code
2. **CVE announcements** via GitHub Security Advisories
3. **Total commit count** since our fork point

### Manual Trigger

```bash
# Run the upstream check manually
gh workflow run upstream-sync-check.yml
```

## Merge Process

### 1. Review Upstream Changes

```bash
# Add Bitcoin Core remote (one-time)
git remote add bitcoin https://github.com/bitcoin/bitcoin.git

# Fetch latest
git fetch bitcoin master

# View changes in critical files
git log --oneline origin/main..bitcoin/master -- src/pow.cpp src/validation.cpp
```

### 2. Cherry-Pick Security Fixes

For security fixes, cherry-pick individual commits rather than rebasing:

```bash
# Create a branch for the merge
git checkout -b upstream-security-YYYY-MM

# Cherry-pick specific commits
git cherry-pick <commit-hash>

# If conflicts in RandomX-modified files, resolve manually
# Ensure RandomX logic is preserved
```

### 3. Test Thoroughly

```bash
# Run full test suite
make check

# Run RandomX-specific tests
./src/test/test_opensy --run_test=randomx*

# Regtest validation
./src/opensy-cli -regtest generatetoaddress 200 <address>
```

### 4. Document Changes

Update this file with:
- Date of merge
- Bitcoin Core commit range merged
- Any conflicts resolved
- Files that required manual intervention

## Merge History

| Date | Bitcoin Core Range | Notes |
|------|-------------------|-------|
| 2024-12-08 | Fork from v28.0 | Initial fork with RandomX |
| *Future* | - | - |

## Security Response

### If Critical CVE in Bitcoin Core

1. **Immediate assessment**: Does it affect OpenSY?
   - PoW-related: Likely needs OpenSY-specific patch
   - Wallet/RPC/Net: Likely can cherry-pick directly

2. **Priority merge**: Cherry-pick within 24-48 hours

3. **Release**: Tag new version, announce to node operators

### Contact

- Security issues: security@opensyria.net
- Upstream sync questions: [Create GitHub issue with `upstream-sync` label]
