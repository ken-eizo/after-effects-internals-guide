---
date: 2026-10-12
status: PASS pinned BEE2025/26 offline native Shape command/owner boundary
evidence: E2-L PE + Capstone disassembly + verified command table
---

# EXP-SHAPE-056 — Shape Undo command + native Comp attachment + 32-byte dispatch registry

This experiment continues the native Shape Layer internals investigation beyond the 183 typed TDB registrations and Canonical Contents reconstruction. It does NOT claim a foreign CNL class is installed.

**Validated twice** from installed AE 2025 / 2026 on-disk BEE binaries:

- `BEE_CmdNewVectorLayer` enters the common worker `0x667610 / 0x682F90`, which calls `BEE_StartGroup`, `BEE_DoCommand` and `BEE_EndGroup` in that sequence.
- Native type-4 Shape creation and `BEE_CompItem::AttachLayerToCompOnly` appear in the same real function `0x3A7CA0 / 0x3B4110`, including comp ownership, layer ID/state and position handling.
- The public/private distinction: `BEE_DoCommand` has an internal common executor `0x64EB80 / 0x669840`, whose command table contains fixed 32-byte records. AE2025 table `0xFEC250`, 155 decoded slots / 149 occupied pointer pairs; AE2026 `0x104C530`, 160 slots / 155 occupied.
- The table's +0x08/+0x10 pointers are validated and the native executable dereferences/calls a function pointer. No table item directly contains the native NewVectorLayer address, and no direct matching handler body found.
- The remaining command-table-to-specific-creation-helper **indirect edge is not yet proven**; `BEE_Layer::CreateLayerFromType` remains a fixed stock layer-type switch. No third-party owner registration claimed.

Artifacts archived alongside the actual verifier `verify_shape_native_undo_command_table.py` and separate extractors. Cross-version verifier PASS. All actions were read-only native disk PE analysis; Adobe AEX private registrar untouched, AE GUI not operated, `CompNodeAE` left alone, Phase F not started.

Findings: `research/findings/F-VECTOR-056-native-shape-layer-command-registration-dispatch-undo.md`.
