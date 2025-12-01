#!/bin/bash
# Update block subsidy and consensus params

# Update comments in amount.h
sed -i '' 's/The amount of satoshis in one BTC/The amount of qirsh in one SYL/' src/consensus/amount.h
sed -i '' 's/(in satoshi)/(in qirsh)/' src/consensus/amount.h

# Update GetBlockSubsidy in validation.cpp
# Change initial reward from 50 to 10000 SYL
sed -i '' 's/CAmount nSubsidy = 50 \* COIN;/CAmount nSubsidy = 10000 * COIN; \/\/ 10,000 SYL initial reward/' src/validation.cpp
# Update comment 
sed -i '' 's/Subsidy is cut in half every 210,000 blocks/Subsidy is cut in half every 1,050,000 blocks/' src/validation.cpp

echo "Done updating block subsidy!"
