#!/bin/bash
# Update chainparams.cpp with OpenSyria parameters

# Update halving interval from 210000 to 1050000 blocks
sed -i '' 's/nSubsidyHalvingInterval = 210000;/nSubsidyHalvingInterval = 1050000; \/\/ ~4 years with 2-min blocks/' src/kernel/chainparams.cpp

# Update block time from 10 minutes (600 seconds) to 2 minutes (120 seconds)
sed -i '' 's/nPowTargetSpacing = 10 \* 60;/nPowTargetSpacing = 2 * 60; \/\/ 2-minute blocks/' src/kernel/chainparams.cpp

# Update target timespan for difficulty adjustment 
# Bitcoin: 2016 blocks * 10 minutes = 2 weeks
# OpenSyria: Keep 2-week adjustment but with 2-min blocks: 2016 * 5 = 10080 blocks
# Or we can keep similar adjustment frequency: 2016 blocks = ~2.8 days
# Let's use: 2 weeks = 14 days * 24 hours * 60 min / 2 min = 10080 blocks
# But the formula uses timespan, so we keep 14 * 24 * 60 * 60 (two weeks in seconds)

echo "Done updating chainparams!"
