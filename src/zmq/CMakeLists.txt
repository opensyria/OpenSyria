# Copyright (c) 2023-present The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or https://opensource.org/license/mit/.

add_library(opensyria_zmq STATIC EXCLUDE_FROM_ALL
  zmqabstractnotifier.cpp
  zmqnotificationinterface.cpp
  zmqpublishnotifier.cpp
  zmqrpc.cpp
  zmqutil.cpp
)
target_compile_definitions(opensyria_zmq
  INTERFACE
    ENABLE_ZMQ=1
)
target_link_libraries(opensyria_zmq
  PRIVATE
    core_interface
    univalue
    zeromq
)
