// Copyright (c) 2025 The OpenSyria Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <crypto/randomx_context.h>
#include <logging.h>
#include <util/check.h>

#include <randomx.h>

#include <chrono>
#include <stdexcept>
#include <thread>
#include <vector>

std::unique_ptr<RandomXContext> g_randomx_context;

void RandomXContext::Cleanup()
{
    AssertLockHeld(m_mutex);

    if (m_vm) {
        randomx_destroy_vm(m_vm);
        m_vm = nullptr;
    }
    if (m_cache) {
        randomx_release_cache(m_cache);
        m_cache = nullptr;
    }
    m_initialized = false;
    m_keyBlockHash = uint256();
}

RandomXContext::~RandomXContext()
{
    LOCK(m_mutex);
    Cleanup();
}

bool RandomXContext::Initialize(const uint256& keyBlockHash)
{
    LOCK(m_mutex);

    // Skip if already initialized with same key
    if (m_initialized && m_keyBlockHash == keyBlockHash) {
        return true;
    }

    // Cleanup any existing state
    Cleanup();

    // Create cache with light mode flags (suitable for validation)
    // RANDOMX_FLAG_DEFAULT uses the best available optimization for this CPU
    randomx_flags flags = randomx_get_flags();
    // Light mode uses less memory (256KB vs 2GB) suitable for validation
    flags = static_cast<randomx_flags>(flags | RANDOMX_FLAG_DEFAULT);

    m_cache = randomx_alloc_cache(flags);
    if (!m_cache) {
        return false;
    }

    // Initialize cache with key (block hash bytes)
    randomx_init_cache(m_cache, keyBlockHash.begin(), keyBlockHash.size());

    // Create VM in light mode
    m_vm = randomx_create_vm(flags, m_cache, nullptr);
    if (!m_vm) {
        randomx_release_cache(m_cache);
        m_cache = nullptr;
        return false;
    }

    m_keyBlockHash = keyBlockHash;
    m_initialized = true;

    return true;
}

uint256 RandomXContext::CalculateHash(const std::vector<unsigned char>& input)
{
    LOCK(m_mutex);

    if (!m_initialized || !m_vm) {
        throw std::runtime_error("RandomX context not initialized");
    }

    // RandomX produces a 256-bit (32-byte) hash
    uint256 result;
    randomx_calculate_hash(m_vm, input.data(), input.size(), result.begin());

    return result;
}

uint256 RandomXContext::CalculateHash(const unsigned char* data, size_t len)
{
    LOCK(m_mutex);

    if (!m_initialized || !m_vm) {
        throw std::runtime_error("RandomX context not initialized");
    }

    // RandomX produces a 256-bit (32-byte) hash
    uint256 result;
    randomx_calculate_hash(m_vm, data, len, result.begin());

    return result;
}

bool RandomXContext::IsInitialized() const
{
    LOCK(m_mutex);
    return m_initialized;
}

uint256 RandomXContext::GetKeyBlockHash() const
{
    LOCK(m_mutex);
    return m_keyBlockHash;
}

randomx_cache* RandomXContext::GetCache() const
{
    LOCK(m_mutex);
    return m_cache;
}

randomx_flags_int RandomXContext::GetFlags() const
{
    LOCK(m_mutex);
    return static_cast<randomx_flags_int>(randomx_get_flags());
}

// ============================================================================
// RandomXMiningContext - Full dataset mode for efficient mining
// ============================================================================

void RandomXMiningContext::Cleanup()
{
    AssertLockHeld(m_mutex);

    if (m_dataset) {
        randomx_release_dataset(m_dataset);
        m_dataset = nullptr;
    }
    if (m_cache) {
        randomx_release_cache(m_cache);
        m_cache = nullptr;
    }
    m_initialized = false;
    m_keyBlockHash = uint256();
}

RandomXMiningContext::~RandomXMiningContext()
{
    LOCK(m_mutex);
    Cleanup();
}

bool RandomXMiningContext::Initialize(const uint256& keyBlockHash, unsigned int numThreads)
{
    LOCK(m_mutex);

    // Skip if already initialized with same key
    if (m_initialized && m_keyBlockHash == keyBlockHash) {
        return true;
    }

    // Cleanup any existing state
    Cleanup();

    LogPrintf("RandomX Mining: Initializing with %u threads...\n", numThreads);
    auto startTime = std::chrono::steady_clock::now();

    // Get optimal flags for this CPU
    m_flags = static_cast<randomx_flags_int>(randomx_get_flags());
    // Enable full memory mode for mining (uses ~2GB but much faster)
    m_flags = m_flags | RANDOMX_FLAG_FULL_MEM;

    // Allocate cache
    m_cache = randomx_alloc_cache(static_cast<randomx_flags>(m_flags));
    if (!m_cache) {
        LogPrintf("RandomX Mining: Failed to allocate cache\n");
        return false;
    }

    // Initialize cache with key
    randomx_init_cache(m_cache, keyBlockHash.begin(), keyBlockHash.size());

    // Allocate dataset (~2GB)
    m_dataset = randomx_alloc_dataset(static_cast<randomx_flags>(m_flags));
    if (!m_dataset) {
        LogPrintf("RandomX Mining: Failed to allocate dataset (need ~2GB RAM)\n");
        randomx_release_cache(m_cache);
        m_cache = nullptr;
        return false;
    }

    // Initialize dataset using multiple threads
    unsigned long datasetItemCount = randomx_dataset_item_count();
    if (numThreads > 1) {
        std::vector<std::thread> initThreads;
        unsigned long itemsPerThread = datasetItemCount / numThreads;
        
        for (unsigned int i = 0; i < numThreads; ++i) {
            unsigned long startItem = i * itemsPerThread;
            unsigned long itemCount = (i == numThreads - 1) 
                ? (datasetItemCount - startItem) 
                : itemsPerThread;
            
            initThreads.emplace_back([this, startItem, itemCount]() {
                randomx_init_dataset(m_dataset, m_cache, startItem, itemCount);
            });
        }
        
        for (auto& t : initThreads) {
            t.join();
        }
    } else {
        randomx_init_dataset(m_dataset, m_cache, 0, datasetItemCount);
    }

    m_keyBlockHash = keyBlockHash;
    m_initialized = true;

    auto endTime = std::chrono::steady_clock::now();
    auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(endTime - startTime).count();
    LogPrintf("RandomX Mining: Initialized in %lld ms\n", elapsed);

    return true;
}

randomx_vm* RandomXMiningContext::CreateVM()
{
    LOCK(m_mutex);
    
    if (!m_initialized || !m_dataset) {
        return nullptr;
    }

    // Create VM with full dataset (fast mode)
    // Each thread gets its own VM but shares the dataset (read-only)
    return randomx_create_vm(static_cast<randomx_flags>(m_flags), nullptr, m_dataset);
}

bool RandomXMiningContext::IsInitialized() const
{
    LOCK(m_mutex);
    return m_initialized;
}

uint256 RandomXMiningContext::GetKeyBlockHash() const
{
    LOCK(m_mutex);
    return m_keyBlockHash;
}

void InitRandomXContext()
{
    if (!g_randomx_context) {
        g_randomx_context = std::make_unique<RandomXContext>();
    }
}

void ShutdownRandomXContext()
{
    if (g_randomx_context) {
        g_randomx_context.reset();
    }
}
