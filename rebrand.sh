#!/bin/bash
# Rebrand Bitcoin to OpenSyria

echo "Rebranding Bitcoin to OpenSyria..."

# Update client name and version strings
grep -rl "Bitcoin Core" src/ doc/ | head -20 | while read f; do
    sed -i '' 's/Bitcoin Core/OpenSyria Core/g' "$f" 2>/dev/null
done

# Update "bitcoin" references in key files
sed -i '' 's/bitcoin-cli/opensyria-cli/g' src/bitcoin-cli.cpp 2>/dev/null
sed -i '' 's/bitcoind/opensyriad/g' src/bitcoind.cpp 2>/dev/null

# Update copyright and headers
sed -i '' 's/The Bitcoin Core developers/The Bitcoin Core developers \& OpenSyria developers/g' src/clientversion.cpp 2>/dev/null

echo "Basic rebranding done!"
