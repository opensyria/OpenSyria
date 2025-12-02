// Copyright (c) 2023 Bitcoin Developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include "nontrivial-threadlocal.h"

#include <clang-tidy/ClangTidyModule.h>
#include <clang-tidy/ClangTidyModuleRegistry.h>

class OpenSyriaModule final : public clang::tidy::ClangTidyModule
{
public:
    void addCheckFactories(clang::tidy::ClangTidyCheckFactories& CheckFactories) override
    {
        CheckFactories.registerCheck<opensyria::NonTrivialThreadLocal>("opensyria-nontrivial-threadlocal");
    }
};

static clang::tidy::ClangTidyModuleRegistry::Add<OpenSyriaModule>
    X("opensyria-module", "Adds opensyria checks.");

volatile int OpenSyriaModuleAnchorSource = 0;
