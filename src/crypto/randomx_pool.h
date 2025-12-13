// Copyright (c) 2025 The OpenSyria Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#ifndef OPENSYRIA_CRYPTO_RANDOMX_POOL_H
#define OPENSYRIA_CRYPTO_RANDOMX_POOL_H

#include <crypto/randomx_context.h>
#include <sync.h>
#include <uint256.h>
#include <util/time.h>

#include <chrono>
#include <condition_variable>
#include <memory>
#include <optional>
#include <vector>

/**
 * A bounded pool of RandomX contexts to prevent unbounded memory growth.
 *
 * SECURITY FIX [H-01]: Thread-Local RandomX Context Memory Accumulation
 *
 * Previously, each thread had its own thread_local RandomX context (~256KB each),
 * leading to unbounded memory growth under high concurrency. This pool:
 *
 * 1. Limits the total number of contexts to MAX_CONTEXTS
 * 2. Uses RAII guards for automatic checkout/checkin
 * 3. Implements key-aware context reuse (LRU eviction)
 * 4. Blocks threads when pool is exhausted (bounded memory)
 *
 * Usage:
 *   auto guard = g_randomx_pool.Acquire(keyBlockHash);
 *   uint256 hash = guard->CalculateHash(data, len);
 *   // Context automatically returned to pool when guard destructs
 */
class RandomXContextPool
{
public:
    //! Maximum number of contexts in the pool
    //! Tune based on expected parallelism and available memory
    //! 8 contexts * 256KB = 2MB maximum memory usage
    static constexpr size_t MAX_CONTEXTS = 8;

    //! Timeout for acquiring a context (prevents deadlock)
    static constexpr std::chrono::seconds ACQUIRE_TIMEOUT{30};

    /**
     * RAII guard that holds a context and returns it to the pool on destruction.
     */
    class ContextGuard
    {
    public:
        ContextGuard(RandomXContext* ctx, RandomXContextPool& pool, size_t index)
            : m_ctx(ctx), m_pool(pool), m_index(index) {}

        ~ContextGuard() { m_pool.Return(m_index); }

        // Non-copyable
        ContextGuard(const ContextGuard&) = delete;
        ContextGuard& operator=(const ContextGuard&) = delete;

        // Movable
        ContextGuard(ContextGuard&& other) noexcept
            : m_ctx(other.m_ctx), m_pool(other.m_pool), m_index(other.m_index)
        {
            other.m_ctx = nullptr;
            other.m_index = SIZE_MAX;
        }

        ContextGuard& operator=(ContextGuard&&) = delete;

        //! Access the underlying context
        RandomXContext* operator->() const { return m_ctx; }
        RandomXContext& operator*() const { return *m_ctx; }
        RandomXContext* get() const { return m_ctx; }

    private:
        RandomXContext* m_ctx;
        RandomXContextPool& m_pool;
        size_t m_index;
    };

    RandomXContextPool();
    ~RandomXContextPool();

    // Non-copyable, non-movable
    RandomXContextPool(const RandomXContextPool&) = delete;
    RandomXContextPool& operator=(const RandomXContextPool&) = delete;

    /**
     * Acquire a context from the pool, initialized with the given key.
     *
     * If the pool is exhausted, this will block until a context becomes available
     * or the timeout expires.
     *
     * @param[in] keyBlockHash The RandomX key block hash
     * @return A guard holding the context, or nullopt on timeout
     */
    std::optional<ContextGuard> Acquire(const uint256& keyBlockHash);

    /**
     * Get current pool statistics for monitoring.
     */
    struct PoolStats {
        size_t total_contexts;      //!< Total contexts created
        size_t active_contexts;     //!< Currently checked out
        size_t available_contexts;  //!< Ready for use
        size_t total_acquisitions;  //!< Total successful acquires
        size_t total_waits;         //!< Times a thread had to wait
        size_t total_timeouts;      //!< Times acquisition timed out
        size_t key_reinitializations; //!< Times a context was reinitialized for new key
    };

    PoolStats GetStats() const;

    /**
     * Configure the maximum number of contexts.
     * Can only be called before any contexts are acquired.
     */
    bool SetMaxContexts(size_t max_contexts);

private:
    struct PoolEntry {
        std::unique_ptr<RandomXContext> context;
        uint256 key_hash;
        std::chrono::steady_clock::time_point last_used;
        bool in_use{false};
    };

    mutable Mutex m_mutex;
    std::condition_variable m_cv;
    std::vector<PoolEntry> m_pool GUARDED_BY(m_mutex);
    size_t m_max_contexts GUARDED_BY(m_mutex){MAX_CONTEXTS};

    // Statistics
    size_t m_total_acquisitions GUARDED_BY(m_mutex){0};
    size_t m_total_waits GUARDED_BY(m_mutex){0};
    size_t m_total_timeouts GUARDED_BY(m_mutex){0};
    size_t m_key_reinitializations GUARDED_BY(m_mutex){0};

    /**
     * Return a context to the pool.
     * Called by ContextGuard destructor.
     */
    void Return(size_t index);

    /**
     * Find or create a context for the given key.
     * Returns the index of the context, or SIZE_MAX if none available.
     */
    size_t FindOrCreateContext(const uint256& keyBlockHash) EXCLUSIVE_LOCKS_REQUIRED(m_mutex);
};

//! Global RandomX context pool instance
extern RandomXContextPool g_randomx_pool;

#endif // OPENSYRIA_CRYPTO_RANDOMX_POOL_H
