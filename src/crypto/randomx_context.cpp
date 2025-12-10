// Copyright (c) 2025 The OpenSyria Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <crypto/randomx_context.h>
#include <util/check.h>

#include <randomx.h>

#include <stdexcept>

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
