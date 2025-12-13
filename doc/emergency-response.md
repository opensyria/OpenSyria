# OpenSyria Emergency Response Procedures

**Version:** 1.0  
**Date:** December 2025  
**Classification:** Operational Security

---

## Overview

This document outlines procedures for responding to security incidents, network attacks, and critical software issues affecting the OpenSyria network. All node operators and core developers should be familiar with these procedures.

---

## Contact Information

### Security Team

- **Primary Contact:** security@opensyria.org
- **PGP Key ID:** [Published on opensyria.org/security]
- **Response Time SLA:** 24 hours for critical issues

### Communication Channels

- **Private Disclosure:** security@opensyria.org (encrypted)
- **Developer Coordination:** Private IRC/Matrix channel (invite-only)
- **Public Announcements:** opensyria.org/announcements

---

## Incident Classification

### Severity Levels

| Level | Description | Response Time | Examples |
|-------|-------------|---------------|----------|
| **P0 - Critical** | Active exploitation, network at risk | Immediate | Consensus bug, active 51% attack |
| **P1 - High** | Severe vulnerability, no active exploitation | < 24 hours | Memory exhaustion DoS, key leak |
| **P2 - Medium** | Moderate risk, workaround available | < 72 hours | Peer banning bypass, sync issues |
| **P3 - Low** | Minor issues, informational | < 7 days | UI bugs, documentation errors |

---

## Emergency Procedures

### 1. Consensus Bug / Chain Split

**Symptoms:**
- Multiple chain tips reported by different nodes
- Block validation failures in logs
- Conflicting transactions confirmed on different chains

**Immediate Actions:**
1. **Verify:** Confirm chain split using multiple independent nodes
2. **Alert:** Notify security team and major mining pools immediately
3. **Assess:** Determine root cause (bug vs attack)
4. **Communicate:** Issue preliminary advisory via all channels

**Recovery Options:**
- **Option A (Reorganization):** If split is recent (<10 blocks), coordinate miners to orphan minority chain
- **Option B (Emergency Release):** Deploy hotfix with consensus fix
- **Option C (Rollback):** In extreme cases, coordinate manual rollback to last known-good block

**Post-Incident:**
- Full root cause analysis
- Release detailed post-mortem within 7 days
- Update test suites to prevent regression

---

### 2. 51% Attack / Double Spend

**Symptoms:**
- Large reorganizations (>6 blocks)
- Sudden hashrate spike from unknown source
- Exchange reports of double-spent deposits

**Immediate Actions:**
1. **Monitor:** Track attack depth and miner identities
2. **Alert:** Notify exchanges to increase confirmation requirements
3. **Coordinate:** Contact affected exchanges directly
4. **Document:** Record all attack blocks for analysis

**Mitigations:**
- Increase exchange confirmation requirements (recommend 100+ blocks during attack)
- Coordinate with honest miners to out-compete attacker
- Consider temporary trading halt if attack is severe

**Recovery:**
- Document financial losses
- Coordinate with law enforcement if applicable
- Review network security assumptions

---

### 3. Memory Exhaustion / DoS Attack

**Symptoms:**
- Nodes crashing with OOM errors
- Excessive memory consumption in logs
- Network-wide sync issues

**Immediate Actions:**
1. **Identify:** Determine attack vector (headers, peers, transactions)
2. **Mitigate:** Apply rate limiting (may require restart with new flags)
3. **Deploy:** If hotfix available, coordinate emergency release

**Command-Line Mitigations:**
```bash
# Reduce memory usage
opensyriad -maxconnections=8 -maxmempool=100 -dbcache=100

# Disconnect misbehaving peers (via RPC)
opensyria-cli disconnectnode "<ip:port>"

# Ban attacking IP
opensyria-cli setban "<ip>" "add" 86400
```

---

### 4. Private Key Leak / Wallet Compromise

**Symptoms:**
- Unauthorized transactions from known addresses
- Developer key used to sign malicious software
- Stolen funds from official addresses

**Immediate Actions:**
1. **Verify:** Confirm compromise is real (not user error)
2. **Contain:** Move remaining funds to secure addresses immediately
3. **Revoke:** Revoke compromised keys (PGP, code signing)
4. **Alert:** Issue security advisory with affected key fingerprints

**User Guidance:**
- If release signing key is compromised, instruct users to NOT upgrade
- Provide new key fingerprints via out-of-band channels (social media verification)

---

### 5. RandomX-Specific Issues

**Key Rotation Failure:**
If RandomX key rotation fails or produces invalid keys:
1. Check logs for `RandomX: Failed to acquire context`
2. Verify RandomX pool is not exhausted (`getmemoryinfo` RPC)
3. Increase pool size: `-randomxpoolsize=16`

**Hash Rate Anomalies:**
If block times deviate significantly (>2x or <0.5x target):
1. Monitor difficulty adjustment progress
2. Check for mining pool concentration
3. Prepare communication for users about expected timeline

---

## Communication Templates

### Security Advisory Template

```
OpenSyria Security Advisory [OSA-YYYY-XXX]

Title: [Brief Description]
Severity: [Critical/High/Medium/Low]
CVE: [If assigned]
Affected Versions: [List]
Fixed Versions: [List]

Summary:
[1-2 sentence description of the issue]

Impact:
[Description of potential harm]

Mitigation:
[Steps to protect before upgrade]

Resolution:
[Steps to fix, usually "upgrade to version X.Y.Z"]

Timeline:
- [Date]: Issue reported
- [Date]: Fix developed
- [Date]: Advisory published
- [Date]: Public disclosure

Credits:
[Acknowledge reporter if they wish]

References:
- [Links to patches, discussion]
```

---

## Escalation Matrix

| Situation | First Response | Escalation | Final Authority |
|-----------|---------------|------------|-----------------|
| Bug report | Security team | Lead developer | Consensus call |
| Active attack | All developers | Mining pools | Emergency release |
| Code compromise | Security team | All maintainers | New signing key ceremony |
| Infrastructure outage | Ops team | Core developers | Infra leads |

---

## Post-Incident Checklist

After any P0 or P1 incident:

- [ ] Immediate threat neutralized
- [ ] All affected parties notified
- [ ] Incident timeline documented
- [ ] Root cause identified
- [ ] Fix deployed and verified
- [ ] Public communication published
- [ ] Post-mortem scheduled (within 7 days)
- [ ] Lessons learned incorporated into procedures
- [ ] Test cases added to prevent regression
- [ ] Security documentation updated

---

## Regular Security Exercises

To ensure readiness, conduct quarterly exercises:

1. **Tabletop Exercise:** Walk through hypothetical attack scenarios
2. **Communication Test:** Verify all contact channels are functional
3. **Key Ceremony Review:** Ensure signing keys are accessible and secure
4. **Backup Verification:** Confirm critical backups are restorable

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | December 2025 | Security Team | Initial version |

---

*This document should be reviewed and updated quarterly.*
