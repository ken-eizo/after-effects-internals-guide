---
status: internal-implementation-reference
last_verified: 2026-10-15
evidence: E2-L + E0-H + H
versions: Original Windows AE2025 and AE2026 MEE.dll / PLUG.dll; macOS private ABI unverified
---

# General Plug-in Setdown — MEE Callback, PLUG Unprep and Registration Lifetime

When After Effects shuts down a third-party **general plug-in**, the internal native machinery distinguishes the plug-in's callback invocation, its prepared routine state, its registration record and the lifetime of its loaded module. A callback completing successfully does **not** by itself establish that the plug-in DLL has been unloaded, nor that all foreign objects are gone.

This chapter documents the **Adobe first-party implementation of general plug-in shutdown**. The `MEE` and `PLUG` functions below are private C++ entrypoints, not a recommended or supported external calling convention.

## Lifecycle layers and native responsibilities

| Internal operation | Observed responsibility | What it does not establish |
| --- | --- | --- |
| `MEE::SetdownGeneralPlugins` (exported `SetdownGeneralPlugins`) | Iterate registered general plug-in records, call callback if set, conditionally unprep routine | No guarantee of OS-level DLL unload |
| `PLUG_UnprepRoutine` | Lock PLUG routine state, invoke descriptor method and update preparation data | Not equivalent to every routine descriptor being unregistered |
| `PLUG_UnregisterRoutine` | Registered routine descriptor removal | Does not inherently prove external Stream objects are gone |
| `MEE_AEGP_Terminate` | Uses distinct PLUG Unprep and Unregister calls | Not synonymous with general Setdown callback |
| `PLUG_Death` | Module-level PLUG subsystem teardown that also calls Unregister | Runs at different aelib lifecycle stage |

## SetdownGeneralPlugins: per-record iteration

In both AE2025 and AE2026, the `MEE.dll` implementation traverses native plug-in records at a stride of **`0xB8` (184 bytes)**.

The inspected offsets, normalized to the beginning of one native record, are:

| Native record member | Offset | Meaning supported by machine code |
| --- | ---: | --- |
| Callback context / refcon | `+0x10` | Passed as the callback's first argument |
| Callback function pointer | `+0x58` | Called only when non-null |
| Prepared-state flag | `+0xB0` | Checked and set to zero before conditional Unprep |
| Next record | `+0xB8` | Native iteration stride |

```text
SetdownGeneralPlugins:
  for each general plug-in record:
      if callback != null:
          callback(refcon)

      if prepared_flag != 0:
          prepared_flag = 0
          PLUG_UnprepRoutine(record's routine descriptor)

  clean up internal record backing state
```

The 2025 compiler represents the iterator as `record + 0xB0` in the inner loop; 2026 represents the record base directly. Both resolve to the same layout above. This is an **E2-L static success-path reconstruction**, not a complete guarantee about callback exceptions or every possible record.

### Exact callback / Unprep sites

| Operation | AE2025 `MEE.dll` RVA | AE2026 RVA |
| --- | ---: | ---: |
| `SetdownGeneralPlugins` | `0x54960` | `0x49CE0` |
| Indirect callback invocation | `0x549A0` | `0x49D1D` |
| Prepared-state check | `0x549A2` | `0x49D1F` |
| Flag clear | `0x549AE` | `0x49D2B` |
| Imported `PLUG_UnprepRoutine` call | `0x549B1` | `0x49D32` |

The callback pointer is invoked by `call rax`, not a TDB Stream Creator callback and not a native property-class registration call.

## PLUG_UnprepRoutine and actual module unloading

The native `PLUG_UnprepRoutine` function:

1. acquires PLUG state under a recursive mutex;
2. locates the relevant routine descriptor;
3. calls an **indirect descriptor virtual method** at vtable `+0x30`;
4. performs additional internal bookkeeping; and
5. releases the mutex.

| Native site | AE2025 `PLUG.dll` RVA | AE2026 RVA |
| --- | ---: | ---: |
| `PLUG_UnprepRoutine` | `0x8B70` | `0x1CDD0` |
| First recursive mutex lock | `0x8BA9` | `0x1CDFE` |
| Descriptor vtable `+0x30` call | `0x8C23` | `0x1CE78` |
| Final observed mutex unlock | `0x8D5A` | `0x1CFAF` |

Neither inspected Unprep function makes a **direct import call** to `FreeLibrary`. This is a *bounded observation*, not a proof that the actual plug-in module stays loaded. PLUG can delegate through descriptor methods, private helpers or module wrappers. The installed AE2026 PLUG DLL contains `FreeLibrary` imports **elsewhere**.

Do not assume a private C++ object's vtable has become invalid solely because an AEGP setdown callback returned; conversely, do not assume the loaded-image lifetime protects a foreign Stream during all of its eventual native Undo/history destruction.

## AEGP Terminate and PLUG Death are distinct from Setdown

`MEE_AEGP_Terminate` contains a separate path that calls `PLUG_UnprepRoutine` and then `PLUG_UnregisterRoutine`. `PLUG_Death`, called from `aelib.dll`'s Stage **14**, contains its own `PLUG_UnregisterRoutine` call.

| Native function / callsite | AE2025 RVA | AE2026 RVA |
| --- | ---: | ---: |
| `MEE_AEGP_Terminate` | `0x4EB60` | `0x43EF0` |
| Its Unprep call | `0x4EC4D` | `0x43FCD` |
| Its Unregister call | `0x4EDD9` | `0x44143` |
| `PLUG_Death` | `0x4F30` | `0x19970` |
| Its native Unregister call | `0x50AF` | `0x19AEF` |

In the normal full **descending native shutdown**, `aelib`'s Stage **32** invokes `MEE_AEGP_Death → MEE_AEGP_Terminate → SetdownGeneralPlugins`; after that the first-party Stream type providers shut down in Stages **29 BEE → 27 FLT → 25 OM → 15 TDB**, followed by `PLUG_Death` in Stage **14**. See [aelib Native Module Lifecycle](../../architecture/native-module-startup-shutdown.md).

All these are conditional native host execution branches; the static order does not prove that a specific third-party plug-in or type has been initialized or that every DLL has been unloaded.

## A foreign native Stream provider has an additional lifetime problem

The first-party `BEE_DoRemoveIndexedGroupTask` creates a reciprocal `BEE_DoAddToIndexedStreamGroupTask`, which can hold a detached `TDB_StreamBase` pointer. When the owning Add task's destructor later runs, it may invoke the **concrete Stream's own virtual deleting destructor**. The native Project's UndoContext can own such task records until project close or history deletion.

Therefore, safe external native type support would need **all** of these independent guarantees: registered Creator/prototype, approved parent policy, project instance ownership, Native Undo task retention, asynchronous/render consumers, and the ability to keep code and allocators available until every reference is gone. The public AEGP SDK provides none of these as a general foreign `TDB_StreamBase`-class admission contract.

**No independent `CNL:` Stream type has been registered or saved/reopened in the actual host in this experiment.**

## Validation and sources

Strict offline verifier:

```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_mee_plug_setdown_unprep_unregister.py"
```

Result: **PASS in both original installed Windows AE2025 and 2026**. It pins the original MEE and PLUG DLL SHA-256 digests and verifies native callbacks, field offsets, IAT calls, lock and descriptor call edges. The original Adobe DLLs were read only; no private Adobe runtime function was executed.

- Finding: F-VECTOR-107.
- Data: `datasets/ae-mee-plug-general-plugin-setdown-unprep-unregister-2025-2026.json`.
- Background: [Native Module Lifecycle](../../architecture/native-module-startup-shutdown.md), [AEGP Runtime](index.md), [BEE Undo Task Lifecycle](../../state-model/native-property-system/undo-task-lifecycle.md), [Native Stream Factory Lifetime](../../state-model/native-property-system/factory-registration-lifetime.md).
