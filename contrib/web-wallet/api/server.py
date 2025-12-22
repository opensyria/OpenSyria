#!/usr/bin/env python3
"""
OpenSY Web Wallet API Server

A lightweight REST API that provides read-only blockchain data for the web wallet.
This server sits between the public web interface and the private OpenSY node.

Security Features:
- Read-only endpoints only (no signing, no sending)
- Rate limiting per IP
- Request validation
- CORS configured for specific origins
- No RPC credentials exposed to frontend

Usage:
    python3 server.py --rpc-host 127.0.0.1 --rpc-port 9632 --rpc-user USER --rpc-password PASS

Production:
    gunicorn -w 4 -b 0.0.0.0:8080 server:app
"""

import os
import sys
import json
import time
import hashlib
import argparse
import logging
from functools import wraps
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from collections import defaultdict
import threading

# Flask for REST API
try:
    from flask import Flask, request, jsonify, abort
    from flask_cors import CORS
except ImportError:
    print("Please install Flask: pip install flask flask-cors")
    sys.exit(1)

# For RPC calls
import urllib.request
import urllib.error
import base64

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# =============================================================================
# Configuration
# =============================================================================

class Config:
    # RPC connection (set via environment or command line)
    RPC_HOST = os.environ.get('OPENSY_RPC_HOST', '127.0.0.1')
    RPC_PORT = int(os.environ.get('OPENSY_RPC_PORT', '9632'))
    RPC_USER = os.environ.get('OPENSY_RPC_USER', '')
    RPC_PASSWORD = os.environ.get('OPENSY_RPC_PASSWORD', '')
    
    # API settings
    API_PORT = int(os.environ.get('API_PORT', '8080'))
    
    # CORS - allowed origins (update for production)
    ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '*').split(',')
    
    # Rate limiting
    RATE_LIMIT_REQUESTS = 100  # requests per window
    RATE_LIMIT_WINDOW = 60     # seconds
    
    # Cache settings
    CACHE_TTL_BLOCKCHAIN = 10   # seconds
    CACHE_TTL_ADDRESS = 30      # seconds
    CACHE_TTL_TX = 300          # 5 minutes (tx don't change)

config = Config()

# =============================================================================
# CORS Configuration
# =============================================================================

CORS(app, resources={
    r"/api/*": {
        "origins": config.ALLOWED_ORIGINS,
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# =============================================================================
# Rate Limiting
# =============================================================================

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = defaultdict(list)
        self.lock = threading.Lock()
    
    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        
        with self.lock:
            # Clean old requests
            self.requests[client_id] = [
                t for t in self.requests[client_id] if t > window_start
            ]
            
            if len(self.requests[client_id]) >= self.max_requests:
                return False
            
            self.requests[client_id].append(now)
            return True
    
    def get_remaining(self, client_id: str) -> int:
        now = time.time()
        window_start = now - self.window_seconds
        
        with self.lock:
            recent = [t for t in self.requests[client_id] if t > window_start]
            return max(0, self.max_requests - len(recent))

rate_limiter = RateLimiter(config.RATE_LIMIT_REQUESTS, config.RATE_LIMIT_WINDOW)

def get_client_ip() -> str:
    """Get client IP, considering proxies."""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr or 'unknown'

def rate_limit(f):
    """Rate limiting decorator."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = get_client_ip()
        
        if not rate_limiter.is_allowed(client_ip):
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return jsonify({
                'error': 'Rate limit exceeded',
                'retry_after': config.RATE_LIMIT_WINDOW
            }), 429
        
        response = f(*args, **kwargs)
        return response
    
    return decorated_function

# =============================================================================
# Caching
# =============================================================================

class Cache:
    def __init__(self):
        self.data: Dict[str, tuple] = {}  # key -> (value, expiry_time)
        self.lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key in self.data:
                value, expiry = self.data[key]
                if time.time() < expiry:
                    return value
                else:
                    del self.data[key]
            return None
    
    def set(self, key: str, value: Any, ttl: int):
        with self.lock:
            self.data[key] = (value, time.time() + ttl)
    
    def clear(self):
        with self.lock:
            self.data.clear()

cache = Cache()

# =============================================================================
# RPC Client
# =============================================================================

class RPCClient:
    def __init__(self, host: str, port: int, user: str, password: str):
        self.url = f"http://{host}:{port}/"
        self.auth = base64.b64encode(f"{user}:{password}".encode()).decode()
    
    def call(self, method: str, params: list = None, wallet: str = None) -> Any:
        """Make RPC call to OpenSY node."""
        url = self.url
        if wallet:
            url = f"{self.url}wallet/{wallet}"
        
        payload = json.dumps({
            'jsonrpc': '1.0',
            'id': int(time.time() * 1000),
            'method': method,
            'params': params or []
        }).encode()
        
        headers = {
            'Content-Type': 'application/json'
        }
        if self.auth:
            headers['Authorization'] = f'Basic {self.auth}'
        
        req = urllib.request.Request(url, data=payload, headers=headers)
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode())
                if result.get('error'):
                    raise Exception(result['error'].get('message', 'RPC Error'))
                return result.get('result')
        except urllib.error.HTTPError as e:
            raise Exception(f"HTTP Error: {e.code}")
        except urllib.error.URLError as e:
            raise Exception(f"Connection Error: {e.reason}")

rpc: Optional[RPCClient] = None

# =============================================================================
# Validation Helpers
# =============================================================================

def validate_address(address: str) -> bool:
    """Validate OpenSY address format."""
    if not address:
        return False
    
    # Bech32 addresses start with 'syl1'
    if address.startswith('syl1'):
        return 42 <= len(address) <= 62
    
    # Legacy addresses start with 'F' (base58)
    if address.startswith('F'):
        return 26 <= len(address) <= 35
    
    return False

def validate_txid(txid: str) -> bool:
    """Validate transaction ID format."""
    if not txid:
        return False
    return len(txid) == 64 and all(c in '0123456789abcdef' for c in txid.lower())

def validate_block_hash(hash: str) -> bool:
    """Validate block hash format."""
    return validate_txid(hash)  # Same format

# =============================================================================
# API Endpoints
# =============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        info = rpc.call('getblockchaininfo')
        return jsonify({
            'status': 'healthy',
            'chain': info.get('chain'),
            'blocks': info.get('blocks'),
            'synced': info.get('verificationprogress', 0) > 0.999
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

@app.route('/api/info', methods=['GET'])
@rate_limit
def get_info():
    """Get blockchain and network info."""
    cache_key = 'blockchain_info'
    cached = cache.get(cache_key)
    if cached:
        return jsonify(cached)
    
    try:
        blockchain_info = rpc.call('getblockchaininfo')
        network_info = rpc.call('getnetworkinfo')
        mining_info = rpc.call('getmininginfo')
        
        result = {
            'chain': blockchain_info.get('chain'),
            'blocks': blockchain_info.get('blocks'),
            'headers': blockchain_info.get('headers'),
            'difficulty': blockchain_info.get('difficulty'),
            'mediantime': blockchain_info.get('mediantime'),
            'verificationprogress': blockchain_info.get('verificationprogress'),
            'pruned': blockchain_info.get('pruned'),
            'network': {
                'version': network_info.get('version'),
                'subversion': network_info.get('subversion'),
                'connections': network_info.get('connections'),
                'connections_in': network_info.get('connections_in'),
                'connections_out': network_info.get('connections_out')
            },
            'mining': {
                'networkhashps': mining_info.get('networkhashps'),
                'difficulty': mining_info.get('difficulty')
            },
            'timestamp': int(time.time())
        }
        
        cache.set(cache_key, result, config.CACHE_TTL_BLOCKCHAIN)
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error getting info: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/address/<address>', methods=['GET'])
@rate_limit
def get_address_info(address: str):
    """Get address balance and transaction count."""
    if not validate_address(address):
        return jsonify({'error': 'Invalid address format'}), 400
    
    cache_key = f'address:{address}'
    cached = cache.get(cache_key)
    if cached:
        return jsonify(cached)
    
    # Pagination for UTXOs
    page = request.args.get('page', 1, type=int)
    limit = min(request.args.get('limit', 20, type=int), 100)  # Max 100 per page
    
    try:
        # Use scantxoutset to get UTXO data for address
        # This works without a wallet
        scan_result = rpc.call('scantxoutset', ['start', [f'addr({address})']])
        
        # Get all UTXOs and sort by height (most recent first)
        all_utxos = scan_result.get('unspents', [])
        all_utxos.sort(key=lambda u: u.get('height', 0), reverse=True)
        
        # Paginate
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        page_utxos = all_utxos[start_idx:end_idx]
        
        result = {
            'address': address,
            'balance': scan_result.get('total_amount', 0),
            'utxo_count': len(all_utxos),
            'utxos': [
                {
                    'txid': u.get('txid'),
                    'vout': u.get('vout'),
                    'amount': u.get('amount'),
                    'height': u.get('height')
                }
                for u in page_utxos
            ],
            'pagination': {
                'page': page,
                'limit': limit,
                'total_pages': (len(all_utxos) + limit - 1) // limit,
                'has_more': end_idx < len(all_utxos)
            },
            'timestamp': int(time.time())
        }
        
        # Only cache first page (most common request)
        if page == 1:
            cache.set(cache_key, result, config.CACHE_TTL_ADDRESS)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error getting address info for {address}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/address/<address>/txs', methods=['GET'])
@rate_limit
def get_address_transactions(address: str):
    """Get transactions for an address."""
    if not validate_address(address):
        return jsonify({'error': 'Invalid address format'}), 400
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    limit = min(request.args.get('limit', 25, type=int), 100)
    
    try:
        # This requires address index or wallet import
        # For now, return the UTXOs we can find
        scan_result = rpc.call('scantxoutset', ['start', [f'addr({address})']])
        
        # Get transaction details for each UTXO
        txs = []
        seen_txids = set()
        
        for utxo in scan_result.get('unspents', []):
            txid = utxo.get('txid')
            if txid in seen_txids:
                continue
            seen_txids.add(txid)
            
            try:
                tx = rpc.call('getrawtransaction', [txid, True])
                txs.append({
                    'txid': txid,
                    'blockhash': tx.get('blockhash'),
                    'blockheight': tx.get('height'),
                    'time': tx.get('time'),
                    'confirmations': tx.get('confirmations', 0),
                    'amount': utxo.get('amount')
                })
            except:
                pass  # Skip if tx not found
        
        # Sort by time descending
        txs.sort(key=lambda x: x.get('time', 0), reverse=True)
        
        # Paginate
        start = (page - 1) * limit
        end = start + limit
        
        return jsonify({
            'address': address,
            'transactions': txs[start:end],
            'total': len(txs),
            'page': page,
            'limit': limit,
            'has_more': end < len(txs)
        })
    
    except Exception as e:
        logger.error(f"Error getting transactions for {address}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/tx/<txid>', methods=['GET'])
@rate_limit
def get_transaction(txid: str):
    """Get transaction details."""
    if not validate_txid(txid):
        return jsonify({'error': 'Invalid transaction ID'}), 400
    
    cache_key = f'tx:{txid}'
    cached = cache.get(cache_key)
    if cached:
        return jsonify(cached)
    
    try:
        tx = rpc.call('getrawtransaction', [txid, True])
        
        result = {
            'txid': tx.get('txid'),
            'hash': tx.get('hash'),
            'version': tx.get('version'),
            'size': tx.get('size'),
            'vsize': tx.get('vsize'),
            'weight': tx.get('weight'),
            'locktime': tx.get('locktime'),
            'blockhash': tx.get('blockhash'),
            'confirmations': tx.get('confirmations', 0),
            'time': tx.get('time'),
            'blocktime': tx.get('blocktime'),
            'vin': [
                {
                    'txid': vin.get('txid'),
                    'vout': vin.get('vout'),
                    'coinbase': vin.get('coinbase')
                }
                for vin in tx.get('vin', [])
            ],
            'vout': [
                {
                    'value': vout.get('value'),
                    'n': vout.get('n'),
                    'address': vout.get('scriptPubKey', {}).get('address')
                }
                for vout in tx.get('vout', [])
            ]
        }
        
        cache.set(cache_key, result, config.CACHE_TTL_TX)
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error getting transaction {txid}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/block/<identifier>', methods=['GET'])
@rate_limit
def get_block(identifier: str):
    """Get block by hash or height."""
    try:
        # Determine if it's a hash or height
        if identifier.isdigit():
            block_hash = rpc.call('getblockhash', [int(identifier)])
        elif validate_block_hash(identifier):
            block_hash = identifier
        else:
            return jsonify({'error': 'Invalid block identifier'}), 400
        
        block = rpc.call('getblock', [block_hash, 1])  # Verbosity 1
        
        return jsonify({
            'hash': block.get('hash'),
            'height': block.get('height'),
            'version': block.get('version'),
            'time': block.get('time'),
            'mediantime': block.get('mediantime'),
            'nonce': block.get('nonce'),
            'difficulty': block.get('difficulty'),
            'chainwork': block.get('chainwork'),
            'nTx': block.get('nTx'),
            'previousblockhash': block.get('previousblockhash'),
            'nextblockhash': block.get('nextblockhash'),
            'tx': block.get('tx', [])[:50]  # Limit transactions
        })
    
    except Exception as e:
        logger.error(f"Error getting block {identifier}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/blocks/recent', methods=['GET'])
@rate_limit
def get_recent_blocks():
    """Get recent blocks."""
    count = min(request.args.get('count', 10, type=int), 50)
    
    cache_key = f'recent_blocks:{count}'
    cached = cache.get(cache_key)
    if cached:
        return jsonify(cached)
    
    try:
        tip_height = rpc.call('getblockcount')
        blocks = []
        
        for i in range(count):
            height = tip_height - i
            if height < 0:
                break
            
            block_hash = rpc.call('getblockhash', [height])
            block = rpc.call('getblock', [block_hash, 1])
            
            blocks.append({
                'hash': block.get('hash'),
                'height': block.get('height'),
                'time': block.get('time'),
                'nTx': block.get('nTx'),
                'size': block.get('size'),
                'weight': block.get('weight')
            })
        
        result = {
            'blocks': blocks,
            'tip_height': tip_height
        }
        
        cache.set(cache_key, result, config.CACHE_TTL_BLOCKCHAIN)
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error getting recent blocks: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mempool', methods=['GET'])
@rate_limit
def get_mempool_info():
    """Get mempool statistics."""
    cache_key = 'mempool_info'
    cached = cache.get(cache_key)
    if cached:
        return jsonify(cached)
    
    try:
        mempool_info = rpc.call('getmempoolinfo')
        
        result = {
            'loaded': mempool_info.get('loaded'),
            'size': mempool_info.get('size'),
            'bytes': mempool_info.get('bytes'),
            'usage': mempool_info.get('usage'),
            'total_fee': mempool_info.get('total_fee'),
            'maxmempool': mempool_info.get('maxmempool'),
            'mempoolminfee': mempool_info.get('mempoolminfee'),
            'minrelaytxfee': mempool_info.get('minrelaytxfee')
        }
        
        cache.set(cache_key, result, config.CACHE_TTL_BLOCKCHAIN)
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error getting mempool info: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/estimate-fee', methods=['GET'])
@rate_limit
def estimate_fee():
    """Estimate transaction fee."""
    conf_target = request.args.get('blocks', 6, type=int)
    conf_target = max(1, min(conf_target, 1008))  # Limit range
    
    try:
        estimate = rpc.call('estimatesmartfee', [conf_target])
        
        return jsonify({
            'feerate': estimate.get('feerate'),
            'blocks': estimate.get('blocks'),
            'conf_target': conf_target
        })
    
    except Exception as e:
        logger.error(f"Error estimating fee: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# Static File Serving (for development)
# =============================================================================

@app.route('/')
def serve_index():
    """Serve the main HTML file."""
    import os
    html_path = os.path.join(os.path.dirname(__file__), '..', 'index.html')
    try:
        with open(html_path, 'r') as f:
            return f.read(), 200, {'Content-Type': 'text/html'}
    except FileNotFoundError:
        return "index.html not found", 404

# =============================================================================
# Error Handlers
# =============================================================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

# =============================================================================
# Main
# =============================================================================

def init_rpc():
    """Initialize the RPC client from config."""
    global rpc
    rpc = RPCClient(config.RPC_HOST, config.RPC_PORT, config.RPC_USER, config.RPC_PASSWORD)
    return rpc

def test_rpc_connection():
    """Test if we can connect to the OpenSY node."""
    global rpc
    if rpc is None:
        init_rpc()
    try:
        info = rpc.call('getblockchaininfo')
        logger.info(f"Connected to OpenSY node: chain={info.get('chain')}, blocks={info.get('blocks')}")
        return True
    except Exception as e:
        logger.warning(f"OpenSY node not available: {e}")
        return False

def main():
    global rpc, config
    
    parser = argparse.ArgumentParser(description='OpenSY Web Wallet API Server')
    parser.add_argument('--rpc-host', default=config.RPC_HOST, help='RPC host')
    parser.add_argument('--rpc-port', type=int, default=config.RPC_PORT, help='RPC port')
    parser.add_argument('--rpc-user', default=config.RPC_USER, help='RPC username')
    parser.add_argument('--rpc-password', default=config.RPC_PASSWORD, help='RPC password')
    parser.add_argument('--port', type=int, default=config.API_PORT, help='API server port')
    parser.add_argument('--host', default='0.0.0.0', help='API server host')
    parser.add_argument('--origins', default='*', help='Allowed CORS origins (comma-separated)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Update config
    config.RPC_HOST = args.rpc_host
    config.RPC_PORT = args.rpc_port
    config.RPC_USER = args.rpc_user
    config.RPC_PASSWORD = args.rpc_password
    config.API_PORT = args.port
    config.ALLOWED_ORIGINS = args.origins.split(',')
    
    # Initialize RPC client
    init_rpc()
    
    # Test connection (but don't exit if it fails)
    if test_rpc_connection():
        logger.info("OpenSY node is available")
    else:
        logger.warning("OpenSY node is not available. API will return errors until node is up.")
        logger.warning("Make sure opensyd is running with server=1 in opensy.conf")
    
    logger.info(f"Starting OpenSY Web Wallet API on {args.host}:{args.port}")
    logger.info(f"Allowed origins: {config.ALLOWED_ORIGINS}")
    
    app.run(host=args.host, port=args.port, debug=args.debug)

# Initialize RPC client for gunicorn (when not run via main())
init_rpc()

if __name__ == '__main__':
    main()
