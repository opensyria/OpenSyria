#!/usr/bin/env python3
# Copyright (c) 2023 The OpenSyria Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Test validateaddress for main chain"""

from test_framework.test_framework import OpenSyriaTestFramework

from test_framework.util import assert_equal

INVALID_DATA = [
    # BIP 173
    (
        "tc1qw508d6qejxtdg4y5r3zarvary0c5xw7kg3g4ty",
        "Invalid or unsupported Segwit (Bech32) or Base58 encoding.",  # Invalid hrp
        [],
    ),
    ("syl1qw508d6qejxtdg4y5r3zarvary0c5xw7k6tacws", "Invalid Bech32 checksum", [41]),
    (
        "BC13W508D6QEJXTDG4Y5R3ZARVARY0C5XW7KN40WF2",
        "Version 1+ witness address must use Bech32m checksum",
        [],
    ),
    (
        "syl1rw5cdvw6h",
        "Version 1+ witness address must use Bech32m checksum",  # Invalid program length
        [],
    ),
    (
        "syl10w508d6qejxtdg4y5r3zarvary0c5xw7kw508d6qejxtdg4y5r3zarvary0c5xw7kw5x4c2zj",
        "Version 1+ witness address must use Bech32m checksum",  # Invalid program length
        [],
    ),
    (
        "BC1QR508D6QEJXTDG4Y5R3ZARVARYV98GJ9P",
        "Invalid Bech32 v0 address program size (16 bytes), per BIP141",
        [],
    ),
    (
        "tsyl1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysq5kvxfL5k7",
        "Invalid or unsupported Segwit (Bech32) or Base58 encoding.",  # tb1, Mixed case
        [],
    ),
    (
        "BC1QW508D6QEJXTDG4Y5R3ZARVARY0C5XW7KV8F3t4",
        "Invalid character or mixed case",  # bc1, Mixed case, not in BIP 173 test vectors
        [40],
    ),
    (
        "syl1zw508d6qejxtdg4y5r3zarvaryvq88gvzn",
        "Version 1+ witness address must use Bech32m checksum",  # Wrong padding
        [],
    ),
    (
        "tsyl1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3ptu70wl",
        "Invalid or unsupported Segwit (Bech32) or Base58 encoding.",  # tb1, Non-zero padding in 8-to-5 conversion
        [],
    ),
    ("syl1smsmsx", "Empty Bech32 data section", []),
    # BIP 350
    (
        "tc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vq5zuyut",
        "Invalid or unsupported Segwit (Bech32) or Base58 encoding.",  # Invalid human-readable part
        [],
    ),
    (
        "syl1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vq8tndjx",
        "Version 1+ witness address must use Bech32m checksum",  # Invalid checksum (Bech32 instead of Bech32m)
        [],
    ),
    (
        "tsyl1z0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqyewurc",
        "Invalid or unsupported Segwit (Bech32) or Base58 encoding.",  # tb1, Invalid checksum (Bech32 instead of Bech32m)
        [],
    ),
    (
        "BC1S0XLXVLHEMJA6C4DQV22UAPCTQUPFHLXM9H8Z3K2E72Q4K9HCZ7VQ54WELL",
        "Version 1+ witness address must use Bech32m checksum",  # Invalid checksum (Bech32 instead of Bech32m)
        [],
    ),
    (
        "syl1qw508d6qejxtdg4y5r3zarvary0c5xw7k6tacws",
        "Version 0 witness address must use Bech32 checksum",  # Invalid checksum (Bech32m instead of Bech32)
        [],
    ),
    (
        "tsyl1q0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqxnh640",
        "Invalid or unsupported Segwit (Bech32) or Base58 encoding.",  # tb1, Invalid checksum (Bech32m instead of Bech32)
        [],
    ),
    (
        "syl1p38j9r5y49hruaue7wxjce0updqjuyyx0kh56v8s25huc6995vvzs49mow4",
        "Invalid Base 32 character",  # Invalid character in checksum
        [59],
    ),
    (
        "BC130XLXVLHEMJA6C4DQV22UAPCTQUPFHLXM9H8Z3K2E72Q4K9HCZ7VQ7ZWS8R",
        "Invalid Bech32 address witness version",
        [],
    ),
    ("syl1pw5uf7fpw", "Invalid Bech32 address program size (1 byte)", []),
    (
        "syl1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7v8n0nx0muaewav25p5j0ln",
        "Invalid Bech32 address program size (41 bytes)",
        [],
    ),
    (
        "BC1QR508D6QEJXTDG4Y5R3ZARVARYV98GJ9P",
        "Invalid Bech32 v0 address program size (16 bytes), per BIP141",
        [],
    ),
    (
        "tsyl1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hclm7z4uZagq",
        "Invalid or unsupported Segwit (Bech32) or Base58 encoding.",  # tb1, Mixed case
        [],
    ),
    (
        "syl1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7v07q22zl53",
        "Invalid padding in Bech32 data section",  # zero padding of more than 4 bits
        [],
    ),
    (
        "tsyl1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vp3jrxsp",
        "Invalid or unsupported Segwit (Bech32) or Base58 encoding.",  # tb1, Non-zero padding in 8-to-5 conversion
        [],
    ),
    ("syl1smsmsx", "Empty Bech32 data section", []),
]
VALID_DATA = [
    # BIP 350
    (
        "BC1QW508D6QEJXTDG4Y5R3ZARVARY0C5XW7KV8F3T4",
        "0014751e76e8199196d454941c45d1b3a323f1433bd6",
    ),
    # (
    #   "tsyl1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3qk226nd",
    #   "00201863143c14c5166804bd19203356da136c985678cd4d27a1b8c6329604903262",
    # ),
    (
        "syl1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3qa9wyvc",
        "00201863143c14c5166804bd19203356da136c985678cd4d27a1b8c6329604903262",
    ),
    (
        "syl1pw508d6qejxtdg4y5r3zarvary0c5xw7kw508d6qejxtdg4y5r3zarvary0c5xw7kcvl4ml",
        "5128751e76e8199196d454941c45d1b3a323f1433bd6751e76e8199196d454941c45d1b3a323f1433bd6",
    ),
    ("BC1SW50QGDZ25J", "6002751e"),
    ("syl1zw508d6qejxtdg4y5r3zarvaryvlr632f", "5210751e76e8199196d454941c45d1b3a323"),
    # (
    #   "tsyl1qqqqqp399et2xygdj5xreqhjjvcmzhxw4aywxecjdzew6hylgvses6uz5jh",
    #   "0020000000c4a5cad46221b2a187905e5266362b99d5e91c6ce24d165dab93e86433",
    # ),
    (
        "syl1qqqqqp399et2xygdj5xreqhjjvcmzhxw4aywxecjdzew6hylgvses3nx2dz",
        "0020000000c4a5cad46221b2a187905e5266362b99d5e91c6ce24d165dab93e86433",
    ),
    # (
    #   "tsyl1pqqqqp399et2xygdj5xreqhjjvcmzhxw4aywxecjdzew6hylgvsesstza2t",
    #   "5120000000c4a5cad46221b2a187905e5266362b99d5e91c6ce24d165dab93e86433",
    # ),
    (
        "syl1pqqqqp399et2xygdj5xreqhjjvcmzhxw4aywxecjdzew6hylgvsesmyxr47",
        "5120000000c4a5cad46221b2a187905e5266362b99d5e91c6ce24d165dab93e86433",
    ),
    (
        "syl1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vq8tndjx",
        "512079be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798",
    ),
    # PayToAnchor(P2A)
    (
        "syl1pfeese8ra2x",
        "51024e73",
    ),
]


class ValidateAddressMainTest(OpenSyriaTestFramework):
    def set_test_params(self):
        self.setup_clean_chain = True
        self.chain = ""  # main
        self.num_nodes = 1
        self.extra_args = [["-prune=899"]] * self.num_nodes

    def check_valid(self, addr, spk):
        info = self.nodes[0].validateaddress(addr)
        assert_equal(info["isvalid"], True)
        assert_equal(info["scriptPubKey"], spk)
        assert "error" not in info
        assert "error_locations" not in info

    def check_invalid(self, addr, error_str, error_locations):
        res = self.nodes[0].validateaddress(addr)
        assert_equal(res["isvalid"], False)
        assert_equal(res["error"], error_str)
        assert_equal(res["error_locations"], error_locations)

    def test_validateaddress(self):
        for (addr, error, locs) in INVALID_DATA:
            self.check_invalid(addr, error, locs)
        for (addr, spk) in VALID_DATA:
            self.check_valid(addr, spk)

    def run_test(self):
        self.test_validateaddress()


if __name__ == "__main__":
    ValidateAddressMainTest(__file__).main()
