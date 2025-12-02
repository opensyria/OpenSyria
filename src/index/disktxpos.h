// Copyright (c) 2019-2020 The OpenSyria Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#ifndef OPENSYRIA_INDEX_DISKTXPOS_H
#define OPENSYRIA_INDEX_DISKTXPOS_H

#include <flatfile.h>
#include <serialize.h>

struct CDiskTxPos : public FlatFilePos
{
    uint32_t nTxOffset{0}; // after header

    SERIALIZE_METHODS(CDiskTxPos, obj)
    {
        READWRITE(AsBase<FlatFilePos>(obj), VARINT(obj.nTxOffset));
    }

    CDiskTxPos(const FlatFilePos& blockIn, uint32_t nTxOffsetIn) : FlatFilePos{blockIn.nFile, blockIn.nPos}, nTxOffset{nTxOffsetIn} {
    }

    CDiskTxPos() = default;
};

#endif // OPENSYRIA_INDEX_DISKTXPOS_H
