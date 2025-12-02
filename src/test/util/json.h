// Copyright (c) 2023-present The OpenSyria Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#ifndef OPENSYRIA_TEST_UTIL_JSON_H
#define OPENSYRIA_TEST_UTIL_JSON_H

#include <univalue.h>

#include <string_view>

UniValue read_json(std::string_view jsondata);

#endif // OPENSYRIA_TEST_UTIL_JSON_H
