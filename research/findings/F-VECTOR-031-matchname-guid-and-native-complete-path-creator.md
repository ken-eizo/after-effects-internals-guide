---
status: strongly-supported-static
last_verified: 2026-10-12
evidence: E2-L
versions: installed AE2025 and AE2026 TDB.dll
---

# F-VECTOR-031 — TDB_MatchName 16-byte GUID and Adobe-complete ParamPathStream Creator

## Objective and accuracy boundary

For a future independent CompNodeAE native vector type, determine whether a completely constructed existing Adobe stream class could be used to **test registry admissibility under a new MatchName** before attempting an external arbitrary custom StreamBase subclass. This is not the target native vector layer, native Contents owner, Pen editing, or vector renderer. It is a test of **one** underlying private host type factory, not the five integration gates.

## Pinned native facts verified in AE2025 and AE2026

1. The exported TDB_MatchName(char const*,bool) constructor initializes a native dvacore Guid, calls TDBp_MatchNamePool::GuidFromName and executes a 16-byte x64 xmm store into its object. Thus a static 16-byte GUID payload is verified, though the complete class ABI is not promised for other versions.
2. TDB_ParamPathStream::Create uses native U.dll U_MemTrackedObject allocation with a literal size **0x468 bytes** in both installed versions, then invokes Adobe's full TDB_DerivedStream<TDB_ParamPathStreamTraits> constructor. It returns a real polymorphic TDB_StreamBase-derived class rather than a guessed foreign vtable.
3. TDB_IndexedStreamGroup constructor invokes TDB_StreamGroup constructor and initializes its own indexed data; the group class is separate from the ParamPathStream class.
4. The private TDB_StreamFactory::RegisterFactoryFunc synchronously calls CreateStream and invokes virtual methods on its newly created object (F-VECTOR-026); complete Adobe native classes are thus less speculative as a callback than a dummy home-built subclass.
5. TDB_MatchName class identity depends on the TDB MatchName pool and GUID mapping, not on writing a display string directly into an unknown native object.

| Function | AE2025 RVA | AE2026 RVA |
| --- | --- | --- |
| TDB_MatchName(char const*,bool) | 0x2c610 | 0x2d1f0 |
| TDB_ParamPathStream::Create | 0x10750 | 0x107c0 |
| TDB_ParamPathStream native constructor | 0xea90 | 0xeb30 |
| TDB_IndexedStreamGroup native constructor | 0x32330 | 0x32e30 |
| TDB_StreamFactory::RegisterFactoryFunc | 0x27400 | 0x285d0 |

All observations are static, confirmed independently against the exact pinned binary SHA256 fingerprints; no Adobe private method was invoked in this experiment.

## Crucial limitation: ParamPathStream is not Shape Contents

The exposed C++ class uses TDB_ParamPathStreamTraits. It is an internal parameter-path stream, **not** a BEE_VectorArt Path or a new BEE_VectorLayer. The class name and implementation do not demonstrate an independent owner or native renderer. Even a successful registration under a new key would initially prove ONLY that the type registry admitted an external callback.

Public CanAddStream's positive prefix checks on existing Shape Contents do not solve this. Native external creation, canonical handling, Timeline parent identity, native Pen editing and the BEE evaluator registry each require separately verified contracts.

## Safety / research bridge

Since C++ MSVC std::function creator callbacks are passed by value, a future external probe needs compatible function-object layout and lifetime. Offline project tdb-callback-abi-mock builds a separate x64 DLL and EXE, verifies copying, eager native-like virtual method dispatch, canonical object, duplicate rejection and reverse-order unregister. This is **not** actual Adobe ABI validation.

An experimental separate AEX is prepared with a manual-only disposable test, exact pinned binary hash, specific export and opcode checks, explicit two-factor acknowledgment and automatic best-effort unregister after registration; it is NOT installed, NOT exercised in AE and may crash or corrupt host state. It is fundamentally different from the safe native-vector-host-probe AEX, which only checks exports/getter and creates independent CNL cubics.

## Evidence

- datasets/ae-native-tdb-built-in-path-creator-registration-feasibility-2025-2026.json
- datasets/ae-tdb-matchname-guid-and-built-in-path-creator-check-2025-2026.json
- experiments/vector-shape/probe-src/tools/audit_tdb_builtin_creator_as_external_bootstrap.py
- experiments/vector-shape/probe-src/tools/verify_tdb_matchname_guid_and_builtin_creator.py
- F-VECTOR-030 hypothesis, EXP-SHAPE-027/029.

No host-native registration proven. No arbitrary layer subclass, editable independent Contents or BEE renderer created.
