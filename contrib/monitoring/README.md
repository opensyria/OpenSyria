# OpenSY Monitoring Tools

Security and operational monitoring scripts for OpenSY node operators.

## Tools

### distribution_analyzer.py

Analyzes the UTXO set and mining distribution to monitor for centralization risks.
Part of security remediation M-05 (distribution analysis).

**Features:**
- UTXO set statistics
- Mining pool/address distribution analysis
- Gini coefficient calculation for decentralization measurement
- Top miner concentration tracking
- Risk assessment reporting

**Usage:**
```bash
python3 distribution_analyzer.py \
    --rpc-host 127.0.0.1 \
    --rpc-port 8332 \
    --rpc-user YOUR_USER \
    --rpc-password YOUR_PASSWORD \
    --blocks 1000
```

**Requirements:**
- Python 3.8+
- requests library (`pip3 install requests`)
- Running opensyd with RPC enabled

**Sample Output:**
```
============================================================
OPENSY DISTRIBUTION ANALYSIS REPORT
============================================================

📊 UTXO SET STATISTICS
----------------------------------------
  Block Height:    150,000
  Total UTXOs:     2,345,678
  Total Supply:    12,500,000.00000000 SYL

⛏️  MINING DISTRIBUTION
----------------------------------------
  Blocks Analyzed: 1,000
  Unique Miners:   45
  Total Rewards:   50,000.00 SYL

  Top 10 Miners:
     1. sy1qxyz123abc...: 120 blocks (12.0%)
     2. sy1qabc456def...: 95 blocks (9.5%)
     ...

  Top 10 Concentration: 65.2%
  Gini Coefficient:     0.5234
  Decentralization:     47.7%

📋 RISK ASSESSMENT
----------------------------------------
  ⚠️  Moderate mining concentration (Gini 0.4-0.6)
  ⚠️  Top 10 miners control 50-70% of blocks
```

---

### peer_monitor.py

Real-time monitoring of peer connections, misbehavior scores, and network health.
Displays live dashboard of connected peers with color-coded risk indicators.

**Features:**
- Real-time peer connection monitoring
- Misbehavior score tracking (integrated with M-04 graduated scoring)
- Client version distribution
- Latency monitoring
- New connection alerts
- Suspicious peer detection

**Usage:**
```bash
python3 peer_monitor.py \
    --rpc-host 127.0.0.1 \
    --rpc-port 8332 \
    --rpc-user YOUR_USER \
    --rpc-password YOUR_PASSWORD \
    --interval 5
```

**Requirements:**
- Python 3.8+
- requests library
- Terminal with ANSI color support

**Features Displayed:**
- Connection count (inbound/outbound)
- Client version distribution
- Per-peer: address, version, ping time, data transferred, ban score
- Color-coded scores: Green (<20), Yellow (20-50), Red (>50)
- Alerts for suspicious, high-latency, and new peers

---

## Security Context

These tools are part of the security remediation effort documented in 
[SECURITY_REMEDIATION_PLAN.md](../../SECURITY_REMEDIATION_PLAN.md).

Relevant findings:
- **M-04**: Graduated peer scoring (peer_monitor.py tracks scores)
- **M-05**: Distribution analysis (distribution_analyzer.py monitors concentration)

## Recommended Usage

1. **Daily Monitoring**: Run `distribution_analyzer.py` daily to track 
   centralization trends over time.

2. **Real-time Alerts**: Run `peer_monitor.py` on a dedicated terminal when
   troubleshooting network issues or during suspected attacks.

3. **Automated Checks**: Consider setting up cron jobs to run these analyses
   and alert on concerning metrics.

## Configuration

Both tools require RPC access to a running opensyd instance. Ensure your
`opensy.conf` has RPC enabled:

```conf
server=1
rpcuser=your_username
rpcpassword=your_secure_password
rpcallowip=127.0.0.1
```

For remote monitoring, configure appropriate firewall rules and consider
using SSH tunnels rather than exposing RPC directly.
