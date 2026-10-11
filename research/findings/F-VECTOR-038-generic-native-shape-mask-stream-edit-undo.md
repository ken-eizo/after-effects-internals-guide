---
status: strongly-supported-static-cross-version
last_verified: 2026-10-12
evidence: E2-L
versions: exact installed AE2025 and AE2026 BEE.dll
---

# F-VECTOR-038 — Native Mask and Vector Shape reset converge on a common generic stream value writer and Undo

## Why this matters

A new independently owned, editable plugin vector **does not necessarily need its own separate value-write/Undo algorithm** if its native source is a genuine TDB_StreamIDPath under a legal BEE_Layer owner. This study goes beyond matching symbol names: it follows the actual machine-code call graph in both installed After Effects versions. The result is a reusable, owner-generic native stream editing substrate — but not yet native Pen input for externally owned paths.

## Direct verified entrypoints

`BEE_CmdResetMaskShape(BEE_Layer*,...)` and `BEE_CmdResetVectorShape(BEE_Layer*,TDB_StreamIDPath const&,...)` both call the SAME unexported helper:

| Version | Shared helper RVA |
| --- | --- |
| AE2025 | `0x67a350` |
| AE2026 | `0x696380` |

The helper's .pdata bounded code (AE2025 region 0x67a350-0x67a8db) directly calls, in its various branches, the following:

- `BEE_StartGroup` and `BEE_EndGroup`: bracket host undo group processing.
- `BEE_CmdSetStreamFPVPlus`: called **four times** in each version.
- `BEE_DoCommand`: is called.
- `BEE_IsMaskStreamPath`, `BEE_GetMaskIndexFromPath` and `BEE_MaskStreamIDPath` constructors: there are mask-specific conditional side effects, rather than pretending Mask and Vector implementations are completely identical.

Separately, the actual generic `BEE_CmdSetStreamFPVPlus(BEE_Layer*,TDB_StreamIDPath const&,...)` code in both versions calls:

1. `BEE_StreamTypeHasStream`
2. `BEE_GetStreamWithSpec`
3. `BEE_StartGroupNamed`
4. `BEE_SetStreamFPV`
5. `BEE_DoCommand`
6. `BEE_EndGroup`

These are direct CALL targets recovered by x64 disassembly, not speculative names. Original definition declares `BEE_Layer*`, not `BEE_VectorLayer*`. A same-function generic write and Undo endpoint therefore serves both shape and mask reset, even though concrete selection/type gates and mask metadata vary.

## Potential capability if owner attachment becomes possible

The promising technical separation is **authored stream ownership vs a general stream write transaction**. If a genuinely plugin-owned TDB group can be given an acceptable identity, source value and stream type under a legal BEE_Layer owner, some native value-setting, timeline updates and Undo may already be reusable. This reduces the need for a parallel fake property-edit/Undo system.

The first concrete implementation target should be an independently owned genuine TDB property on a non-Shape/non-Mask carrier, resolving by `BEE_GetStreamWithSpec` and persisting its stream ID and value under host Undo. Merely calling `BEE_CmdSetStreamFPVPlus` by a guessed signature is NOT a valid experiment before object type, allocator, threading, rollback and host lifetime contracts are known.

The remaining essential gates are still: an independent host-accepted Contents owner; native path hit-test/Pen drag identity and writeback; BEE_VectorArt and the production RG renderer; serialization/Undo round-trip. A reset command being generic is NOT proof that ordinary Pen gestures will reach plugin-owned Bezier handles or that generic BEE_Layer renders vectors.

## Evidence and reproducibility

- `datasets/ae-native-generic-stream-write-contract-2025-2026.json`
- `datasets/ae-shared-mask-vector-reset-helper-2025-2026.json`
- `datasets/ae-shared-native-edit-contract-verified-2025-2026.json`
- `experiments/vector-shape/probe-src/tools/audit_native_generic_stream_write_contract.py`
- `experiments/vector-shape/probe-src/tools/trace_shared_shape_mask_edit_helper.py`
- `experiments/vector-shape/probe-src/tools/verify_generic_vector_edit_contract.py`

Verification checks called function identity on both complete pinned native PE binaries, including four calls to the generic setter and all six native setter dependencies. No Adobe private ABI executed in host; source-level discovery only. F-VECTOR-017 and F-VECTOR-021 provide related native editable stream identity and indexed child substrate.
