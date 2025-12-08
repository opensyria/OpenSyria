#ifndef OPENSYRIA_CHAINPARAMSSEEDS_H
#define OPENSYRIA_CHAINPARAMSSEEDS_H
/**
 * List of fixed seed nodes for the OpenSyria network
 * Generated: December 8, 2025 - Network Launch Day! 🇸🇾
 *
 * Each line contains a BIP155 serialized (networkID, addr, port) tuple.
 * Format: 0x01 (IPv4), 4 bytes IP, 2 bytes port (big-endian)
 */

// Mainnet seeds - First OpenSyria seed node!
// 157.175.40.131:9633 (node1.opensyria.net, AWS Bahrain)
static const uint8_t chainparams_seed_main[] = {
    0x01,                         // IPv4 network ID
    0x9d, 0xaf, 0x28, 0x83,       // 157.175.40.131
    0x25, 0xa1                    // Port 9633 (0x25a1)
};
constexpr size_t chainparams_seed_main_size = 1;

// Signet seeds - empty until OpenSyria signet nodes are established
static const uint8_t chainparams_seed_signet[] = {0x00};
constexpr size_t chainparams_seed_signet_size = 0;

// Testnet seeds - empty until OpenSyria testnet nodes are established
static const uint8_t chainparams_seed_test[] = {0x00};
constexpr size_t chainparams_seed_test_size = 0;

// Testnet4 seeds - empty until OpenSyria testnet4 nodes are established
static const uint8_t chainparams_seed_testnet4[] = {0x00};
constexpr size_t chainparams_seed_testnet4_size = 0;

#endif // OPENSYRIA_CHAINPARAMSSEEDS_H
