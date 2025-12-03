#!/usr/bin/env bash
# Update genesis block parameters for OpenSyria
export LC_ALL=C

# Update the genesis block timestamp message
sed -i '' 's/The Times 03\/Jan\/2009 Chancellor on brink of second bailout for banks/OpenSyria - First Syrian Blockchain - For Syria Future and Reconstruction 2025/' src/kernel/chainparams.cpp

# Update the initial genesis reward from 50 * COIN to 10000 * COIN in CreateGenesisBlock calls
sed -i '' 's/50 \* COIN/10000 * COIN/g' src/kernel/chainparams.cpp

# For now, comment out the genesis hash assertions so we can mine a new one
# We'll update these after we compute the actual hashes
sed -i '' 's/assert(consensus.hashGenesisBlock == uint256/\/\/ TODO: Update after mining new genesis: assert(consensus.hashGenesisBlock == uint256/g' src/kernel/chainparams.cpp
sed -i '' 's/assert(genesis.hashMerkleRoot == uint256/\/\/ TODO: Update after mining new genesis: assert(genesis.hashMerkleRoot == uint256/g' src/kernel/chainparams.cpp

echo "Genesis block parameters updated!"
