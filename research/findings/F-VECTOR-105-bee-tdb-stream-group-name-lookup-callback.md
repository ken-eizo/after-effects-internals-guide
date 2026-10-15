---
date: 2026-10-15
status: PASS offline strict original AE2025/AE2026 x64 BEE_Birth to TDB StreamGroup name-search callback installation and dispatch
evidence: E2-L pinned BEE/TDB PE exports/imports, direct IAT call, std::function global storage and native callable invocation; no private runtime call
---

# F-VECTOR-105 — BEE_Birth installs a native TDB name-lookup callback, not a new Stream class factory

## Discovery

Original Adobe AE2025 and AE2026 Windows native binaries expose an additional **host internal extension seam** that must be distinguished from the `TDB_StreamFactory` Creator registration model researched in F-VECTOR-093–096.

During `BEE_Birth`, Adobe BEE code constructs a private C++ `std::function` callback and calls the TDB export:

`TDB_StreamGroup::SetFindStreamByNameNullOKFunction(...)`

The implementation of that setter stores/assigns a function object in **TDB.dll's global module data**. `TDB_StreamGroup::FindStreamByNameNullOK` subsequently reads the stored callable; if absent it returns a null pointer, and if present it dispatches through the native `std::function` invocation slot **`+0x10`**.

These facts are independently verified for both original installed releases by a strict SHA-pinned static disassembly script.

## Precisely scoped execution model

```text
AE host invokes BEE_Birth
  └─ BEE constructs a native name-search std::function
      └─ TDB_StreamGroup::SetFindStreamByNameNullOKFunction(callback)
          └─ TDB global stored function object (one static storage location)

Later: TDB_StreamGroup::FindStreamByNameNullOK(group, name, ...)
  ├─ fetch installed function object
  ├─ if absent: return nullptr
  └─ if present: invoke installed C++ callable via slot +0x10
```

The compiled setter is a small leaf function that forwards to another internal std::function assignment helper. The static storage base for that function and the exact pointer load inside the consumer have an identical offset relationship in both versions.

| Machine-code observation | AE2025 TDB.dll | AE2026 TDB.dll |
| --- | ---: | ---: |
| `SetFindStreamByNameNullOKFunction` RVA | `0x2B690` | `0x2C440` |
| Stored C++ function object base RVA | `0xA79D0` | `0xC0C60` |
| Indirect stored callable pointer RVA | `0xA7A08` | `0xC0C98` |
| Storage pointer offset in function object | `+0x38` | `+0x38` |
| `FindStreamByNameNullOK` RVA | `0x2B540` | `0x2C280` |
| Search calls stored callable via vtable offset | `+0x10` | `+0x10` |
| Absent callable result | `nullptr` | `nullptr` |

`BEE_Birth` calls the TDB setter at **BEE RVA `0x64A5F2` (2025) / `0x66502E` (2026)**. Its import resolves to the exact `TDB_StreamGroup::SetFindStreamByNameNullOKFunction` export.

### This is NOT a class registration interface

The existence of a setter with "Function" in its name is not sufficient to establish arbitrary native property registration.

| Distinct native mechanism | Lookup key or request | Verified operation |
| --- | --- | --- |
| `TDB_StreamFactory::RegisterFactoryFunc` | `TDB_MatchName` | Register a typed C++ Creator and eagerly construct a canonical prototype |
| `TDB_StreamFactory::CreateStream` | Registered `TDB_MatchName` | Invoke Creator and construct an actual new C++ Stream object |
| `TDB_StreamGroup::SetFindStreamByNameNullOKFunction` | Function object | Install the host's name-lookup callback |
| `TDB_StreamGroup::FindStreamByNameNullOK` | Group and UTF-16 name | Request an **existing** Stream by name from the callback |

The name-lookup function is **not** a `RegisterFactoryFunc` call, does not create a canonical prototype, does not install a Stream class under a MatchName key, and does not bypass parent `CanStore` or object ownership requirements.

Because the global stored callback is a native C++ function object, its callback owner and code lifetime may matter during module teardown. However, this static experiment has **not** established `BEE_Death` callback reset behavior, safety during concurrent search, exception propagation, or foreign DLL unloading.

## Code anchors and verification

| Cross-module observation | AE2025 | AE2026 |
| --- | ---: | ---: |
| `BEE_Birth` entry | `0x64A530` | `0x664F70` |
| `BEE_Birth` calls TDB setter | `0x64A5F2` | `0x66502E` |
| TDB setter entry | `0x2B690` | `0x2C440` |
| TDB name search entry | `0x2B540` | `0x2C280` |

Verified machine code: setter writes/assigns into TDB module static storage, search loads the callable at static-function-base+`0x38`, checks null, calls vtable+`0x10`, and has an explicit null-return branch. Both imported/exported signatures were compared against their actual symbol declarations in the PE export tables.

This is **read-only PE disassembly**, not live plugin registration, not a public AEGP API, and not proof that third-party code can override the callback safely. The exact registered BEE callback's complete branch behavior and side effects remain a separate research target.

## Reproducibility

```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_bee_tdb_stream_name_lookup_callback.py"
```

The verifier SHA-pins the *original* installed `BEE.dll` and `TDB.dll`, checks both ends of the cross-module call, and records the exact storage and dispatch site without invoking Adobe code. Receipt: `datasets/ae-bee-tdb-native-name-lookup-callback-2025-2026.json`.

Feature page: `docs/state-model/native-property-system/name-lookup-callback-bridge.md`. Compare [F-VECTOR-095/096] factory registration and canonical prototype lifetime. Product gate **NOT_DELIVERED_HOST_NATIVE_CUSTOM_STREAM** remains unchanged.
