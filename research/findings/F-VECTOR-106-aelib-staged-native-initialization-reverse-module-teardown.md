---
date: 2026-10-15
status: PASS strict original installed AE2025/AE2026 aelib native x64 initialization and reverse teardown stage mapping
evidence: E2-L SHA-pinned original aelib.dll export/IAT, switch tables, iterator machine-code and cross-module calls; no private host runtime invocation
---

# F-VECTOR-106 — Native aelib initialization is forward, module teardown is reverse; AEGP setdown precedes BEE native type unregistration

## Discovery

Adobe's `aelib.dll` drives **both** the first-party startup and teardown of its native subsystem modules through a numbered internal state machine, not the visual order of functions in a binary.

In both installed Windows After Effects 2025 and 2026:

- `aelib::InitIterator::operator++` dispatches the native module initialization for the iterator's current numbered stage and advances its state.
- `aelib::TerminateIterator::operator--` accepts the current **one-based** stage N, selects a 35-entry branch-table target using `N - 1`, executes that stage's native teardown and stores **N - 1** back to its iterator.
- `aelib::Terminate()` has a loop repeatedly invoking the latter until the tracked initialized stage reaches zero, subject to its native initialization/mode preconditions.
- A second `TerminateIterator::backward` loop is independently observed and delegates to the same decrementing dispatcher.

Therefore, when the full host-level termination route visits all initialized stages, the four modules relevant to native Stream type registration are reached **in reverse of their initialization order**.

| Native subsystem | Startup stage | Original birth API | Teardown stage | Original death API |
| --- | ---: | --- | ---: | --- |
| TDB | 15 | `TDB_Birth` | 15 | `TDB_Death` |
| OM | 25 | `OM_Birth` | 25 | `OM_Death` |
| FLT | 27 | `FLT_Birth` | 27 | `FLT_Death` |
| BEE | 29 | `BEE_Birth` | 29 | `BEE_Death` |

**Normal forward native initialization**: TDB → OM → FLT → BEE.

**Normal reverse native teardown**: BEE → FLT → OM → TDB.

Each of the eight calls is resolved using the actual `aelib` switch table, an instruction-boundary decoded RIP-relative DLL import and the original binary. In other words, **the stage number**, **the actual import call**, and **the iteration direction** agree independently across both versions.

### Another important lifecycle boundary: general AEGP/plugin setdown

Native termination **stage 32**, executed **before stage 29** on the normal reverse traversal, performs:

```text
MEE_AEGP_Death()
 -> MEE_AEGP_Terminate()
 -> SetdownGeneralPlugins()
```

These are three ordered calls inside the same selected switch branch, observed in both original AE versions:

| Native host callsite (aelib.dll RVA) | AE2025 | AE2026 |
| --- | ---: | ---: |
| `SetdownGeneralPlugins` | `0x6EFC3` | `0x71353` |
| `BEE_Death` | `0x6EF56` | `0x712E6` |
| `FLT_Death` | `0x6EF40` | `0x712D0` |
| `OM_Death` | `0x6EF24` | `0x712B4` |
| `TDB_Death` | `0x6EEC0` | `0x71250` |

The **numeric program addresses do not imply time order**. It is the switch-table *case index* and the `TerminateIterator` decrement that establish the staged order. This distinction prevents an easy but serious reverse-engineering error.

## Relation to native Stream factory lifetime and Undo tasks

Prior research establishes a separate and conditional chain:

```text
Project deletion
 -> BEE_Project::~BEE_Project
 -> BEE_UndoContext::~BEE_UndoContext
 -> native task deleting destructor
 -> eligible Add inverse task's owned Stream deleting destructor
```

(F-VECTOR-099–104). This new finding instead qualifies the host **module-level** lifecycle around that chain:

```text
aelib native TerminateIterator (descending)
  Stage 32: MEE_AEGP_Death, MEE_AEGP_Terminate, SetdownGeneralPlugins
  Stage 29: BEE_Death       [BEE built-in native class unregister]
  Stage 27: FLT_Death       [native FLT stream classes unregister]
  Stage 25: OM_Death        [native OM Mask Shape class unregister]
  Stage 15: TDB_Death       [TDB host base registry shutdown]
```

**Critical limitation:** an ordinary plugin's *setdown callback being requested* does **not** prove its DLL image has been unloaded at stage 32. Likewise this diagram does not prove when all Project objects, queued Undo tasks or render callbacks are destroyed relative to `aelib::Terminate()`, that the host always traverses every stage under partial startup/failure, nor that any outside plugin can register a foreign `TDB_StreamBase`. In particular, type registration, canonical prototype destruction and general plugin setdown are **separate kinds of lifetime event**.

Consequently, simply unregistering a foreign factory or returning from a plugin's setdown hook cannot be treated as proof that the host holds no callback or vtable into its code.

## Exact reproducible code anchors

| Machine-code evidence | AE2025 aelib RVA | AE2026 RVA |
| --- | ---: | ---: |
| InitIterator dispatch function | `0x6D9B0` | `0x6FD80` |
| Initialization 35-stage switch table | `0x6ED34` | `0x710C4` |
| TerminateIterator dispatch function | `0x6EDC0` | `0x71150` |
| Termination 35-stage switch table | `0x6F1DC` | `0x71570` |
| `aelib::Terminate` orchestrator | `0x83220` | `0x86B60` |
| `TerminateIterator::backward` loop | `0x186D0` | `0x15E70` |
| Init TDB (stage 15) | `0x6DEA3` | `0x70283` |
| Init OM (stage 25) | `0x6E05D` | `0x70444` |
| Init FLT (stage 27) | `0x6E08B` | `0x70472` |
| Init BEE (stage 29) | `0x6E272` | `0x70647` |

The original DLL SHA-256 and all sites are recorded in the generated JSON dataset.

## Why this matters for a third-party native provider

An independently authored ChapeLayer Stream type needs a **guaranteed admission and unregister contract**, not merely a working function pointer. An external plugin could register a Creator while the host's TDB registry exists, but would still need to meet native parent `CanStore`, type-specific C++ vtable, project serialization, Undo task retention, renderer callback and actual module image lifetime requirements.

This module order is necessary architectural context, but **not a proof of a supported Adobe extension point or a successful foreign native Stream registration**.

## Reproduction

```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_aelib_native_staged_init_reverse_teardown.py"
```

Independent verifier results: **AE2025 PASS / AE2026 PASS**. It checks exact SHA-pinned original Adobe `aelib.dll` files, real switch tables, exports, actual imported calls and `aelib::Terminate` backward traversal. No host process was opened; no private Adobe function was called, no user project or binary was patched.

Receipt: `datasets/ae-aelib-native-staged-birth-reverse-death-2025-2026.json`.

Feature documentation: `docs/architecture/native-module-startup-shutdown.md`. Earlier related evidence: F-VECTOR-073–075, 093–096, 099–104.
