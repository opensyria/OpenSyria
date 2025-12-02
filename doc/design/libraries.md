# Libraries

| Name                     | Description |
|--------------------------|-------------|
| *libopensyria_cli*         | RPC client functionality used by *opensyria-cli* executable |
| *libopensyria_common*      | Home for common functionality shared by different executables and libraries. Similar to *libopensyria_util*, but higher-level (see [Dependencies](#dependencies)). |
| *libopensyria_consensus*   | Consensus functionality used by *libopensyria_node* and *libopensyria_wallet*. |
| *libopensyria_crypto*      | Hardware-optimized functions for data encryption, hashing, message authentication, and key derivation. |
| *libopensyria_kernel*      | Consensus engine and support library used for validation by *libopensyria_node*. |
| *libopensyriaqt*           | GUI functionality used by *opensyria-qt* and *opensyria-gui* executables. |
| *libopensyria_ipc*         | IPC functionality used by *opensyria-node* and *opensyria-gui* executables to communicate when [`-DENABLE_IPC=ON`](multiprocess.md) is used. |
| *libopensyria_node*        | P2P and RPC server functionality used by *opensyriad* and *opensyria-qt* executables. |
| *libopensyria_util*        | Home for common functionality shared by different executables and libraries. Similar to *libopensyria_common*, but lower-level (see [Dependencies](#dependencies)). |
| *libopensyria_wallet*      | Wallet functionality used by *opensyriad* and *opensyria-wallet* executables. |
| *libopensyria_wallet_tool* | Lower-level wallet functionality used by *opensyria-wallet* executable. |
| *libopensyria_zmq*         | [ZeroMQ](../zmq.md) functionality used by *opensyriad* and *opensyria-qt* executables. |

## Conventions

- Most libraries are internal libraries and have APIs which are completely unstable! There are few or no restrictions on backwards compatibility or rules about external dependencies. An exception is *libopensyria_kernel*, which, at some future point, will have a documented external interface.

- Generally each library should have a corresponding source directory and namespace. Source code organization is a work in progress, so it is true that some namespaces are applied inconsistently, and if you look at [`add_library(opensyria_* ...)`](../../src/CMakeLists.txt) lists you can see that many libraries pull in files from outside their source directory. But when working with libraries, it is good to follow a consistent pattern like:

  - *libopensyria_node* code lives in `src/node/` in the `node::` namespace
  - *libopensyria_wallet* code lives in `src/wallet/` in the `wallet::` namespace
  - *libopensyria_ipc* code lives in `src/ipc/` in the `ipc::` namespace
  - *libopensyria_util* code lives in `src/util/` in the `util::` namespace
  - *libopensyria_consensus* code lives in `src/consensus/` in the `Consensus::` namespace

## Dependencies

- Libraries should minimize what other libraries they depend on, and only reference symbols following the arrows shown in the dependency graph below:

<table><tr><td>

```mermaid

%%{ init : { "flowchart" : { "curve" : "basis" }}}%%

graph TD;

opensyria-cli[opensyria-cli]-->libopensyria_cli;

opensyriad[opensyriad]-->libopensyria_node;
opensyriad[opensyriad]-->libopensyria_wallet;

opensyria-qt[opensyria-qt]-->libopensyria_node;
opensyria-qt[opensyria-qt]-->libopensyriaqt;
opensyria-qt[opensyria-qt]-->libopensyria_wallet;

opensyria-wallet[opensyria-wallet]-->libopensyria_wallet;
opensyria-wallet[opensyria-wallet]-->libopensyria_wallet_tool;

libopensyria_cli-->libopensyria_util;
libopensyria_cli-->libopensyria_common;

libopensyria_consensus-->libopensyria_crypto;

libopensyria_common-->libopensyria_consensus;
libopensyria_common-->libopensyria_crypto;
libopensyria_common-->libopensyria_util;

libopensyria_kernel-->libopensyria_consensus;
libopensyria_kernel-->libopensyria_crypto;
libopensyria_kernel-->libopensyria_util;

libopensyria_node-->libopensyria_consensus;
libopensyria_node-->libopensyria_crypto;
libopensyria_node-->libopensyria_kernel;
libopensyria_node-->libopensyria_common;
libopensyria_node-->libopensyria_util;

libopensyriaqt-->libopensyria_common;
libopensyriaqt-->libopensyria_util;

libopensyria_util-->libopensyria_crypto;

libopensyria_wallet-->libopensyria_common;
libopensyria_wallet-->libopensyria_crypto;
libopensyria_wallet-->libopensyria_util;

libopensyria_wallet_tool-->libopensyria_wallet;
libopensyria_wallet_tool-->libopensyria_util;

classDef bold stroke-width:2px, font-weight:bold, font-size: smaller;
class opensyria-qt,opensyriad,opensyria-cli,opensyria-wallet bold
```
</td></tr><tr><td>

**Dependency graph**. Arrows show linker symbol dependencies. *Crypto* lib depends on nothing. *Util* lib is depended on by everything. *Kernel* lib depends only on consensus, crypto, and util.

</td></tr></table>

- The graph shows what _linker symbols_ (functions and variables) from each library other libraries can call and reference directly, but it is not a call graph. For example, there is no arrow connecting *libopensyria_wallet* and *libopensyria_node* libraries, because these libraries are intended to be modular and not depend on each other's internal implementation details. But wallet code is still able to call node code indirectly through the `interfaces::Chain` abstract class in [`interfaces/chain.h`](../../src/interfaces/chain.h) and node code calls wallet code through the `interfaces::ChainClient` and `interfaces::Chain::Notifications` abstract classes in the same file. In general, defining abstract classes in [`src/interfaces/`](../../src/interfaces/) can be a convenient way of avoiding unwanted direct dependencies or circular dependencies between libraries.

- *libopensyria_crypto* should be a standalone dependency that any library can depend on, and it should not depend on any other libraries itself.

- *libopensyria_consensus* should only depend on *libopensyria_crypto*, and all other libraries besides *libopensyria_crypto* should be allowed to depend on it.

- *libopensyria_util* should be a standalone dependency that any library can depend on, and it should not depend on other libraries except *libopensyria_crypto*. It provides basic utilities that fill in gaps in the C++ standard library and provide lightweight abstractions over platform-specific features. Since the util library is distributed with the kernel and is usable by kernel applications, it shouldn't contain functions that external code shouldn't call, like higher level code targeted at the node or wallet. (*libopensyria_common* is a better place for higher level code, or code that is meant to be used by internal applications only.)

- *libopensyria_common* is a home for miscellaneous shared code used by different OpenSyria Core applications. It should not depend on anything other than *libopensyria_util*, *libopensyria_consensus*, and *libopensyria_crypto*.

- *libopensyria_kernel* should only depend on *libopensyria_util*, *libopensyria_consensus*, and *libopensyria_crypto*.

- The only thing that should depend on *libopensyria_kernel* internally should be *libopensyria_node*. GUI and wallet libraries *libopensyriaqt* and *libopensyria_wallet* in particular should not depend on *libopensyria_kernel* and the unneeded functionality it would pull in, like block validation. To the extent that GUI and wallet code need scripting and signing functionality, they should be able to get it from *libopensyria_consensus*, *libopensyria_common*, *libopensyria_crypto*, and *libopensyria_util*, instead of *libopensyria_kernel*.

- GUI, node, and wallet code internal implementations should all be independent of each other, and the *libopensyriaqt*, *libopensyria_node*, *libopensyria_wallet* libraries should never reference each other's symbols. They should only call each other through [`src/interfaces/`](../../src/interfaces/) abstract interfaces.

## Work in progress

- Validation code is moving from *libopensyria_node* to *libopensyria_kernel* as part of [The libopensyriakernel Project #27587](https://github.com/opensyria/opensyria/issues/27587)
