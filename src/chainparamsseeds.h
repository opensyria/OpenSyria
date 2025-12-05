#ifndef OPENSYRIA_CHAINPARAMSSEEDS_H
#define OPENSYRIA_CHAINPARAMSSEEDS_H
/**
 * List of fixed seed nodes for the OpenSyria network
 *
 * IMPORTANT: These arrays are intentionally empty for the initial launch.
 * OpenSyria is a new blockchain and does not have any established seed nodes yet.
 *
 * For initial network bootstrap:
 * - Use -addnode=<ip:port> to connect to known nodes
 * - Use -connect=<ip:port> to connect only to specific nodes
 *
 * Once the OpenSyria network is established, run contrib/seeds/generate-seeds.py
 * to populate these arrays with actual OpenSyria node addresses.
 *
 * Each line contains a BIP155 serialized (networkID, addr, port) tuple.
 */

// Mainnet seeds - empty until OpenSyria mainnet nodes are established
static const uint8_t chainparams_seed_main[] = {0x00};
constexpr size_t chainparams_seed_main_size = 0;

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
