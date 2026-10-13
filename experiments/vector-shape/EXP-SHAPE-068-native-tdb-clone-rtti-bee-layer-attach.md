---
date: 2026-10-14
status: PASS E2-L pinned compiled Adobe native x64 clone/RTTI path in AE2025 and AE2026
---
# EXP-SHAPE-068 — Native clone-to-CompItem is actual TDB clone plus MSVC RTTI BEE Layer cast

Two independently installed BEE binaries prove the common function BEE_Layer::CloneAndAttach:
(1) calls a genuine imported TDB_StreamBase::Clone in TDB.dll;
(2) executes __RTDynamicCast from the actual RTTI TypeDescriptor for TDB_StreamBase to that for BEE_Layer;
(3) then passes the clone to BEE_CompItem::AttachLayerToCompAndLayerParamsOnly.

AE2025 clone entry RVA 0x2E20E0, imported clone call 0x2E20FE, attach site 0x2E218F.
AE2026 clone entry RVA 0x2EB090, imported clone call 0x2EB0A3, attach site 0x2EB140.

Offline machine-code and PE import verifier PASS for both versions. This defeats the shortcut idea that an arbitrary pointer can be attached to Comp; it does NOT prove the admission of a new custom native BEE_Layer class. See F-VECTOR-068.
