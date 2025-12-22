#!/usr/bin/env python3
# Copyright (c) 2025 The OpenSY developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

"""
OpenSY AssumeUTXO Snapshot Manager

This script manages AssumeUTXO snapshots for faster node synchronization.
It can:
1. Generate new UTXO snapshots at specified heights
2. Verify existing snapshots
3. Generate C++ code for chainparams.cpp updates
4. Publish snapshots to release artifacts

AssumeUTXO allows new nodes to sync in minutes instead of hours by loading
a pre-verified UTXO set snapshot.

Usage:
    # Generate snapshot at current height - 100 (for safety margin)
    python3 assumeutxo_manager.py generate --rpc-user user --rpc-password pass
    
    # Generate at specific height
    python3 assumeutxo_manager.py generate --height 50000 --rpc-user user --rpc-password pass
    
    # Verify existing snapshot
    python3 assumeutxo_manager.py verify --snapshot /path/to/utxo.dat --rpc-user user --rpc-password pass
    
    # Generate chainparams.cpp code
    python3 assumeutxo_manager.py codegen --snapshot /path/to/utxo.dat
"""

import argparse
import hashlib
import json
import logging
import os
import struct
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip3 install requests")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Snapshot magic bytes
SNAPSHOT_MAGIC = b'utxo\xff'


class RPCClient:
    """Simple JSON-RPC client for opensyd."""
    
    def __init__(self, host: str, port: int, user: str, password: str):
        self.url = f"http://{host}:{port}"
        self.auth = (user, password)
        self.headers = {"Content-Type": "application/json"}
    
    def call(self, method: str, params: list = None) -> Any:
        """Execute an RPC call."""
        payload = {
            "jsonrpc": "2.0",
            "id": "assumeutxo_manager",
            "method": method,
            "params": params or []
        }
        try:
            response = requests.post(
                self.url,
                json=payload,
                auth=self.auth,
                headers=self.headers,
                timeout=3600  # Long timeout for dumptxoutset
            )
            response.raise_for_status()
            result = response.json()
            if "error" in result and result["error"]:
                raise Exception(f"RPC error: {result['error']}")
            return result.get("result")
        except requests.exceptions.RequestException as e:
            raise Exception(f"RPC connection failed: {e}")


class AssumeUTXOManager:
    """Manages AssumeUTXO snapshots for OpenSY."""
    
    def __init__(self, rpc: RPCClient, output_dir: str = None):
        self.rpc = rpc
        self.output_dir = Path(output_dir) if output_dir else Path.cwd()
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def get_blockchain_info(self) -> Dict:
        """Get current blockchain info."""
        return self.rpc.call("getblockchaininfo")
    
    def get_block_hash(self, height: int) -> str:
        """Get block hash at height."""
        return self.rpc.call("getblockhash", [height])
    
    def get_block_header(self, blockhash: str) -> Dict:
        """Get block header."""
        return self.rpc.call("getblockheader", [blockhash])
    
    def get_chain_tx_stats(self, nblocks: int = None, blockhash: str = None) -> Dict:
        """Get chain transaction statistics."""
        params = []
        if nblocks:
            params.append(nblocks)
        if blockhash:
            if not nblocks:
                params.append(None)
            params.append(blockhash)
        return self.rpc.call("getchaintxstats", params if params else None)
    
    def dump_txoutset(self, path: str, height: int = None) -> Dict:
        """Generate UTXO set snapshot."""
        params = [path]
        if height:
            params.append("rollback")
            params.append({"rollback": height})
        return self.rpc.call("dumptxoutset", params)
    
    def generate_snapshot(self, height: int = None, safety_margin: int = 100) -> Dict:
        """Generate a new UTXO snapshot."""
        # Get current chain info
        info = self.get_blockchain_info()
        current_height = info["blocks"]
        
        # Determine target height
        if height is None:
            # Use current height minus safety margin (for reorg protection)
            height = current_height - safety_margin
            if height < 0:
                raise ValueError(f"Chain too short (height {current_height}) for safety margin {safety_margin}")
        
        if height > current_height:
            raise ValueError(f"Target height {height} exceeds current chain height {current_height}")
        
        # Round to nearest 10000 for clean snapshot heights
        rounded_height = (height // 10000) * 10000
        if rounded_height < 10000:
            rounded_height = height  # Use exact height for very short chains
        
        logger.info(f"Generating snapshot at height {rounded_height} (current: {current_height})")
        
        # Get block info at snapshot height
        blockhash = self.get_block_hash(rounded_height)
        header = self.get_block_header(blockhash)
        
        # Generate snapshot filename
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        filename = f"utxo-{rounded_height}-{timestamp}.dat"
        filepath = self.output_dir / filename
        
        logger.info(f"Dumping UTXO set to {filepath}...")
        logger.info("This may take several minutes for large chains...")
        
        start_time = time.time()
        result = self.dump_txoutset(str(filepath), rounded_height)
        elapsed = time.time() - start_time
        
        logger.info(f"Snapshot generated in {elapsed:.1f} seconds")
        
        # Calculate file hash
        file_hash = self._sha256_file(filepath)
        
        # Get transaction count
        tx_stats = self.get_chain_tx_stats(rounded_height, blockhash)
        tx_count = tx_stats.get("txcount", rounded_height + 1)
        
        snapshot_info = {
            "height": rounded_height,
            "blockhash": blockhash,
            "hash_serialized": result.get("hash_serialized_2", result.get("hash_serialized")),
            "coins_count": result.get("coins_count", 0),
            "txoutset_hash": result.get("txoutset_hash", ""),
            "chain_tx_count": tx_count,
            "file_path": str(filepath),
            "file_size": os.path.getsize(filepath),
            "file_sha256": file_hash,
            "block_time": header.get("time", 0),
            "generated_at": datetime.utcnow().isoformat(),
        }
        
        # Save metadata
        meta_path = filepath.with_suffix(".json")
        with open(meta_path, "w") as f:
            json.dump(snapshot_info, f, indent=2)
        
        logger.info(f"Snapshot info saved to {meta_path}")
        
        return snapshot_info
    
    def verify_snapshot(self, snapshot_path: str) -> Dict:
        """Verify a snapshot file."""
        path = Path(snapshot_path)
        if not path.exists():
            raise FileNotFoundError(f"Snapshot not found: {snapshot_path}")
        
        logger.info(f"Verifying snapshot: {snapshot_path}")
        
        # Read magic bytes
        with open(path, "rb") as f:
            magic = f.read(5)
            if magic != SNAPSHOT_MAGIC:
                raise ValueError(f"Invalid snapshot magic: {magic.hex()}")
            
            # Read version
            version = struct.unpack("<H", f.read(2))[0]
            logger.info(f"Snapshot version: {version}")
            
            # Read network magic
            network_magic = f.read(4)
            logger.info(f"Network magic: {network_magic.hex()}")
            
            # Read base blockhash
            blockhash = f.read(32)[::-1].hex()  # Reverse for display
            logger.info(f"Base blockhash: {blockhash}")
            
            # Read coins count
            coins_count = struct.unpack("<Q", f.read(8))[0]
            logger.info(f"Coins count: {coins_count:,}")
        
        # Calculate file hash
        file_hash = self._sha256_file(path)
        file_size = os.path.getsize(path)
        
        # Try to find corresponding metadata
        meta_path = path.with_suffix(".json")
        metadata = None
        if meta_path.exists():
            with open(meta_path) as f:
                metadata = json.load(f)
        
        result = {
            "valid_magic": True,
            "version": version,
            "network_magic": network_magic.hex(),
            "blockhash": blockhash,
            "coins_count": coins_count,
            "file_size": file_size,
            "file_sha256": file_hash,
            "metadata": metadata,
        }
        
        logger.info("✅ Snapshot format verified")
        return result
    
    def generate_chainparams_code(self, snapshot_info: Dict) -> str:
        """Generate C++ code for chainparams.cpp."""
        height = snapshot_info["height"]
        hash_serialized = snapshot_info["hash_serialized"]
        tx_count = snapshot_info["chain_tx_count"]
        blockhash = snapshot_info["blockhash"]
        block_time = snapshot_info.get("block_time", 0)
        
        code = f'''        // AssumeUTXO data - enables instant sync by loading a verified UTXO snapshot
        // Generated on {datetime.utcnow().strftime("%b %d, %Y")} at block {height}
        // Snapshot SHA256: {snapshot_info.get("file_sha256", "N/A")}
        // To generate: opensy-cli dumptxoutset /path/to/utxo-{height}.dat rollback '{{"rollback": {height}}}'
        m_assumeutxo_data = {{
            {{
                .height = {height},
                .hash_serialized = AssumeutxoHash{{uint256{{"{hash_serialized}"}}}},
                .m_chain_tx_count = {tx_count},
                .blockhash = uint256{{"{blockhash}"}},
            }},
        }};

        // Chain transaction data - for sync time estimation
        // Updated at block {height}
        chainTxData = ChainTxData{{
            .nTime    = {block_time}, // Block {height} timestamp
            .tx_count = {tx_count},
            .dTxRate  = 0.038, // Update based on actual tx rate
        }};'''
        
        return code
    
    def _sha256_file(self, filepath: Path) -> str:
        """Calculate SHA256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()


def cmd_generate(args):
    """Generate a new snapshot."""
    rpc = RPCClient(args.rpc_host, args.rpc_port, args.rpc_user, args.rpc_password)
    manager = AssumeUTXOManager(rpc, args.output_dir)
    
    try:
        info = manager.generate_snapshot(
            height=args.height,
            safety_margin=args.safety_margin
        )
        
        print("\n" + "=" * 60)
        print("SNAPSHOT GENERATED SUCCESSFULLY")
        print("=" * 60)
        print(f"Height:          {info['height']:,}")
        print(f"Block Hash:      {info['blockhash']}")
        print(f"Hash Serialized: {info['hash_serialized']}")
        print(f"Coins:           {info['coins_count']:,}")
        print(f"TX Count:        {info['chain_tx_count']:,}")
        print(f"File:            {info['file_path']}")
        print(f"Size:            {info['file_size'] / 1024 / 1024:.2f} MB")
        print(f"SHA256:          {info['file_sha256']}")
        print("=" * 60)
        
        # Generate chainparams code
        code = manager.generate_chainparams_code(info)
        print("\nC++ code for chainparams.cpp:")
        print("-" * 60)
        print(code)
        print("-" * 60)
        
        # Save code to file
        code_path = Path(info['file_path']).with_suffix(".cpp.txt")
        with open(code_path, "w") as f:
            f.write(code)
        print(f"\nCode saved to: {code_path}")
        
    except Exception as e:
        logger.error(f"Failed to generate snapshot: {e}")
        sys.exit(1)


def cmd_verify(args):
    """Verify an existing snapshot."""
    rpc = RPCClient(args.rpc_host, args.rpc_port, args.rpc_user, args.rpc_password) if args.rpc_user else None
    manager = AssumeUTXOManager(rpc)
    
    try:
        result = manager.verify_snapshot(args.snapshot)
        
        print("\n" + "=" * 60)
        print("SNAPSHOT VERIFICATION RESULT")
        print("=" * 60)
        print(f"Valid Magic:    {'✅ Yes' if result['valid_magic'] else '❌ No'}")
        print(f"Version:        {result['version']}")
        print(f"Network Magic:  {result['network_magic']}")
        print(f"Block Hash:     {result['blockhash']}")
        print(f"Coins Count:    {result['coins_count']:,}")
        print(f"File Size:      {result['file_size'] / 1024 / 1024:.2f} MB")
        print(f"SHA256:         {result['file_sha256']}")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        sys.exit(1)


def cmd_codegen(args):
    """Generate chainparams code from snapshot metadata."""
    meta_path = Path(args.snapshot)
    
    # Try to find metadata file
    if meta_path.suffix == ".dat":
        meta_path = meta_path.with_suffix(".json")
    
    if not meta_path.exists():
        logger.error(f"Metadata file not found: {meta_path}")
        logger.error("Run 'generate' first or provide the .json metadata file")
        sys.exit(1)
    
    with open(meta_path) as f:
        info = json.load(f)
    
    rpc = None
    manager = AssumeUTXOManager(rpc)
    code = manager.generate_chainparams_code(info)
    
    print(code)


def cmd_update_chainparams(args):
    """Update chainparams.cpp with new snapshot data."""
    # This is a helper that shows what to update
    rpc = RPCClient(args.rpc_host, args.rpc_port, args.rpc_user, args.rpc_password)
    manager = AssumeUTXOManager(rpc, args.output_dir)
    
    try:
        # Generate new snapshot
        info = manager.generate_snapshot(
            height=args.height,
            safety_margin=args.safety_margin
        )
        
        code = manager.generate_chainparams_code(info)
        
        print("\n" + "=" * 60)
        print("UPDATE INSTRUCTIONS")
        print("=" * 60)
        print("\n1. Replace the m_assumeutxo_data block in:")
        print("   src/kernel/chainparams.cpp (CMainParams section)")
        print("\n2. Code to insert:\n")
        print(code)
        print("\n3. Rebuild and test:")
        print("   cmake --build build")
        print("   ./build/bin/test_opensy --run_test=*assumeutxo*")
        print("\n4. Commit changes:")
        print(f"   git add src/kernel/chainparams.cpp")
        print(f"   git commit -m 'Update AssumeUTXO snapshot to height {info['height']}'")
        print("\n5. Publish snapshot file:")
        print(f"   - Upload {info['file_path']} to GitHub releases")
        print(f"   - SHA256: {info['file_sha256']}")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Failed: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="OpenSY AssumeUTXO Snapshot Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate snapshot at safe height (current - 100)
  python3 assumeutxo_manager.py generate --rpc-user user --rpc-password pass
  
  # Generate at specific height
  python3 assumeutxo_manager.py generate --height 50000 --rpc-user user --rpc-password pass
  
  # Verify snapshot
  python3 assumeutxo_manager.py verify --snapshot utxo-50000.dat
  
  # Generate C++ code from metadata
  python3 assumeutxo_manager.py codegen --snapshot utxo-50000.json
  
  # Full update workflow
  python3 assumeutxo_manager.py update --rpc-user user --rpc-password pass
"""
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate new UTXO snapshot")
    gen_parser.add_argument("--rpc-host", default="127.0.0.1", help="RPC host")
    gen_parser.add_argument("--rpc-port", type=int, default=9632, help="RPC port")
    gen_parser.add_argument("--rpc-user", required=True, help="RPC username")
    gen_parser.add_argument("--rpc-password", required=True, help="RPC password")
    gen_parser.add_argument("--height", type=int, help="Target height (default: current - safety_margin)")
    gen_parser.add_argument("--safety-margin", type=int, default=100, help="Blocks before tip (default: 100)")
    gen_parser.add_argument("--output-dir", default=".", help="Output directory")
    gen_parser.set_defaults(func=cmd_generate)
    
    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify existing snapshot")
    verify_parser.add_argument("--snapshot", required=True, help="Path to snapshot file")
    verify_parser.add_argument("--rpc-host", default="127.0.0.1", help="RPC host")
    verify_parser.add_argument("--rpc-port", type=int, default=9632, help="RPC port")
    verify_parser.add_argument("--rpc-user", help="RPC username (optional)")
    verify_parser.add_argument("--rpc-password", help="RPC password")
    verify_parser.set_defaults(func=cmd_verify)
    
    # Codegen command
    code_parser = subparsers.add_parser("codegen", help="Generate chainparams.cpp code")
    code_parser.add_argument("--snapshot", required=True, help="Path to snapshot .json metadata")
    code_parser.set_defaults(func=cmd_codegen)
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Generate snapshot and show update instructions")
    update_parser.add_argument("--rpc-host", default="127.0.0.1", help="RPC host")
    update_parser.add_argument("--rpc-port", type=int, default=9632, help="RPC port")
    update_parser.add_argument("--rpc-user", required=True, help="RPC username")
    update_parser.add_argument("--rpc-password", required=True, help="RPC password")
    update_parser.add_argument("--height", type=int, help="Target height")
    update_parser.add_argument("--safety-margin", type=int, default=100, help="Blocks before tip")
    update_parser.add_argument("--output-dir", default=".", help="Output directory")
    update_parser.set_defaults(func=cmd_update_chainparams)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()
