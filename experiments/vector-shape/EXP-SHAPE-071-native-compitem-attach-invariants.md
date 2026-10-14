---
date: 2026-10-14
status: PASS E2-L two pinned native BEE binaries; no Adobe host execution
---
# EXP-SHAPE-071 — AE2025/2026 native BEE_CompItem attachment object layout and virtual calls

**Question:** Is a native `BEE_Layer*` RTTI cast sufficient to attach a novel foreign class safely, or does native CompItem attachment itself impose further host object invariants?

**Method:** Parse export, import and unwind (.pdata) tables in real installed BEE.dll (2025 and 2026); disassemble the exact `BEE_CompItem::AttachLayerToCompOnly` native function with Capstone. Save all instruction RVAs and raw decorated references. Independently compare pinned SHA-256 and mandatory exact assembly instructions with a fail-closed verifier. No DLL was loaded/executed and no private method was called.

**Verified results:** Both real versions read an internal 32-bit Layer field (`rbx+0x2d8` versus `rbx+0x26c`), make four Layer virtual calls at vtable slot +0x278 with observed integer operands 2/1/5/7, call another Layer virtual method at +0x550 versus +0x560, and conditionally increment a CompItem integer at +0x3c8 versus +0x420. Multiple additional native host calls, temporary-object cleanup and null/error branches are present. The verifier passed AE2025 and AE2026, 2/2.

**Interpretation limit:** This proves attach-time layout and polymorphic behavior assumptions, NOT the names of these unnamed methods, their semantics, foreign-type admission, a new native Layer kind, safe private ABI or actual timeline registration. It is necessary evidence for evaluating any cross-DLL subclass plan; it is not sufficient for implementing one.

**Artifacts:**
- `research/findings/F-VECTOR-071-native-compitem-attach-host-invariants.md`
- `datasets/ae-bee-compitem-attach-owner-contract-2025-2026.json`
- `experiments/vector-shape/probe-src/tools/audit_compitem_native_attach_contract.py`
- `experiments/vector-shape/probe-src/tools/verify_compitem_native_attach_contract.py`

**Safety:** Only offline reads of pinned PE files. No AE launch, in-host registration, modifications to Adobe DLLs, experimental unsafe AEX or CompNodeAE changes.
