// Copyright (c) 2022 The OpenSyria Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#ifndef OPENSYRIA_POLICY_FEES_BLOCK_POLICY_ESTIMATOR_ARGS_H
#define OPENSYRIA_POLICY_FEES_BLOCK_POLICY_ESTIMATOR_ARGS_H

#include <util/fs.h>

class ArgsManager;

/** @return The fee estimates data file path. */
fs::path FeeestPath(const ArgsManager& argsman);

#endif // OPENSYRIA_POLICY_FEES_BLOCK_POLICY_ESTIMATOR_ARGS_H
