---
date: 2026-10-15
status: PASS original AE2025/AE2026 native MEE/PLUG DLL strict SHA-pinned Setdown/Unprep/Unregister boundary; no proof of actual OS-level module unload
evidence: E2-L PE named C++ exports, x64 bounded instruction dispatch, per-plugin record layout, original cross-DLL RIP-relative IAT and guarded callback; no private runtime calls
---

# F-VECTOR-107 — General plug-in setdown is a callback followed by Unprep, not equivalent to Stream or module destruction

## Why this finding matters

F-VECTOR-106 proved the real `aelib.dll` staged module lifecycle: general AEGP/plugin setdown belongs to **Stage 32**, and first-party native BEE/TDB type registration is torn down at later reversed **Stages 29 and 15**. However, merely naming `SetdownGeneralPlugins` did not establish what a general plugin's shutdown actually does.

This experiment examines **two independent first-party subsystems**: `MEE.dll`, which loops over registered general plugins, and `PLUG.dll`, which maintains loaded/prepared routine descriptors.

The success-path machine-code results match in AE2025 and AE2026.

## Concrete per-plugin Setdown loop

`MEE.dll!SetdownGeneralPlugins` processes a vector of native plugin records with **stride `0xB8` bytes** and executes:

```text
for each registered MEE general-plugin record:
  if record.callback[+0x58] is nonnull:
      callback(record.refcon[+0x10])
  if record.prepared_flag[+0xB0] != 0:
      record.prepared_flag = 0
      PLUG.dll!PLUG_UnprepRoutine(record.routine_descriptor)
```

The relative member offsets are the same in both builds. AE2025 optimizes its loop using a pointer to `record +0xB0`; AE2026 directly uses the record base. Both normalize to the same structure.

The host does **not** unconditionally invoke Unprep for every record: it is gated by the prepared flag. The callback also may be null. The current static inspection does not qualify what every third-party callback does when invoked.

### Code evidence

| `MEE.dll` native operation | AE2025 RVA | AE2026 RVA |
| --- | ---: | ---: |
| `SetdownGeneralPlugins` | `0x54960` | `0x49CE0` |
| Callback `call rax` | `0x549A0` | `0x49D1D` |
| Check prepared flag | `0x549A2` | `0x49D1F` |
| Clear prepared flag | `0x549AE` | `0x49D2B` |
| Cross-DLL `PLUG_UnprepRoutine` call | `0x549B1` | `0x49D32` |

## What PLUG_UnprepRoutine does and does not prove

The native `PLUG_UnprepRoutine` implementation obtains a recursive mutex, looks up and processes the PLUG routine description, executes **an indirect descriptor virtual method at `+0x30`**, updates internal bookkeeping and releases the lock.

| `PLUG.dll` native evidence | AE2025 | AE2026 |
| --- | --- | --- |
| `PLUG_UnprepRoutine` RVA | `0x8B70` | `0x1CDD0` |
| First recursive mutex lock | `0x8BA9` | `0x1CDFE` |
| Descriptor virtual `+0x30` call | `0x8C23` | `0x1CE78` |
| Final mutex unlock | `0x8D5A` | `0x1CFAF` |
| Direct `FreeLibrary` import call in this method | **None** | **None** |

The absence of a direct `FreeLibrary` call in this bounded function does **not** prove module retention. Its indirect descriptor callback, private helper calls and destruction of any released owner objects can have additional effects.

Indeed, the AE2026 `PLUG.dll` imports the Windows `FreeLibrary` API elsewhere in the DLL, but those calls occur in other native helpers, not directly in this specific `PLUG_UnprepRoutine` body. AE2025 may delegate module loading/unloading to a different wrapper such as `ASL::Module`.

## Unprep, Unregister and native module Death are different operations

The `MEE_AEGP_Terminate` native function has its own calls to both **`PLUG_UnprepRoutine`** and **`PLUG_UnregisterRoutine`**, in that order on the inspected path.

Separately, the native **`PLUG_Death`** also calls `PLUG_UnregisterRoutine` while cleaning up the PLUG subsystem. The separate `aelib` stage machine places `PLUG_Death` at **Stage 14**, which follows `TDB_Death` Stage 15 on the normal reverse shutdown path.

| Native operation | AE2025 RVA | AE2026 RVA |
| --- | ---: | ---: |
| `MEE_AEGP_Terminate` | `0x4EB60` | `0x43EF0` |
| Its `PLUG_UnprepRoutine` call | `0x4EC4D` | `0x43FCD` |
| Its `PLUG_UnregisterRoutine` call | `0x4EDD9` | `0x44143` |
| `PLUG_Death` | `0x4F30` | `0x19970` |
| `PLUG_Death → PLUG_UnregisterRoutine` | `0x50AF` | `0x19AEF` |

These observations prove **distinct native operations and static call edges**, not that each operation always executes on a single plugin descriptor or that it unconditionally succeeds.

## How it changes the foreign native-type lifecycle problem

A third-party provider would have to distinguish at least four events:

1. General plugin's **Setdown callback** is invoked.
2. Its PLUG routine descriptor is **Unprepped**.
3. A PLUG routine descriptor is **Unregistered**.
4. The owning PE/DLL image is **actually unloaded by the OS** when its lifetime management permits.

**These four events are not interchangeable.** The examined `MEE` and `PLUG` functions do not establish that all four happen at the same stage or in every host execution mode.

The concrete first-party `BEE_DoAddToIndexedStreamGroupTask` can conditionally retain an actual native `TDB_StreamBase` subclass and later invoke its virtual deleting destructor when Undo history is cleared (F-VECTOR-101–103). This means a hypothetical foreign type provider must maintain valid code/allocator/vtables for that complete lifetime; returning from an AEGP setdown hook is not proof of safe unload.

**No third-party native Stream type was registered**, and no AEP save/reopen or OS DLL unload was executed. Complete indirect module release, Mac ABI, error handling and code unloading conditions remain open.

## Strict reproduction

```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_mee_plug_setdown_unprep_unregister.py"
```

SHA-pinned original MEE.dll and PLUG.dll read-only analysis returns **PASS for both Windows AE2025 and 2026**. Receipt: `datasets/ae-mee-plug-general-plugin-setdown-unprep-unregister-2025-2026.json`.

Companion feature page: `docs/host-integration/aegp/general-plugin-setdown-lifetime.md`; module-level stage ordering F-VECTOR-106 and `docs/architecture/native-module-startup-shutdown.md`. No private Adobe function was executed or imported into an external AEX.
