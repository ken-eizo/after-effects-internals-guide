---
date: 2026-10-14
status: PASS real Adobe native BEE object and vtable ABI mismatch AE2025 and AE2026
---
# EXP-SHAPE-070 — Per-version native BEE_Layer memory/vtable drift proven

Real BEE_Layer::CloneAndAttach compiled code retains this in RBP and then accesses CompItem pointer from [RBP+0x2B8] for AE2025 but [RBP+0x260] in AE2026. A separate same-role flag query calls vtable [RDX+0x2A8] for AE2025 but [RDX+0x2B8] for AE2026.

The caller method's equivalent Comp attachment callsites are 0x2E218F (AE2025) and 0x2EB140 (AE2026). The SHA256-pinned verifier checks each exact instruction and relative order in both installed BEE.dll files, PASS twice.

This is concrete evidence that member layout and vtable indices differ. Unsafe hard-coded external native BEE subclass injection cannot be treated as portable and must never execute without complete version-specific ABI guarantees. F-VECTOR-070 records full details. No host private call was made.
