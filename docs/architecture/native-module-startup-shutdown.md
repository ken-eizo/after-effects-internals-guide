---
status: internal-implementation-reference
last_verified: 2026-10-15
evidence: E2-L + H
versions: Windows After Effects 2025 / 2026 original Adobe aelib.dll
---

# aelib Native Module Lifecycle — Forward Initialization and Reverse Shutdown

`aelib.dll` coordinates startup and shutdown of several first-party After Effects native subsystems. In the two inspected Windows releases, this is implemented using **numbered lifecycle stages** and two separate internal iterators, rather than one unconditionally executed list of functions.

This page concerns **host internals**, not public SDK callbacks. A third-party effect's setup or setdown is not equivalent to invoking `TDB_Birth`, `BEE_Birth` or their module-level private teardown functions.

## Internal interfaces

| Private class/function | Purpose | Public SDK status |
| --- | --- | --- |
| `aelib::InitIterator::operator++` | Dispatch currently selected subsystem initialization and advance stage | Internal only |
| `aelib::TerminateIterator::operator--` | Dispatch one subsystem teardown and decrement stage | Internal only |
| `aelib::Terminate()` | Drive termination of stages recorded as initialized | Internal only |
| `aelib::TerminateIterator::backward` | Loop backward toward a target stage | Internal only |
| `BEE_Birth` / `BEE_Death` | First-party BEE module lifecycle, including registered native Layer/AV/Text/Vector Stream classes | Internal only |
| `TDB_Birth` / `TDB_Death` | Native stream/state base infrastructure lifecycle | Internal only |
| `OM_Birth` / `OM_Death` | First-party Mask Shape and OM Stream infrastructure | Internal only |
| `FLT_Birth` / `FLT_Death` | First-party filter/effect Stream classes and host infrastructure | Internal only |

These names were verified against actual exported C++ symbols and x64 imports in installed Adobe binaries, not reconstructed into callable third-party headers.

## Stage-based native initialization

The native `InitIterator` uses a **35-entry switch jump table** indexed by its current stage counter. On each successful traversal step it advances toward the next stage.

The following stage IDs and direct imported-module calls are the same in AE 2025 and AE 2026:

| Initialization stage | Native call | Why it matters for properties |
| ---: | --- | --- |
| 15 | `TDB_Birth` | Establishes the underlying native TDB stream subsystem |
| 25 | `OM_Birth` | Registers/initializes OM-owned Mask Shape stream machinery |
| 27 | `FLT_Birth` | Initializes first-party filter/effect stream groups |
| 29 | `BEE_Birth` | Initializes BEE's native layer groups including Vector/Text |

```text
aelib InitIterator (advances stage)
  Stage 15 → TDB_Birth
  Stage 25 → OM_Birth
  Stage 27 → FLT_Birth
  Stage 29 → BEE_Birth
```

This ordering is an observation of the host's internal initialization stage machine, **not a promise that third-party plug-ins are permitted to add custom stage IDs**. Other stages also exist; this table shows the property-related subset.

### Verified stage callsite locations

| Module Birth call | AE2025 aelib RVA | AE2026 aelib RVA |
| --- | ---: | ---: |
| TDB | `0x6DEA3` | `0x70283` |
| OM | `0x6E05D` | `0x70444` |
| FLT | `0x6E08B` | `0x70472` |
| BEE | `0x6E272` | `0x70647` |

## Reverse native teardown

The **`TerminateIterator` subtracts one** from its current one-based stage N to select a jump-table case at N-1, executes that stage's native shutdown callback, and stores N-1 as its next state.

Both the exported `aelib::Terminate()` and `TerminateIterator::backward` drive this dispatcher with a backward loop. In a full, normally initialized shutdown, relevant steps execute in this order:

```text
aelib TerminateIterator (descends from initialized stage)
  Stage 32 → MEE_AEGP_Death
              MEE_AEGP_Terminate
              SetdownGeneralPlugins
  Stage 29 → BEE_Death
  Stage 27 → FLT_Death
  Stage 25 → OM_Death
  Stage 15 → TDB_Death
```

This establishes a meaningful first-party contract: native BEE/FLT/OM tear down while their TDB base subsystem's teardown stage has **not yet been dispatched** along that normal reverse path.

**Important:** this does not prove when every concrete TDB Stream object is deleted, or that its registration map is guaranteed usable from all threads until Stage 15; internal module lifecycle and native object lifetime are not synonyms.

### Native teardown call locations

| Teardown operation | Stage | AE2025 aelib RVA | AE2026 RVA |
| --- | ---: | ---: | ---: |
| `MEE_AEGP_Death` | 32 | Verified in stage-32 dispatch | Verified in stage-32 dispatch |
| `MEE_AEGP_Terminate` | 32 | Verified in stage-32 dispatch | Verified in stage-32 dispatch |
| `SetdownGeneralPlugins` | 32 | `0x6EFC3` | `0x71353` |
| `BEE_Death` | 29 | `0x6EF56` | `0x712E6` |
| `FLT_Death` | 27 | `0x6EF40` | `0x712D0` |
| `OM_Death` | 25 | `0x6EF24` | `0x712B4` |
| `TDB_Death` | 15 | `0x6EEC0` | `0x71250` |

A critical reading rule: **RVA numerical order is not execution order**. The actual stage selector and decrementing iterator establish the order. A static scan that simply sorts the call instructions in `aelib.dll` would give a misleading result.

## General plug-in setdown versus DLL unloading

At Stage 32, the imported `MEE_AEGP_Death`, `MEE_AEGP_Terminate` and `SetdownGeneralPlugins` routines are called **before** the Stage-29 `BEE_Death` case would be visited in a complete reverse shutdown.

What this **proves**: a normal reverse shutdown requests general plugin setdown at a numerically earlier termination step than the built-in BEE module teardown.

What this **does not prove**: that every third-party DLL has already been unloaded, that its callbacks are inaccessible, or that the host's document/Undo/history tasks no longer hold foreign object pointers.

This boundary is especially important for a proposed foreign `TDB_StreamBase` provider. The existing first-party `BEE_DoAddToIndexedStreamGroupTask` can conditionally **own a detached noncanonical Stream and call its virtual deleting destructor during history disposal** (F-VECTOR-101/102). A provider cannot assume that factory unregistration, a plugin setdown callback and destruction of all live Stream objects are the same event.

## What Stage 32 actually performs

The `MEE.dll` native `SetdownGeneralPlugins` implementation has now been independently verified (F-VECTOR-107). It iterates 184-byte general-plugin records, calls each non-null callback with the stored refcon and—when the record is marked prepared—clears that flag and calls `PLUG_UnprepRoutine`. The separate `MEE_AEGP_Terminate` method contains a `PLUG_UnregisterRoutine` path, while `PLUG_Death` runs at **Stage 14** on a full reverse shutdown.

This does **not** identify the actual OS-level unload moment. PLUG Unprep can invoke an indirect routine-descriptor method and the PLUG module may manage DLL images through other helper code. See [General Plug-in Setdown and Routine Lifetime](../host-integration/aegp/general-plugin-setdown-lifetime.md) for the concrete versioned native calls.

## Initialization failure and partial host shutdown

The stage machine is conditional on the current initialized state and call-site guards. The existence of a Stage-29 `BEE_Death` branch does **not** imply it runs after a partially failed initialization that never reached stage 29. The `Terminate()` routine checks host state and selects different paths depending on mode/initialization conditions.

The present static evidence does not establish every exception/unwind branch, every asynchronous service's quiescence, or the exact native Project-close point relative to module-level teardown. It also does not establish a supported general third-party Stream registration interface.

## Cross-version code and evidence

| Private aelib method/data | AE2025 RVA | AE2026 RVA |
| --- | ---: | ---: |
| `InitIterator::operator++` | `0x6D9B0` | `0x6FD80` |
| Initialization jump table | `0x6ED34` | `0x710C4` |
| `TerminateIterator::operator--` | `0x6EDC0` | `0x71150` |
| Termination jump table | `0x6F1DC` | `0x71570` |
| `aelib::Terminate` | `0x83220` | `0x86B60` |
| `TerminateIterator::backward` | `0x186D0` | `0x15E70` |

All code locations belong to the exact SHA-256-pinned original installed Adobe `aelib.dll` files. Treat them as **version-specific research addresses**, not SDK imports to use in your software.

The strict read-only verifier is `experiments/vector-shape/probe-src/tools/verify_aelib_native_staged_init_reverse_teardown.py`. Both installed Windows releases **PASS**. Machine-readable data: `datasets/ae-aelib-native-staged-birth-reverse-death-2025-2026.json`.

Research: F-VECTOR-073/074 (BEE stream class startup/teardown), F-VECTOR-093–096 (OM/FLT/BEE native factory registration), F-VECTOR-099–104 (native Undo task and Project lifetime), F-VECTOR-106 (aelib stage and ordering proof).

Related references: [Native Property Startup to Shutdown](../state-model/native-property-system/startup-to-shutdown.md), [Native Factory Registration and Lifetime](../state-model/native-property-system/factory-registration-lifetime.md), [BEE Project UndoContext](../state-model/native-property-system/project-undo-context-lifecycle.md) and [Subsystem Boundaries](subsystem-boundaries.md).
