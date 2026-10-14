---
date: 2026-10-14
status: PASS exact native OM_Stream typed cross-DLL construction and safe-shutdown order in pinned AE2025/AE2026 binaries, static only
evidence: E2-L OM.dll actual PE exports, IAT, x64 .pdata, Capstone byte-exact C++ constructor and allocator/teardown evidence; no private host runtime call
---
# F-VECTOR-094 — OM_Stream actual C++ native object layout, allocation, inheritance, vtable, MatchName lifetime

## Why this matters

F-VECTOR-093 proved that `OM.dll`, rather than TDB/BEE, independently implements and registers Adobe's genuine `ADBE Mask Shape` stream. Here we take one step deeper: how does its **real concrete C++ native subclass object** get allocated and how are its private factory identifier and lifetime handled?

The fundamental difficulty for ChapeLayer is not only calling `RegisterFactoryFunc` but implementing a foreign `TDB_StreamBase` with correct allocation/ABI, typed value processing, clone/archive and unload contracts. `OM_Stream` is the strongest visible shipped model for the required construction pattern, although it is an **Adobe internal module, not a licensed third-party SDK**.

## Direct x64 code evidence

Both installed AE Windows versions have a concrete export

```cpp
OM_Stream::Create(
    TDB_MatchName const&,
    TDB_StreamFactory*,
    bool,
    unsigned int,
    bool
) -> TDB_StreamBase*
```

matching the native TDB factory `std::function` callback's MSVC signature, not a PF effect parameter callback.

### Object construction chain

```text
OM_Stream::Create
 ├─ U.dll!U_MemTrackedObject::operator new(0x450)
 └─ OM_Stream::OM_Stream(type, matchName, factory, bool)
      ├─ TDB_DerivedStream<OM_MaskShapeStreamTraits>::constructor(...)
      ├─ this->vtable = &OM_Stream native vtable
      └─ byte at this+0x448 initialized to 0
```

| Constructed code artifact | AE2025 RVA | AE2026 RVA |
| --- | --- | --- |
| `OM_Stream::Create` | `0x2610` | `0x2650` |
| `OM_Stream::OM_Stream` | `0x29210` | `0x28A60` |
| `TDB_DerivedStream<OM_MaskShapeStreamTraits>` constructor | `0x2040` | `0x2080` |
| `OM_Stream` vtable | `0x8AFE0` | `0x9CFC0` |
| **C++ native class allocation** | **0x450 = 1104 bytes** | **0x450 = 1104 bytes** |
| Final initialized byte observed | `+0x448` | `+0x448` |

These values are derived from disassembled **actual allocation instructions and native C++ virtual-layout initialization** in the original OM DLLs. We did not guess structure sizes from a fabricated external class. The equality of allocation sizes in two releases **does not imply identical layouts across all slots, an ABI guarantee, thread safety or future-version compatibility**.

### Native MatchName and shutdown

OM_Birth allocates **0x10 = 16 bytes** using `U_MemTrackedObject::operator new`, passes the real literal `ADBE Mask Shape` into `TDB_MatchName`'s constructor, and keeps the resulting object pointer in exported `OM_StreamNamePtr_MASK_SHAPE`.

Registration:
- OM 2025 `RegisterFactoryFunc` actual native CALL RVA `0x332B`
- OM 2026 `RegisterFactoryFunc` native CALL RVA `0x322A`

At `OM_Death`, the exact MatchName pointer is reused:
- 2025: `UnregisterFactoryFunc` `0x3402`, then U allocator `operator delete` `0x341F`, then global pointer is assigned zero.
- 2026: `UnregisterFactoryFunc` `0x3302`, then U allocator `operator delete` `0x331F`, then global pointer is assigned zero.

A confirmed teardown ordering is important, but **not evidence that arbitrary Stream instances can survive an experimental external factory removal**; OM is loaded/retained by Adobe as part of native host lifecycle, with native owners controlling object availability.

### Host-owned native value, archive and clone interface

The installed OM.dll explicitly exports `OM_Stream::CloneStream`, `Read`, `Write`, `GetValueEx`, `SetValue` and `CanHaveExpression`. Thus the class is a substantial value-bearing and serializable native Adobe object, not a no-op placeholder.

Our tests check the existence of these exports, the creator/constructor chain, allocator imports, exact virtual table address references, MatchName allocation and teardown order. They **do not exercise archive roundtrip or prove that a foreign subclass can use Adobe's editor/Undo services**.

## Product implications / remaining gaps

The pattern below is a **design reference extracted from first-party code**, not a public API:

```text
Host module startup
  → stable native MatchName in host allocator
  → native C++ derived Stream class Creator callback
  → TDB factory registration
  → registered parent canonical grammar / owner
  → host-rendered/editable and serializable value
  → deterministic host-controlled lifecycle
  → unregister before releasing callback/module/MatchName
```

For ChapeLayer, missing proofs remain: a supported entry point from independently loaded AEX to native registration during acceptable startup state, a foreign `TDB_StreamBase` subclass ABI (including every virtual method contract and host memory allocator), a compatible parent `CanStore`/canonical UILayout, .aep persistence and Undo, Timeline editor, native renderer, unload without dangling host instances, and macOS implementation.

No private Adobe function was called in the real AE process. The existing dangerous disposable AEX is not activated and the requested VM upgrade/install is still paused. `CompNodeAE` and Adobe installations were not modified.

## Reproducible offline verifier

```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\audit_om_native_stream_abi_and_teardown.py"
```

Data:
`datasets/ae-om-native-maskshape-stream-abi-and-teardown-2025-2026.json`.

This is further evidence for the cross-DLL registration model in **F-VECTOR-093**, not a claim that the independently authored ChapeLayer native Stream implementation is complete.
