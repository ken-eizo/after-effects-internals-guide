---
status: pass-static-cross-version
last_verified: 2026-10-12
evidence: E2-L
---

# EXP-SHAPE-037 — Shared native Mask/Vector reset and generic stream write/Undo

The goal is to locate a real native editable stream writing substrate without generating Masks or native Shape Layers as a substitute. In AE2025 and AE2026, BEE_CmdResetMaskShape and BEE_CmdResetVectorShape directly call one identical native private helper per version: RVAs 0x67a350 and 0x696380. Their shared implementation calls BEE_StartGroup/BEE_EndGroup and BEE_DoCommand, and invokes the generic BEE_CmdSetStreamFPVPlus four times.

A second independent native code trace confirms that BEE_CmdSetStreamFPVPlus(BEE_Layer*, TDB_StreamIDPath const&,...) calls BEE_StreamTypeHasStream, BEE_GetStreamWithSpec, BEE_StartGroupNamed, BEE_SetStreamFPV, BEE_DoCommand, and BEE_EndGroup in both installed builds.

Cross-check script verify_generic_vector_edit_contract.py PASS for both versions against actual PE code disassembly datasets. Source scripts and complete code evidence are mirrored under AEIG experiments/vector-shape/probe-src/tools and datasets. See F-VECTOR-038.

Scope: This proves a shared generic value-setting/Undo path. A plugin-owned TDB stream, native Pen drag callback and direct custom VectorArt renderer are NOT yet supported by the evidence. No private host code called.
