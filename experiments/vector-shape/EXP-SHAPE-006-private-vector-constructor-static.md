---
status: observed-static-only
last_verified: 2026-10-11
evidence: E2-L
versions: AE2025 and AE2026
---
# EXP-SHAPE-006 — Native shape layer creation and selection function boundaries

Read-only code: `D:\Developer\ShapeLayerAE\tools\trace_vector_layer_creation.py`. It parses version-specific `dumpbin /exports`, finds `BEE_CmdNewVectorLayer`, `BEE_VectorLayer` constructor, `BEE_GetSelectedShapePathsVec`, and `RegisterStreams`, then disassembles bounded function-entry windows via Capstone. Direct call destinations are resolved against the **same version** of BEE exports. A call through an import/virtual table remains unresolved and is not interpreted as a missing operation.

Key observations: VectorLayer constructor calls `InitArtCache` and `Set3DGeometryType` in both versions; 2025 immediate constructor parent-related call resolves to `BEE_AVLayer`, 2026 to `BEE_MaterialOverrideLayer`. Selected Shape Paths enumeration links to `BEE_SelIterate` and `BEE_LayerSelSpec::Clear` in both versions. `BEE_CmdNewVectorLayer` is present but private and has only an unresolved indirect call in the scanned window.

Inputs: pinned installed AE2025 `BEE.dll` SHA-256 `98c682351e30f38cb7021eaa142f5ec473aea92885e14915d87c157cda971730`; AE2026 `5fd8d318456228b9fd2a6733a5758f6b84206b7a8effcba5202957cd27ac680e`.

Output: `datasets/ae-vector-layer-construction-2025-2026.json`. This does **not** provide full function boundaries, source type definitions, a complete control-flow graph, or AE native extension authorization.
