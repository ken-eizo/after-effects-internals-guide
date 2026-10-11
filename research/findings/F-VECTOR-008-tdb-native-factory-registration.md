---
status: strongly-supported-local-artifact
last_verified: 2026-10-11
evidence: E2-L plus E2-X capability-admission control
versions: AE 2025 + AE 2026 TDB/BEE binaries
---
# F-VECTOR-008 — Native TDB stream type factory registration is an actual internal host mechanism

## Concrete artifact and cross-module control-flow evidence

The installed AE 2025 / AE 2026 runtimes contain a distinct `TDB.dll`. Export enumeration shows 1,282 and 1,291 exports respectively; binary hashes:
- 2025: `2ed19824997f3de797a75fef6f22d4d11ac8548c9d35f6093aa2afc1a6ed2e69`.
- 2026: `82677a20bdf871878b579522c4b4e0def8af0a50a810e3b9972da1170f546c1b`.

These binaries expose C++ decorated names:

| Mechanism | AE 2025 RVA | AE 2026 RVA |
| --- | --- | --- |
| `Get_AE_StreamFactory()` | `0x8100` | `0x81B0` |
| `TDB_StreamFactory::CreateStream` | `0x26710` | `0x27920` |
| `TDB_StreamFactory::GetCanonicalInstance` | `0x26CC0` | `0x27EB0` |
| `TDB_StreamFactory::RegisterCanonicalInstance` | `0x27130` | `0x28300` |
| `TDB_StreamFactory::RegisterFactoryFunc` | `0x27400` | `0x285D0` |
| `TDB_StreamFactory::UnregisterFactoryFunc` | `0x28BC0` | `0x29C10` |
| `TDB_ScRegisterStreams::Register` | `0x27060` | `0x28220` |
| `TDB_ScRegisterStreams::UnregisterAll` | `0x287A0` | `0x29850` |

Exact raw decorated signatures, module hashes and callsites are preserved in `datasets/ae-tdb-native-stream-factory-2025-2026.json`, `datasets/ae-tdb-register-callsite-disasm-2025-2026.json`, and `datasets/ae-bee-registerstreams-iat-targets-2025-2026.json`.

## Call chain proven by offline x64 disassembly and IAT mapping

```text
BEE_Layer::RegisterStreams(bool)         [BEE.dll]
    |-- calls TDB.dll!Get_AE_StreamFactory()
    |-- uses TDB_ScRegisterStreams
    |-- calls TDB_ScRegisterStreams::Register(matchName, creator, ...)
    |       \-- TDB_StreamFactory::RegisterFactoryFunc(matchName, std::function, bool)
    |               |-- lock RecursiveMutex
    |               |-- look up match name
    |               |-- CreateStream(...) for canonical data
    |               \-- RegisterSeparatedDimensions(...)
    \-- when disabling/unregistering: TDB_ScRegisterStreams::UnregisterAll()
            \-- TDB_StreamFactory::UnregisterFactoryFunc(matchName)
```

The line up to `RegisterFactoryFunc` is backed by explicit **resolved IAT/direct CALL instructions in two installed versions**. The register/unregister branch is indicated by `BEE_Layer::RegisterStreams(bool)` instructions (`test bl,bl`, conditional path to `UnregisterAll`). The sampled factory routine performs a mutex lock, match-name checks, `CreateStream`, and `RegisterSeparatedDimensions`. This is stronger than simply finding exported method names.

The global accessor `Get_AE_StreamFactory()` in AE2026 starts with `mov rax, [rip+...]; ret`: it loads a host-managed pointer from global storage. Its existence does **not** establish valid lifetime at arbitrary plug-in callback times or permission to register.

## Structural interpretation

There is indeed an **internal pluggable callback/creator registry** for native TDB stream types, at least for AE's own modules. This is a stronger, evidence-backed statement than the earlier generic idea that Contents might be factory-built.

It remains **unproven** that a third-party AEGP/Effect plug-in can legally and safely install its own `std::function` creator, preserve host ownership/serialization, get an indexed Contents owner recognized by AE's timeline, and attach native Pen-tool/VectorArt behavior.

The existence of private `TDB_IndexedStreamGroup` and `TDB_NamedStreamGroup` constructors, `GetEditableStream`, `TDB_StreamGroup::CanStore`, `AddStreamToUILayout`, and `TDB_ScRegisterStreams` narrows the code frontier. A `std::function` internal ABI, `TDB_MatchName` representation, canonical prototype lifespan, locking, and module unload order remain barriers. Export addresses differ between AE versions.

## Falsification gates for new native plug-in class

1. Get/validate the host factory pointer in a disposable host session using only the pinned no-argument getter. **Do not dereference or register** during this initial experiment.
2. Determine whether unique unregistered match names are accepted by the parent Contents `CanStore`/public `CanAddStream`, **without** calling `AddStream`.
3. Independently reconstruct a structurally valid stream class/prototype/creator callback in an isolated test host. This is **not** authorized by the public SDK, must not run inside a working AE process, and requires rollback and exact ABI evidence before testing.
4. Native Timeline hierarchy/Undo/save/reopen, Pen-tool selection, and VectorArt->AGM rendering each require distinct host evidence.

## Unexpected public experiment limit

EXP-SHAPE-005 reports 359/359 `AEGP_GetUniqueStreamID` outputs equal to zero with zero recorded error codes on AE2026, despite distributed SDK version6/public Guide saying session-unique ID. It cannot be presumed to map directly to private `TDB_StreamIDPath`. A separate sentinel-based probe is planned; see F-VECTOR-009.

**No private factory registration has been executed**. The observed internal factory supports built-in registration; third-party extensibility is the remaining hypothesis.
