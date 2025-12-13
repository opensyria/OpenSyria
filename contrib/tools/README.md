# OpenSY Development Tools

This directory contains standalone utilities created during the OpenSY fork process.

## Files

### `genesis_miner.cpp`
Displays OpenSY chain parameters and genesis block information.
- **Usage**: Standalone utility, compile with `g++ -o genesis_miner genesis_miner.cpp`
- **Purpose**: Reference for chain parameters when setting up new networks

### `print_genesis.cpp`  
Prints genesis block hashes for all OpenSY networks (mainnet, testnet, regtest, etc.)
- **Usage**: Requires OpenSY libraries, compile from build directory
- **Purpose**: Verify genesis block configuration after changes to chainparams.cpp

## OpenSY Chain Parameters

| Parameter | Value |
|-----------|-------|
| Coin Symbol | SYL |
| Block Reward | 10,000 SYL |
| Max Supply | 21 billion SYL |
| Block Time | 2 minutes |
| Halving Interval | 1,050,000 blocks (~4 years) |
| Difficulty Adjustment | Every 10,080 blocks (~2 weeks) |
| Mainnet Port | 9633 |
| Testnet Port | 19633 |
| Address Prefix | 'F' (mainnet), 'f' (testnet) - Freedom |

## License

MIT License - see COPYING in the root directory.
