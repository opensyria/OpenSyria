// Copyright (c) 2017-2022 The OpenSyria Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#ifndef OPENSYRIA_RPC_MEMPOOL_H
#define OPENSYRIA_RPC_MEMPOOL_H

class CTxMemPool;
class UniValue;

/** Mempool information to JSON */
UniValue MempoolInfoToJSON(const CTxMemPool& pool);

/** Mempool to JSON */
UniValue MempoolToJSON(const CTxMemPool& pool, bool verbose = false, bool include_mempool_sequence = false);

#endif // OPENSYRIA_RPC_MEMPOOL_H
