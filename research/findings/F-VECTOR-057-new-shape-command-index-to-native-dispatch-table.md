---
date: 2026-10-12
status: PASS-exact-native-NewVector-command-id-to-private-BEE-table-2025-2026
evidence: E2-L pinned BEE.dll real x64 instructions, four-QWORD table entries and callback bodies
---

# F-VECTOR-057 — Exact native New Shape Layer command ID → BEE command table → execution callback

## New fundamental connection beyond F-VECTOR-056

F-VECTOR-056 reconstructed a real 32-byte BEE command table and separately verified (1) `BEE_CmdNewVectorLayer`'s Undo transaction and (2) the actual type-4 Shape Layer creation and CompItem attachment helper. The last indirect command routing edge was unproven.

Now the **exact integer argument of `BEE_CmdNewVectorLayer`** has been recovered from actual machine code in AE 2025 and AE 2026. Both versions use a thin native wrapper:

```assembly
mov r9, rdx          ; original CommandInfo argument
mov r8d, 0x306       ; common descriptive/resource value
mov edx, <command-id>
jmp common_layer_command_worker
```

The IDs differ between versions:

| Native value | AE2025 | AE2026 |
| --- | --- | --- |
| `BEE_CmdNewVectorLayer` entry RVA | `0x65CDD0` | `0x6783E0` |
| **BEE command integer ID** | **`0x65` (101)** | **`0x6A` (106)** |
| Shared worker RVA | `0x667610` | `0x682F90` |
| Resource/group identifier | `0x306` | `0x306` |
| BEE command table base RVA | `0xFEC250` | `0x104C530` |
| **Actual command-record RVA** | **`0xFECEF0`** | **`0x104D270`** |
| Pointer `+0x08` | `0x646BD0` | `0x660C10` |
| Pointer `+0x10` | `0x646C30` | `0x660C70` |

The record identity is **computed from the original data** as `table_base + command_id * 32` and verified against actual PE bytes; no guessed pointer values or memory calls.

The `+0x08` callback body calls native `0x5443E0` / `0x563200`. The `+0x10` execution callback body calls native `0x544470` / `0x563290`. Both handlers were independently disassembled from the exact pinned BEE versions.

Critically, the generic `BEE_DoCommand` code independently range-checks the ID, shifts the index left by five bits (32-byte entries) and loads `[entry + 0x08]` for an indirect native callback. Therefore this is not an unrelated same-number coincidence: the wrapper's command index leads to a real occupied table row in the very same native command executor.

## What remains unresolved despite mapping the record

The recorded `+0x10` execution callback is NOT itself `BEE_Layer::CreateLayerFromType` or the known helper that executes `CreateLayerFromType(4) → BEE_CompItem::AttachLayerToCompOnly`. A six-level static direct-call traversal starting at each `+0x10` handler explored **72 candidate functions in 2025** and **78 in 2026**, without reaching the type-4 create+attach helper.

This indicates an unresolved branch involving an indirect/virtual callback, data-driven command state, or a separate routed layer-creation subsystem. It does **not** prove the Shape Layer command never reaches that helper at runtime. The exact handler-to-owner insertion edge remains a research requirement and an important blocker for a third-party CNL native owner.

The private command table's memory layout is **not a supported plug-in ABI**. Do not patch the PE image, write into the command records, or invoke private BEE/TDB functions in AE on the user's behalf. The 2025/2026 command IDs are even different, showing how risky hard-coded assumptions would be.

The mission continues to be an **independent true native Shape/Contents owner**, not an ordinary effect, existing Shape Layer carrier or mask trick. The CNL Effect's demonstrated save/reopen does not imply native Timeline editability or BEE_VectorArt. External native BEE owner registration, safe factory teardown, Pen target, Undo transactions for CNL authored streams and rendering remain unproven.

## Reproduction

- `experiments/vector-shape/probe-src/tools/trace_exact_new_shape_command_table_handlers.py`
- `experiments/vector-shape/probe-src/tools/trace_newshape_command_handler_to_comp_creation.py`
- `experiments/vector-shape/probe-src/tools/verify_newshape_native_command_table_exact_id.py`
- `datasets/ae-bee-shape-command-exact-id-handlers-2025-2026.json`
- `datasets/ae-bee-shape-command-execution-callgraph-2025-2026.json`
- `datasets/ae-bee-shape-command-exact-id-verified-2025-2026.json`

No Adobe DLL was modified, loaded by the test, or called. No CNL plugin was installed, no private factory registration was executed, and `D:/Developer/CompNodeAE` was not touched.
