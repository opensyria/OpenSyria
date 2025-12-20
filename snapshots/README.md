# OpenSY UTXO Snapshots

This directory contains verified UTXO set snapshots for instant sync (AssumeUTXO).

## Available Snapshots

| File | Block Height | Block Hash | UTXO Hash | Coins | Size |
|------|-------------|------------|-----------|-------|------|
| `utxo-10000.dat` | 10,000 | `d1f5665be...` | `83fd9a76...` | 10,000 | 597 KB |

## How to Use

### New Node Instant Sync

```bash
# Start a new node with the snapshot (after building with updated chainparams)
./opensyd -loadtxoutset=/path/to/utxo-10000.dat
```

The node will:
1. Load the UTXO snapshot and immediately have a usable chain tip at block 10000
2. Begin syncing new blocks from block 10001 onwards
3. Validate the snapshot in the background by syncing from genesis

### Verification

These snapshots are embedded in the chainparams and verified by the binary:

```cpp
// src/kernel/chainparams.cpp
m_assumeutxo_data = {
    {
        .height = 10000,
        .hash_serialized = AssumeutxoHash{uint256{"83fd9a7607e167d17a17b904dfa8f447be9829ecd5dc46972d8455f14284608f"}},
        .m_chain_tx_count = 10001,
        .blockhash = uint256{"d1f5665be3354945d995816b8dbf5d9105cad6af1bb2b443fe4c07c72bc5ef22"},
    },
};
```

### Generate New Snapshots

To generate a snapshot at a specific height:

```bash
# Ensure node is synced to at least that height
./opensy-cli -rpcclienttimeout=0 dumptxoutset /path/to/utxo-HEIGHT.dat rollback '{"rollback": HEIGHT}'
```

## Security Considerations

- Only use snapshots from trusted sources or verify them yourself
- The snapshot hash is consensus-critical and hardcoded in the binary
- An incorrect snapshot hash would cause the node to reject the snapshot

## Snapshot Details

### utxo-10000.dat

Generated: December 20, 2025  
Block: 10000  
Chain Work: `0x28102810`  
Total Supply: 100,000,000 SYL  
Transaction Count: 10,001

This snapshot was generated after the first successful difficulty adjustment period, 
marking a significant milestone for chain stability.
