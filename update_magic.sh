#!/bin/bash
# Update magic bytes for OpenSyria mainnet
# Using "SYL" themed bytes

# Find and replace mainnet magic bytes
# Bitcoin mainnet: 0xf9, 0xbe, 0xb4, 0xd9
# OpenSyria mainnet: 0x53, 0x59, 0x4c, 0x4d (S, Y, L, M - Syrian Lira Main)

# Use Python for precise byte replacement in the mainnet section
python3 << 'PYTHON'
import re

with open('src/kernel/chainparams.cpp', 'r') as f:
    content = f.read()

# Update mainnet magic bytes (in CMainParams section)
# Pattern: pchMessageStart[0] = 0xf9; followed by 0xbe, 0xb4, 0xd9
content = content.replace(
    'pchMessageStart[0] = 0xf9;\n        pchMessageStart[1] = 0xbe;\n        pchMessageStart[2] = 0xb4;\n        pchMessageStart[3] = 0xd9;',
    "pchMessageStart[0] = 0x53; // 'S'\n        pchMessageStart[1] = 0x59; // 'Y'\n        pchMessageStart[2] = 0x4c; // 'L'\n        pchMessageStart[3] = 0x4d; // 'M' for mainnet"
)

# Update testnet magic bytes (0x0b, 0x11, 0x09, 0x07 -> 0x53, 0x59, 0x4c, 0x54 "SYLT")
content = content.replace(
    'pchMessageStart[0] = 0x0b;\n        pchMessageStart[1] = 0x11;\n        pchMessageStart[2] = 0x09;\n        pchMessageStart[3] = 0x07;',
    "pchMessageStart[0] = 0x53; // 'S'\n        pchMessageStart[1] = 0x59; // 'Y'\n        pchMessageStart[2] = 0x4c; // 'L'\n        pchMessageStart[3] = 0x54; // 'T' for testnet"
)

# Update testnet4 magic bytes
content = content.replace(
    'pchMessageStart[0] = 0x1c;\n        pchMessageStart[1] = 0x16;\n        pchMessageStart[2] = 0x3f;\n        pchMessageStart[3] = 0x28;',
    "pchMessageStart[0] = 0x53; // 'S'\n        pchMessageStart[1] = 0x59; // 'Y'\n        pchMessageStart[2] = 0x4c; // 'L'\n        pchMessageStart[3] = 0x34; // '4' for testnet4"
)

# Update regtest magic bytes (0xfa, 0xbf, 0xb5, 0xda -> 0x53, 0x59, 0x4c, 0x52 "SYLR")
content = content.replace(
    'pchMessageStart[0] = 0xfa;\n        pchMessageStart[1] = 0xbf;\n        pchMessageStart[2] = 0xb5;\n        pchMessageStart[3] = 0xda;',
    "pchMessageStart[0] = 0x53; // 'S'\n        pchMessageStart[1] = 0x59; // 'Y'\n        pchMessageStart[2] = 0x4c; // 'L'\n        pchMessageStart[3] = 0x52; // 'R' for regtest"
)

with open('src/kernel/chainparams.cpp', 'w') as f:
    f.write(content)

print("Magic bytes updated!")
PYTHON
