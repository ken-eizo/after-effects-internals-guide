---
date: 2026-10-12
status: PASS-static-cross-version-owner-attachment-undo-and-command-entry
evidence: E2-L exact installed AE2025/AE2026 native BEE.dll x64 code, PE table values
---

# F-VECTOR-056 — Native Shape creation/Comp attachment, Undo command transaction and 32-byte command table

## Objective and scope

The objective is not a CPU raster Effect or an editable opaque ARB property; it is the actual native Adobe Shape/Contents/Path implementation that might support a new CNL-owned type with Timeline hierarchy, Pen/Selection, native undo and BEE_VectorArt. F-VECTOR-054 reconstructed its typed Contents creation and F-VECTOR-055 distinguished a detached TDB-created BEE_VectorLayer from a comp-owned Shape Layer. This experiment traces the **native command/ownership control plane** without executing any undocumented API.

## 1. Real new Shape command has a host Undo transaction

Native exported `BEE_CmdNewVectorLayer` forwards into a shared layer command worker (2025 RVA `0x667610`, 2026 RVA `0x682F90`). The actual code calls, in order:

```text
BEE_StartGroup(BEE_UndoContext&, descriptive_string, flags)
    → BEE_DoCommand(BEE_Project*, command_id, BEE_CommandInfo*)
    → BEE_EndGroup(BEE_UndoContext&)
```

The transaction entry code is verified in both installed versions. **Opening and closing an Undo group is not proof that a foreign stream can participate in it.** The command's native class creator and its selection, cache and serialization transactions are more restrictive.

## 2. Native type-4 Shape ownership is more than setting a parent pointer

Both versions contain a bounded native helper function that:

- Calls `BEE_Layer::CreateLayerFromType` with literal type **4** (a stock Shape Layer), passing its actual `BEE_CompItem*`.
- Conditionally calls `BEE_CompItem::AttachLayerToCompOnly(layer, position, boolean)` later in **that same compiled function**.
- Supplies actual positioning and a boolean, not just a raw `SetParentComp` pointer assignment.

Verified RVA:
- 2025: helper `0x3A7CA0`; Create at `0x3A7CE4`; Attach at `0x3A7DD8`.
- 2026: helper `0x3B4110`; Create at `0x3B4154`; Attach at `0x3B4236`.

The attach routine itself performs multiple internal calls, including checking the layer's native ID, writing placement and state, consulting virtual layer capabilities, calling `SetParentComp` and further initialization. The `AttachLayerToCompAndLayerParamsOnly` wrapper performs additional work and calls `AttachLayerToCompOnly`. Therefore an isolated third-party call to `SetParentComp` is **not a valid implementation of native timeline admission**.

This is the native ownership transaction corresponding to the detached versus comp-owned constructor boundary in F-VECTOR-055.

## 3. Actual BEE_DoCommand fixed-stride command registry identified

We disassembled both real `BEE_DoCommand` overloads. Each transfers to a common internal executor: 2025 RVA `0x64EB80`, 2026 RVA `0x669840`. The executor:

- Range-checks an integer command index.
- Computes its table address using `shl ...,5`, a **32-byte stride**.
- Retrieves native callback pointers at **+0x08 and +0x10** and rejects entries missing either.
- Has a reachable `call rdx` after loading the function pointer from `[entry+0x08]`.

The table is a real 32-byte-entry PE data structure, **not** a proposed SDK interface:

| Detail | AE2025 | AE2026 |
| --- | --- | --- |
| Native table RVA | `0xFEC250` | `0x104C530` |
| Decoded entries | 155 | 160 |
| Entries with both callback pointers populated | 149 | 155 |
| Index boundary immediate in code | `0x99` | `0x9E` |
| Callback fields | `+0x08`, `+0x10` | `+0x08`, `+0x10` |

The table structures are validated against PE bytes and indexed function pointers. **Neither the table cells nor their immediately invoked function bodies contains a direct reference to `BEE_CmdNewVectorLayer`** in this direct-call audit. This is a negative result only for direct links; indirect command routing, callbacks, and separately installed Adobe handlers remain to be resolved.

**Do not modify these memory tables from a plug-in.** Their exact fields, lifecycle, ownership, startup registration and teardown are not a documented ABI. A raw function pointer in a PE image is not a public plugin extension point.

## 4. The remaining missing edge is explicit

We have verified separately:

```text
UI: BEE_CmdNewVectorLayer
    → shared native command worker
      → BEE_StartGroup
      → BEE_DoCommand → command table / callbacks
      → BEE_EndGroup
```

and:

```text
Native layer creation code:
    → BEE_Layer::CreateLayerFromType(4, comp)
    → BEE_CompItem::AttachLayerToCompOnly(layer, placement, flags)
    → owner/ID/state/virtual-method bookkeeping
```

The exact **indirect handler edge from `BEE_DoCommand` into the type-4 creation helper remains unproven**. Avoid treating these two individually verified chains as one completely proven dynamic call graph. New independent CNL layer kind registration is still **not** proven; the built-in layer kind switch remains closed. Host Pen, Undo for a foreign data class, native Contents insertion and BEE VectorArt evaluator/AGM also remain open.

No in-host private functions called, no binaries patched, no AE GUI operated and no `CompNodeAE` files modified. Phase F remains paused awaiting the user's separate design approval.

## Reproduce

Archival Python scripts are in `experiments/vector-shape/probe-src/tools/` and derived read-only PE receipts in `datasets/ae-bee-shape-command-*.json`. Verifier `verify_shape_native_undo_command_table.py` checks both installed versions. See EXP-SHAPE-056.
