#!/usr/bin/env python3
"""
Convert Bitcoin xpub/xprv test vectors to OpenSY spub/sprv in descriptor_tests.cpp

This script converts all Bitcoin-style BIP32 extended keys (xpub/xprv/tpub/tprv)
to OpenSY equivalents (spub/sprv/stpb/stpv).

OpenSY BIP32 version bytes:
  Mainnet: EXT_PUBLIC_KEY = 0x04535944 (prefix "spub")
           EXT_SECRET_KEY = 0x04535945 (prefix "sprv")  
  Testnet: EXT_PUBLIC_KEY = 0x04355359 (prefix "stpb")
           EXT_SECRET_KEY = 0x04355345 (prefix "stpv")
"""

import re
import hashlib

# Base58 alphabet
BASE58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def base58_decode(s):
    """Decode a Base58 string to bytes."""
    n = 0
    for c in s:
        n = n * 58 + BASE58_ALPHABET.index(c)
    
    # Convert to bytes
    h = '%x' % n
    if len(h) % 2:
        h = '0' + h
    result = bytes.fromhex(h)
    
    # Add leading zeros
    pad_size = len(s) - len(s.lstrip('1'))
    return b'\x00' * pad_size + result

def base58_encode(data):
    """Encode bytes to Base58 string."""
    n = int.from_bytes(data, 'big')
    
    result = ''
    while n > 0:
        n, remainder = divmod(n, 58)
        result = BASE58_ALPHABET[remainder] + result
    
    # Add leading 1s for leading zero bytes
    for byte in data:
        if byte == 0:
            result = '1' + result
        else:
            break
    
    return result

def double_sha256(data):
    """Compute double SHA256."""
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def decode_bip32_key(key_str):
    """Decode a BIP32 key and return raw bytes and version."""
    decoded = base58_decode(key_str)
    # Remove 4-byte checksum
    payload = decoded[:-4]
    checksum = decoded[-4:]
    
    # Verify checksum
    expected_checksum = double_sha256(payload)[:4]
    if checksum != expected_checksum:
        raise ValueError(f"Invalid checksum for {key_str}")
    
    version = payload[:4]
    rest = payload[4:]
    
    return version, rest

def encode_bip32_key(version, rest):
    """Encode version + rest to BIP32 key string."""
    payload = version + rest
    checksum = double_sha256(payload)[:4]
    return base58_encode(payload + checksum)

# Bitcoin version bytes
BITCOIN_XPUB = bytes([0x04, 0x88, 0xB2, 0x1E])  # xpub
BITCOIN_XPRV = bytes([0x04, 0x88, 0xAD, 0xE4])  # xprv
BITCOIN_TPUB = bytes([0x04, 0x35, 0x87, 0xCF])  # tpub
BITCOIN_TPRV = bytes([0x04, 0x35, 0x83, 0x94])  # tprv

# OpenSY version bytes (from chainparams.cpp)
# Mainnet: produces "spub" and "sprv" prefixes
OPENSY_XPUB = bytes([0x04, 0x53, 0x59, 0x4C])  # spub
OPENSY_XPRV = bytes([0x04, 0x53, 0x59, 0x45])  # sprv
# Testnet: produces "stpb" and "stpv" prefixes
OPENSY_TPUB = bytes([0x04, 0x35, 0x53, 0x59])  # stpb
OPENSY_TPRV = bytes([0x04, 0x35, 0x53, 0x45])  # stpv

def convert_key(key_str):
    """Convert a Bitcoin BIP32 key to OpenSY format."""
    try:
        version, rest = decode_bip32_key(key_str)
    except Exception as e:
        print(f"Warning: Could not decode {key_str}: {e}")
        return None
    
    # Determine new version
    if version == BITCOIN_XPUB:
        new_version = OPENSY_XPUB
    elif version == BITCOIN_XPRV:
        new_version = OPENSY_XPRV
    elif version == BITCOIN_TPUB:
        new_version = OPENSY_TPUB
    elif version == BITCOIN_TPRV:
        new_version = OPENSY_TPRV
    else:
        print(f"Unknown version {version.hex()} for {key_str}")
        return None
    
    return encode_bip32_key(new_version, rest)

def process_file(input_path, output_path=None):
    """Process a C++ file and convert all BIP32 keys."""
    if output_path is None:
        output_path = input_path
    
    with open(input_path, 'r') as f:
        content = f.read()
    
    # Find all potential BIP32 keys (xpub, xprv, tpub, tprv followed by base58 chars)
    pattern = r'\b(xpub[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{79,112})\b'
    pattern_xprv = r'\b(xprv[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{79,112})\b'
    pattern_tpub = r'\b(tpub[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{79,112})\b'
    pattern_tprv = r'\b(tprv[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{79,112})\b'
    
    converted_count = 0
    failed = []
    
    def replace_key(match):
        nonlocal converted_count, failed
        old_key = match.group(1)
        new_key = convert_key(old_key)
        if new_key:
            converted_count += 1
            return new_key
        else:
            failed.append(old_key)
            return old_key
    
    # Replace all patterns
    content = re.sub(pattern, replace_key, content)
    content = re.sub(pattern_xprv, replace_key, content)
    content = re.sub(pattern_tpub, replace_key, content)
    content = re.sub(pattern_tprv, replace_key, content)
    
    # Also update the CountXpubs function to look for "spub" instead of "xpub"
    content = content.replace('desc.find("xpub"', 'desc.find("spub"')
    content = content.replace('"xpub\\\\w+?(?=/)"', '"spub\\\\w+?(?=/)"')
    
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"Converted {converted_count} keys")
    if failed:
        print(f"Failed to convert {len(failed)} keys:")
        for k in failed[:10]:
            print(f"  {k[:50]}...")
    
    return converted_count, failed

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <input_file> [output_file]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    process_file(input_path, output_path)
