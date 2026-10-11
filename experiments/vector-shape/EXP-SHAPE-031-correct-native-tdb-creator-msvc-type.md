---
status: pass-compiled-exact-symbol-abi-not-host
last_verified: 2026-10-12
evidence: E2-B + E2-L
---

# EXP-SHAPE-031 — Type-correct private TDB native Creator callback and cross-build MSVC mangling

## Question

Does the CNL experimental callback's std::function TEMPLATE TYPE match Adobe's native private TDB_StreamFactory::RegisterFactoryFunc exported parameter ABI? This is distinct from proving that Adobe accepts external registration and that allocator/lifetime/layout are fully compatible.

## Finding

The previous experimental AEX was WRONG: its native callback signature used bool,unsigned,unsigned where the actual native function is bool,unsigned int,bool. The std::function return/source parameter class types were also generic void* rather than exact named TDB classes. Treat the previous AEX as invalid and replace rather than running it.

MSVC2022 independently compiled a C++ symbol from NativeABISignatureProbe.cpp with forward-declared TDB_StreamBase, TDB_StreamFactory and TDB_MatchName and exact std::function type. Extract its mangled parameter-type suffix with dumpbin /symbols. Compare it byte-for-byte to the actual Adobe RegisterFactoryFunc mangled export in both pinned AE2025/AE2026 TDB.dll; BOTH pass.

The revised AEX uses the same typed Creator: TDB_StreamBase*(TDB_MatchName const&, TDB_StreamFactory*, bool, unsigned int, bool). BEE layer/editor/raster output remains unproven.

## Reproduction

Build tdb-callback-abi-mock with CMake VS2022 x64, which now also compiles CNLABISignatureProbe static target; run verify_symbol_abi.py. Also run CTest cross-module callback model and verify_no_host_load.py against the rebuilt experimental AEX.

## Limit

Exact compiler mangling is a necessary condition, NOT proof of:
- correct private class size/layout for any real TDB_StreamBase owner,
- permitted post-initialization external registration,
- consistent allocator, canonical instances and module unload,
- native indexed Contents, AE Pen, BEE evaluator, or VectorArt rendering.

The AE runtime has NOT called the mutating registration method.

See F-VECTOR-034, datasets/ae-tdb-exact-msvc-callback-abi-receipt-20261012.json.
