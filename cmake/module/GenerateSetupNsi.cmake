# Copyright (c) 2023-present The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or https://opensource.org/license/mit/.

function(generate_setup_nsi)
  set(abs_top_srcdir ${PROJECT_SOURCE_DIR})
  set(abs_top_builddir ${PROJECT_BINARY_DIR})
  set(CLIENT_URL ${PROJECT_HOMEPAGE_URL})
  set(CLIENT_TARNAME "opensyria")
  set(OPENSYRIA_WRAPPER_NAME "opensyria")
  set(OPENSYRIA_GUI_NAME "opensyria-qt")
  set(OPENSYRIA_DAEMON_NAME "opensyriad")
  set(OPENSYRIA_CLI_NAME "opensyria-cli")
  set(OPENSYRIA_TX_NAME "opensyria-tx")
  set(OPENSYRIA_WALLET_TOOL_NAME "opensyria-wallet")
  set(OPENSYRIA_TEST_NAME "test_opensyria")
  set(EXEEXT ${CMAKE_EXECUTABLE_SUFFIX})
  configure_file(${PROJECT_SOURCE_DIR}/share/setup.nsi.in ${PROJECT_BINARY_DIR}/opensyria-win64-setup.nsi USE_SOURCE_PERMISSIONS @ONLY)
endfunction()
