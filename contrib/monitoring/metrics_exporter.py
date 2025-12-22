#!/usr/bin/env python3
"""
OpenSY Node Metrics Exporter for Prometheus

Exposes OpenSY node metrics in Prometheus format.
Run alongside your OpenSY node to enable monitoring.

Usage:
    python metrics_exporter.py [--port 9100] [--rpc-url http://127.0.0.1:9632]

Metrics exported:
    - opensy_block_height: Current block height
    - opensy_difficulty: Current mining difficulty
    - opensy_network_hashrate: Estimated network hashrate
    - opensy_peer_count: Number of connected peers
    - opensy_mempool_size: Transactions in mempool
    - opensy_mempool_bytes: Mempool size in bytes
    - opensy_node_uptime: Node uptime in seconds
    - opensy_chain_work: Total chain work (log scale)
    - opensy_verification_progress: Sync progress (0-1)
"""

import argparse
import json
import logging
import os
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import urllib.request
import base64

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OpenSYMetrics:
    """Collects metrics from OpenSY node via RPC."""
    
    def __init__(self, rpc_url: str, rpc_user: str = None, rpc_password: str = None):
        self.rpc_url = rpc_url
        self.rpc_user = rpc_user
        self.rpc_password = rpc_password
        self.node_start_time = time.time()
        
        # Try to load cookie auth if no credentials provided
        if not rpc_password:
            self._load_cookie_auth()
    
    def _load_cookie_auth(self):
        """Load RPC credentials from cookie file."""
        cookie_paths = [
            Path.home() / '.opensy' / '.cookie',
            Path.home() / 'Library' / 'Application Support' / 'OpenSY' / '.cookie',
            Path('/var/lib/opensy/.cookie'),
        ]
        
        for cookie_path in cookie_paths:
            if cookie_path.exists():
                try:
                    content = cookie_path.read_text().strip()
                    if ':' in content:
                        self.rpc_user, self.rpc_password = content.split(':', 1)
                        logger.info(f"Loaded cookie auth from {cookie_path}")
                        return
                except Exception as e:
                    logger.warning(f"Failed to read cookie: {e}")
    
    def _rpc_call(self, method: str, params: list = None) -> dict:
        """Make RPC call to OpenSY node."""
        if params is None:
            params = []
        
        payload = json.dumps({
            "jsonrpc": "1.0",
            "id": "metrics",
            "method": method,
            "params": params
        }).encode('utf-8')
        
        request = urllib.request.Request(
            self.rpc_url,
            data=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if self.rpc_user and self.rpc_password:
            credentials = f"{self.rpc_user}:{self.rpc_password}"
            auth = base64.b64encode(credentials.encode()).decode()
            request.add_header('Authorization', f'Basic {auth}')
        
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode())
                if data.get('error'):
                    logger.error(f"RPC error: {data['error']}")
                    return None
                return data.get('result')
        except Exception as e:
            logger.error(f"RPC call failed: {e}")
            return None
    
    def collect(self) -> dict:
        """Collect all metrics from node."""
        metrics = {}
        
        # Blockchain info
        blockchain_info = self._rpc_call('getblockchaininfo')
        if blockchain_info:
            metrics['opensy_block_height'] = {
                'value': blockchain_info.get('blocks', 0),
                'type': 'gauge',
                'help': 'Current block height'
            }
            metrics['opensy_headers'] = {
                'value': blockchain_info.get('headers', 0),
                'type': 'gauge',
                'help': 'Number of validated headers'
            }
            metrics['opensy_difficulty'] = {
                'value': blockchain_info.get('difficulty', 0),
                'type': 'gauge',
                'help': 'Current mining difficulty'
            }
            metrics['opensy_verification_progress'] = {
                'value': blockchain_info.get('verificationprogress', 0),
                'type': 'gauge',
                'help': 'Blockchain verification progress (0-1)'
            }
            metrics['opensy_pruned'] = {
                'value': 1 if blockchain_info.get('pruned', False) else 0,
                'type': 'gauge',
                'help': 'Whether the node is pruned'
            }
            
            # Chain work as log2 (the raw value is too large)
            chainwork = blockchain_info.get('chainwork', '0')
            if chainwork:
                try:
                    work_int = int(chainwork, 16)
                    if work_int > 0:
                        import math
                        metrics['opensy_chain_work_log2'] = {
                            'value': math.log2(work_int),
                            'type': 'gauge',
                            'help': 'Total chain work (log2 scale)'
                        }
                except:
                    pass
        
        # Mining info
        mining_info = self._rpc_call('getmininginfo')
        if mining_info:
            metrics['opensy_network_hashrate'] = {
                'value': mining_info.get('networkhashps', 0),
                'type': 'gauge',
                'help': 'Estimated network hashrate (H/s)'
            }
            metrics['opensy_pooled_tx'] = {
                'value': mining_info.get('pooledtx', 0),
                'type': 'gauge',
                'help': 'Number of transactions in mempool'
            }
        
        # Network info
        network_info = self._rpc_call('getnetworkinfo')
        if network_info:
            metrics['opensy_version'] = {
                'value': network_info.get('version', 0),
                'type': 'gauge',
                'help': 'Node version number'
            }
            metrics['opensy_connections'] = {
                'value': network_info.get('connections', 0),
                'type': 'gauge',
                'help': 'Total peer connections'
            }
            metrics['opensy_connections_in'] = {
                'value': network_info.get('connections_in', 0),
                'type': 'gauge',
                'help': 'Inbound peer connections'
            }
            metrics['opensy_connections_out'] = {
                'value': network_info.get('connections_out', 0),
                'type': 'gauge',
                'help': 'Outbound peer connections'
            }
            metrics['opensy_network_active'] = {
                'value': 1 if network_info.get('networkactive', False) else 0,
                'type': 'gauge',
                'help': 'Whether P2P networking is enabled'
            }
        
        # Mempool info
        mempool_info = self._rpc_call('getmempoolinfo')
        if mempool_info:
            metrics['opensy_mempool_size'] = {
                'value': mempool_info.get('size', 0),
                'type': 'gauge',
                'help': 'Number of transactions in mempool'
            }
            metrics['opensy_mempool_bytes'] = {
                'value': mempool_info.get('bytes', 0),
                'type': 'gauge',
                'help': 'Mempool size in bytes'
            }
            metrics['opensy_mempool_usage'] = {
                'value': mempool_info.get('usage', 0),
                'type': 'gauge',
                'help': 'Total memory usage for mempool'
            }
            metrics['opensy_mempool_max'] = {
                'value': mempool_info.get('maxmempool', 0),
                'type': 'gauge',
                'help': 'Maximum mempool size in bytes'
            }
            metrics['opensy_mempool_minfee'] = {
                'value': float(mempool_info.get('mempoolminfee', 0)),
                'type': 'gauge',
                'help': 'Minimum fee rate to enter mempool (SYL/kvB)'
            }
        
        # Uptime
        uptime = self._rpc_call('uptime')
        if uptime is not None:
            metrics['opensy_uptime_seconds'] = {
                'value': uptime,
                'type': 'counter',
                'help': 'Node uptime in seconds'
            }
        
        # TX output set info (UTXO stats)
        txoutset_info = self._rpc_call('gettxoutsetinfo', ['none'])
        if txoutset_info:
            metrics['opensy_txout_count'] = {
                'value': txoutset_info.get('txouts', 0),
                'type': 'gauge',
                'help': 'Number of unspent transaction outputs'
            }
            metrics['opensy_total_supply'] = {
                'value': float(txoutset_info.get('total_amount', 0)),
                'type': 'gauge',
                'help': 'Total SYL in circulation'
            }
            metrics['opensy_utxo_disk_size'] = {
                'value': txoutset_info.get('disk_size', 0),
                'type': 'gauge',
                'help': 'UTXO set disk size in bytes'
            }
        
        # Add collection timestamp
        metrics['opensy_last_scrape'] = {
            'value': time.time(),
            'type': 'gauge',
            'help': 'Timestamp of last successful metric collection'
        }
        
        return metrics
    
    def format_prometheus(self, metrics: dict) -> str:
        """Format metrics in Prometheus exposition format."""
        lines = []
        
        for name, data in metrics.items():
            # Add HELP line
            lines.append(f"# HELP {name} {data['help']}")
            # Add TYPE line
            lines.append(f"# TYPE {name} {data['type']}")
            # Add metric value
            lines.append(f"{name} {data['value']}")
        
        return '\n'.join(lines) + '\n'


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Prometheus metrics endpoint."""
    
    metrics_collector = None
    
    def do_GET(self):
        if self.path == '/metrics':
            try:
                metrics = self.metrics_collector.collect()
                output = self.metrics_collector.format_prometheus(metrics)
                
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.send_header('Content-Length', len(output))
                self.end_headers()
                self.wfile.write(output.encode('utf-8'))
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
                self.send_error(500, str(e))
        
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        
        else:
            # Landing page
            html = """<!DOCTYPE html>
<html>
<head><title>OpenSY Metrics Exporter</title></head>
<body>
<h1>OpenSY Metrics Exporter</h1>
<p><a href="/metrics">Metrics</a></p>
<p><a href="/health">Health</a></p>
</body>
</html>"""
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Suppress default logging, use our logger."""
        logger.debug(f"{self.address_string()} - {format % args}")


def main():
    parser = argparse.ArgumentParser(description='OpenSY Prometheus Metrics Exporter')
    parser.add_argument('--port', type=int, default=9100, help='Port to serve metrics on')
    parser.add_argument('--rpc-url', default='http://127.0.0.1:9632', help='OpenSY RPC URL')
    parser.add_argument('--rpc-user', help='RPC username (optional, uses cookie auth by default)')
    parser.add_argument('--rpc-password', help='RPC password (optional)')
    args = parser.parse_args()
    
    # Create metrics collector
    collector = OpenSYMetrics(
        rpc_url=args.rpc_url,
        rpc_user=args.rpc_user,
        rpc_password=args.rpc_password
    )
    
    # Test connection
    logger.info("Testing RPC connection...")
    test = collector._rpc_call('getblockchaininfo')
    if test:
        logger.info(f"Connected to OpenSY node at block {test.get('blocks', 0)}")
    else:
        logger.warning("Could not connect to OpenSY node. Metrics may be empty.")
    
    # Set up handler with collector
    MetricsHandler.metrics_collector = collector
    
    # Start server
    server = HTTPServer(('0.0.0.0', args.port), MetricsHandler)
    logger.info(f"Starting metrics server on port {args.port}")
    logger.info(f"Metrics available at http://localhost:{args.port}/metrics")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        server.shutdown()


if __name__ == '__main__':
    main()
