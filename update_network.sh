#!/bin/bash
# Update network identifiers for OpenSyria
# Using unique magic bytes and ports to differentiate from Bitcoin

# Update mainnet magic bytes (0xf9beb4d9 -> 0x53594c00 "SYL\0")
# pchMessageStart[0] = 0x53 = 'S'
# pchMessageStart[1] = 0x59 = 'Y'  
# pchMessageStart[2] = 0x4c = 'L'
# pchMessageStart[3] = 0x00

# Update mainnet port from 8333 to 9333
sed -i '' 's/nDefaultPort = 8333;/nDefaultPort = 9333; \/\/ OpenSyria mainnet port/' src/kernel/chainparams.cpp

# Update testnet port from 18333 to 19333
sed -i '' 's/nDefaultPort = 18333;/nDefaultPort = 19333; \/\/ OpenSyria testnet port/' src/kernel/chainparams.cpp

# Update testnet4 port from 48333 to 49333
sed -i '' 's/nDefaultPort = 48333;/nDefaultPort = 49333; \/\/ OpenSyria testnet4 port/' src/kernel/chainparams.cpp

# Update signet port from 38333 to 39333
sed -i '' 's/nDefaultPort = 38333;/nDefaultPort = 39333; \/\/ OpenSyria signet port/' src/kernel/chainparams.cpp

# Update regtest port from 18444 to 19444
sed -i '' 's/nDefaultPort = 18444;/nDefaultPort = 19444; \/\/ OpenSyria regtest port/' src/kernel/chainparams.cpp

echo "Network identifiers updated!"
