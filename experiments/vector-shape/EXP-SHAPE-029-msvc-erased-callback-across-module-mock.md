---
status: pass-compiled-offline-mock
last_verified: 2026-10-12
evidence: E2-B
versions: MSVC VS2022 x64, no Adobe runtime
---

# EXP-SHAPE-029 — Separate DLL / EXE native callback ABI and lifetime mock

## Question

Does our MSVC toolchain correctly pass and copy a by-value std::function native-stream Creator across module boundaries, keep it alive for synchronous canonical object creation, then dispose the callback and object after explicit unregister? This is one narrow prerequisite for the future Adobe registrar test.

## Implementation

Code: experiments/vector-shape/tdb-callback-abi-mock/ (HostABI.h, HostMock.cpp DLL, ClientTest.cpp EXE, CMakeLists.txt, release verifier). Uses an artificial GUID-like 16-byte MatchName and abstract StreamLike virtual methods; does NOT implement Adobe TDB classes.

The DLL accepts a std::function<StreamLike*(MatchNameLike const&,void*,bool,unsigned,unsigned)> by value from the EXE, copies/retains it, eagerly constructs a complete derived StreamLike, invokes its virtual predicates/canonical setup, detects duplicate registration and explicitly unregisters stored entries. EXE checks callback captured shared_ptr lifetime survives calling scope and expires only after unregister. Two registrations removed in reverse order.

## Results

CMake VS2022 Release build PASS; CTest actual DLL/EXE test PASS; independent verifier confirms exported host functions and no TDB/BEE dependency. Receipt: datasets/ae-tdb-callback-abi-mock-build-receipt-20261012.json.

## Critical limit

**This does not validate Adobe's ABI.** HostMock is a constructed analog, not the real native factory; Adobe's TDB_StreamBase layout, U.dll tracked allocator, canonical layouts, type metadata, shutdown and native caller thread constraints are NOT simulated. This is E2-B engineering, not E2-X native AE type registration.
