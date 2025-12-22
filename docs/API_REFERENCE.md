# OpenSY API Reference

Complete documentation for OpenSY RPC API and Web Wallet REST API.

## Table of Contents

1. [RPC API](#rpc-api)
2. [Web Wallet REST API](#web-wallet-rest-api)
3. [Error Handling](#error-handling)
4. [Rate Limits](#rate-limits)
5. [Examples](#examples)

---

## RPC API

OpenSY inherits Bitcoin Core's JSON-RPC interface with OpenSY-specific additions.

### Connection

```
Host: 127.0.0.1 (default)
Port: 9632 (mainnet), 19632 (testnet), 19444 (regtest)
Protocol: HTTP POST with JSON-RPC 1.0
```

### Authentication

Two methods:
1. **Cookie authentication** (default, recommended):
   - Cookie file: `~/.opensy/.cookie` or `~/Library/Application Support/OpenSY/.cookie`
   - Format: `__cookie__:hexstring`

2. **RPC credentials** in `opensy.conf`:
   ```
   rpcuser=yourusername
   rpcpassword=yourpassword
   ```

### Request Format

```json
{
  "jsonrpc": "1.0",
  "id": "unique-id",
  "method": "method_name",
  "params": []
}
```

### Response Format

```json
{
  "result": { ... },
  "error": null,
  "id": "unique-id"
}
```

---

## Blockchain Methods

### getblockchaininfo

Returns blockchain state information.

**Parameters:** None

**Response:**
```json
{
  "chain": "main",
  "blocks": 10378,
  "headers": 10378,
  "bestblockhash": "000000...",
  "difficulty": 0.0001,
  "mediantime": 1766362000,
  "verificationprogress": 1.0,
  "chainwork": "00000000000...",
  "pruned": false
}
```

### getblockcount

Returns the current block height.

**Parameters:** None

**Response:** `10378` (integer)

### getblockhash

Returns block hash at height.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| height | integer | Yes | Block height |

**Example:**
```bash
opensy-cli getblockhash 100
```

### getblock

Returns block data.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| blockhash | string | Yes | Block hash |
| verbosity | integer | No | 0=hex, 1=json, 2=json+tx |

**Response (verbosity=1):**
```json
{
  "hash": "000000...",
  "confirmations": 100,
  "height": 10278,
  "version": 536870912,
  "merkleroot": "...",
  "time": 1766360000,
  "nonce": 12345,
  "bits": "1e0ffff0",
  "difficulty": 0.0001,
  "nTx": 1,
  "tx": ["txid1", "txid2"]
}
```

### getbestblockhash

Returns the hash of the current tip.

**Parameters:** None

**Response:** `"000000abc123..."` (string)

---

## Transaction Methods

### getrawtransaction

Returns raw transaction data.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| txid | string | Yes | Transaction ID |
| verbose | boolean | No | If true, returns JSON |
| blockhash | string | No | Block containing tx |

**Response (verbose=true):**
```json
{
  "txid": "abc123...",
  "hash": "abc123...",
  "version": 2,
  "size": 225,
  "vsize": 144,
  "weight": 573,
  "locktime": 0,
  "vin": [{
    "txid": "prev_txid",
    "vout": 0,
    "scriptSig": { "asm": "...", "hex": "..." },
    "sequence": 4294967295
  }],
  "vout": [{
    "value": 10000.0,
    "n": 0,
    "scriptPubKey": {
      "asm": "OP_0 OP_PUSHBYTES_20 ...",
      "hex": "...",
      "address": "syl1q...",
      "type": "witness_v0_keyhash"
    }
  }],
  "blockhash": "000000...",
  "confirmations": 50,
  "time": 1766360000,
  "blocktime": 1766360000
}
```

### sendrawtransaction

Submits a raw transaction to the network.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| hexstring | string | Yes | Signed raw transaction |
| maxfeerate | numeric | No | Max fee rate in SYL/kvB |

**Response:** `"txid"` (string)

### decoderawtransaction

Decodes a raw transaction hex string.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| hexstring | string | Yes | Raw transaction hex |

---

## Address Methods

### scantxoutset

Scans the UTXO set for addresses.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| action | string | Yes | "start", "abort", or "status" |
| scanobjects | array | Yes* | Address descriptors |

**Scan Objects Format:**
```json
["addr(syl1q...)", "addr(F...)"]
```

**Response:**
```json
{
  "success": true,
  "txouts": 1000000,
  "height": 10378,
  "bestblock": "000000...",
  "unspents": [
    {
      "txid": "abc123...",
      "vout": 0,
      "scriptPubKey": "...",
      "amount": 10000.0,
      "height": 100
    }
  ],
  "total_amount": 103780000.0
}
```

### validateaddress

Validates an address.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| address | string | Yes | OpenSY address |

**Response:**
```json
{
  "isvalid": true,
  "address": "syl1q...",
  "scriptPubKey": "...",
  "isscript": false,
  "iswitness": true,
  "witness_version": 0,
  "witness_program": "..."
}
```

---

## Wallet Methods

### getbalance

Returns wallet balance.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| dummy | string | No | Must be "*" or omitted |
| minconf | integer | No | Minimum confirmations |

**Response:** `102780000.0` (numeric, in SYL)

### getnewaddress

Generates a new receiving address.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| label | string | No | Address label |
| address_type | string | No | "legacy", "p2sh-segwit", "bech32" |

**Response:** `"syl1q..."` (string)

### sendtoaddress

Sends SYL to an address.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| address | string | Yes | Recipient address |
| amount | numeric | Yes | Amount in SYL |
| comment | string | No | Transaction comment |
| subtractfeefromamount | boolean | No | Deduct fee from amount |

**Response:** `"txid"` (string)

### listunspent

Lists UTXOs in wallet.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| minconf | integer | No | Minimum confirmations |
| maxconf | integer | No | Maximum confirmations |
| addresses | array | No | Filter addresses |

---

## Mining Methods

### getmininginfo

Returns mining information.

**Response:**
```json
{
  "blocks": 10378,
  "difficulty": 0.0001234,
  "networkhashps": 1000000,
  "pooledtx": 5,
  "chain": "main"
}
```

### getnetworkhashps

Returns estimated network hash rate.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| nblocks | integer | No | Blocks to average (default 120) |
| height | integer | No | Block height (-1 for current) |

**Response:** `1234567.89` (hashes per second)

### generatetoaddress

Mines blocks to an address (regtest only in production).

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| nblocks | integer | Yes | Number of blocks |
| address | string | Yes | Mining reward address |

---

## Network Methods

### getnetworkinfo

Returns network information.

**Response:**
```json
{
  "version": 280000,
  "subversion": "/OpenSY:28.0.0/",
  "protocolversion": 70016,
  "connections": 8,
  "connections_in": 2,
  "connections_out": 6,
  "networkactive": true,
  "networks": [
    { "name": "ipv4", "reachable": true },
    { "name": "ipv6", "reachable": true },
    { "name": "onion", "reachable": false }
  ]
}
```

### getpeerinfo

Returns peer information.

**Response:** Array of connected peer objects.

### addnode

Adds a node to connection list.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| node | string | Yes | Node address (IP:port) |
| command | string | Yes | "add", "remove", or "onetry" |

---

## Mempool Methods

### getmempoolinfo

Returns mempool statistics.

**Response:**
```json
{
  "loaded": true,
  "size": 15,
  "bytes": 5420,
  "usage": 32000,
  "maxmempool": 300000000,
  "mempoolminfee": 0.00001,
  "minrelaytxfee": 0.00001,
  "incrementalrelayfee": 0.00001
}
```

### getrawmempool

Returns mempool transaction IDs.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| verbose | boolean | No | Include tx details |

---

## Fee Estimation

### estimatesmartfee

Estimates fee rate for confirmation.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| conf_target | integer | Yes | Target confirmations |
| estimate_mode | string | No | "economical" or "conservative" |

**Response:**
```json
{
  "feerate": 0.00001,
  "blocks": 2
}
```

---

## Web Wallet REST API

The Web Wallet provides a simplified REST API for public access.

### Base URL

```
Production: https://wallet.opensyria.net/api
Development: http://127.0.0.1:8080/api
```

### Endpoints

#### GET /api/health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "chain": "main",
  "blocks": 10378,
  "synced": true
}
```

#### GET /api/info

Blockchain and network information.

**Response:**
```json
{
  "chain": "main",
  "blocks": 10378,
  "headers": 10378,
  "difficulty": 0.0001234,
  "mediantime": 1766362000,
  "verificationprogress": 1.0,
  "network": {
    "version": 280000,
    "subversion": "/OpenSY:28.0.0/",
    "connections": 8
  },
  "mining": {
    "networkhashps": 1234567,
    "difficulty": 0.0001234
  },
  "timestamp": 1766362500
}
```

#### GET /api/address/{address}

Get address balance and UTXOs.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| address | path | OpenSY address (syl1... or F...) |
| page | query | Page number (default 1) |
| limit | query | UTXOs per page (default 20, max 100) |

**Response:**
```json
{
  "address": "syl1q...",
  "balance": 103780000.0,
  "utxo_count": 10378,
  "utxos": [
    {
      "txid": "abc123...",
      "vout": 0,
      "amount": 10000.0,
      "height": 10378
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total_pages": 519,
    "has_more": true
  },
  "timestamp": 1766362500
}
```

#### GET /api/address/{address}/txs

Get address transaction history.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| address | path | OpenSY address |
| page | query | Page number |
| limit | query | Transactions per page |

**Response:**
```json
{
  "address": "syl1q...",
  "transactions": [
    {
      "txid": "abc123...",
      "blockhash": "000000...",
      "blockheight": 10378,
      "time": 1766362000,
      "confirmations": 1,
      "amount": 10000.0
    }
  ],
  "total": 100,
  "page": 1,
  "limit": 25,
  "has_more": true
}
```

#### GET /api/tx/{txid}

Get transaction details.

**Response:**
```json
{
  "txid": "abc123...",
  "hash": "abc123...",
  "version": 2,
  "size": 225,
  "vsize": 144,
  "blockhash": "000000...",
  "confirmations": 50,
  "time": 1766360000,
  "vin": [...],
  "vout": [...]
}
```

#### GET /api/block/{identifier}

Get block by hash or height.

**Response:**
```json
{
  "hash": "000000...",
  "height": 10378,
  "confirmations": 1,
  "time": 1766362000,
  "nTx": 1,
  "difficulty": 0.0001234,
  "tx": ["txid1", "txid2"]
}
```

#### GET /api/blocks/recent

Get recent blocks.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| count | query | Number of blocks (default 10, max 50) |

**Response:**
```json
{
  "blocks": [
    {
      "hash": "000000...",
      "height": 10378,
      "time": 1766362000,
      "tx_count": 1
    }
  ],
  "count": 10
}
```

#### GET /api/mempool

Get mempool statistics.

**Response:**
```json
{
  "size": 15,
  "bytes": 5420,
  "mempoolminfee": 0.00001
}
```

#### GET /api/estimate-fee

Get fee estimation.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| target | query | Confirmation target (default 6) |

**Response:**
```json
{
  "feerate": 0.00001,
  "blocks": 6,
  "conf_target": 6
}
```

---

## Error Handling

### RPC Errors

```json
{
  "result": null,
  "error": {
    "code": -32600,
    "message": "Invalid Request"
  },
  "id": "unique-id"
}
```

**Common Error Codes:**
| Code | Description |
|------|-------------|
| -1 | General error |
| -3 | Invalid type |
| -5 | Invalid address |
| -6 | Insufficient funds |
| -8 | Invalid parameter |
| -25 | TX verify failed |
| -26 | TX already in chain |
| -32600 | Invalid request |
| -32601 | Method not found |

### REST API Errors

```json
{
  "error": "Error message here"
}
```

**HTTP Status Codes:**
| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad request (invalid parameters) |
| 404 | Not found |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
| 503 | Service unavailable (node down) |

---

## Rate Limits

### Web Wallet API

| Limit | Value |
|-------|-------|
| Requests per minute | 100 |
| Requests per IP | Per-IP tracking |
| Burst | 20 requests |

**Rate Limit Response (HTTP 429):**
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60
}
```

---

## Examples

### cURL - Get Block Count

```bash
curl --user __cookie__:$(cat ~/.opensy/.cookie | cut -d: -f2) \
  --data-binary '{"jsonrpc":"1.0","id":"1","method":"getblockcount","params":[]}' \
  -H 'content-type: text/plain;' \
  http://127.0.0.1:9632/
```

### cURL - Check Address Balance (REST)

```bash
curl https://wallet.opensyria.net/api/address/syl1qvg2uuau5xegn0nt8fly5m2xm84uvgn3m3aermx
```

### Python - RPC Client

```python
import requests
import json

def rpc_call(method, params=[]):
    url = "http://127.0.0.1:9632/"
    headers = {"content-type": "application/json"}
    
    # Read cookie
    with open("/path/to/.cookie") as f:
        cookie = f.read().strip()
    user, password = cookie.split(":")
    
    payload = {
        "jsonrpc": "1.0",
        "id": "python",
        "method": method,
        "params": params
    }
    
    response = requests.post(
        url,
        auth=(user, password),
        headers=headers,
        data=json.dumps(payload)
    )
    
    return response.json()["result"]

# Example usage
block_count = rpc_call("getblockcount")
print(f"Current block: {block_count}")
```

### JavaScript - REST API

```javascript
async function getAddressBalance(address) {
    const response = await fetch(
        `https://wallet.opensyria.net/api/address/${address}`
    );
    const data = await response.json();
    console.log(`Balance: ${data.balance} SYL`);
    return data;
}

// Example usage
getAddressBalance('syl1qvg2uuau5xegn0nt8fly5m2xm84uvgn3m3aermx');
```

---

## OpenSY-Specific Notes

### Address Formats

| Type | Prefix | Example |
|------|--------|---------|
| Bech32 (SegWit) | syl1 | syl1qvg2uuau5xegn0nt8fly5m2xm84uvgn3m3aermx |
| Legacy (P2PKH) | F | Fxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx |

### Block Reward

| Height Range | Reward |
|--------------|--------|
| 0 - ∞ | 10,000 SYL |

### RandomX Mining

OpenSY uses RandomX proof-of-work (same as Monero):

- **Mining**: Full memory mode (~2GB RAM, ~1000+ H/s per core)
- **Validation**: Light mode (~256MB RAM, ~100 H/s)

Validation at ~100 H/s means blocks verify in 10-100ms, which is acceptable for:
- Initial block download
- New block verification
- Transaction validation

### Ports

| Network | P2P Port | RPC Port |
|---------|----------|----------|
| Mainnet | 9633 | 9632 |
| Testnet | 19633 | 19632 |
| Regtest | 19444 | 19443 |

---

## See Also

- [Mining Guide](MINING_GUIDE.md)
- [Wallet Guide](WALLET_GUIDE.md)
- [Node Setup](../INSTALL.md)
