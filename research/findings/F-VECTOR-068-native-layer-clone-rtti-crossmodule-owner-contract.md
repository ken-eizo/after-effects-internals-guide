---
date: 2026-10-14
status: PASS native AE2025/2026 exact BEE clone-to-CompItem path; external native owner UNPROVEN
evidence: E2-L pinned native x64 real BEE.dll and TDB.dll import and MSVC RTTI TypeDescriptors
---
# F-VECTOR-068 — BEE_Layer::CloneAndAttach requires a TDB clone and BEE_Layer RTTI identity

F-VECTOR-067 found a generic-looking BEE_Layer::CloneAndAttach path that attaches an existing Layer pointer to the native CompItem, seemingly bypassing the closed LayerType integer constructor switch. This pathway is now more precisely understood from its real executable code and imports:

- AE2025: BEE_Layer::CloneAndAttach RVA 0x2E20E0 first calls imported TDB.dll virtual method TDB_StreamBase::Clone at 0x2E20FE. The returned TDB Stream object passes through MSVC __RTDynamicCast with source RTTI type .?AVTDB_StreamBase@@ and target .?AVBEE_Layer@@, then the cloned typed Layer attaches to BEE_CompItem at 0x2E218F.
- AE2026: BEE_Layer::CloneAndAttach RVA 0x2EB090 calls the same imported TDB_StreamBase::Clone at 0x2EB0A3, performs the same MSVC RTTI cast from TDB_StreamBase to BEE_Layer, then attaches at 0x2EB140.
- These RTTI names were read from real native TypeDescriptors referenced through RIP-relative LEA instructions, and the imported clone was resolved through actual DLL import tables, not inferred from symbols alone.

This is a true C++ type and lifetime boundary. Merely creating a custom TDB MatchName, a standalone typed CNL node, or an unrelated C++ object cannot satisfy it. A foreign class would need authentic native TDB cloning, an actual RTTI-compatible BEE_Layer identity and lifecycle, and an already instantiated source, in addition to the CompItem's state bookkeeping.

The exact path DOES NOT establish that Adobe permits foreign subclass construction, registration, native Timeline editing, or serialization. The full BEE/Adobe SDK does not publish this as a stable AEGP API. Native AE host calls were not made.

Evidence:
- experiments/vector-shape/probe-src/tools/trace_native_clone_and_attach_virtual_contract.py
- experiments/vector-shape/probe-src/tools/resolve_native_layer_clone_attach_imports.py
- experiments/vector-shape/probe-src/tools/verify_clone_attach_tdb_rtti_crossmodule.py
- datasets/ae-bee-clone-attach-native-virtual-contract-2025-2026.json
- datasets/ae-bee-clone-attach-crossmodule-rtti-2025-2026.json

Safe compiled cross-DLL C++ experiment: EXP-SHAPE-069. No Adobe DLL modification or CompNodeAE edit.
