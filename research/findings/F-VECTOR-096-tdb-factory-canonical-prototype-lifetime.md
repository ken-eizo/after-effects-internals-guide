---
date: 2026-10-14
status: PASS native TDB factory creator/canonical prototype insertion and destruction ordering both AE2025/AE2026; static native machine-code evidence only
evidence: E2-L exact installed TDB.dll original binary x64 PE unwind boundaries, exported C++ symbols, Capstone instruction boundaries and pointer-proven virtual deletion; 2/2 strict repeatable verifier
---
# F-VECTOR-096 — Native TDB factory registration lifetime: two maps, eager prototype, reverse-order unlink and virtual destruction

## New verified architectural result

Registering a true new `TDB_StreamBase` subclass in the host requires more than a callable C++ Creator: the native `TDB_StreamFactory` owns **two distinct internal MatchName-indexed lookup structures**, one for Creator callbacks and one for canonical instances, which are populated **in order** and removed in reverse order.

A strict x64 disassembly validator checks two installed AE versions:

```text
TDB_StreamFactory::RegisterFactoryFunc:
  lock recursive mutex
  search MatchName (duplicate detection)
  insert Creator into factory+0x28 map
  call TDB_StreamFactory::CreateStream           ← eagerly instantiate prototype
  insert canonical prototype into factory+0x38 map
  virtual IsLeaf / GetAsLeaf / IsSeparationLeader
  conditional virtual SetupCanonicalLayout
  unlock

TDB_StreamFactory::UnregisterFactoryFunc:
  call private ...UnregisterFactoryFunc_NullOK(false)
    lock recursive mutex
    find canonical instance by MatchName in factory+0x38
    hold canonical prototype pointer
    remove matching canonical map entry
    remove matching Creator map entry in factory+0x28
    invoke saved prototype's virtual deleting destructor
    unlock
```

These steps are based on machine-code addressing of the factory's `+0x28` and `+0x38` internal members, matched `TDB_MatchName` compare calls, real `CreateStream` export calls, ordered helpers called with the corresponding addresses as RCX, the saved prototype pointer `r12`, explicit null test, `edx=1` and virtual `call qword ptr [rax]` in the success path.

The helper functions are private STL/native internals without an exported semantic name. They are classified as map insertion/removal from observed data-structure traversals and the pointer/count checks, **not from a public documented ABI**. The direct code witness does not prove behavior of every conditional error/exception path.

## Exact verified sites

| Evidence | AE2025 TDB.dll | AE2026 TDB.dll |
| --- | --- | --- |
| Registrar function RVA | `0x27400` | `0x285D0` |
| Creator container offset | `factory + 0x28` | `factory + 0x28` |
| Canonical instance container offset | `factory + 0x38` | `factory + 0x38` |
| Eager `CreateStream` callsite | `0x2757F` | `0x2874B` |
| Unregister canonical-container removal CALL | `0x28D25` | `0x29D65` |
| Unregister Creator-container removal CALL | `0x28DE5` | `0x29E25` |
| Canonical prototype virtual deleting destructor CALL | `0x28E10` | `0x29E4C` |

The public-looking `UnregisterFactoryFunc` export is a small wrapper, passing `false` to the private `UnregisterFactoryFunc_NullOK` method. This method's success path checks removal count and calls the prototype's vtable slot 0 after `mov edx,1`, consistent with the native deleting destructor convention.

## Risk/engineering implications

1. **The Creator callback is installed before canonical construction.** If construction, virtual dispatch or group initialization throws/asserts/crashes, the process may have partially modified the factory. Native exception/unwind logic and all rollback paths have not yet been proven; therefore *never* describe a failed external registration as fully rolled back.
2. Canonical prototype lifetime is owned by the host factory, not merely by a short-lived menu-command stack frame. A plugin must keep C++ Creator pointers, the entire implementation module, dependent allocator and virtual method targets loaded until the registry has removed and destroyed every relevant host-owned Stream.
3. A successful return from `UnregisterFactoryFunc` cannot alone prove there are no surviving project child instances or Undo/history holders referencing the foreign vtable; a full product must separately verify child instance lifetimes, serialization, clone, AE timeline cache, render threads and safe module teardown.
4. The two internal offsets remained equal across these **two installed versions**. This is *not* a supported/portable ABI guarantee, and macOS may differ entirely.
5. Combining F-VECTOR-095 and this finding gives the actual private host sequence needed for future native-group experiments: `register Creator → eagerly instantiate → virtual canonical layout → parent admission → host-own child instances → final unregistration and cleanup`. Parent admission/editor/renderer are still separate unsolved contracts.

## Offline verification

```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_tdb_native_creator_canonical_lifetime.py"
```

Output `datasets/ae-tdb-native-creator-canonical-lifetime-2025-2026.json` with installed original binary SHA256, exact code offsets and limited source classifications. **Both Windows Adobe host versions PASS**.

No third-party TDB subclass or new CNL timeline property was registered. No private Adobe runtime APIs invoked, no Adobe installation modified, and Windows VM construction remains paused per user request. Thus `NOT_DELIVERED_HOST_NATIVE_CUSTOM_STREAM` remains the completion status.
