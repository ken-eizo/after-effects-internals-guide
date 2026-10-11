---
status: strongly-supported-static
last_verified: 2026-10-11
evidence: E2-L + H
versions: AE2025 and AE2026 installed BEE.dll
---
# F-VECTOR-007 — Native VectorLayer initialization includes ArtCache and geometry setup; selection uses a host selection iterator

Offline disassembly of exports `BEE_VectorLayer::BEE_VectorLayer(TDB_MatchName const*, TDB_StreamFactory*, BEE_CompItem*, unsigned char, bool)`, `BEE_CmdNewVectorLayer` and `BEE_GetSelectedShapePathsVec` across 2025/2026 revealed:

- The VectorLayer's constructor invokes the C++ layer/base-side construction machinery, `BEE_VectorLayer::InitArtCache()`, and `BEE_AVLayer::Set3DGeometryType(int)` in both builds. The **immediate resolved constructor call differs**: 2025 resolves to `BEE_AVLayer::BEE_AVLayer(...)`, 2026 resolves to `BEE_MaterialOverrideLayer::BEE_MaterialOverrideLayer(...)`. This is evidence of an implementation/initialization change, **not** proof of a changed class inheritance layout without RTTI/vtable corroboration.
- `BEE_GetSelectedShapePathsVec(BEE_Layer*, std::vector<TDB_StreamIDPath>*)` invokes `BEE_LayerSelSpec::Clear()` and `BEE_SelIterate(...)` in both builds. This links the shape-path selection helper to the **host layer-selection iterator** at the static call-target level; it does not identify the native Pen-tool handle registration mechanism.
- `BEE_CmdNewVectorLayer(BEE_Project*, BEE_CommandInfo*)` is exported in both builds. Its bounded export-region disassembly contains an unresolved indirect call. That is not enough to determine layer allocation ownership or allow third-party layer registration.
- `BEE_VectorLayer::RegisterStreams` contains stream operation/command callbacks and sits in a central multi-layer registration sequence, but the exact factory registry storage is still unlocated.

The practical implication is a *native* shape replacement must satisfy not just path geometry, but scene/layer ownership, art-cache setup, geometry mode, host selection iteration, property identity, and the native renderer. A local arbitrary C++ object created with a private constructor and no host registration would not satisfy this.

**Negative boundary:** no function examined here has been invoked from a third-party plug-in, and no private ABI entrypoint has passed a controlled host test. The discovered symbols are research leads only.

Raw data: `datasets/ae-vector-layer-construction-2025-2026.json` and `datasets/ae-vector-selection-origin-xrefs-2025-2026.json`. No Adobe binary redistributed.
