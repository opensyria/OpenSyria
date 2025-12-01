#!/bin/bash
# OpenSyria Blockchain Modification Script
# Specs: 21B total supply, 2-min blocks, 10,000 SYL initial reward, 1,050,000 block halving

echo "=== Modifying OpenSyria Chain Parameters ==="

# 1. Modify consensus/amount.h - Update MAX_MONEY for 21 billion SYL
echo "1. Updating amount.h..."
sed -i '' 's/static constexpr CAmount MAX_MONEY = 21000000 \* COIN;/static constexpr CAmount MAX_MONEY = 21000000000 * COIN; \/\/ 21 billion SYL/' src/consensus/amount.h

# Also add comment for qirsh
sed -i '' 's/\/\*\* Amount in satoshis/\/** Amount in qirsh (smallest unit of SYL)/' src/consensus/amount.h

# 2. Modify policy/feerate.h - Change BTC to SYL
echo "2. Updating feerate.h..."
sed -i '' 's/const std::string CURRENCY_UNIT = "BTC";/const std::string CURRENCY_UNIT = "SYL"; \/\/ Syrian Digital Lira/' src/policy/feerate.h

echo "Done with basic modifications!"
