---
status: architecture-reference
last_verified: 2026-10-15
evidence: E2-L + E0-H + H
versions: Windows AE2025 / AE2026 private TDB; Adobe public SDK25.6
---

# TDB_StreamFactory — Registration, Canonical Instances and Lifetime

This is an internal **Adobe runtime implementation reference**. The names below are exported C++ ABI identifiers observed in `TDB.dll`, *not declarations supplied by the public After Effects 25.6 SDK*. This chapter explains the complete registration lifecycle and its failure modes without implying a supported external plugin registration contract.

## Type registry and parameters

```cpp
// Internal concept reconstructed from exported C++ symbols.
// NOT an SDK header, NOT a compilable or supported third-party declaration.
TDB_StreamFactory::RegisterFactoryFunc(
    TDB_MatchName const& key,
    std::function<TDB_StreamBase*(/* host-specific arguments */)> creator,
    bool setup_canonical /* semantic inference; exact ABI/version required */
);
```

The signature above is **illustrative**. It intentionally omits compiler-specific arguments and object ownership details; do not use this pseudocode to call private functions.

| API/type | Purpose | Ownership | Evidence | SDK status |
| --- | --- | --- | --- | --- |
| `TDB_MatchName` | Type key | Native MatchName object | F-VECTOR-093/094 | Private |
| `Get_AE_StreamFactory` | Host-wide Stream factory getter | Host | F-VECTOR-008/010/093 | Private |
| `TDB_ScRegisterStreams::Register` | Internal scoped native registrar | Provider wrapper | F-VECTOR-054/084/093 | Private |
| `TDB_StreamFactory::RegisterFactoryFunc` | MatchName → native Creator + eager canonical instance | Factory | F-VECTOR-095/096 | Private |
| `TDB_StreamFactory::CreateStream` | Instantiate concrete native Stream | Caller/factory context | F-VECTOR-095 | Private |
| `TDB_StreamFactory::GetCanonicalInstance` | Access already registered canonical prototype | Factory (do not assume caller owns) | F-VECTOR-084/095 | Private |
| `TDB_ScRegisterStreams::UnregisterAll` | Scoped unregister at provider teardown | Scoped registrar | F-VECTOR-093 | Private |
| `TDB_StreamFactory::UnregisterFactoryFunc` | Remove type's canonical instance, callback, destroy prototype | Factory | F-VECTOR-094/096 | Private |

## Startup entrypoints

The Adobe first-party modules register at native host startup. `OM.dll` demonstrates direct `RegisterFactoryFunc` with `OM_Stream::Create` and `ADBE Mask Shape`. `FLT.dll` uses `TDB_ScRegisterStreams::Register` for native Effect/Mask groups. `BEE.dll` registers families of Layers, Paint, Text and Vectors. See [Application startup to shutdown](startup-to-shutdown.md).

`Required/Paint.aex` *does not* directly import TDB or implement PaintAtom's native class Creator by itself; its `Paint Suite` bridge is separate (F-VECTOR-080/081).

## Registration algorithm and internal containers

The successful Windows x64 code path is:

```text
RegisterFactoryFunc(key, creator, options)
  lock host recursive mutex
  if key already exists:
      take native duplicate/failure branch
  creator_registry[key] = creator              // factory +0x28
  canonical = CreateStream(key, host arguments) // happens immediately
  canonical_registry[key] = canonical          // factory +0x38
  is_leaf = canonical->IsLeaf()                 // vtable +0x58
  if leaf: evaluate GetAsLeaf() / IsSeparationLeader()
  if requested: canonical->SetupCanonicalLayout() // vtable +0x150
  unlock
```

The private offsets `+0x28` and `+0x38` are pinned to **installed 2025/2026 builds**, not promised fields. The precise error/duplicate return codes and all exception handlers have not yet been established; this intentionally stops short of speculative implementation code.

| Call or slot | AE2025 RVA | AE2026 RVA | Meaning |
| --- | ---: | ---: | --- |
| `RegisterFactoryFunc` | `0x27400` | `0x285D0` | Registry entry |
| Eager `CreateStream` call | `0x2757F` | `0x2874B` | Canonical construction |
| `IsLeaf`, virtual `+0x58` | `0x275BA` | `0x28786` | Leaf/group dispatch |
| `IsSeparationLeader`, virtual `+0x298` | `0x275D3` | `0x2879F` | Optional dimension state |
| `SetupCanonicalLayout`, virtual `+0x150` | `0x275FF` | `0x287CB` | Schema setup |

These are *callsite RVAs*, not documented public function offsets. See `datasets/ae-tdb-eager-canonical-vtable-2025-2026.json` and F-VECTOR-095.

## Why it immediately invokes virtual methods

A registered native class is validated/initialized through a **real instance**. This is why a dummy callback is not a safe factory-registration test: a wrong C++ calling convention, partial object, bad host allocator, invalid vtable or uninitialized group fields can fail **inside registration**. A separately compiled mock host does not prove correct Adobe ownership.

For a native Group, `SetupCanonicalLayout` further invokes `FillInCanonicalUILayout`. See [Canonical groups and admission](canonical-groups-admission.md).

## Creating document Stream instances

Factory registration constructs a canonical prototype, but \`TDB_StreamFactory::CreateStream\` is also used separately to create real native child instances. On the observed success path, it copies a native \`std::function\` Creator under the factory mutex, unlocks, then **invokes the callback after the unlock**; it may initialize default leaf key data and conditionally decanonicalize a group subtree. [Native instance construction](stream-instance-creation.md) documents the independent entry and flags.

A real group then needs a separate [Indexed insertion](indexed-group-insertion.md) operation that enforces the parent's \`CanStore\` and establishes its parent/StreamIDPath caches. A saved project reconstructs children from serialized MatchNames through the same Creator and insertion machinery; see [StreamGroup Read / Write](document-stream-serialization.md). These lifecycle steps are independently verified in F-VECTOR-097/098, without a foreign plugin being executed.

### Creator availability and project reload

Serialized group members are reconstructed using the same registered Creator factory. Across both installed Windows builds, Named group loaders pass missing-type report flag zero, while Indexed group loaders pass one. The factory conditionally calls Adobe U.dll error-reporting, but actual recovery/UX is still unknown (F-VECTOR-100). See [Archive Type Compatibility](archive-type-compatibility.md).

## Unregistration and native object ownership

On the observed successful path:

```text
UnregisterFactoryFunc(key)
  → ...UnregisterFactoryFunc_NullOK(false)
     → acquire host mutex
     → find and remove canonical entry, factory+0x38
     → find and remove Creator callback, factory+0x28
     → call retained canonical prototype virtual deleting destructor
     → unlock
```

| Callsite | AE2025 | AE2026 |
| --- | --- | --- |
| Remove canonical map entry | `0x28D25` | `0x29D65` |
| Remove Creator entry | `0x28DE5` | `0x29E25` |
| Virtual deleting destructor | `0x28E10` | `0x29E4C` |

`OM_Death` first unregisters its `ADBE Mask Shape` class and then frees and nulls its separately allocated `TDB_MatchName`. `FLT.dll` uses scoped `UnregisterAll`. See F-VECTOR-093/094/096 and `datasets/ae-tdb-native-creator-canonical-lifetime-2025-2026.json`.

## Error paths and unload contract

**Not verified:** the complete registration failure rollback, duplicate-MatchName behavior in all paths, exception safety when the Creator itself throws, destruction of independently created project Stream instances, Undo references, outstanding render requests or macOS ABI. A foreign module must not unload while any host object retains its Creator, virtual function or code pointer.

Do **not** attempt private factory calls in a regular AE installation, or interpret a built disposable `CNLPrivateTDBDisposable.aex` as a safe product: it borrows an Adobe-built leaf Creator and cannot prove custom group registration.

## Reproduction (read-only)

```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_tdb_eager_canonical_vtable_dispatch.py"
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_tdb_native_creator_canonical_lifetime.py"
```

Sources: F-VECTOR-008, 080, 084, 093–096. Implementation presence is **E2-L**; no official public `TDB_StreamFactory` registrar was found in the 70 inspected SDK25.6 headers (F-VECTOR-088).
