# Security Policy

## Supported Versions

See our website for versions of OpenSY that are currently supported with
security updates: https://opensyria.net/en/lifecycle/#schedule

## Reporting a Vulnerability

To report security issues send an email to security@opensyria.net (not for support).

**Please do not report security vulnerabilities through public GitHub issues.**

### What to Include

Your report should include:
- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact assessment
- Any suggested fixes (optional)

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Resolution Target**: Depends on severity

### Responsible Disclosure

We kindly ask that you:
- Give us reasonable time to address the issue before public disclosure
- Make a good faith effort to avoid privacy violations and data destruction
- Do not exploit the vulnerability beyond what is necessary to demonstrate it

## Security Contacts

The OpenSY security team can be reached at:

| Contact | Email |
|---------|-------|
| Security Team | security@opensyria.net |

<!-- TODO: Add GPG keys for encrypted communication once team keys are established -->

## Bug Bounty

We are currently establishing a bug bounty program. Details will be announced at
https://opensyria.net/security/ once available.

## Known Security Issues & Fixes

### SY-2024-001: RandomX Key Rotation Use-After-Free (Fixed)

**Severity**: High  
**Status**: Fixed in current development branch  
**CVE**: Pending

**Description**: A use-after-free vulnerability existed in the RandomX mining subsystem 
during key rotation events. Mining threads created VMs that held raw pointers to the 
dataset, which could be freed during key rotation (every 32 blocks on mainnet) while 
the VMs were still in use.

**Root Cause**: The `Initialize()` method called `Cleanup()` before allocating a new 
dataset, freeing the previous dataset while mining thread VMs might still reference it.

**Fix**: Implemented epoch-based VM invalidation mechanism:
- Added atomic `m_dataset_epoch` counter to `RandomXMiningContext`
- Epoch increments when dataset is freed during reinitialization
- Mining threads capture epoch at start and check periodically (every 1000 hashes)
- Stale VMs are detected and threads abort safely before accessing freed memory

**Verification**:
- 82 unit tests passing including 6 new epoch-based invalidation tests
- ASAN (AddressSanitizer) testing: No memory errors detected
- TSAN (ThreadSanitizer) testing: No data races detected
- Regtest validation: 1100+ blocks mined across multiple key rotation boundaries

## Acknowledgments

We appreciate the security research community's efforts in helping keep OpenSY safe.
Reporters who follow responsible disclosure guidelines will be credited (with permission)
in our security advisories.
