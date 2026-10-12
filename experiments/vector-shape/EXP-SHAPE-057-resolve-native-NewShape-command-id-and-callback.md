---
date: 2026-10-12
status: PASS native exact command ID -> table -> callbacks; native handler-to-owner link still open
evidence: E2-L real installed BEE.dll AE2025/26 static x64 code
---

# EXP-SHAPE-057 — Match New Shape Layer command ID to actual native BEE command handlers

**Decisive progress:** the real `BEE_CmdNewVectorLayer` C++ wrapper passes **command ID 101 (2025), 106 (2026)** to the common `BEE_StartGroup → BEE_DoCommand → BEE_EndGroup` worker. The BEE command table has 32-byte entries; the corresponding cells at `0xFECEF0 / 0x104D270` contain real callbacks `+8: 0x646BD0 / 0x660C10` and `+16: 0x646C30 / 0x660C70`. The execution handlers call `0x544470 / 0x563290`.

This is verified twice by `verify_newshape_native_command_table_exact_id.py` against the exact installed PE SHA256, published table records, native wrapper instructions and callback disassembly. **PASS both versions**.

A separate bounded static direct-call graph test out to six edges (`trace_newshape_command_handler_to_comp_creation.py`) did **not** reach the native `CreateLayerFromType(4) + AttachLayerToCompOnly` helper (72 visited functions for 2025, 78 for 2026). This is an explicit unresolved indirect/virtual dispatch boundary, not evidence that the regular command cannot create a Shape Layer at runtime.

**Not implemented:** independent CNL native BEE layer type, host Timeline Contents, Pen-native editing, BEE_VectorArt. No AE host private invocation, no Adobe DLL patching, no `CompNodeAE` edit, no Phase F integration. Details in F-VECTOR-057.
