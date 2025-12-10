# Copyright (c) 2023-present The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or https://opensource.org/license/mit/.

include(AddWindowsResources)

configure_file(${PROJECT_SOURCE_DIR}/cmake/opensyria-build-config.h.in opensyria-build-config.h USE_SOURCE_PERMISSIONS @ONLY)
include_directories(${CMAKE_CURRENT_BINARY_DIR} ${CMAKE_CURRENT_SOURCE_DIR})

#=============================
# Subprojects
#=============================
# Subprojects include subdirectories that do or could have tests
# and/or benchmark binaries, such as all subtrees and univalue.
# These need to be included before CMAKE_*_OUTPUT_DIRECTORY variables
# are set, so output locations of subproject tests and libraries are
# not overridden.
include(../cmake/crc32c.cmake)
include(../cmake/leveldb.cmake)
include(../cmake/minisketch.cmake)
include(../cmake/randomx.cmake)
add_subdirectory(univalue)
if (ENABLE_IPC AND NOT WITH_EXTERNAL_LIBMULTIPROCESS)
  include(../cmake/libmultiprocess.cmake)
  add_libmultiprocess(ipc/libmultiprocess)
endif()
include(../cmake/secp256k1.cmake)
add_secp256k1(secp256k1)

# Set top-level target output locations.
if(NOT CMAKE_RUNTIME_OUTPUT_DIRECTORY)
  set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${PROJECT_BINARY_DIR}/bin)
endif()
if(NOT CMAKE_LIBRARY_OUTPUT_DIRECTORY)
  set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${PROJECT_BINARY_DIR}/lib)
endif()
if(NOT CMAKE_ARCHIVE_OUTPUT_DIRECTORY)
  set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${PROJECT_BINARY_DIR}/lib)
endif()

add_custom_target(generate_build_info
  BYPRODUCTS ${PROJECT_BINARY_DIR}/src/opensyria-build-info.h
  COMMAND ${CMAKE_COMMAND} -DBUILD_INFO_HEADER_PATH=${PROJECT_BINARY_DIR}/src/opensyria-build-info.h -DSOURCE_DIR=${PROJECT_SOURCE_DIR} -P ${PROJECT_SOURCE_DIR}/cmake/script/GenerateBuildInfo.cmake
  COMMENT "Generating opensyria-build-info.h"
  VERBATIM
)
add_library(opensyria_clientversion STATIC EXCLUDE_FROM_ALL
  clientversion.cpp
)
target_link_libraries(opensyria_clientversion
  PRIVATE
    core_interface
)
add_dependencies(opensyria_clientversion generate_build_info)

add_subdirectory(crypto)
add_subdirectory(util)
if(ENABLE_IPC)
  add_subdirectory(ipc)
endif()

add_library(opensyria_consensus STATIC EXCLUDE_FROM_ALL
  arith_uint256.cpp
  consensus/merkle.cpp
  consensus/tx_check.cpp
  hash.cpp
  primitives/block.cpp
  primitives/transaction.cpp
  pubkey.cpp
  script/interpreter.cpp
  script/script.cpp
  script/script_error.cpp
  uint256.cpp
)
target_link_libraries(opensyria_consensus
  PRIVATE
    core_interface
    opensyria_crypto
    secp256k1
)

if(WITH_ZMQ)
  add_subdirectory(zmq)
endif()

# Home for common functionality shared by different executables and libraries.
# Similar to `opensyria_util` library, but higher-level.
add_library(opensyria_common STATIC EXCLUDE_FROM_ALL
  addresstype.cpp
  base58.cpp
  bech32.cpp
  chain.cpp
  chainparams.cpp
  chainparamsbase.cpp
  coins.cpp
  common/args.cpp
  common/bloom.cpp
  common/config.cpp
  common/init.cpp
  common/interfaces.cpp
  common/messages.cpp
  common/netif.cpp
  common/pcp.cpp
  common/run_command.cpp
  common/settings.cpp
  common/signmessage.cpp
  common/system.cpp
  common/url.cpp
  compressor.cpp
  core_read.cpp
  core_write.cpp
  deploymentinfo.cpp
  external_signer.cpp
  init/common.cpp
  kernel/chainparams.cpp
  key.cpp
  key_io.cpp
  merkleblock.cpp
  musig.cpp
  net_permissions.cpp
  net_types.cpp
  netaddress.cpp
  netbase.cpp
  outputtype.cpp
  policy/feerate.cpp
  policy/policy.cpp
  pow.cpp
  protocol.cpp
  psbt.cpp
  rpc/rawtransaction_util.cpp
  rpc/request.cpp
  rpc/util.cpp
  scheduler.cpp
  script/descriptor.cpp
  script/miniscript.cpp
  script/parsing.cpp
  script/sign.cpp
  script/signingprovider.cpp
  script/solver.cpp
)
target_link_libraries(opensyria_common
  PRIVATE
    core_interface
    opensyria_consensus
    opensyria_util
    univalue
    secp256k1
    Boost::headers
    $<TARGET_NAME_IF_EXISTS:USDT::headers>
    $<$<PLATFORM_ID:Windows>:ws2_32>
)

include(InstallBinaryComponent)

if(ENABLE_WALLET)
  add_subdirectory(wallet)

  if(BUILD_WALLET_TOOL)
    add_executable(opensyria-wallet
      opensyria-wallet.cpp
      init/opensyria-wallet.cpp
      wallet/wallettool.cpp
    )
    set_target_properties(opensyria-wallet PROPERTIES OUTPUT_NAME opensyria-wallet)
    set_target_properties(opensyria-wallet PROPERTIES OUTPUT_NAME opensyria-wallet)
    add_windows_resources(opensyria-wallet opensyria-wallet-res.rc)
    add_windows_application_manifest(opensyria-wallet)
    target_link_libraries(opensyria-wallet
      core_interface
      opensyria_wallet
      opensyria_common
      opensyria_util
      Boost::headers
    )
    install_binary_component(opensyria-wallet HAS_MANPAGE)
  endif()
endif()


# P2P and RPC server functionality used by `opensyriad` and `opensyria-qt` executables.
add_library(opensyria_node STATIC EXCLUDE_FROM_ALL
  addrdb.cpp
  addrman.cpp
  banman.cpp
  bip324.cpp
  blockencodings.cpp
  blockfilter.cpp
  consensus/tx_verify.cpp
  dbwrapper.cpp
  deploymentstatus.cpp
  flatfile.cpp
  headerssync.cpp
  httprpc.cpp
  httpserver.cpp
  i2p.cpp
  index/base.cpp
  index/blockfilterindex.cpp
  index/coinstatsindex.cpp
  index/txindex.cpp
  init.cpp
  kernel/chain.cpp
  kernel/checks.cpp
  kernel/coinstats.cpp
  kernel/context.cpp
  kernel/cs_main.cpp
  kernel/disconnected_transactions.cpp
  kernel/mempool_removal_reason.cpp
  mapport.cpp
  net.cpp
  net_processing.cpp
  netgroup.cpp
  node/abort.cpp
  node/blockmanager_args.cpp
  node/blockstorage.cpp
  node/caches.cpp
  node/chainstate.cpp
  node/chainstatemanager_args.cpp
  node/coin.cpp
  node/coins_view_args.cpp
  node/connection_types.cpp
  node/context.cpp
  node/database_args.cpp
  node/eviction.cpp
  node/interface_ui.cpp
  node/interfaces.cpp
  node/kernel_notifications.cpp
  node/mempool_args.cpp
  node/mempool_persist.cpp
  node/mempool_persist_args.cpp
  node/miner.cpp
  node/mini_miner.cpp
  node/minisketchwrapper.cpp
  node/peerman_args.cpp
  node/psbt.cpp
  node/timeoffsets.cpp
  node/transaction.cpp
  node/txdownloadman_impl.cpp
  node/txorphanage.cpp
  node/txreconciliation.cpp
  node/utxo_snapshot.cpp
  node/warnings.cpp
  noui.cpp
  policy/ephemeral_policy.cpp
  policy/fees/block_policy_estimator.cpp
  policy/fees/block_policy_estimator_args.cpp
  policy/packages.cpp
  policy/rbf.cpp
  policy/settings.cpp
  policy/truc_policy.cpp
  rest.cpp
  rpc/blockchain.cpp
  rpc/external_signer.cpp
  rpc/fees.cpp
  rpc/mempool.cpp
  rpc/mining.cpp
  rpc/net.cpp
  rpc/node.cpp
  rpc/output_script.cpp
  rpc/rawtransaction.cpp
  rpc/server.cpp
  rpc/server_util.cpp
  rpc/signmessage.cpp
  rpc/txoutproof.cpp
  script/sigcache.cpp
  signet.cpp
  torcontrol.cpp
  txdb.cpp
  txgraph.cpp
  txmempool.cpp
  txrequest.cpp
  validation.cpp
  validationinterface.cpp
  versionbits.cpp
  $<$<TARGET_EXISTS:opensyria_wallet>:wallet/init.cpp>
  $<$<NOT:$<TARGET_EXISTS:opensyria_wallet>>:dummywallet.cpp>
)
target_link_libraries(opensyria_node
  PRIVATE
    core_interface
    opensyria_common
    opensyria_util
    $<TARGET_NAME_IF_EXISTS:opensyria_zmq>
    leveldb
    minisketch
    univalue
    Boost::headers
    $<TARGET_NAME_IF_EXISTS:libevent::core>
    $<TARGET_NAME_IF_EXISTS:libevent::extra>
    $<TARGET_NAME_IF_EXISTS:libevent::pthreads>
    $<TARGET_NAME_IF_EXISTS:USDT::headers>
)

# OpenSyria wrapper executable that can call other executables.
if(BUILD_OPENSYRIA_BIN)
  add_executable(opensyria opensyria.cpp)
  set_target_properties(opensyria PROPERTIES OUTPUT_NAME opensyria)
  set_target_properties(opensyria PROPERTIES OUTPUT_NAME opensyria)
  add_windows_resources(opensyria opensyria-res.rc)
  add_windows_application_manifest(opensyria)
  target_link_libraries(opensyria core_interface opensyria_common opensyria_util)
  install_binary_component(opensyria HAS_MANPAGE)
endif()

# OpenSyria Core opensyriad.
if(BUILD_DAEMON)
  add_executable(opensyriad
    opensyriad.cpp
    init/opensyriad.cpp
  )
    set_target_properties(opensyriad PROPERTIES OUTPUT_NAME opensyriad)
    set_target_properties(opensyriad PROPERTIES OUTPUT_NAME opensyriad)
  add_windows_resources(opensyriad opensyriad-res.rc)
  add_windows_application_manifest(opensyriad)
  target_link_libraries(opensyriad
    core_interface
    opensyria_node
    $<TARGET_NAME_IF_EXISTS:opensyria_wallet>
  )
  install_binary_component(opensyriad HAS_MANPAGE)
endif()
if(ENABLE_IPC AND BUILD_DAEMON)
  add_executable(opensyria-node
    opensyriad.cpp
    init/opensyria-node.cpp
  )
    set_target_properties(opensyria-node PROPERTIES OUTPUT_NAME opensyria-node)
    set_target_properties(opensyria-node PROPERTIES OUTPUT_NAME opensyria-node)
  target_link_libraries(opensyria-node
    core_interface
    opensyria_node
    opensyria_ipc
    $<TARGET_NAME_IF_EXISTS:opensyria_wallet>
  )
  install_binary_component(opensyria-node INTERNAL)
endif()

if(ENABLE_IPC AND BUILD_TESTS)
    # opensyria_ipc_test library target is defined here in src/CMakeLists.txt
    # instead of src/test/CMakeLists.txt so capnp files in src/test/ are able to
    # reference capnp files in src/ipc/capnp/ by relative path. The Cap'n Proto
    # compiler only allows importing by relative path when the importing and
    # imported files are underneath the same compilation source prefix, so the
    # source prefix must be src/, not src/test/
    add_library(opensyria_ipc_test STATIC EXCLUDE_FROM_ALL
      test/ipc_test.cpp
    )
    target_capnp_sources(opensyria_ipc_test ${PROJECT_SOURCE_DIR}
      test/ipc_test.capnp
    )
    add_dependencies(opensyria_ipc_test opensyria_ipc_headers)
endif()


add_library(opensyria_cli STATIC EXCLUDE_FROM_ALL
  compat/stdin.cpp
  rpc/client.cpp
)
target_link_libraries(opensyria_cli
  PUBLIC
    core_interface
    univalue
)


# OpenSyria RPC client
if(BUILD_CLI)
  add_executable(opensyria-cli opensyria-cli.cpp)
  set_target_properties(opensyria-cli PROPERTIES OUTPUT_NAME opensyria-cli)
  set_target_properties(opensyria-cli PROPERTIES OUTPUT_NAME opensyria-cli)
  add_windows_resources(opensyria-cli opensyria-cli-res.rc)
  add_windows_application_manifest(opensyria-cli)
  target_link_libraries(opensyria-cli
    core_interface
    opensyria_cli
    opensyria_common
    opensyria_util
    libevent::core
    libevent::extra
  )
  install_binary_component(opensyria-cli HAS_MANPAGE)
endif()


if(BUILD_TX)
  add_executable(opensyria-tx opensyria-tx.cpp)
  set_target_properties(opensyria-tx PROPERTIES OUTPUT_NAME opensyria-tx)
  set_target_properties(opensyria-tx PROPERTIES OUTPUT_NAME opensyria-tx)
  add_windows_resources(opensyria-tx opensyria-tx-res.rc)
  add_windows_application_manifest(opensyria-tx)
  target_link_libraries(opensyria-tx
    core_interface
    opensyria_common
    opensyria_util
    univalue
  )
  install_binary_component(opensyria-tx HAS_MANPAGE)
endif()


if(BUILD_UTIL)
  add_executable(opensyria-util opensyria-util.cpp)
  set_target_properties(opensyria-util PROPERTIES OUTPUT_NAME opensyria-util)
  set_target_properties(opensyria-util PROPERTIES OUTPUT_NAME opensyria-util)
  add_windows_resources(opensyria-util opensyria-util-res.rc)
  add_windows_application_manifest(opensyria-util)
  target_link_libraries(opensyria-util
    core_interface
    opensyria_common
    opensyria_util
  )
  install_binary_component(opensyria-util HAS_MANPAGE)
endif()


if(BUILD_GUI)
  add_subdirectory(qt)
endif()


if(BUILD_KERNEL_LIB)
  add_subdirectory(kernel)
  if (BUILD_KERNEL_TEST)
    add_subdirectory(test/kernel)
  endif()
  if(BUILD_UTIL_CHAINSTATE)
    add_executable(opensyria-chainstate
      opensyria-chainstate.cpp
    )
    set_target_properties(opensyria-chainstate PROPERTIES OUTPUT_NAME opensyria-chainstate)
    set_target_properties(opensyria-chainstate PROPERTIES OUTPUT_NAME opensyria-chainstate)
    add_windows_application_manifest(opensyria-chainstate)
    target_link_libraries(opensyria-chainstate
      PRIVATE
        core_interface
        opensyriakernel
    )
    install_binary_component(opensyria-chainstate INTERNAL)
  endif()
endif()


add_subdirectory(test/util)
if(BUILD_BENCH)
  add_subdirectory(bench)
endif()

if(BUILD_TESTS)
  add_subdirectory(test)
endif()

if(BUILD_FUZZ_BINARY)
  add_subdirectory(test/fuzz)
endif()
