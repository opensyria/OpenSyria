# OpenSyria DNS Seeder

This document describes how to set up and run a DNS seeder for the OpenSyria network.

## Overview

The DNS seeder crawls the OpenSyria network for active nodes and serves their IP addresses via DNS. When a new OpenSyria node starts, it queries `seed.opensyria.net` to discover peers to connect to.

## Prerequisites

- Ubuntu 22.04+ server with public IP
- Port 53 (UDP) open in firewall
- Domain with DNS control (for NS records)

## Building the Seeder

The OpenSyria seeder is a fork of bitcoin-seeder, available at:
https://github.com/opensyria/opensyria-seeder

```bash
# Clone and build
git clone https://github.com/opensyria/opensyria-seeder.git
cd opensyria-seeder
make

# Install
sudo mkdir -p /opt/opensyria-seeder
sudo cp dnsseed /opt/opensyria-seeder/
```

## DNS Configuration

You need to set up DNS records to delegate `seed.yourdomain.net` to your seeder server.

### Required DNS Records

| Type | Name | Value |
|------|------|-------|
| NS | seed | ns1.yourdomain.net |
| A | ns1 | YOUR_SERVER_IP |

Example for opensyria.net (in Cloudflare):
- NS record: `seed` → `ns1.opensyria.net`
- A record: `ns1` → `157.175.40.131`

## IPv4/IPv6 Bridge Setup

The seeder uses IPv6 sockets internally. On servers with IPv4-only routing (like AWS EC2), you need `socat` to bridge IPv4 traffic to the IPv6 socket.

```bash
# Install socat
sudo apt-get install -y socat
```

## Systemd Services

### Seeder Service

Create `/etc/systemd/system/opensyria-seeder.service`:

```ini
[Unit]
Description=OpenSyria DNS Seeder
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/opensyria-seeder
ExecStart=/opt/opensyria-seeder/dnsseed -h seed.opensyria.net -n ns1.opensyria.net -m admin@opensyria.net -p 5353 -s 157.175.40.131
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Socat Bridge Service

Create `/etc/systemd/system/opensyria-socat.service`:

```ini
[Unit]
Description=OpenSyria DNS Socat Bridge (IPv4 to IPv6)
After=network.target opensyria-seeder.service
Requires=opensyria-seeder.service

[Service]
Type=simple
User=root
ExecStart=/usr/bin/socat UDP4-LISTEN:53,fork,reuseaddr UDP6:[::1]:5353
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Enable and Start Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable opensyria-seeder opensyria-socat
sudo systemctl start opensyria-seeder
sudo systemctl start opensyria-socat
```

## Firewall Configuration

### iptables
```bash
sudo iptables -A INPUT -p udp --dport 53 -j ACCEPT
```

### AWS Security Group
Add inbound rule:
- Type: Custom UDP
- Port: 53
- Source: 0.0.0.0/0

## Seeder Options

```
Usage: ./dnsseed -h <host> -n <ns> [-m <mbox>] [-t <threads>] [-p <port>]

Options:
-s <seed>       Seed node to collect peers from (replaces default)
-h <host>       Hostname of the DNS seed (e.g., seed.opensyria.net)
-n <ns>         Hostname of the nameserver (e.g., ns1.opensyria.net)
-m <mbox>       E-Mail address reported in SOA records
-t <threads>    Number of crawlers to run in parallel (default 96)
-d <threads>    Number of DNS server threads (default 4)
-a <address>    Address to listen on (default ::)
-p <port>       UDP port to listen on (default 53)
--p2port <port> P2P port to connect to (default: 9633)
--magic <hex>   Magic string/network prefix (default: 0x53594c4d)
--wipeban       Wipe list of banned nodes
--wipeignore    Wipe list of ignored nodes
```

## Testing

```bash
# Direct query to seeder
dig @YOUR_SERVER_IP seed.opensyria.net A +short

# Query via public DNS (after propagation)
dig @8.8.8.8 seed.opensyria.net A +short

# Check service status
sudo systemctl status opensyria-seeder opensyria-socat
```

## Monitoring

Check seeder statistics:
```bash
journalctl -u opensyria-seeder -f
```

Output shows: available nodes, tried nodes, banned nodes, DNS requests.

## Current Infrastructure

| Service | Host | Details |
|---------|------|---------|
| DNS Seed | seed.opensyria.net | Primary seeder |
| Nameserver | ns1.opensyria.net | 157.175.40.131 |

## Troubleshooting

### No DNS responses
1. Check if seeder is running: `systemctl status opensyria-seeder`
2. Check if socat is running: `systemctl status opensyria-socat`
3. Test locally: `dig @127.0.0.1 -p 5353 seed.opensyria.net A +short`
4. Check firewall: `sudo iptables -L -n | grep 53`

### Seeder shows 0 available nodes
1. Ensure at least one OpenSyria node is running and reachable
2. Use `-s IP_ADDRESS` to specify a known good seed node
3. Use `--wipeban` to clear banned node list
