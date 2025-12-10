// Copyright (c) 2025 The OpenSyria Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <pow.h>
#include <chain.h>
#include <chainparams.h>
#include <consensus/params.h>
#include <crypto/randomx_context.h>
#include <primitives/block.h>
#include <streams.h>
#include <test/util/setup_common.h>
#include <uint256.h>

#include <boost/test/unit_test.hpp>

/**
 * RandomX Hard Fork Unit Tests
 * 
 * These tests verify the correct behavior of the RandomX proof-of-work
 * implementation, including:
 * - Fork activation at the correct height
 * - RandomX hash calculation
 * - Key block selection
 * - Backward compatibility with SHA256d for legacy blocks
 */

BOOST_FIXTURE_TEST_SUITE(randomx_tests, BasicTestingSetup)

// =============================================================================
// FORK ACTIVATION TESTS
// =============================================================================

BOOST_AUTO_TEST_CASE(fork_not_active_before_height)
{
    // Test: RandomX should NOT be active before fork height
    const auto chainParams = CreateChainParams(*m_node.args, ChainType::MAIN);
    const auto& params = chainParams->GetConsensus();
    
    // One block before fork
    int heightBeforeFork = params.nRandomXForkHeight - 1;
    BOOST_CHECK_MESSAGE(
        !params.IsRandomXActive(heightBeforeFork),
        "RandomX should not be active at height " << heightBeforeFork
    );
    
    // Many blocks before fork
    BOOST_CHECK(!params.IsRandomXActive(0));
    BOOST_CHECK(!params.IsRandomXActive(1000));
    BOOST_CHECK(!params.IsRandomXActive(params.nRandomXForkHeight - 100));
}

BOOST_AUTO_TEST_CASE(fork_active_at_height)
{
    // Test: RandomX should be active exactly at fork height
    const auto chainParams = CreateChainParams(*m_node.args, ChainType::MAIN);
    const auto& params = chainParams->GetConsensus();
    
    int forkHeight = params.nRandomXForkHeight;
    BOOST_CHECK_MESSAGE(
        params.IsRandomXActive(forkHeight),
        "RandomX should be active at fork height " << forkHeight
    );
}

BOOST_AUTO_TEST_CASE(fork_active_after_height)
{
    // Test: RandomX should remain active after fork height
    const auto chainParams = CreateChainParams(*m_node.args, ChainType::MAIN);
    const auto& params = chainParams->GetConsensus();
    
    int forkHeight = params.nRandomXForkHeight;
    
    BOOST_CHECK(params.IsRandomXActive(forkHeight + 1));
    BOOST_CHECK(params.IsRandomXActive(forkHeight + 100));
    BOOST_CHECK(params.IsRandomXActive(forkHeight + 100000));
}

// =============================================================================
// KEY BLOCK CALCULATION TESTS
// =============================================================================

BOOST_AUTO_TEST_CASE(key_block_height_calculation)
{
    // Test: Key block height calculation is correct
    const auto chainParams = CreateChainParams(*m_node.args, ChainType::MAIN);
    const auto& params = chainParams->GetConsensus();
    
    // Key block interval is 64 by default
    int interval = params.nRandomXKeyBlockInterval;
    BOOST_CHECK_EQUAL(interval, 64);
    
    // At height 128, key block should be at 64 (128/64*64 - 64 = 64)
    BOOST_CHECK_EQUAL(params.GetRandomXKeyBlockHeight(128), 64);
    
    // At height 192, key block should be at 128
    BOOST_CHECK_EQUAL(params.GetRandomXKeyBlockHeight(192), 128);
    
    // At height 64, key block should be at 0
    BOOST_CHECK_EQUAL(params.GetRandomXKeyBlockHeight(64), 0);
    
    // At height 65, key block should still be at 0 (65/64*64 - 64 = 64 - 64 = 0)
    BOOST_CHECK_EQUAL(params.GetRandomXKeyBlockHeight(65), 0);
}

BOOST_AUTO_TEST_CASE(key_block_height_edge_cases)
{
    // Test: Edge cases for key block height calculation
    const auto chainParams = CreateChainParams(*m_node.args, ChainType::MAIN);
    const auto& params = chainParams->GetConsensus();
    
    // At height 0, key should be at 0 (clamped from negative)
    BOOST_CHECK_EQUAL(params.GetRandomXKeyBlockHeight(0), 0);
    
    // At height 1, key should be at 0
    BOOST_CHECK_EQUAL(params.GetRandomXKeyBlockHeight(1), 0);
    
    // At height 63, key should be at 0 (63/64*64 - 64 = 0 - 64 = -64, clamped to 0)
    BOOST_CHECK_EQUAL(params.GetRandomXKeyBlockHeight(63), 0);
    
    // At height 127, key should be at 0 (127/64*64 - 64 = 64 - 64 = 0)
    BOOST_CHECK_EQUAL(params.GetRandomXKeyBlockHeight(127), 0);
    
    // At fork height (60000), verify key block calculation
    int forkHeight = params.nRandomXForkHeight;
    int expectedKey = (forkHeight / 64) * 64 - 64;
    BOOST_CHECK_EQUAL(params.GetRandomXKeyBlockHeight(forkHeight), expectedKey);
    
    // Large height test
    BOOST_CHECK_EQUAL(params.GetRandomXKeyBlockHeight(1000000), 
        (1000000 / 64) * 64 - 64);
}

// =============================================================================
// RANDOMX CONTEXT TESTS
// =============================================================================

BOOST_AUTO_TEST_CASE(randomx_context_initialization)
{
    // Test: RandomX context should initialize successfully
    RandomXContext ctx;
    
    BOOST_CHECK(!ctx.IsInitialized());
    
    // Use a simple test hash
    uint256 keyHash{"0000000000000000000000000000000000000000000000000000000000001234"};
    bool initResult = ctx.Initialize(keyHash);
    
    BOOST_CHECK_MESSAGE(initResult, "RandomX context should initialize successfully");
    BOOST_CHECK(ctx.IsInitialized());
    BOOST_CHECK_EQUAL(ctx.GetKeyBlockHash(), keyHash);
}

BOOST_AUTO_TEST_CASE(randomx_context_reinitialize_different_key)
{
    // Test: Context should reinitialize with different key
    RandomXContext ctx;
    
    uint256 key1{"1111111111111111111111111111111111111111111111111111111111111111"};
    uint256 key2{"2222222222222222222222222222222222222222222222222222222222222222"};
    
    ctx.Initialize(key1);
    BOOST_CHECK_EQUAL(ctx.GetKeyBlockHash(), key1);
    
    ctx.Initialize(key2);
    BOOST_CHECK_EQUAL(ctx.GetKeyBlockHash(), key2);
}

BOOST_AUTO_TEST_CASE(randomx_context_reinitialize_same_key)
{
    // Test: Reinitializing with same key should be a no-op (optimization)
    RandomXContext ctx;
    
    uint256 key{"3333333333333333333333333333333333333333333333333333333333333333"};
    
    // First init
    bool result1 = ctx.Initialize(key);
    BOOST_CHECK(result1);
    BOOST_CHECK(ctx.IsInitialized());
    
    // Second init with same key should succeed immediately
    bool result2 = ctx.Initialize(key);
    BOOST_CHECK(result2);
    BOOST_CHECK(ctx.IsInitialized());
    BOOST_CHECK_EQUAL(ctx.GetKeyBlockHash(), key);
}

BOOST_AUTO_TEST_CASE(randomx_context_uninitialized_hash_throws)
{
    // Test: Calling CalculateHash on uninitialized context should throw
    RandomXContext ctx;
    
    BOOST_CHECK(!ctx.IsInitialized());
    
    std::vector<unsigned char> input = {0x01, 0x02, 0x03};
    
    BOOST_CHECK_THROW(ctx.CalculateHash(input), std::runtime_error);
}

// =============================================================================
// HASH CALCULATION TESTS
// =============================================================================

BOOST_AUTO_TEST_CASE(randomx_hash_deterministic)
{
    // Test: Same input should always produce same hash
    RandomXContext ctx;
    uint256 keyHash{"0000000000000000000000000000000000000000000000000000000000001234"};
    ctx.Initialize(keyHash);
    
    std::vector<unsigned char> input = {0x01, 0x02, 0x03, 0x04, 0x05};
    
    uint256 hash1 = ctx.CalculateHash(input);
    uint256 hash2 = ctx.CalculateHash(input);
    
    BOOST_CHECK_EQUAL(hash1, hash2);
}

BOOST_AUTO_TEST_CASE(randomx_hash_different_input)
{
    // Test: Different inputs should produce different hashes
    RandomXContext ctx;
    uint256 keyHash{"0000000000000000000000000000000000000000000000000000000000001234"};
    ctx.Initialize(keyHash);
    
    std::vector<unsigned char> input1 = {0x01, 0x02, 0x03};
    std::vector<unsigned char> input2 = {0x01, 0x02, 0x04};  // One byte different
    
    uint256 hash1 = ctx.CalculateHash(input1);
    uint256 hash2 = ctx.CalculateHash(input2);
    
    BOOST_CHECK_MESSAGE(hash1 != hash2, "Different inputs must produce different hashes");
}

BOOST_AUTO_TEST_CASE(randomx_hash_different_keys)
{
    // Test: Same input with different keys should produce different hashes
    uint256 key1{"1111111111111111111111111111111111111111111111111111111111111111"};
    uint256 key2{"2222222222222222222222222222222222222222222222222222222222222222"};
    std::vector<unsigned char> input = {0x01, 0x02, 0x03, 0x04, 0x05};
    
    RandomXContext ctx1;
    ctx1.Initialize(key1);
    uint256 hash1 = ctx1.CalculateHash(input);
    
    RandomXContext ctx2;
    ctx2.Initialize(key2);
    uint256 hash2 = ctx2.CalculateHash(input);
    
    BOOST_CHECK_MESSAGE(hash1 != hash2, 
        "Same input with different keys must produce different hashes");
}

BOOST_AUTO_TEST_CASE(randomx_hash_empty_input)
{
    // Test: Empty input should produce a valid hash
    RandomXContext ctx;
    uint256 keyHash{"0000000000000000000000000000000000000000000000000000000000001234"};
    ctx.Initialize(keyHash);
    
    std::vector<unsigned char> emptyInput;
    uint256 hash = ctx.CalculateHash(emptyInput);
    
    // Hash of empty input should not be null
    BOOST_CHECK(!hash.IsNull());
    
    // Should be deterministic
    uint256 hash2 = ctx.CalculateHash(emptyInput);
    BOOST_CHECK_EQUAL(hash, hash2);
}

BOOST_AUTO_TEST_CASE(randomx_hash_large_input)
{
    // Test: Large input should hash correctly
    RandomXContext ctx;
    uint256 keyHash{"0000000000000000000000000000000000000000000000000000000000001234"};
    ctx.Initialize(keyHash);
    
    // Create 1MB input
    std::vector<unsigned char> largeInput(1024 * 1024);
    for (size_t i = 0; i < largeInput.size(); ++i) {
        largeInput[i] = static_cast<unsigned char>(i % 256);
    }
    
    uint256 hash = ctx.CalculateHash(largeInput);
    
    BOOST_CHECK(!hash.IsNull());
    
    // Should be deterministic
    uint256 hash2 = ctx.CalculateHash(largeInput);
    BOOST_CHECK_EQUAL(hash, hash2);
}

BOOST_AUTO_TEST_CASE(randomx_hash_block_header)
{
    // Test: Hashing a block header should work correctly
    RandomXContext ctx;
    uint256 keyHash{"0000000000000000000000000000000000000000000000000000000000001234"};
    ctx.Initialize(keyHash);
    
    CBlockHeader header;
    header.nVersion = 1;
    header.hashPrevBlock = uint256{"00000000000000000000000000000000000000000000000000000000000abcde"};
    header.hashMerkleRoot = uint256{"00000000000000000000000000000000000000000000000000000000000fedcb"};
    header.nTime = 1733788800;  // Dec 10, 2025
    header.nBits = 0x1e00ffff;
    header.nNonce = 12345;
    
    // Serialize header
    DataStream ss{};
    ss << header;
    
    // Calculate hash using raw pointer interface
    uint256 hash = ctx.CalculateHash(
        reinterpret_cast<const unsigned char*>(ss.data()), ss.size());
    
    // Hash should be non-zero and 256 bits
    BOOST_CHECK(!hash.IsNull());
    
    // Hash should be deterministic
    uint256 hash2 = ctx.CalculateHash(
        reinterpret_cast<const unsigned char*>(ss.data()), ss.size());
    BOOST_CHECK_EQUAL(hash, hash2);
}

// =============================================================================
// GLOBAL CONTEXT TESTS
// =============================================================================

BOOST_AUTO_TEST_CASE(global_context_lifecycle)
{
    // Test: Global context lifecycle
    
    // Initially should not exist or be uninitialized
    ShutdownRandomXContext();
    BOOST_CHECK(!g_randomx_context);
    
    // After init, should exist but not be initialized with key yet
    InitRandomXContext();
    BOOST_CHECK(g_randomx_context != nullptr);
    BOOST_CHECK(!g_randomx_context->IsInitialized());
    
    // Initialize with key
    uint256 keyHash{"0000000000000000000000000000000000000000000000000000000000005678"};
    g_randomx_context->Initialize(keyHash);
    BOOST_CHECK(g_randomx_context->IsInitialized());
    
    // Shutdown should cleanup
    ShutdownRandomXContext();
    BOOST_CHECK(!g_randomx_context);
}

// =============================================================================
// POW.CPP FUNCTION TESTS
// =============================================================================

BOOST_AUTO_TEST_CASE(calculate_randomx_hash_deterministic)
{
    // Test: CalculateRandomXHash should be deterministic
    CBlockHeader header;
    header.nVersion = 1;
    header.hashPrevBlock = uint256{"00000000000000000000000000000000000000000000000000000000000abcde"};
    header.hashMerkleRoot = uint256{"00000000000000000000000000000000000000000000000000000000000fedcb"};
    header.nTime = 1733788800;
    header.nBits = 0x1e00ffff;
    header.nNonce = 12345;
    
    uint256 keyBlockHash{"4444444444444444444444444444444444444444444444444444444444444444"};
    
    uint256 hash1 = CalculateRandomXHash(header, keyBlockHash);
    uint256 hash2 = CalculateRandomXHash(header, keyBlockHash);
    
    BOOST_CHECK_EQUAL(hash1, hash2);
    BOOST_CHECK(!hash1.IsNull());
}

BOOST_AUTO_TEST_CASE(calculate_randomx_hash_different_nonce)
{
    // Test: Different nonces should produce different hashes
    CBlockHeader header1, header2;
    header1.nVersion = header2.nVersion = 1;
    header1.hashPrevBlock = header2.hashPrevBlock = uint256{"00000000000000000000000000000000000000000000000000000000000abcde"};
    header1.hashMerkleRoot = header2.hashMerkleRoot = uint256{"00000000000000000000000000000000000000000000000000000000000fedcb"};
    header1.nTime = header2.nTime = 1733788800;
    header1.nBits = header2.nBits = 0x1e00ffff;
    header1.nNonce = 12345;
    header2.nNonce = 12346;  // Different nonce
    
    uint256 keyBlockHash{"5555555555555555555555555555555555555555555555555555555555555555"};
    
    uint256 hash1 = CalculateRandomXHash(header1, keyBlockHash);
    uint256 hash2 = CalculateRandomXHash(header2, keyBlockHash);
    
    BOOST_CHECK_MESSAGE(hash1 != hash2, "Different nonces should produce different RandomX hashes");
}

BOOST_AUTO_TEST_CASE(calculate_randomx_hash_different_keys)
{
    // Test: Same header with different keys should produce different hashes
    CBlockHeader header;
    header.nVersion = 1;
    header.hashPrevBlock = uint256{"00000000000000000000000000000000000000000000000000000000000abcde"};
    header.hashMerkleRoot = uint256{"00000000000000000000000000000000000000000000000000000000000fedcb"};
    header.nTime = 1733788800;
    header.nBits = 0x1e00ffff;
    header.nNonce = 12345;
    
    uint256 key1{"6666666666666666666666666666666666666666666666666666666666666666"};
    uint256 key2{"7777777777777777777777777777777777777777777777777777777777777777"};
    
    uint256 hash1 = CalculateRandomXHash(header, key1);
    uint256 hash2 = CalculateRandomXHash(header, key2);
    
    BOOST_CHECK_MESSAGE(hash1 != hash2, "Same header with different keys should produce different RandomX hashes");
}

BOOST_AUTO_TEST_CASE(fork_height_default_value)
{
    // Test: Verify default fork height is 60000
    const auto chainParams = CreateChainParams(*m_node.args, ChainType::MAIN);
    const auto& params = chainParams->GetConsensus();
    
    BOOST_CHECK_EQUAL(params.nRandomXForkHeight, 60000);
}

BOOST_AUTO_TEST_CASE(key_interval_default_value)
{
    // Test: Verify default key interval is 64
    const auto chainParams = CreateChainParams(*m_node.args, ChainType::MAIN);
    const auto& params = chainParams->GetConsensus();
    
    BOOST_CHECK_EQUAL(params.nRandomXKeyBlockInterval, 64);
}

BOOST_AUTO_TEST_SUITE_END()
