// Copyright (c) 2025 The OpenSY developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <crypto/randomx_pool.h>
#include <logging.h>
#include <util/check.h>

#include <algorithm>

RandomXContextPool g_randomx_pool;

RandomXContextPool::RandomXContextPool() = default;

RandomXContextPool::~RandomXContextPool()
{
    LOCK(m_mutex);
    m_pool.clear();
}

std::optional<RandomXContextPool::ContextGuard> RandomXContextPool::Acquire(const uint256& keyBlockHash)
{
    WAIT_LOCK(m_mutex, lock);

    auto deadline = std::chrono::steady_clock::now() + ACQUIRE_TIMEOUT;

    while (true) {
        size_t index = FindOrCreateContext(keyBlockHash);

        if (index != SIZE_MAX) {
            // Found or created a context
            m_pool[index].in_use = true;
            m_pool[index].last_used = std::chrono::steady_clock::now();
            m_total_acquisitions++;

            // Initialize or reinitialize if key changed
            if (m_pool[index].key_hash != keyBlockHash) {
                if (!m_pool[index].context->Initialize(keyBlockHash)) {
                    // Initialization failed - mark as not in use and return error
                    m_pool[index].in_use = false;
                    m_cv.notify_one();
                    return std::nullopt;
                }
                m_pool[index].key_hash = keyBlockHash;
                m_key_reinitializations++;
            }

            return ContextGuard(m_pool[index].context.get(), *this, index);
        }

        // All contexts are in use - wait for one to become available
        m_total_waits++;

        if (m_cv.wait_until(lock, deadline) == std::cv_status::timeout) {
            m_total_timeouts++;
            LogPrintf("RandomXContextPool: Timeout waiting for context (active=%zu)\n",
                std::count_if(m_pool.begin(), m_pool.end(), [](const PoolEntry& e) { return e.in_use; }));
            return std::nullopt;
        }
    }
}

size_t RandomXContextPool::FindOrCreateContext(const uint256& keyBlockHash)
{
    AssertLockHeld(m_mutex);

    // First, look for an available context with matching key (best case)
    for (size_t i = 0; i < m_pool.size(); ++i) {
        if (!m_pool[i].in_use && m_pool[i].key_hash == keyBlockHash) {
            return i;
        }
    }

    // Second, look for any available context
    for (size_t i = 0; i < m_pool.size(); ++i) {
        if (!m_pool[i].in_use) {
            return i;
        }
    }

    // Third, if pool isn't full, create a new context
    if (m_pool.size() < m_max_contexts) {
        PoolEntry entry;
        entry.context = std::make_unique<RandomXContext>();
        entry.in_use = false;
        m_pool.push_back(std::move(entry));
        return m_pool.size() - 1;
    }

    // Pool is full and all contexts are in use
    return SIZE_MAX;
}

void RandomXContextPool::Return(size_t index)
{
    if (index == SIZE_MAX) return;

    {
        LOCK(m_mutex);
        if (index < m_pool.size()) {
            m_pool[index].in_use = false;
            m_pool[index].last_used = std::chrono::steady_clock::now();
        }
    }
    m_cv.notify_one();
}

RandomXContextPool::PoolStats RandomXContextPool::GetStats() const
{
    LOCK(m_mutex);

    PoolStats stats;
    stats.total_contexts = m_pool.size();
    stats.active_contexts = std::count_if(m_pool.begin(), m_pool.end(),
        [](const PoolEntry& e) { return e.in_use; });
    stats.available_contexts = stats.total_contexts - stats.active_contexts;
    stats.total_acquisitions = m_total_acquisitions;
    stats.total_waits = m_total_waits;
    stats.total_timeouts = m_total_timeouts;
    stats.key_reinitializations = m_key_reinitializations;

    return stats;
}

bool RandomXContextPool::SetMaxContexts(size_t max_contexts)
{
    LOCK(m_mutex);

    // Can only change before any contexts are created
    if (!m_pool.empty()) {
        return false;
    }

    if (max_contexts == 0 || max_contexts > 64) {
        return false;  // Sanity bounds
    }

    m_max_contexts = max_contexts;
    return true;
}
