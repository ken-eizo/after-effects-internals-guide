---
status: internal-implementation-reference
last_verified: 2026-10-15
evidence: E2-L + H
versions: Original Windows AE2025 / AE2026 BEE.dll and TDB.dll native machine code; no macOS qualification
---

# TDB_StreamGroup Name Lookup — BEE Startup Callback Bridge

`TDB_StreamGroup::FindStreamByNameNullOK` uses a private host-wide callback installed during `BEE_Birth` to resolve an existing Stream by a human-readable name.

**This is NOT a native Stream class registration function.** It does not provide a third-party mechanism to add arbitrary C++ Stream subclasses to the AE Timeline. This feature reference separates name-based lookup from factory-backed Stream construction.

## Purpose and native entry points

| Adobe-private C++ function | Native owner | Purpose |
| --- | --- | --- |
| `TDB_StreamGroup::SetFindStreamByNameNullOKFunction` | `TDB.dll` | Set the private C++ `std::function` callback used for name lookup |
| `TDB_StreamGroup::FindStreamByNameNullOK` | `TDB.dll` | Invoke callback when available, otherwise return null |
| `BEE_Birth` | `BEE.dll` | Install BEE-provided callback during internal host initialization |

The TDB name-search function takes a StreamGroup and a UTF-16 name, plus additional output/reference arguments. The exact semantic meaning of all auxiliary arguments and the full BEE callback implementation have not yet been reconstructed.

## Real native path

```text
BEE_Birth
  └─ construct a host callback object
      └─ TDB_StreamGroup::SetFindStreamByNameNullOKFunction(callback)
          └─ assign callback into TDB global std::function storage

TDB_StreamGroup::FindStreamByNameNullOK
  ├─ load stored callable
  ├─ if nullptr: return nullptr
  └─ call native std::function invocation virtual slot +0x10
       └─ BEE-provided name lookup
```

The original code for the setter consists of a short forwarding wrapper to a private std::function assignment helper. The real search function loads the pointer from the **same TDB static storage** and checks it before indirect dispatch.

### Per-version implementation

| Original native item | AE2025 | AE2026 |
| --- | --- | --- |
| `BEE_Birth` entry | `0x64A530` | `0x664F70` |
| BEE calls TDB callback setter | `0x64A5F2` | `0x66502E` |
| `TDB_StreamGroup::SetFindStreamByNameNullOKFunction` entry | `0x2B690` | `0x2C440` |
| TDB static callable storage base | `0xA79D0` | `0xC0C60` |
| Stored callable pointer load RVA | `0xA7A08` | `0xC0C98` |
| `FindStreamByNameNullOK` entry | `0x2B540` | `0x2C280` |
| Absent callback behavior | Return null | Return null |
| Registered callback invocation | `vtable+0x10` | `vtable+0x10` |

All addresses are **RVAs for original observed binaries**, not documented or stable third-party SDK ABI offsets.

## Critical distinction: lookup is not registration

The native implementation has separate planes of responsibility.

| Mechanism | Input | Result |
| --- | --- | --- |
| `TDB_StreamGroup::FindStreamByNameNullOK` | Group plus display/name string | Find an existing Stream through installed callback |
| `TDB_StreamFactory::RegisterFactoryFunc` | `TDB_MatchName` plus C++ type Creator | Register new native class Creator and build a canonical prototype |
| `TDB_StreamFactory::CreateStream` | An already registered MatchName | Construct a new C++ object |
| Parent `CanStore / InsertStream` | Registered child MatchName and instance | Decide whether a group may adopt a child and establish ownership |

Merely providing a name-search callback does **not** register a new MatchName or a valid custom C++ class. It also does not construct a host-owned property, grant Timeline editing rights or prove save/reopen support.

## Lifetime considerations and unknowns

The callback object is stored within `TDB.dll`, while its installed implementation originates from BEE startup. That is a cross-module code-lifetime relationship. However, the following remain **unverified**: the exact BEE implementation of the callback, its complete output/reference argument semantics, whether and how it is cleared during `BEE_Death`, concurrent lookup/update safety and any support for unrelated third-party callbacks.

No private Adobe function was called by this experiment; the original host and projects remain unchanged.

## Evidence and related pages

Research: **F-VECTOR-105**. Independent cross-version SHA-pinned static verifier:

```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_bee_tdb_stream_name_lookup_callback.py"
```

Machine-readable receipt: `datasets/ae-bee-tdb-native-name-lookup-callback-2025-2026.json`.

Related feature references: [Factory Registration and Lifetime](factory-registration-lifetime.md), [Stream Object Model](stream-object-model.md), [Native API Atlas](api-atlas.md), [Canonical Groups](canonical-groups-admission.md), and [Startup to Shutdown](startup-to-shutdown.md).
