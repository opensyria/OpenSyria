# Copyright (c) 2025 The OpenSyria Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or https://opensource.org/license/mit/.

# RandomX library integration for ASIC-resistant Proof-of-Work
# RandomX is used by Monero and provides CPU-optimized mining
# Documentation: https://github.com/tevador/RandomX

include(FetchContent)

message(STATUS "Configuring RandomX library...")

FetchContent_Declare(
    randomx
    GIT_REPOSITORY https://github.com/tevador/RandomX.git
    GIT_TAG        v1.2.1
    GIT_SHALLOW    TRUE
)

# Disable building RandomX tests and benchmarks
set(RANDOMX_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(RANDOMX_BUILD_TOOLS OFF CACHE BOOL "" FORCE)
set(RANDOMX_BUILD_SHARED OFF CACHE BOOL "" FORCE)

# Fetch and build RandomX
FetchContent_MakeAvailable(randomx)

# Verify RandomX target is available
if(NOT TARGET randomx)
    message(FATAL_ERROR "RandomX target not found after FetchContent")
endif()

# Make RandomX headers available - add include directory to target
FetchContent_GetProperties(randomx)
target_include_directories(randomx PUBLIC ${randomx_SOURCE_DIR}/src)

message(STATUS "RandomX library configured successfully")
