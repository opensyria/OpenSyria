#!/usr/bin/env python3
"""
OpenSY Peer Monitor

Real-time monitoring of peer connections and misbehavior scores.
Useful for detecting attacks and monitoring network health.

Usage:
    python3 peer_monitor.py [--rpc-host HOST] [--rpc-port PORT] [--interval SECONDS]

Requires: python3, requests
"""

import argparse
import json
import sys
import time
from datetime import datetime
from typing import Dict, List

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip3 install requests")
    sys.exit(1)


class PeerMonitor:
    def __init__(self, host: str, port: int, user: str, password: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.peer_history: Dict[str, List[Dict]] = {}
        
    def rpc_call(self, method: str, params: list = None) -> dict:
        """Make an RPC call to opensyd."""
        url = f"http://{self.host}:{self.port}/"
        headers = {"content-type": "application/json"}
        payload = {
            "jsonrpc": "2.0",
            "id": "monitor",
            "method": method,
            "params": params or []
        }
        
        try:
            response = requests.post(
                url,
                data=json.dumps(payload),
                headers=headers,
                auth=(self.user, self.password) if self.user else None,
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_peer_info(self) -> List[Dict]:
        """Get information about connected peers."""
        result = self.rpc_call("getpeerinfo")
        if "error" in result and result["error"]:
            print(f"Error getting peer info: {result['error']}")
            return []
        return result.get("result", [])
    
    def get_network_info(self) -> Dict:
        """Get network information."""
        result = self.rpc_call("getnetworkinfo")
        if "error" in result and result["error"]:
            return {}
        return result.get("result", {})
    
    def get_banned_peers(self) -> List[Dict]:
        """Get list of banned peers."""
        result = self.rpc_call("listbanned")
        if "error" in result and result["error"]:
            return []
        return result.get("result", [])
    
    def analyze_peers(self, peers: List[Dict]) -> Dict:
        """Analyze peer connections for anomalies."""
        analysis = {
            "total_peers": len(peers),
            "inbound": 0,
            "outbound": 0,
            "by_version": {},
            "by_services": {},
            "suspicious_peers": [],
            "high_latency_peers": [],
            "new_peers": []
        }
        
        now = time.time()
        
        for peer in peers:
            # Count direction
            if peer.get("inbound", False):
                analysis["inbound"] += 1
            else:
                analysis["outbound"] += 1
            
            # Track versions
            version = peer.get("subver", "unknown")
            analysis["by_version"][version] = analysis["by_version"].get(version, 0) + 1
            
            # Track services
            services = hex(peer.get("services", 0))
            analysis["by_services"][services] = analysis["by_services"].get(services, 0) + 1
            
            # Check for suspicious behavior
            peer_addr = peer.get("addr", "unknown")
            
            # High ban score
            if peer.get("banscore", 0) > 50:
                analysis["suspicious_peers"].append({
                    "addr": peer_addr,
                    "reason": f"High ban score: {peer.get('banscore', 0)}",
                    "score": peer.get("banscore", 0)
                })
            
            # High latency
            if peer.get("pingtime", 0) > 5.0:
                analysis["high_latency_peers"].append({
                    "addr": peer_addr,
                    "ping": peer.get("pingtime", 0)
                })
            
            # New connection (less than 5 minutes)
            conntime = peer.get("conntime", now)
            if now - conntime < 300:
                analysis["new_peers"].append({
                    "addr": peer_addr,
                    "connected_seconds_ago": int(now - conntime)
                })
        
        return analysis
    
    def print_status(self, peers: List[Dict], analysis: Dict, network_info: Dict):
        """Print current peer status."""
        # Clear screen for real-time updates
        print("\033[H\033[J", end="")
        
        print("=" * 70)
        print(f"OPENSY PEER MONITOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Network summary
        print(f"\n📡 NETWORK STATUS")
        print("-" * 50)
        print(f"  Version:     {network_info.get('subversion', 'N/A')}")
        print(f"  Connections: {analysis['total_peers']} ({analysis['inbound']} in / {analysis['outbound']} out)")
        print(f"  Warnings:    {network_info.get('warnings', 'None')}")
        
        # Version distribution
        print(f"\n📊 CLIENT VERSIONS")
        print("-" * 50)
        for version, count in sorted(analysis["by_version"].items(), key=lambda x: -x[1])[:5]:
            bar = "█" * min(count * 2, 30)
            print(f"  {version[:40]:40} {count:3} {bar}")
        
        # Peer table
        print(f"\n👥 CONNECTED PEERS (Top 20 by data)")
        print("-" * 70)
        print(f"  {'Address':30} {'Ver':8} {'Ping':6} {'Recv':>8} {'Sent':>8} {'Score':5}")
        print("-" * 70)
        
        # Sort by total bytes transferred
        sorted_peers = sorted(
            peers, 
            key=lambda p: p.get("bytesrecv", 0) + p.get("bytessent", 0),
            reverse=True
        )[:20]
        
        for peer in sorted_peers:
            addr = peer.get("addr", "?")[:30]
            version = peer.get("subver", "?")[:8]
            ping = peer.get("pingtime", 0)
            recv = peer.get("bytesrecv", 0) / 1024 / 1024  # MB
            sent = peer.get("bytessent", 0) / 1024 / 1024  # MB
            score = peer.get("banscore", 0)
            
            # Color code by score
            if score > 50:
                color = "\033[91m"  # Red
            elif score > 20:
                color = "\033[93m"  # Yellow
            else:
                color = "\033[92m"  # Green
            
            print(f"  {addr:30} {version:8} {ping:5.1f}s {recv:7.1f}M {sent:7.1f}M {color}{score:5}\033[0m")
        
        # Alerts
        if analysis["suspicious_peers"]:
            print(f"\n⚠️  SUSPICIOUS PEERS")
            print("-" * 50)
            for peer in analysis["suspicious_peers"][:5]:
                print(f"  \033[91m{peer['addr']}: {peer['reason']}\033[0m")
        
        if analysis["high_latency_peers"]:
            print(f"\n🐢 HIGH LATENCY PEERS")
            print("-" * 50)
            for peer in analysis["high_latency_peers"][:5]:
                print(f"  {peer['addr']}: {peer['ping']:.1f}s")
        
        # Recent connections
        if analysis["new_peers"]:
            print(f"\n🆕 NEW CONNECTIONS (last 5 min)")
            print("-" * 50)
            for peer in analysis["new_peers"][:10]:
                print(f"  {peer['addr']} ({peer['connected_seconds_ago']}s ago)")
        
        print("\n" + "-" * 70)
        print("Press Ctrl+C to exit")
    
    def run(self, interval: int = 5):
        """Run the monitor loop."""
        print("Starting peer monitor...")
        
        try:
            while True:
                peers = self.get_peer_info()
                network_info = self.get_network_info()
                analysis = self.analyze_peers(peers)
                
                self.print_status(peers, analysis, network_info)
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\nMonitor stopped.")


def main():
    parser = argparse.ArgumentParser(description="OpenSY Peer Monitor")
    parser.add_argument("--rpc-host", default="127.0.0.1", help="RPC host")
    parser.add_argument("--rpc-port", type=int, default=8332, help="RPC port")
    parser.add_argument("--rpc-user", default="", help="RPC username")
    parser.add_argument("--rpc-password", default="", help="RPC password")
    parser.add_argument("--interval", type=int, default=5, help="Refresh interval in seconds")
    args = parser.parse_args()
    
    monitor = PeerMonitor(args.rpc_host, args.rpc_port, args.rpc_user, args.rpc_password)
    monitor.run(args.interval)


if __name__ == "__main__":
    main()
