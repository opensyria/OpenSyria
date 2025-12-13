#!/usr/bin/env python3
"""
OpenSyria Distribution Analyzer

Analyzes the UTXO set distribution to track wealth concentration
and mining pool diversity. Part of security monitoring for M-05.

Usage:
    python3 distribution_analyzer.py [--rpc-host HOST] [--rpc-port PORT]

Requires: python3, requests
"""

import argparse
import json
import sys
from collections import defaultdict
from typing import Dict, List, Tuple
import math

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip3 install requests")
    sys.exit(1)


def rpc_call(method: str, params: list = None, host: str = "127.0.0.1", 
             port: int = 8332, user: str = "", password: str = "") -> dict:
    """Make an RPC call to opensyriad."""
    url = f"http://{host}:{port}/"
    headers = {"content-type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": "analyzer",
        "method": method,
        "params": params or []
    }
    
    try:
        response = requests.post(
            url,
            data=json.dumps(payload),
            headers=headers,
            auth=(user, password) if user else None,
            timeout=300
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def calculate_gini_coefficient(values: List[float]) -> float:
    """
    Calculate the Gini coefficient for wealth distribution.
    0 = perfect equality, 1 = perfect inequality
    """
    if not values or len(values) == 0:
        return 0.0
    
    sorted_values = sorted(values)
    n = len(sorted_values)
    
    if n == 1:
        return 0.0
    
    cumulative = 0
    for i, value in enumerate(sorted_values):
        cumulative += (2 * (i + 1) - n - 1) * value
    
    mean = sum(sorted_values) / n
    if mean == 0:
        return 0.0
    
    return cumulative / (n * n * mean)


def analyze_utxo_distribution(host: str, port: int, user: str, password: str) -> Dict:
    """Analyze UTXO set distribution."""
    print("Fetching UTXO set statistics...")
    
    # Get blockchain info
    info = rpc_call("getblockchaininfo", host=host, port=port, user=user, password=password)
    if "error" in info and info["error"]:
        return {"error": f"Failed to get blockchain info: {info['error']}"}
    
    result = info.get("result", {})
    height = result.get("blocks", 0)
    
    # Get UTXO stats
    utxo_stats = rpc_call("gettxoutsetinfo", ["muhash"], host=host, port=port, 
                          user=user, password=password)
    if "error" in utxo_stats and utxo_stats["error"]:
        return {"error": f"Failed to get UTXO stats: {utxo_stats['error']}"}
    
    utxo_result = utxo_stats.get("result", {})
    
    return {
        "height": height,
        "total_utxos": utxo_result.get("txouts", 0),
        "total_amount": utxo_result.get("total_amount", 0),
        "hash_serialized": utxo_result.get("hash_serialized_3", ""),
    }


def analyze_block_rewards(host: str, port: int, user: str, password: str, 
                          num_blocks: int = 1000) -> Dict:
    """Analyze recent block reward distribution among miners."""
    print(f"Analyzing last {num_blocks} blocks for mining distribution...")
    
    # Get current height
    info = rpc_call("getblockchaininfo", host=host, port=port, user=user, password=password)
    if "error" in info and info["error"]:
        return {"error": f"Failed to get blockchain info: {info['error']}"}
    
    height = info.get("result", {}).get("blocks", 0)
    
    # Track miner addresses
    miner_blocks: Dict[str, int] = defaultdict(int)
    miner_rewards: Dict[str, float] = defaultdict(float)
    
    for h in range(max(1, height - num_blocks + 1), height + 1):
        block_hash = rpc_call("getblockhash", [h], host=host, port=port, 
                             user=user, password=password)
        if "error" in block_hash and block_hash["error"]:
            continue
        
        block = rpc_call("getblock", [block_hash.get("result", ""), 2], 
                        host=host, port=port, user=user, password=password)
        if "error" in block and block["error"]:
            continue
        
        block_data = block.get("result", {})
        if not block_data.get("tx"):
            continue
        
        # Coinbase transaction is first
        coinbase = block_data["tx"][0]
        if coinbase.get("vout"):
            for vout in coinbase["vout"]:
                address = None
                if vout.get("scriptPubKey", {}).get("address"):
                    address = vout["scriptPubKey"]["address"]
                elif vout.get("scriptPubKey", {}).get("addresses"):
                    address = vout["scriptPubKey"]["addresses"][0]
                
                if address:
                    miner_blocks[address] += 1
                    miner_rewards[address] += vout.get("value", 0)
                    break  # Only count primary output
        
        # Progress indicator
        if (height - h) % 100 == 0:
            print(f"  Processed block {h}/{height}")
    
    # Calculate statistics
    total_blocks = sum(miner_blocks.values())
    total_rewards = sum(miner_rewards.values())
    
    # Sort by blocks mined
    sorted_miners = sorted(miner_blocks.items(), key=lambda x: x[1], reverse=True)
    
    # Top miners
    top_10 = sorted_miners[:10]
    top_10_blocks = sum(blocks for _, blocks in top_10)
    
    # Gini coefficient for mining concentration
    if miner_blocks:
        gini = calculate_gini_coefficient(list(miner_blocks.values()))
    else:
        gini = 0.0
    
    return {
        "blocks_analyzed": total_blocks,
        "unique_miners": len(miner_blocks),
        "total_rewards": total_rewards,
        "top_10_miners": [
            {
                "address": addr[:16] + "..." if len(addr) > 16 else addr,
                "blocks": blocks,
                "percentage": (blocks / total_blocks * 100) if total_blocks > 0 else 0
            }
            for addr, blocks in top_10
        ],
        "top_10_concentration": (top_10_blocks / total_blocks * 100) if total_blocks > 0 else 0,
        "gini_coefficient": gini,
        "decentralization_score": (1 - gini) * 100  # 100 = perfectly decentralized
    }


def print_report(utxo_analysis: Dict, mining_analysis: Dict):
    """Print formatted analysis report."""
    print("\n" + "=" * 60)
    print("OPENSYRIA DISTRIBUTION ANALYSIS REPORT")
    print("=" * 60)
    
    if "error" in utxo_analysis:
        print(f"\nUTXO Analysis Error: {utxo_analysis['error']}")
    else:
        print("\n📊 UTXO SET STATISTICS")
        print("-" * 40)
        print(f"  Block Height:    {utxo_analysis.get('height', 'N/A'):,}")
        print(f"  Total UTXOs:     {utxo_analysis.get('total_utxos', 'N/A'):,}")
        print(f"  Total Supply:    {utxo_analysis.get('total_amount', 'N/A'):,.8f} SYL")
    
    if "error" in mining_analysis:
        print(f"\nMining Analysis Error: {mining_analysis['error']}")
    else:
        print("\n⛏️  MINING DISTRIBUTION")
        print("-" * 40)
        print(f"  Blocks Analyzed: {mining_analysis.get('blocks_analyzed', 'N/A'):,}")
        print(f"  Unique Miners:   {mining_analysis.get('unique_miners', 'N/A')}")
        print(f"  Total Rewards:   {mining_analysis.get('total_rewards', 'N/A'):,.2f} SYL")
        
        print("\n  Top 10 Miners:")
        for i, miner in enumerate(mining_analysis.get("top_10_miners", []), 1):
            print(f"    {i:2}. {miner['address']}: {miner['blocks']:,} blocks ({miner['percentage']:.1f}%)")
        
        print(f"\n  Top 10 Concentration: {mining_analysis.get('top_10_concentration', 0):.1f}%")
        print(f"  Gini Coefficient:     {mining_analysis.get('gini_coefficient', 0):.4f}")
        print(f"  Decentralization:     {mining_analysis.get('decentralization_score', 0):.1f}%")
        
        # Risk assessment
        gini = mining_analysis.get("gini_coefficient", 0)
        top10 = mining_analysis.get("top_10_concentration", 0)
        
        print("\n📋 RISK ASSESSMENT")
        print("-" * 40)
        
        if gini < 0.4:
            print("  ✅ Mining distribution is healthy (Gini < 0.4)")
        elif gini < 0.6:
            print("  ⚠️  Moderate mining concentration (Gini 0.4-0.6)")
        else:
            print("  ❌ High mining concentration risk (Gini > 0.6)")
        
        if top10 < 50:
            print("  ✅ Top 10 miners control < 50% of blocks")
        elif top10 < 70:
            print("  ⚠️  Top 10 miners control 50-70% of blocks")
        else:
            print("  ❌ Top 10 miners control > 70% of blocks - centralization risk")
    
    print("\n" + "=" * 60)
    print("Report generated for security monitoring (M-05)")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="OpenSyria Distribution Analyzer")
    parser.add_argument("--rpc-host", default="127.0.0.1", help="RPC host")
    parser.add_argument("--rpc-port", type=int, default=8332, help="RPC port")
    parser.add_argument("--rpc-user", default="", help="RPC username")
    parser.add_argument("--rpc-password", default="", help="RPC password")
    parser.add_argument("--blocks", type=int, default=1000, help="Number of blocks to analyze")
    args = parser.parse_args()
    
    print("OpenSyria Distribution Analyzer v1.0")
    print("Part of Security Remediation M-05\n")
    
    utxo_analysis = analyze_utxo_distribution(
        args.rpc_host, args.rpc_port, args.rpc_user, args.rpc_password
    )
    
    mining_analysis = analyze_block_rewards(
        args.rpc_host, args.rpc_port, args.rpc_user, args.rpc_password, args.blocks
    )
    
    print_report(utxo_analysis, mining_analysis)


if __name__ == "__main__":
    main()
